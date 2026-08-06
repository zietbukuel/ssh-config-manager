#!/usr/bin/env python3
"""
ssh-config-manager — Modern CLI tool to manage SSH config entries with safety,
validation, and Include directive support.

Features:
- Add, list, search, show, edit, delete SSH config entries
- Automatic backup before writes with rotation
- Hostname/port/identity file validation
- Include directive support (config.d/ directories)
- Shell completion (argcomplete + manual completion command)
- Rich formatted output
- Atomic file operations for safety
"""

from __future__ import annotations

import argparse
import ipaddress
import logging
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from sshconf import empty_ssh_config_file, read_ssh_config  # type: ignore

try:
    import argcomplete  # type: ignore
    ARGC_COMPLETE_AVAILABLE = True
except ImportError:
    ARGC_COMPLETE_AVAILABLE = False

# Initialize Rich console
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# SSH config paths - respect environment variables
DEFAULT_SSH_DIR = Path(os.environ.get("SSH_DIR", Path.home() / ".ssh"))
DEFAULT_SSH_CONFIG_PATH = Path(os.environ.get("SSH_CONFIG", DEFAULT_SSH_DIR / "config"))
DEFAULT_BACKUP_DIR = DEFAULT_SSH_DIR / "backups"
DEFAULT_INCLUDE_DIR = DEFAULT_SSH_DIR / "config.d"

# Validation constants
MAX_PORT = 65535
MIN_PORT = 1
MAX_BACKUPS = 10  # Maximum number of backups to keep
HOSTNAME_REGEX = re.compile(
    r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$'
)
IPV4_REGEX = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')


class ConfigField(Enum):
    """Enumeration of valid SSH config fields."""
    HOSTNAME = "hostname"
    USER = "user"
    PORT = "port"
    IDENTITYFILE = "identityfile"


class SSHConfigError(Exception):
    """Base exception for SSH config manager errors."""
    pass


class HostNotFoundError(SSHConfigError):
    """Raised when a host is not found in the config."""
    pass


class ValidationError(SSHConfigError):
    """Raised when validation fails."""
    pass


class FileOperationError(SSHConfigError):
    """Raised when file operations fail."""
    pass


