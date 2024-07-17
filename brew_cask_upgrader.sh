#!/bin/bash

# Function to find the best Homebrew Cask name for an app
find_brew_cask_name() {
    local app_name="$1"
    local matches=()
    
    # Search for possible matches
    while IFS= read -r cask; do
        if [[ "$cask" == *"$app_name"* ]]; then
            matches+=("$cask")
        fi
    done < <(brew search --cask "$app_name")
    
    echo "${matches[@]}"
}

# Function to check if a Homebrew Cask package is installed
is_brew_cask_installed() {
    local cask_name="$1"
    brew list --cask | grep -q "^$cask_name\$"
}

# Function to check if an application process is running
is_app_process_running() {
    local app_name="$1"
    pgrep -f "$app_name" > /dev/null
}

# Function to restart the application
restart_app() {
    local app_name="$1"
    local app_path="/Applications/$app_name.app"
    
    if [ -d "$app_path" ]; then
        echo "Restarting $app_name"
        open "$app_path"
    else
        echo "Application $app_name not found in /Applications"
    fi
}

# Total number of applications in the /Applications directory
total_apps=$(ls /Applications/*.app | wc -l | tr -d ' ')
current_app=0

# Iterate through the /Applications directory
for app in /Applications/*.app; do
    ((current_app++))
    app_name=$(basename "$app" .app | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
    
    # Find possible Homebrew Cask names
    brew_cask_names=$(find_brew_cask_name "$app_name")
    IFS=' ' read -r -a brew_cask_names_array <<< "$brew_cask_names"
    
    # Check if any of the possible Cask names are installed
    is_installed=false
    for brew_cask_name in "${brew_cask_names_array[@]}"; do
        if is_brew_cask_installed "$brew_cask_name"; then
            is_installed=true
            break
        fi
    done

    # Only process the app if no Homebrew Cask package is installed
    if ! $is_installed; then
        echo "Processing $app_name..."

        if [ ${#brew_cask_names_array[@]} -eq 0 ]; then
            echo "No Homebrew Cask found for $app_name"
        else
            echo "Possible Homebrew Casks for $app_name:"
            select brew_cask_name in "${brew_cask_names_array[@]}" "Skip"; do
                if [ "$REPLY" -ge 1 ] && [ "$REPLY" -le ${#brew_cask_names_array[@]} ]; then
                    echo "Found Homebrew Cask: $brew_cask_name. Reinstalling..."

                    # Check if the app process is running
                    process_was_running=false
                    if is_app_process_running "$app_name"; then
                        process_was_running=true
                        echo "Process for $app_name is running."
                        read -p "Do you want to kill this process? (y/n): " choice
                        if [[ "$choice" == [Yy]* ]]; then
                            kill_app_process "$app_name"
                        else
                            echo "Skipping process termination for $app_name"
                        fi
                    fi

                    # Reinstall the application
                    brew install --cask --force "$brew_cask_name"

                    # Restart the application if it was running before
                    if $process_was_running; then
                        restart_app "$app_name"
                    fi
                    break
                elif [ "$REPLY" -eq $((${#brew_cask_names_array[@]} + 1)) ]; then
                    echo "Skipping $app_name"
                    break
                else
                    echo "Invalid option. Please try again."
                fi
            done
        fi
    fi
    
    # Display progress in percentage
    progress=$(echo "scale=2; $current_app / $total_apps * 100" | bc)
    echo "Progress: $progress% ($current_app/$total_apps)"
done