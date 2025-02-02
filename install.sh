#!/bin/bash

# Variables
SCRIPT_NAME="ssh_manager.py"
EXECUTABLE_NAME="ssh-manager"
INSTALL_DIR="/usr/local/bin"
REQUIREMENTS_FILE="requirements.txt"
SKIP_DEPS=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        *)
            echo "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# Check if the script file exists
if [[ ! -f "$SCRIPT_NAME" ]]; then
    echo "Error: $SCRIPT_NAME not found in the current directory."
    exit 1
fi

# Step 1: Make the script executable
echo "Making $SCRIPT_NAME executable..."
chmod +x "$SCRIPT_NAME"

# Step 2: Copy the script to /usr/local/bin
echo "Copying $SCRIPT_NAME to $INSTALL_DIR as $EXECUTABLE_NAME..."
sudo cp "$SCRIPT_NAME" "$INSTALL_DIR/$EXECUTABLE_NAME"

# Check if the copy was successful
if [[ $? -ne 0 ]]; then
    echo "Error: Failed to copy $SCRIPT_NAME to $INSTALL_DIR."
    exit 1
fi

# Step 3: Install dependencies (unless skipped)
if [[ "$SKIP_DEPS" = false ]]; then
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        echo "Error: $REQUIREMENTS_FILE not found in the current directory."
        exit 1
    fi

    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install --user -r "$REQUIREMENTS_FILE"

    # Check if pip installation was successful
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to install dependencies."
        exit 1
    fi
else
    echo "Skipping dependency installation (--skip-deps flag provided)."
fi

# Step 4: Verify installation
echo "Verifying installation..."
if command -v "$EXECUTABLE_NAME" >/dev/null 2>&1; then
    echo "Installation successful! You can now run '$EXECUTABLE_NAME --help' from anywhere."
else
    echo "Error: Installation failed. '$EXECUTABLE_NAME' is not in your PATH."
    exit 1
fi