class SSHConfigManager:
    """Manages SSH config file operations with safety and validation."""

    def __init__(self, config_path: Path = DEFAULT_SSH_CONFIG_PATH):
        self.config_path = config_path
        self.ssh_dir = config_path.parent
        self.backup_dir = self.ssh_dir / "backups"
        self.include_dir = self.ssh_dir / "config.d"
        # Create directories with proper permissions (only if they don't exist)
        for directory in [self.ssh_dir, self.backup_dir, self.include_dir]:
            if not directory.exists():
                directory.mkdir(mode=0o700, parents=True)
            else:
                # Ensure existing directories have correct permissions
                try:
                    current_mode = directory.stat().st_mode & 0o777
                    if current_mode != 0o700:
                        directory.chmod(0o700)
                        logger.debug(f"Fixed permissions on {directory}")
                except OSError as e:
                    logger.warning(f"Could not fix permissions on {directory}: {e}")

    def _rotate_backups(self) -> None:
        """Remove old backups keeping only the most recent MAX_BACKUPS."""
        try:
            if not self.backup_dir.exists():
                return
            
            backups = sorted(
                self.backup_dir.glob("config.backup.*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            for old_backup in backups[MAX_BACKUPS:]:
                try:
                    old_backup.unlink()
                    logger.info(f"Rotated out old backup: {old_backup}")
                except OSError as e:
                    logger.warning(f"Failed to remove old backup {old_backup}: {e}")
        except OSError as e:
            logger.warning(f"Failed to rotate backups: {e}")

    def _create_backup(self) -> Path | None:
        """Create a timestamped backup of the SSH config file using atomic operations."""
        if not self.config_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"config.backup.{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            # Use atomic copy with temporary file
            with tempfile.NamedTemporaryFile(
                dir=self.backup_dir,
                delete=False,
                mode='wb',
                prefix='.tmp_backup_'
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_file.write(self.config_path.read_bytes())
                tmp_path.chmod(0o600)
            
            # Atomic rename to final backup name
            tmp_path.rename(backup_path)
            console.print(f"[dim]Backup created: {backup_path}[/dim]")
            
            # Rotate old backups
            self._rotate_backups()
            
            return backup_path
        except OSError as e:
            logger.error(f"Failed to create backup: {e}")
            raise FileOperationError(f"Backup creation failed: {e}") from e

    def _atomic_write(self, content: str) -> None:
        """Write content to config file atomically using temp file + rename."""
        try:
            # Create temp file in same directory for atomic rename
            with tempfile.NamedTemporaryFile(
                dir=self.config_path.parent,
                delete=False,
                mode='w',
                prefix='.tmp_ssh_config_'
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_file.write(content)
                tmp_path.chmod(0o600)
            
            # Atomic rename
            tmp_path.rename(self.config_path)
            logger.debug(f"Successfully wrote config to {self.config_path}")
        except OSError as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals() and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            logger.error(f"Failed to write config: {e}")
            raise FileOperationError(f"Config write failed: {e}") from e

    def load_config(self) -> Any:
        """Load SSH config, creating empty if missing."""
        try:
            if not self.config_path.exists():
                return empty_ssh_config_file()
            return read_ssh_config(str(self.config_path))
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise FileOperationError(f"Failed to load config: {e}") from e

    def save_config(self, config: Any) -> None:
        """Save config with automatic backup using atomic operations."""
        try:
            self._create_backup()
            # sshconf's write method expects a file path, not a file object or StringIO
            # Write to temp file in the same directory, then use atomic rename
            import tempfile as tmp
            with tmp.NamedTemporaryFile(
                dir=self.config_path.parent,
                delete=False,
                mode='w',
                prefix='.tmp_ssh_config_',
                suffix='.tmp'
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
            
            # Write config to the temp file path
            config.write(str(tmp_path))
            tmp_path.chmod(0o600)
            
            # Atomic rename to final destination
            tmp_path.rename(self.config_path)
            logger.debug(f"Successfully wrote config to {self.config_path}")
        except FileOperationError:
            raise
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals() and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            logger.error(f"Failed to save config: {e}")
            raise FileOperationError(f"Config save failed: {e}") from e

    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """Validate hostname or IP address using proper IP validation."""
        if not hostname:
            return False
        
        # Try IPv4 validation
        if IPV4_REGEX.match(hostname):
            parts = hostname.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        
        # Try IPv6 validation using ipaddress module (handles all valid formats)
        try:
            ipaddress.IPv6Address(hostname)
            return True
        except ipaddress.AddressValueError:
            pass
        
        # Fall back to hostname regex validation
        return bool(HOSTNAME_REGEX.match(hostname))

    @staticmethod
    def validate_port(port: int) -> bool:
        """Validate port number."""
        return MIN_PORT <= port <= MAX_PORT

    @staticmethod
    def validate_identity_file(path: str) -> bool:
        """Validate identity file exists and is readable."""
        expanded = Path(path).expanduser()
        return expanded.exists() and expanded.is_file()

    @staticmethod
    def validate_host_alias(host: str) -> bool:
        """Validate host alias (no spaces, not empty)."""
        return bool(host and not host.isspace() and ' ' not in host)

    def list_entries(self, verbose: bool = False) -> list[dict]:
        """List all SSH config entries."""
        config = self.load_config()
        hosts = config.hosts()
        entries = []
        for host in hosts:
            host_data = config.host(host)
            entry = {
                "host": host,
                "hostname": host_data.get("hostname", "N/A"),
                "user": host_data.get("user", "N/A"),
                "port": str(host_data.get("port", "N/A")),
            }
            if verbose:
                entry["identityfile"] = host_data.get("identityfile", "N/A")
                # Include any additional fields
                for key, value in host_data.items():
                    if key not in entry:
                        entry[key] = value
            entries.append(entry)
        return entries

    def search_entries(self, query: str) -> list[dict]:
        """Search entries by host alias or hostname."""
        config = self.load_config()
        hosts = config.hosts()
        results = []
        for host in hosts:
            host_data = config.host(host)
            # Check if the query matches the host alias or hostname
            if query.lower() in host.lower() or query.lower() in host_data.get("hostname", "").lower():
                results.append({
                    "host": host,
                    "hostname": host_data.get("hostname", "N/A"),
                    "user": host_data.get("user", "N/A"),
                    "port": str(host_data.get("port", "N/A")),
                })
        return results

    def get_host(self, host: str) -> dict | None:
        """Get detailed info for a specific host."""
        config = self.load_config()
        if host not in config.hosts():
            return None
        host_data = config.host(host)
        return dict(host_data.items())

    def add_entry(self, host: str, hostname: str, user: str, port: int,
                  identity_file: str | None = None) -> None:
        """Add a new SSH config entry with validation."""
        # Validate inputs
        if not self.validate_host_alias(host):
            raise ValidationError("Invalid host alias: must not be empty or contain spaces")
        if not self.validate_hostname(hostname):
            raise ValidationError(f"Invalid hostname/IP: {hostname}")
        if not self.validate_port(port):
            raise ValidationError(f"Port must be between {MIN_PORT} and {MAX_PORT}")
        if identity_file and not self.validate_identity_file(identity_file):
            raise ValidationError(f"Identity file not found or not readable: {identity_file}")

        config = self.load_config()
        if host in config.hosts():
            raise ValueError(f"Host '{host}' already exists")

        params = {"hostname": hostname, "user": user, "port": port}
        if identity_file:
            params["identityfile"] = str(Path(identity_file).expanduser())

        config.add(host, **params)
        self.save_config(config)

    def edit_entry(self, host: str, field: str, value: str) -> None:
        """Edit a specific field of an existing entry."""
        config = self.load_config()
        if host not in config.hosts():
            raise HostNotFoundError(f"Host '{host}' does not exist")

        # Validate field-specific values using enum
        try:
            field_enum = ConfigField(field.lower())
        except ValueError:
            valid_fields = [f.value for f in ConfigField]
            raise ValidationError(f"Invalid field. Valid fields are: {', '.join(valid_fields)}")

        val_to_set: str | int = value
        if field_enum == ConfigField.PORT:
            try:
                port_val = int(value)
                if not self.validate_port(port_val):
                    raise ValidationError(f"Port must be between {MIN_PORT} and {MAX_PORT}")
                val_to_set = port_val
            except ValueError as e:
                if "Port must be between" in str(e):
                    raise
                raise ValidationError("Port must be a valid integer") from e
        elif field_enum == ConfigField.HOSTNAME:
            if not self.validate_hostname(value):
                raise ValidationError(f"Invalid hostname/IP: {value}")
        elif field_enum == ConfigField.IDENTITYFILE:
            if not self.validate_identity_file(value):
                raise ValidationError(f"Identity file not found or not readable: {value}")
            val_to_set = str(Path(value).expanduser())

        config.set(host, **{field_enum.value: val_to_set})
        self.save_config(config)

    def delete_entry(self, host: str, force: bool = False) -> None:
        """Delete an SSH config entry."""
        config = self.load_config()
        if host not in config.hosts():
            raise HostNotFoundError(f"Host '{host}' does not exist")

        config.remove(host)
        self.save_config(config)

    def list_includes(self) -> list[Path]:
        """List all Include directive files."""
        return sorted(self.include_dir.glob("*.conf"))

    def add_include(self, name: str, content: str) -> Path:
        """Add a new Include config file."""
        if not name.endswith(".conf"):
            name += ".conf"
        
        # Sanitize filename to prevent directory traversal
        safe_name = Path(name).name
        if safe_name != name:
            raise ValidationError(f"Invalid include file name: {name}")
        
        include_path = self.include_dir / safe_name
        if include_path.exists():
            raise ValueError(f"Include file '{safe_name}' already exists")
        
        # Write atomically using temp file
        try:
            with tempfile.NamedTemporaryFile(
                dir=self.include_dir,
                delete=False,
                mode='w',
                prefix='.tmp_include_'
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_file.write(content)
                tmp_path.chmod(0o600)
            tmp_path.rename(include_path)
        except OSError as e:
            logger.error(f"Failed to create include file: {e}")
            raise FileOperationError(f"Include file creation failed: {e}") from e
        
        # Update main config to include this directory if not already present
        self._ensure_include_directive()
        return include_path

    def _ensure_include_directive(self) -> None:
        """Ensure main config has Include directive for config.d/"""
        try:
            # Ensure config file exists
            self.config_path.parent.mkdir(mode=0o700, exist_ok=True)
            if not self.config_path.exists():
                self.config_path.write_text("")
                self.config_path.chmod(0o600)

            # Check if Include directive exists (more robust check)
            content = self.config_path.read_text()
            # Look for actual Include directive pattern, not just substring match
            include_pattern = re.compile(r'^\s*Include\s+.*config\.d', re.MULTILINE)
            has_include = bool(include_pattern.search(content))

            if not has_include:
                # Prepend Include directive atomically
                new_content = f"Include config.d/*.conf\n\n{content}"
                self._atomic_write(new_content)
                logger.info("Added Include directive for config.d/")
        except OSError as e:
            logger.error(f"Failed to ensure include directive: {e}")
            raise FileOperationError(f"Failed to update config with Include directive: {e}") from e

    def show_include(self, name: str) -> str | None:
        """Show content of an include file."""
        # Sanitize filename to prevent directory traversal
        safe_name = Path(name).name
        include_path = self.include_dir / safe_name
        if not include_path.exists():
            # Try with .conf extension
            if not safe_name.endswith(".conf"):
                include_path = self.include_dir / f"{safe_name}.conf"
        if include_path.exists():
            return include_path.read_text()
        return None


def print_table(entries: list[dict], title: str, verbose: bool = False) -> None:
    """Print entries as a Rich table."""
    if not entries:
        console.print("[yellow]No SSH entries found.[/yellow]")
        return

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Host", style="cyan", justify="left")
    table.add_column("Hostname", style="green", justify="left")
    table.add_column("User", style="blue", justify="left")
    table.add_column("Port", style="yellow", justify="center")
    if verbose:
        table.add_column("IdentityFile", style="magenta", justify="left")

    for entry in entries:
        row = [entry["host"], entry["hostname"], entry["user"], entry["port"]]
        if verbose:
            row.append(entry.get("identityfile", "N/A"))
        table.add_row(*row)

    console.print(table)


def print_host_details(host: str, host_data: dict) -> None:
    """Print detailed host information."""
    table = Table(title=f"Details for Host '{host}'", show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan", justify="left")
    table.add_column("Value", style="green", justify="left")

    for key, value in sorted(host_data.items()):
        table.add_row(key.capitalize(), str(value))

    console.print(table)


def confirm_deletion(host: str, force: bool = False) -> bool:
    """Prompt user for deletion confirmation unless force is True."""
    if force:
        return True
    response = console.input(f"[bold yellow]Are you sure you want to delete host '{host}'? (y/n): [/]")
    return response.lower() == 'y'


def setup_argcomplete(parser: argparse.ArgumentParser) -> None:
    """Configure argcomplete for shell completion."""
    if not ARGC_COMPLETE_AVAILABLE:
        return

    def host_completer(prefix: str, parsed_args: Any, **kwargs: Any) -> list[str]:
        """Complete host aliases from SSH config."""
        manager = SSHConfigManager()
        try:
            hosts = manager.load_config().hosts()
            return [h for h in hosts if h.startswith(prefix)]
        except Exception:
            return []

    def field_completer(prefix: str, parsed_args: Any, **kwargs: Any) -> list[str]:
        """Complete field names for edit command."""
        fields = ["hostname", "user", "port", "identityfile"]
        return [f for f in fields if f.startswith(prefix)]

    # Add completers to relevant arguments
    for action in parser._actions:
        if action.dest == "host" and action.help and "alias" in action.help:
            action.completer = host_completer  # type: ignore[attr-defined]
        if action.dest == "field":
            action.completer = field_completer  # type: ignore[attr-defined]

    # Register the completion for the main command
    argcomplete.autocomplete(parser)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all commands."""
    parser = argparse.ArgumentParser(
        description="Manage SSH config entries with safety and validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ssh-manager add myserver 192.168.1.100 root 22 --identity-file ~/.ssh/id_ed25519
  ssh-manager list -v
  ssh-manager search myserver
  ssh-manager show myserver
  ssh-manager edit myserver user admin
  ssh-manager delete myserver
  ssh-manager include-list
  ssh-manager include-add myserver "Host myserver\\n  HostName 10.0.0.1"
  ssh-manager include-show myserver
  ssh-manager completion bash
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands", metavar="COMMAND")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new SSH config entry")
    add_parser.add_argument("host", help="Host alias (e.g., myserver)")
    add_parser.add_argument("hostname", help="Server hostname or IP address")
    add_parser.add_argument("user", help="Username to connect as")
    add_parser.add_argument("port", type=int, help="Port number (1-65535)")
    add_parser.add_argument("--identity-file", help="Path to private key file")

    # List command
    list_parser = subparsers.add_parser("list", help="List all SSH config entries")
    list_parser.add_argument("-v", "--verbose", action="store_true",
                             help="Show verbose output including IdentityFile")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search entries by host or hostname")
    search_parser.add_argument("query", help="Search term")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show detailed information for a host")
    show_parser.add_argument("host", help="Host alias to display")

    # Edit command
    edit_parser = subparsers.add_parser("edit", help="Edit an existing SSH config entry")
    edit_parser.add_argument("host", help="Host alias to edit")
    edit_parser.add_argument("field", choices=["hostname", "user", "port", "identityfile"],
                             help="Field to update")
    edit_parser.add_argument("value", help="New value for the field")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete an SSH config entry")
    delete_parser.add_argument("host", help="Host alias to delete")
    delete_parser.add_argument("-f", "--force", action="store_true",
                               help="Skip confirmation prompt")

    # Include commands
    subparsers.add_parser("include-list",
                                                 help="List all Include config files")
    include_add_parser = subparsers.add_parser("include-add",
                                                help="Add a new Include config file")
    include_add_parser.add_argument("name", help="Name of the include file (without .conf)")
    include_add_parser.add_argument("content", help="Content of the include file (use \\n for newlines)")
    include_show_parser = subparsers.add_parser("include-show",
                                                 help="Show content of an Include config file")
    include_show_parser.add_argument("name", help="Name of the include file")

    # Completion command
    completion_parser = subparsers.add_parser("completion",
                                               help="Generate shell completion script")
    completion_parser.add_argument("shell", choices=["bash", "zsh", "fish"],
                                    help="Shell to generate completion for")

    return parser


def _generate_bash_completion() -> str:
    """Generate bash completion script."""
    return """# ssh-manager bash completion
_ssh_manager_complete() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="add list search show edit delete include-list include-add include-show completion --help"

    case "${prev}" in
        add)
            return 0
            ;;
        show|edit|delete)
            # Complete with host aliases from SSH config
            local hosts=$(ssh-manager list 2>/dev/null | grep -E "^│ [a-zA-Z0-9]" | awk '{print $2}' | tr -d "│")
            COMPREPLY=( $(compgen -W "${hosts}" -- ${cur}) )
            return 0
            ;;
        edit)
            # Complete with field names
            COMPREPLY=( $(compgen -W "hostname user port identityfile" -- ${cur}) )
            return 0
            ;;
        completion)
            COMPREPLY=( $(compgen -W "bash zsh fish" -- ${cur}) )
            return 0
            ;;
    esac

    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}
complete -F _ssh_manager_complete ssh-manager
"""


def _generate_zsh_completion() -> str:
    """Generate zsh completion script."""
    return """# ssh-manager zsh completion
#compdef ssh-manager
_ssh_manager() {
    local context state line
    local -A opt_args

    _arguments -C \\
        '(-h --help)'{-h,--help}'[Show help]' \\
        '1: :->cmds' \\
        '*::arg:->args'

    case $state in
        cmds)
            _values 'ssh-manager commands' \\
                'add[Add a new SSH config entry]' \\
                'list[List all SSH config entries]' \\
                'search[Search entries by host or hostname]' \\
                'show[Show detailed information for a host]' \\
                'edit[Edit an existing SSH config entry]' \\
                'delete[Delete an SSH config entry]' \\
                'include-list[List all Include config files]' \\
                'include-add[Add a new Include config file]' \\
                'include-show[Show content of an Include config file]' \\
                'completion[Generate shell completion script]'
            ;;
        args)
            case $line[1] in
                show|edit|delete)
                    local hosts=($(ssh-manager list 2>/dev/null | grep -E "^│ [a-zA-Z0-9]" | awk '{print $2}' | tr -d "│"))
                    _values 'hosts' $hosts
                    ;;
                edit)
                    _values 'fields' 'hostname' 'user' 'port' 'identityfile'
                    ;;
                completion)
                    _values 'shells' 'bash' 'zsh' 'fish'
                    ;;
            esac
            ;;
    esac
}
compdef _ssh_manager ssh-manager
"""


def _generate_fish_completion() -> str:
    """Generate fish completion script."""
    return """# ssh-manager fish completion
