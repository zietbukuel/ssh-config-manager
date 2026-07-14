# SSH Config Manager

SSH Config Manager is a modern CLI tool built with Python to simplify the management of your SSH configuration file (`~/.ssh/config`). With this tool, you can easily add, list, search, edit, and delete SSH entries, all from the command line.

![SSH Config Manager](https://img.shields.io/badge/SSH%20Config%20Manager-v2.0-blue)

## Features

- **Add SSH Entries**: Add new SSH configurations with ease.
- **List SSH Entries**: Display all SSH entries in a clean table format.
- **Search SSH Entries**: Search for hosts by name or hostname.
- **Edit SSH Entries**: Modify specific fields of an existing SSH entry.
- **Delete SSH Entries**: Safely remove unwanted SSH entries.
- **Verbose Output**: View detailed information about each SSH entry.
- **Automatic Backups**: Creates timestamped backups before any write operation.
- **Input Validation**: Validates hostnames, IP addresses, ports, and identity files.
- **Include Directive Support**: Manage `~/.ssh/config.d/` include files.
- **Shell Completion**: Bash, Zsh, and Fish completion support via `argcomplete`.
- **Modern CLI Design**: Beautifully formatted tables with colorized output using `rich`.
- **Modern Python Packaging**: Installable via `pipx` with `pyproject.toml`.
- **Comprehensive Test Suite**: 40+ tests with pytest.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- `pip` (Python package manager)
- `pipx` (recommended for isolated CLI tool installation)

### Recommended: Install with pipx (No sudo required)

```bash
# Install pipx if not already installed
# Arch: sudo pacman -S python-pipx
# Debian/Ubuntu: sudo apt install python3-pipx
# macOS: brew install pipx

# Install ssh-config-manager
pipx install git+https://github.com/zietbukuel/ssh-config-manager.git

# Verify installation
ssh-manager --help
```

### Alternative: Install with pip (editable, for development)

```bash
git clone https://github.com/zietbukuel/ssh-config-manager.git
cd ssh-config-manager
pip install -e .[dev,completion]
```

### Arch Linux (AUR)

```bash
# Using the provided PKGBUILD
git clone https://github.com/zietbukuel/ssh-config-manager.git
cd ssh-config-manager
makepkg -si
```

> **Note:** The old `install.sh` script copied the script to `/usr/local/bin` which required sudo. The modern `pipx` installation method installs to an isolated user directory (`~/.local/pipx/venvs/...`) with a symlink in `~/.local/bin` — no sudo needed!

---

## Shell Completion

Generate and install shell completions for a better CLI experience:

```bash
# Bash
ssh-manager completion bash > ~/.bash_completion.d/ssh-manager
source ~/.bash_completion.d/ssh-manager

# Zsh
ssh-manager completion zsh > ~/.zsh/completions/_ssh-manager
# Add to .zshrc: fpath=(~/.zsh/completions $fpath)
# Then run: compinit

# Fish
ssh-manager completion fish > ~/.config/fish/completions/ssh-manager.fish

# Or enable argcomplete globally (works for bash, zsh, fish):
pipx inject ssh-config-manager argcomplete
eval "$(register-python-argcomplete ssh-manager)"
```

---

## Usage

The tool supports several commands for managing SSH config entries.

### Add an Entry

Add a new SSH entry to your `~/.ssh/config` file.

```bash
ssh-manager add <host> <hostname> <user> <port> [--identity-file <path>]
```

**Example:**
```bash
ssh-manager add myserver 192.168.80.204 root 22 --identity-file ~/.ssh/keyfile.key
```

### List All Entries

Display all SSH entries in a clean table format.

```bash
ssh-manager list
```

For verbose output (includes additional fields like `IdentityFile`):

```bash
ssh-manager list -v
```

### Search Entries

Search for SSH entries by host alias or hostname.

```bash
ssh-manager search <query>
```

**Example:**
```bash
ssh-manager search myserver
```

### Show Host Details

Display detailed information about a specific host.

```bash
ssh-manager show <host>
```

**Example:**
```bash
ssh-manager show myserver
```

### Edit an Entry

Modify a specific field of an existing SSH entry.

```bash
ssh-manager edit <host> <field> <value>
```

Fields: `hostname`, `user`, `port`, `identityfile`

**Example:**
```bash
ssh-manager edit myserver user admin
ssh-manager edit myserver port 2222
ssh-manager edit myserver identityfile ~/.ssh/new_key
```

### Delete an Entry

Remove an SSH entry from your `~/.ssh/config` file.

```bash
ssh-manager delete <host>
```

**Example:**
```bash
ssh-manager delete myserver
```

### Include Directive Support

Manage modular SSH config files in `~/.ssh/config.d/`.

**List include files:**
```bash
ssh-manager include-list
```

**Add a new include file:**
```bash
ssh-manager include-add myserver "Host myserver\n  HostName 10.0.0.1\n  User admin\n  Port 2222"
```

**Show an include file:**
```bash
ssh-manager include-show myserver
```

---

## Example Outputs

### Listing All Entries

```plaintext
SSH Config Entries
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━┓
┃ Host     ┃ Hostname         ┃ User  ┃ Port ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━┩
│ myserver │ 192.168.80.204   │ root  │ 22   │
├──────────┼──────────────────┼───────┼──────┤
│ filesrvr │ 192.168.101.99   │ admin │ 22   │
└──────────┴──────────────────┴───────┴──────┘
```

### Verbose Listing

```plaintext
SSH Config Entries
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Host       ┃ Hostname         ┃ User  ┃ Port ┃ IdentityFile                   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ myserver   │ 192.168.80.204   │ root  │ 22   │ ~/.ssh/keyfile.key             │
├────────────┼──────────────────┼───────┼──────┼────────────────────────────────┤
│ fileserver │ 192.168.101.99   │ admin │ 22   │ N/A                            │
└────────────┴──────────────────┴───────┴──────┴────────────────────────────────┘
```

### Search Results

```plaintext
Search Results for 'myserver'
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━┓
┃ Host     ┃ Hostname         ┃ User  ┃ Port ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━┩
│ myserver │ 192.168.80.204   │ root  │ 22   │
└──────────┴──────────────────┴───────┴──────┘
```

### Show Host Details

```plaintext
Details for Host 'myserver'
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Field            ┃ Value                            ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Hostname         │ 192.168.80.204                   │
│ User             │ root                             │
│ Port             │ 22                               │
│ Identityfile     │ ~/.ssh/keyfile.key               │
└──────────────────┴──────────────────────────────────┘
```

### Include Files

```plaintext
Include Files
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ File             ┃ Size     ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ myserver.conf    │ 58 bytes │
└──────────────────┴──────────┘
```

---

## Validation & Safety

The tool performs comprehensive validation before making changes:

| Validation | Description |
|------------|-------------|
| **Hostname/IP** | Validates IPv4, IPv6, and DNS hostnames (RFC compliant) |
| **Port** | Must be between 1 and 65535 |
| **Identity File** | Must exist and be readable |
| **Host Alias** | Cannot be empty or contain spaces |
| **Duplicates** | Prevents adding duplicate host aliases |

### Automatic Backups

Before every write operation, a timestamped backup is created at:
```
~/.ssh/backups/config.backup.YYYYMMDD_HHMMSS
```

You can restore a backup manually if needed:
```bash
cp ~/.ssh/backups/config.backup.20260706_145311 ~/.ssh/config
```

---

## Project Structure

```
ssh-config-manager/
├── ssh_manager.py          # Main CLI application (single file)
├── pyproject.toml          # Modern Python packaging config
├── tests/
│   └── test_ssh_manager.py # Comprehensive test suite (40 tests)
├── PKGBUILD                # Arch Linux package build script
├── README.md               # This file
├── LICENSE                 # MIT License
└── requirements.txt        # Legacy requirements (deprecated)
```

---

## Development

### Install in development mode

```bash
git clone https://github.com/zietbukuel/ssh-config-manager.git
cd ssh-config-manager
pip install -e .[dev,completion]
```

### Run tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ssh_manager --cov-report=term-missing

# Run specific test class
pytest tests/test_ssh_manager.py::TestValidation -v
```

### Code quality tools

```bash
# Lint with ruff
ruff check .

# Type check with mypy
mypy ssh_manager.py
```

---

## Dependencies

### Runtime
- `rich>=13.7.0` — Beautiful terminal formatting
- `sshconf>=0.1.0` — SSH config parsing

### Development (optional, install with `pip install -e .[dev]`)
- `pytest>=7.4.0` — Testing framework
- `pytest-cov>=4.1.0` — Coverage reporting
- `pytest-mock>=3.11.0` — Mocking utilities
- `ruff>=0.1.0` — Fast Python linter
- `mypy>=1.5.0` — Static type checker

### Completion (optional, install with `pip install -e .[completion]`)
- `argcomplete>=3.0.0` — Shell completion support

---

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Submit a PR

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Author

Created by [Juan Timaná](https://github.com/zietbukuel).

---

## Changelog

### v2.0.0 (2026-07-06)
- **Modern packaging**: Migrated to `pyproject.toml` with `pipx` support
- **Automatic backups**: Timestamped backups before every write
- **Input validation**: Hostname/IP, port, identity file, host alias validation
- **Include directive support**: Manage `~/.ssh/config.d/` files
- **Shell completion**: Bash, Zsh, Fish via `argcomplete` + `completion` command
- **Comprehensive tests**: 40 tests covering all functionality
- **Code quality**: Added `ruff`, `mypy`, `pytest-cov` configs
- **Single-file CLI**: Refactored `ssh_manager.py` with type hints

### v1.0.0
- Initial release with basic CRUD operations
- Rich table output
- Basic validation