#!/bin/bash

# Fix Docker credentials helper issue on macOS
echo "Fixing Docker credentials issue..."
echo ""

# Check if Docker config exists
CONFIG_FILE="$HOME/.docker/config.json"

if [ -f "$CONFIG_FILE" ]; then
    echo "Found Docker config at: $CONFIG_FILE"
    echo ""
    
    # Check if credsStore exists
    if grep -q "credsStore" "$CONFIG_FILE"; then
        echo "Backing up current config..."
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
        
        echo "Removing credsStore from Docker config..."
        # Remove the credsStore line using sed
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' '/"credsStore"/d' "$CONFIG_FILE"
        else
            # Linux
            sed -i '/"credsStore"/d' "$CONFIG_FILE"
        fi
        
        echo "✅ Fixed Docker config!"
        echo "Backup saved at: $CONFIG_FILE.backup"
    else
        echo "No credsStore found in config - credentials issue may be elsewhere."
    fi
else
    echo "Docker config not found. Creating minimal config..."
    mkdir -p "$HOME/.docker"
    echo '{}' > "$CONFIG_FILE"
    echo "✅ Created Docker config"
fi

echo ""
echo "Now try running: ./start.sh"