function __ssh_manager_hosts
    ssh-manager list 2>/dev/null | grep -E "^│ [a-zA-Z0-9]" | awk '{print $2}' | tr -d "│"
end

complete -c ssh-manager -n "__fish_use_subcommand" -f -a "add list search show edit delete include-list include-add include-show completion --help"

complete -c ssh-manager -n "__fish_seen_subcommand_from add" -f

complete -c ssh-manager -n "__fish_seen_subcommand_from show" -f -a "(__ssh_manager_hosts)"

complete -c ssh-manager -n "__fish_seen_subcommand_from edit" -f -a "(__ssh_manager_hosts)"

complete -c ssh-manager -n "__fish_seen_subcommand_from edit" -n "__fish_seen_subcommand_from delete" -f -a "(__ssh_manager_hosts)"

complete -c ssh-manager -n "__fish_seen_subcommand_from edit" -n "__fish_seen_subcommand_from edit" -f -a "hostname user port identityfile"

complete -c ssh-manager -n "__fish_seen_subcommand_from completion" -f -a "bash zsh fish"
"""


def main() -> int:
    """Main entry point."""
    parser = build_parser()

    # Setup shell completion if available
    setup_argcomplete(parser)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    manager = SSHConfigManager()

    try:
        if args.command == "add":
            manager.add_entry(
                args.host, args.hostname, args.user, args.port, args.identity_file
            )
            console.print(f"[bold green]Host '{args.host}' added successfully.[/bold green]")

        elif args.command == "list":
            entries = manager.list_entries(args.verbose)
            print_table(entries, "SSH Config Entries", args.verbose)

        elif args.command == "search":
            results = manager.search_entries(args.query)
            print_table(results, f"Search Results for '{args.query}'")

        elif args.command == "show":
            host_data = manager.get_host(args.host)
            if host_data is None:
                console.print(f"[bold red]Error:[/bold red] Host '{args.host}' does not exist.")
                return 1
            print_host_details(args.host, host_data)

        elif args.command == "edit":
            manager.edit_entry(args.host, args.field, args.value)
            console.print(f"[bold green]Host '{args.host}' updated successfully.[/bold green] "
                          f"Field '{args.field}' set to '{args.value}'.")

        elif args.command == "delete":
            if confirm_deletion(args.host, getattr(args, 'force', False)):
                manager.delete_entry(args.host)
                console.print(f"[bold green]Host '{args.host}' deleted successfully.[/bold green]")
            else:
                console.print("[yellow]Deletion canceled.[/yellow]")

        elif args.command == "include-list":
            includes = manager.list_includes()
            if not includes:
                console.print("[yellow]No Include files found in ~/.ssh/config.d/[/yellow]")
            else:
                table = Table(title="Include Files", show_header=True, header_style="bold magenta")
                table.add_column("File", style="cyan")
                table.add_column("Size", style="green", justify="right")
                for inc in includes:
                    table.add_row(inc.name, f"{inc.stat().st_size} bytes")
                console.print(table)

        elif args.command == "include-add":
            include_path = manager.add_include(args.name, args.content.replace("\\n", "\n"))
            console.print(f"[bold green]Include file created:[/bold green] {include_path}")

        elif args.command == "include-show":
            content = manager.show_include(args.name)
            if content is None:
                console.print(f"[bold red]Error:[/bold red] Include file '{args.name}' not found.")
                return 1
            console.print(content)

        elif args.command == "completion":
            shell = args.shell
            if shell == "bash":
                console.print(_generate_bash_completion())
            elif shell == "zsh":
                console.print(_generate_zsh_completion())
            elif shell == "fish":
                console.print(_generate_fish_completion())

    except (ValueError, ValidationError, HostNotFoundError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1
    except FileOperationError as e:
        logger.error(f"File operation failed: {e}")
        console.print(f"[bold red]Error:[/bold red] File operation failed. Check logs for details.")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        console.print(f"[bold red]Unexpected error:[/bold red] {type(e).__name__}. Check logs for details.")
        return 1

    return 0




if __name__ == "__main__":
    sys.exit(main())
