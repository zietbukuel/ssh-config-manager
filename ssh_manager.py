#!/usr/bin/env python3

# Import necessary libraries
import os  # For file path operations
import sys  # For system-level operations like exiting
import argparse  # For parsing command-line arguments
from rich.console import Console  # For rich text formatting in the terminal
from rich.table import Table  # For creating tables in the terminal
from sshconf import read_ssh_config, empty_ssh_config_file  # For managing SSH config files

# Initialize Rich console for colored and styled output
console = Console()

# Define the path to the SSH config file (~/.ssh/config)
SSH_CONFIG_PATH = os.path.expanduser("~/.ssh/config")

def load_ssh_config():
    """
    Load the SSH config file.
    If the file doesn't exist, return an empty SSH config file object.
    """
    if not os.path.exists(SSH_CONFIG_PATH):
        return empty_ssh_config_file()  # Return an empty config if the file doesn't exist
    return read_ssh_config(SSH_CONFIG_PATH)  # Otherwise, load the existing config

def save_ssh_config(config):
    """
    Save the updated SSH config back to the file.
    """
    config.write(SSH_CONFIG_PATH)  # Write the config object back to the file

def add_entry(host, hostname, user, port, identity_file=None):
    """
    Add a new SSH config entry.
    - host: The alias for the host (e.g., "myserver").
    - hostname: The actual hostname or IP address (e.g., "192.168.1.100").
    - user: The username to connect as (e.g., "root").
    - port: The port number to connect to (e.g., 22).
    - identity_file: (Optional) Path to the private key file.
    """
    config = load_ssh_config()  # Load the current SSH config
    if host in config.hosts():  # Check if the host already exists
        console.print(f"[bold red]Error:[/] Host '{host}' already exists.")
        sys.exit(1)  # Exit with an error code
    
    # Prepare the parameters for the new entry
    params = {
        "hostname": hostname,
        "user": user,
        "port": port,
    }
    if identity_file:
        params["identityfile"] = identity_file  # Add identity file if provided
    
    config.add(host, **params)  # Add the new host to the config
    save_ssh_config(config)  # Save the updated config
    console.print(f"[bold green]Host '{host}' added successfully.[/]")  # Print success message

def list_entries(verbose=False):
    """
    List all SSH config entries.
    - verbose: If True, include additional fields like IdentityFile.
    """
    config = load_ssh_config()  # Load the current SSH config
    hosts = config.hosts()  # Get the list of hosts
    
    if not hosts:  # If no hosts are found, print a message and exit
        console.print("[yellow]No SSH entries found.[/]")
        return
    
    # Create a table to display the SSH entries
    table = Table(title="SSH Config Entries", show_header=True, header_style="bold magenta")
    table.add_column("Host", style="cyan", justify="left")  # Host alias column
    table.add_column("Hostname", style="green", justify="left")  # Hostname/IP column
    table.add_column("User", style="blue", justify="left")  # Username column
    table.add_column("Port", style="yellow", justify="center")  # Port column
    if verbose:  # Add IdentityFile column if verbose mode is enabled
        table.add_column("IdentityFile", style="magenta", justify="left")
    
    # Populate the table with data from the SSH config
    for host in hosts:
        host_data = config.host(host)  # Get details for each host
        row = [
            host,
            host_data.get("hostname", "N/A"),  # Default to "N/A" if field is missing
            host_data.get("user", "N/A"),
            str(host_data.get("port", "N/A")),
        ]
        if verbose:  # Add IdentityFile if verbose mode is enabled
            row.append(host_data.get("identityfile", "N/A"))
        table.add_row(*row)  # Add the row to the table
    
    console.print(table)  # Print the table to the terminal

def search_entries(query):
    """
    Search for SSH config entries by host or hostname.
    - query: The search term (can match either host alias or hostname).
    """
    config = load_ssh_config()  # Load the current SSH config
    hosts = config.hosts()  # Get the list of hosts
    
    results = []  # Store matching results
    for host in hosts:
        host_data = config.host(host)  # Get details for each host
        # Check if the query matches the host alias or hostname
        if query in host or query in host_data.get("hostname", ""):
            results.append((host, host_data))
    
    if not results:  # If no matches are found, print a message and exit
        console.print(f"[yellow]No matches found for query: {query}[/]")
        return
    
    # Create a table to display the search results
    table = Table(title=f"Search Results for '{query}'", show_header=True, header_style="bold magenta")
    table.add_column("Host", style="cyan", justify="left")
    table.add_column("Hostname", style="green", justify="left")
    table.add_column("User", style="blue", justify="left")
    table.add_column("Port", style="yellow", justify="center")
    
    # Populate the table with matching results
    for host, host_data in results:
        table.add_row(
            host,
            host_data.get("hostname", "N/A"),
            host_data.get("user", "N/A"),
            str(host_data.get("port", "N/A")),
        )
    
    console.print(table)  # Print the table to the terminal

