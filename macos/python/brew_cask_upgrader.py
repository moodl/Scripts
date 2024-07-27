import os
import subprocess
import re
from tqdm import tqdm

def find_brew_cask_name(app_name):
    result = subprocess.run(['brew', 'search', '--cask', app_name], capture_output=True, text=True)
    matches = [cask for cask in result.stdout.split('\n') if app_name in cask.lower()]
    return matches

def is_brew_cask_installed(cask_name):
    result = subprocess.run(['brew', 'list', '--cask'], capture_output=True, text=True)
    return cask_name in result.stdout.split()

def is_app_process_running(app_name):
    result = subprocess.run(['pgrep', '-f', app_name], capture_output=True)
    return result.returncode == 0

def restart_app(app_name):
    app_path = f"/Applications/{app_name}.app"
    if os.path.isdir(app_path):
        print(f"Restarting {app_name}")
        subprocess.run(['open', app_path])
    else:
        print(f"Application {app_name} not found in /Applications")

def kill_app_process(app_name):
    subprocess.run(['pkill', '-f', app_name])

# Get total number of applications in the /Applications directory
total_apps = len([app for app in os.listdir('/Applications') if app.endswith('.app')])

# Iterate through the /Applications directory
for app in tqdm(os.listdir('/Applications'), total=total_apps, desc="Processing apps"):
    if not app.endswith('.app'):
        continue

    app_name = app[:-4].replace(' ', '-').lower()
    
    # Find possible Homebrew Cask names
    brew_cask_names = find_brew_cask_name(app_name)
    
    # Check if any of the possible Cask names are installed
    is_installed = any(is_brew_cask_installed(cask) for cask in brew_cask_names)

    # Only process the app if no Homebrew Cask package is installed
    if not is_installed:
        print(f"\nProcessing {app_name}...")

        if not brew_cask_names:
            print(f"No Homebrew Cask found for {app_name}")
        else:
            print(f"Possible Homebrew Casks for {app_name}:")
            for i, cask in enumerate(brew_cask_names, 1):
                print(f"{i}. {cask}")
            print(f"{len(brew_cask_names) + 1}. Skip")

            while True:
                try:
                    choice = int(input("Enter your choice: "))
                    if 1 <= choice <= len(brew_cask_names):
                        brew_cask_name = brew_cask_names[choice - 1]
                        print(f"Found Homebrew Cask: {brew_cask_name}. Reinstalling...")

                        # Check if the app process is running
                        process_was_running = is_app_process_running(app_name)
                        if process_was_running:
                            print(f"Process for {app_name} is running.")
                            if input("Do you want to kill this process? (y/n): ").lower() == 'y':
                                kill_app_process(app_name)
                            else:
                                print(f"Skipping process termination for {app_name}")

                        # Reinstall the application
                        subprocess.run(['brew', 'install', '--cask', '--force', brew_cask_name])

                        # Restart the application if it was running before
                        if process_was_running:
                            restart_app(app_name)
                        break
                    elif choice == len(brew_cask_names) + 1:
                        print(f"Skipping {app_name}")
                        break
                    else:
                        print("Invalid option. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

print("\nAll applications processed.")