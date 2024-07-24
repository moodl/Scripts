import os
import subprocess
import sys
import re

def install_homebrew():
    if not command_exists("brew"):
        answer = input("Homebrew is not installed. Do you want to install Homebrew? (y/n) ")
        if answer.lower().startswith('y'):
            process = subprocess.run(["/bin/bash", "-c", "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"], capture_output=True, text=True)
            if process.returncode != 0:
                print("Homebrew installation failed.")
                sys.exit(1)
            print("Homebrew successfully installed.")
        else:
            print("Homebrew is required. Exiting.")
            sys.exit(1)

def install_ffmpeg():
    if not command_exists("ffmpeg"):
        answer = input("ffmpeg is not installed. Do you want to install ffmpeg? (y/n) ")
        if answer.lower().startswith('y'):
            process = subprocess.run(["brew", "install", "ffmpeg"], capture_output=True, text=True)
            if process.returncode != 0:
                print("ffmpeg installation failed.")
                sys.exit(1)
            print("ffmpeg successfully installed.")
        else:
            print("ffmpeg is required. Exiting.")
            sys.exit(1)

def command_exists(cmd):
    return subprocess.run(["which", cmd], capture_output=True, text=True).returncode == 0

def create_playlist(directory, playlist_file):
    with open(playlist_file, 'w') as f:
        f.write("#EXTM3U\n")
        
        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith('.mp4'):
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, directory)
                    files.append(relative_path)
        
        # Sort files based on numeric parts in the filename
        files.sort(key=lambda f: [int(n) if n.isdigit() else n for n in re.split(r'(\d+)', f)])
        
        for file in files:
            f.write(f"{file}\n")
    
    print(f"Playlist created: {playlist_file}")

def main():
    install_homebrew()
    install_ffmpeg()

    if len(sys.argv) < 2:
        print("Please provide a valid directory.")
        sys.exit(1)

    main_directory = sys.argv[1]
    if not os.path.isdir(main_directory):
        print("Please provide a valid directory.")
        sys.exit(1)

    playlist_name = input("Enter the name of the playlist file (without extension): ")
    playlist_file = os.path.join(main_directory, f"{playlist_name}.m3u")

    create_playlist(main_directory, playlist_file)

if __name__ == "__main__":
    main()