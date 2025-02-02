# SSH Config Manager

SSH Config Manager is a modern CLI tool built with Python to simplify the management of your SSH configuration file (`~/.ssh/config`). With this tool, you can easily add, list, search, edit, and delete SSH entries, all from the command line.

![SSH Config Manager](https://img.shields.io/badge/SSH%20Config%20Manager-v1.0-blue)

## Features

- **Add SSH Entries**: Add new SSH configurations with ease.
- **List SSH Entries**: Display all SSH entries in a clean table format.
- **Search SSH Entries**: Search for hosts by name or hostname.
- **Edit SSH Entries**: Modify specific fields of an existing SSH entry.
- **Delete SSH Entries**: Safely remove unwanted SSH entries.
- **Verbose Output**: View detailed information about each SSH entry.
- **Modern CLI Design**: Beautifully formatted tables with colorized output using `rich`.

---

## Installation

### Prerequisites

- Python 3.6 or higher
- `pip` (Python package manager)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/zietbukuel/ssh-config-manager.git
   cd ssh-config-manager
   ```

2. **Run the Installation Script:**
   Use the provided install.sh script to install the tool. The script automates the following steps:
   - Makes the script executable.
   - Copies the script to /usr/local/bin so it can be accessed globally.
   - Installs the required Python dependencies (rich and sshconf) using pip.
   Run the script with the following command:
   ```bash
   ./install.sh
   ```
   > **Note:** If you prefer not to install dependencies via pip (e.g., because you want to use your system's package manager), you can skip dependency installation by passing the --skip-deps flag:

   ```bash
   ./install.sh --skip-deps
   ```

3. **Verify Installation:**
   After running the script, verify that the tool is installed correctly by checking the help message:

   ```bash
   ssh-manager --help
   ```
   If the installation was successful, you should see the available commands for managing SSH config entries.

## Usage

The tool supports several commands for managing SSH config entries. Below are examples of how to use each command.

### Add an Entry

Add a new SSH entry to your `~/.ssh/config` file.
```bash
python ssh_manager.py add <host> <hostname> <user> <port> [--identity-file <path>]
```
**Example :**
```bash
python ssh_manager.py add myserver 192.168.80.204 root 22 --identity-file ~/.ssh/keyfile.key
```

---


### List All Entries

Display all SSH entries in a clean table format.
```bash
python ssh_manager.py list
```
For verbose output (includes additional fields like `IdentityFile`):
```bash
python ssh_manager.py list -v
```

---


### Search Entries

Search for SSH entries by host or hostname.
```bash
python ssh_manager.py search <query>
```
**Example :**
```bash
python ssh_manager.py search myserver
```

---


### Show Host Details

Display detailed information about a specific host.
```bash
python ssh_manager.py show <host>
```
**Example :**
```bash
python ssh_manager.py show myserver
```

---


### Edit an Entry

Modify a specific field of an existing SSH entry.
```bash
python ssh_manager.py edit <host> <field> <value>
```
Fields : `hostname`, `user`, `port`, `identityfile`
**Example :**
```bash
python ssh_manager.py edit myserver user admin
```

---


### Delete an Entry

Remove an SSH entry from your `~/.ssh/config` file.
```bash
python ssh_manager.py delete <host>
```
**Example :**
```bash
python ssh_manager.py delete myserver
```

---

## Example Outputs

### Listing All Entries

```plaintext
SSH Config Entries
┌──────────┬─────────────────┬───────┬──────┐
│ Host     │ Hostname        │ User  │ Port │
├──────────┼─────────────────┼───────┼──────┤
│ myserver │ 192.168.80.204  │ root  │ 22   │
├──────────┼─────────────────┼───────┼──────┤
│ filesrvr │ 192.168.101.99  │ admin │ 22   │
└──────────┴─────────────────┴───────┴──────┘
```

### Verbose Listing

```plaintext
SSH Config Entries
┌───────────┬─────────────────┬───────┬──────┬───────────────────────┐
│ Host      │ Hostname        │ User  │ Port │ IdentityFile          │
├───────────┼─────────────────┼───────┼──────┼───────────────────────┤
│ myserver  │ 192.168.80.204  │ root  │ 22   │ ~/.ssh/keyfile.key    │
├───────────┼─────────────────┼───────┼──────┼───────────────────────┤
│ fileserver│ 192.168.101.99  │ admin │ 22   │ N/A                   │
└───────────┴─────────────────┴───────┴──────┴───────────────────────┘
```

### Search Results

```plaintext
Search Results for 'myserver'
┌──────────┬─────────────────┬───────┬──────┐
│ Host     │ Hostname        │ User  │ Port │
├──────────┼─────────────────┼───────┼──────┤
│ myserver │ 192.168.80.204  │ root  │ 22   │
└──────────┴─────────────────┴───────┴──────┘
```

### Show Host Details

```plaintext
Details for Host 'myserver'
┌───────────────┬───────────────────────┐
│ Field         │ Value                 │
├───────────────┼───────────────────────┤
│ Hostname      │ 192.168.80.204        │
│ User          │ root                  │
│ Port          │ 22                    │
│ Identityfile  │ ~/.ssh/keyfile.key    │
└───────────────┴───────────────────────┘
```

---


## Dependencies

This tool relies on the following Python libraries:

- `rich` : For rendering beautiful tables and colored output.
- `sshconf` : For managing SSH config files.

Install them using:
```bash
pip install rich sshconf
```

---

## Installing on Arch Linux (PKGBUILD)

For Arch Linux users, you can build and install this tool using the provided `PKGBUILD` file. This allows you to manage the installation via `pacman` or an AUR helper like `yay`.

### Steps to Install Using PKGBUILD

1. **Clone the Repository :**
   ```bash
   git clone https://github.com/zietbukuel/ssh-config-manager.git
   cd ssh-config-manager
   ```

2. **Build the Package :**
   Use `makepkg` to build the package:
   ```bash
   makepkg -si
   ```
   - `-s`: Automatically resolves and installs dependencies.
   - `-i`: Installs the package after building.

3. **Verify Installation :**
   After installation, verify that the tool is available globally:
   ```bash
   ssh-manager --help
   ```


---

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Author

Created by [Juan Timaná](https://github.com/zietbukuel).

