#!/usr/bin/env python3
"""
Test suite for ssh-config-manager.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the current virtualenv's bin directory is in PATH for subprocess tests
if sys.executable:
    bin_dir = os.path.dirname(sys.executable)
    if bin_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

from ssh_manager import SSHConfigManager


@pytest.fixture
def temp_ssh_dir():
    """Create a temporary SSH directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssh_dir = Path(tmpdir) / ".ssh"
        ssh_dir.mkdir(mode=0o700)
        yield ssh_dir


@pytest.fixture
def config_manager(temp_ssh_dir):
    """Create an SSHConfigManager with a temporary config."""
    config_path = temp_ssh_dir / "config"
    return SSHConfigManager(config_path)


@pytest.fixture
def sample_config(temp_ssh_dir):
    """Create a sample SSH config for testing."""
    config_path = temp_ssh_dir / "config"
    config_content = """Host myserver
    HostName 192.168.1.100
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519

Host fileserver
    HostName 192.168.1.200
    User admin
    Port 2222
"""
    config_path.write_text(config_content)
    config_path.chmod(0o600)
    return config_path


class TestValidation:
    """Test validation functions."""

    def test_validate_hostname_valid_ipv4(self, config_manager):
        assert config_manager.validate_hostname("192.168.1.1") is True
        assert config_manager.validate_hostname("10.0.0.1") is True
        assert config_manager.validate_hostname("255.255.255.255") is True

    def test_validate_hostname_invalid_ipv4(self, config_manager):
        assert config_manager.validate_hostname("999.999.999.999") is False
        assert config_manager.validate_hostname("invalid..hostname") is False
        # 5 octets - not valid IPv4, and has leading dots so not valid hostname
        assert config_manager.validate_hostname(".192.168.1.1") is False

    def test_validate_hostname_valid_ipv6(self, config_manager):
        assert config_manager.validate_hostname("::1") is True
        assert config_manager.validate_hostname("::") is True
        assert config_manager.validate_hostname("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True

    def test_validate_hostname_valid_hostname(self, config_manager):
        assert config_manager.validate_hostname("example.com") is True
        assert config_manager.validate_hostname("sub.domain.example.com") is True
        assert config_manager.validate_hostname("localhost") is True
        assert config_manager.validate_hostname("my-server") is True

    def test_validate_hostname_invalid_hostname(self, config_manager):
        assert config_manager.validate_hostname("-invalid.com") is False
        assert config_manager.validate_hostname("invalid-.com") is False
        assert config_manager.validate_hostname("") is False
        assert config_manager.validate_hostname("a" * 254) is False

    def test_validate_port(self, config_manager):
        assert config_manager.validate_port(1) is True
        assert config_manager.validate_port(22) is True
        assert config_manager.validate_port(80) is True
        assert config_manager.validate_port(443) is True
        assert config_manager.validate_port(65535) is True

    def test_validate_port_invalid(self, config_manager):
        assert config_manager.validate_port(0) is False
        assert config_manager.validate_port(65536) is False
        assert config_manager.validate_port(-1) is False

    def test_validate_host_alias(self, config_manager):
        assert config_manager.validate_host_alias("myserver") is True
        assert config_manager.validate_host_alias("my-server") is True
        assert config_manager.validate_host_alias("server123") is True

    def test_validate_host_alias_invalid(self, config_manager):
        assert config_manager.validate_host_alias("") is False
        assert config_manager.validate_host_alias("my server") is False
        assert config_manager.validate_host_alias("  ") is False


class TestSSHConfigManager:
    """Test SSHConfigManager class."""

    def test_load_empty_config(self, config_manager):
        config = config_manager.load_config()
        assert config is not None
        # sshconf returns a tuple from hosts()
        assert list(config.hosts()) == []

    def test_load_existing_config(self, config_manager, sample_config):
        config = config_manager.load_config()
        hosts = config.hosts()
        assert "myserver" in hosts
        assert "fileserver" in hosts

        myserver = config.host("myserver")
        assert myserver["hostname"] == "192.168.1.100"
        assert myserver["user"] == "root"
        assert myserver["port"] == "22"

    def test_add_entry(self, config_manager):
        config_manager.add_entry("newhost", "example.com", "user", 2222)
        config = config_manager.load_config()
        assert "newhost" in config.hosts()
        entry = config.host("newhost")
        assert entry["hostname"] == "example.com"
        assert entry["user"] == "user"
        assert entry["port"] == "2222"

    def test_add_entry_with_identity_file(self, config_manager, temp_ssh_dir):
        identity_file = temp_ssh_dir / "id_test"
        identity_file.write_text("test")
        identity_file.chmod(0o600)

        config_manager.add_entry("keyhost", "example.com", "user", 22, str(identity_file))
        config = config_manager.load_config()
        entry = config.host("keyhost")
        assert "identityfile" in entry

    def test_add_duplicate_host_raises(self, config_manager, sample_config):
        with pytest.raises(ValueError, match="already exists"):
            config_manager.add_entry("myserver", "example.com", "user", 22)

    def test_add_invalid_hostname_raises(self, config_manager):
        with pytest.raises(ValueError, match="Invalid hostname"):
            config_manager.add_entry("badhost", "999.999.999.999", "user", 22)

    def test_add_invalid_port_raises(self, config_manager):
        with pytest.raises(ValueError, match="Port must be between"):
            config_manager.add_entry("badport", "example.com", "user", 99999)

    def test_add_invalid_identity_file_raises(self, config_manager):
        with pytest.raises(ValueError, match="Identity file not found"):
            config_manager.add_entry("badkey", "example.com", "user", 22, "~/.ssh/nonexistent")

    def test_add_invalid_host_alias_raises(self, config_manager):
        with pytest.raises(ValueError, match="Invalid host alias"):
            config_manager.add_entry("", "example.com", "user", 22)

        with pytest.raises(ValueError, match="Invalid host alias"):
            config_manager.add_entry("my host", "example.com", "user", 22)

    def test_edit_entry(self, config_manager, sample_config):
        config_manager.edit_entry("myserver", "user", "newuser")
        config = config_manager.load_config()
        assert config.host("myserver")["user"] == "newuser"

    def test_edit_entry_port(self, config_manager, sample_config):
        config_manager.edit_entry("myserver", "port", "2222")
        config = config_manager.load_config()
        assert config.host("myserver")["port"] == "2222"

    def test_edit_entry_invalid_port_raises(self, config_manager, sample_config):
        with pytest.raises(ValueError, match="Port must be a valid integer"):
            config_manager.edit_entry("myserver", "port", "not_a_number")

    def test_edit_entry_hostname(self, config_manager, sample_config):
        config_manager.edit_entry("myserver", "hostname", "10.0.0.1")
        config = config_manager.load_config()
        assert config.host("myserver")["hostname"] == "10.0.0.1"

    def test_edit_entry_invalid_hostname_raises(self, config_manager, sample_config):
        with pytest.raises(ValueError, match="Invalid hostname"):
            config_manager.edit_entry("myserver", "hostname", "999.999.999.999")

    def test_edit_nonexistent_host_raises(self, config_manager):
        with pytest.raises(ValueError, match="does not exist"):
            config_manager.edit_entry("nonexistent", "user", "test")

    def test_delete_entry(self, config_manager, sample_config):
        config_manager.delete_entry("myserver")
        config = config_manager.load_config()
        assert "myserver" not in config.hosts()
        assert "fileserver" in config.hosts()

    def test_delete_nonexistent_raises(self, config_manager):
        with pytest.raises(ValueError, match="does not exist"):
            config_manager.delete_entry("nonexistent")

    def test_list_entries(self, config_manager, sample_config):
        entries = config_manager.list_entries()
        assert len(entries) == 2
        hosts = {e["host"] for e in entries}
        assert hosts == {"myserver", "fileserver"}

    def test_list_entries_verbose(self, config_manager, sample_config):
        entries = config_manager.list_entries(verbose=True)
        assert len(entries) == 2
        for entry in entries:
            assert "identityfile" in entry

    def test_search_entries(self, config_manager, sample_config):
        results = config_manager.search_entries("myserver")
        assert len(results) == 1
        assert results[0]["host"] == "myserver"

        results = config_manager.search_entries("192.168")
        assert len(results) == 2

        results = config_manager.search_entries("nonexistent")
        assert len(results) == 0

    def test_get_host(self, config_manager, sample_config):
        host_data = config_manager.get_host("myserver")
        assert host_data is not None
        assert host_data["hostname"] == "192.168.1.100"

    def test_get_nonexistent_host(self, config_manager):
        host_data = config_manager.get_host("nonexistent")
        assert host_data is None


class TestIncludeDirectives:
    """Test Include directive support."""

    def test_list_includes_empty(self, config_manager):
        includes = config_manager.list_includes()
        assert includes == []

    def test_add_include(self, config_manager):
        include_path = config_manager.add_include("testhost", "Host testhost\n  HostName 10.0.0.1")
        assert include_path.exists()
        assert include_path.name == "testhost.conf"

        # Check main config has Include directive
        config_content = config_manager.config_path.read_text()
        assert "Include config.d/*.conf" in config_content

    def test_add_duplicate_include_raises(self, config_manager):
        config_manager.add_include("testhost", "Host testhost\n  HostName 10.0.0.1")
        with pytest.raises(ValueError, match="already exists"):
            config_manager.add_include("testhost", "Host testhost\n  HostName 10.0.0.1")

    def test_show_include(self, config_manager):
        config_manager.add_include("showhost", "Host showhost\n  HostName 10.0.0.1")
        content = config_manager.show_include("showhost")
        assert content is not None
        assert "showhost" in content
        assert "10.0.0.1" in content

    def test_show_nonexistent_include(self, config_manager):
        content = config_manager.show_include("nonexistent")
        assert content is None


class TestBackup:
    """Test backup functionality."""

    def test_backup_created_on_save(self, config_manager, sample_config):
        # The save_config method should create a backup
        config = config_manager.load_config()
        config_manager.save_config(config)

        backups = list(config_manager.config_path.parent.glob("backups/*.backup.*"))
        assert len(backups) >= 1

    def test_backup_directory_created(self, config_manager):
        assert config_manager.config_path.parent.joinpath("backups").exists()


class TestCLI:
    """Test CLI commands via subprocess."""

    def test_cli_help(self):
        import subprocess
        result = subprocess.run(["ssh-manager", "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    @pytest.mark.skip(reason="Requires clean SSH config; integration test")
    def test_cli_add_list(self):
        import subprocess
        # Clean up first
        subprocess.run(["ssh-manager", "delete", "clitest"], capture_output=True, text=True, input="y\n")
        # Add
        result = subprocess.run(["ssh-manager", "add", "clitest", "example.com", "user", "22"],
                                capture_output=True, text=True)
        assert result.returncode == 0
        assert "added successfully" in result.stdout
        # List
        result = subprocess.run(["ssh-manager", "list"], capture_output=True, text=True)
        assert "clitest" in result.stdout
        # Clean up
        subprocess.run(["ssh-manager", "delete", "clitest"], capture_output=True, text=True, input="y\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