def show_host(host):
    """
    Display detailed information about a specific host.
    - host: The alias of the host to display.
    """
    config = load_ssh_config()  # Load the current SSH config
    if host not in config.hosts():  # Check if the host exists
        console.print(f"[bold red]Error:[/] Host '{host}' does not exist.")
        sys.exit(1)  # Exit with an error code
    
    host_data = config.host(host)  # Get details for the specified host
    
    # Create a table to display the host's details
    table = Table(title=f"Details for Host '{host}'", show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan", justify="left")  # Field name column
    table.add_column("Value", style="green", justify="left")  # Field value column
    
    # Populate the table with the host's details
    for key, value in host_data.items():
        table.add_row(key.capitalize(), str(value))  # Capitalize field names for readability
    
    console.print(table)  # Print the table to the terminal

def edit_entry(host, field, value):
    """
    Edit an existing SSH config entry.
    - host: The alias of the host to edit.
    - field: The field to update (e.g., "hostname", "user", "port", "identityfile").
    - value: The new value for the field.
    """
    config = load_ssh_config()  # Load the current SSH config
    if host not in config.hosts():  # Check if the host exists
        console.print(f"[bold red]Error:[/] Host '{host}' does not exist.")
        sys.exit(1)  # Exit with an error code
    
    # Update the specified field with the new value
    config.set(host, **{field.lower(): value})  # Convert field to lowercase for consistency
    save_ssh_config(config)  # Save the updated config
    console.print(f"[bold green]Host '{host}' updated successfully.[/] Field '{field}' set to '{value}'.")  # Print success message

def delete_entry(host):
    """
    Delete an SSH config entry.
    - host: The alias of the host to delete.
    """
    config = load_ssh_config()  # Load the current SSH config
    if host not in config.hosts():  # Check if the host exists
        console.print(f"[bold red]Error:[/] Host '{host}' does not exist.")
        sys.exit(1)  # Exit with an error code
    
    # Confirm deletion with the user
    confirm = console.input(f"[bold yellow]Are you sure you want to delete host '{host}'? (y/n): [/]")
    if confirm.lower() != 'y':  # If the user cancels, exit without deleting
        console.print("[yellow]Deletion canceled.[/]")
        return
    
    config.remove(host)  # Remove the host from the config
    save_ssh_config(config)  # Save the updated config
    console.print(f"[bold green]Host '{host}' deleted successfully.[/]")  # Print success message

def main():
    """
    Main function to handle command-line arguments and execute commands.
    """
    parser = argparse.ArgumentParser(description="Manage SSH config entries from the command line.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")  # Add subcommands
    
    # Add command: Add a new SSH config entry
    add_parser = subparsers.add_parser("add", help="Add a new SSH config entry")
    add_parser.add_argument("host", help="The host alias")
    add_parser.add_argument("hostname", help="The server's hostname or IP address")
    add_parser.add_argument("user", help="The username to connect as")
    add_parser.add_argument("port", type=int, help="The port number")
    add_parser.add_argument("--identity-file", help="Path to the private key file")
    
    # List command: List all SSH config entries
    list_parser = subparsers.add_parser("list", help="List all SSH config entries")
    list_parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    
    # Search command: Search for SSH config entries
    search_parser = subparsers.add_parser("search", help="Search for SSH config entries by host or hostname")
    search_parser.add_argument("query", help="The search query")
    
    # Show command: Display detailed information about a specific host
    show_parser = subparsers.add_parser("show", help="Display detailed information about a specific host")
    show_parser.add_argument("host", help="The host alias")
    
    # Edit command: Edit an existing SSH config entry
    edit_parser = subparsers.add_parser("edit", help="Edit an existing SSH config entry")
    edit_parser.add_argument("host", help="The host alias")
    edit_parser.add_argument("field", choices=["hostname", "user", "port", "identityfile"], help="The field to edit")
    edit_parser.add_argument("value", help="The new value for the field")
    
    # Delete command: Delete an SSH config entry
    delete_parser = subparsers.add_parser("delete", help="Delete an SSH config entry")
    delete_parser.add_argument("host", help="The host alias")
    
    args = parser.parse_args()  # Parse the command-line arguments
    
    # Execute the appropriate command based on the parsed arguments
    if args.command == "add":
        add_entry(args.host, args.hostname, args.user, args.port, args.identity_file)
    elif args.command == "list":
        list_entries(args.verbose)
    elif args.command == "search":
        search_entries(args.query)
    elif args.command == "show":
        show_host(args.host)
    elif args.command == "edit":
        edit_entry(args.host, args.field, args.value)
    elif args.command == "delete":
        delete_entry(args.host)
    else:
        parser.print_help()  # Print help if no valid command is provided

if __name__ == "__main__":
    main()  # Call the main function when the script is executed