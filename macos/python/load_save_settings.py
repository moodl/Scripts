import os
import subprocess
import json
import tempfile

# Define the default path for the JSON configuration file
config_file_path = os.path.expanduser("~/Desktop/macos_settings_config.json")

def export_macos_settings():
    """
    Export macOS settings using the `defaults` command.
    """
    print("Exporting macOS settings...")
    try:
        result = subprocess.run(["defaults", "read"], capture_output=True, text=True, check=True)
        macos_settings = result.stdout
        return macos_settings
    except subprocess.CalledProcessError as e:
        print(f"Error exporting macOS settings: {e}")
        return None

def export_zsh_profile():
    """
    Export Terminal settings by reading the .zshrc file.
    """
    print("Exporting Terminal settings...")
    zsh_profile_path = os.path.expanduser("~/.zshrc")
    if os.path.exists(zsh_profile_path):
        with open(zsh_profile_path, 'r') as file:
            zsh_profile_content = file.read()
        return zsh_profile_content
    else:
        print(".zshrc not found. Ensure you have the correct file.")
        return None

def import_macos_settings(settings):
    """
    Import macOS settings using the `defaults` command.
    """
    print("Importing macOS settings...")
    with tempfile.NamedTemporaryFile(delete=False) as temp_plist_file:
        temp_plist_path = temp_plist_file.name
        temp_plist_file.write(settings.encode('utf-8'))
    
    try:
        subprocess.run(["defaults", "import", temp_plist_path], check=True)
        print("macOS settings imported successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error importing macOS settings: {e}")
    finally:
        os.remove(temp_plist_path)

def import_zsh_profile(content):
    """
    Import Terminal settings by writing to the .zshrc file.
    """
    print("Importing Terminal settings...")
    zsh_profile_path = os.path.expanduser("~/.zshrc")
    with open(zsh_profile_path, 'w') as file:
        file.write(content)
    print("Terminal settings imported successfully.")

def save_config(macos_settings, zsh_profile_content):
    """
    Save the exported settings to a JSON file.
    """
    config = {
        "macos_settings": macos_settings,
        "zsh_profile_content": zsh_profile_content
    }
    with open(config_file_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)
    print(f"Configuration saved to {config_file_path}")

def load_config(import_path):
    """
    Load the settings from the JSON configuration file.
    """
    if os.path.exists(import_path):
        with open(import_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    else:
        print(f"{import_path} not found.")
        return None

def main():
    """
    Main function to export or import settings based on user input.
    """
    choice = input("Do you want to export or import settings? (export/import): ").strip().lower()
    
    if choice == "export":
        macos_settings = export_macos_settings()
        zsh_profile_content = export_zsh_profile()
        if macos_settings and zsh_profile_content:
            save_config(macos_settings, zsh_profile_content)
    elif choice == "import":
        import_path = input("Enter the path for the JSON configuration file to import (e.g., ~/Desktop/macos_settings_config.json): ").strip()
        import_path = os.path.expanduser(import_path)
        config = load_config(import_path)
        if config:
            macos_settings = config.get("macos_settings", "")
            zsh_profile_content = config.get("zsh_profile_content", "")
            if macos_settings:
                import_macos_settings(macos_settings)
            if zsh_profile_content:
                import_zsh_profile(zsh_profile_content)
    else:
        print("Invalid choice. Please enter 'export' or 'import'.")

if __name__ == "__main__":
    main()