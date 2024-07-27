import os
import sys

def create_launch_agent(script_path, save_to_launch_agents=False):
    # Extract the base name (without extension) to use as the plist name
    base_name = os.path.splitext(os.path.basename(script_path))[0]
    
    if save_to_launch_agents:
        plist_dir = os.path.expanduser("~/Library/LaunchAgents")
        os.makedirs(plist_dir, exist_ok=True)
        plist_name = os.path.join(plist_dir, f"{base_name}.plist")
    else:
        plist_name = os.path.splitext(script_path)[0] + '.plist'
    
    # Create the content of the plist
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.{base_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/osascript</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>5</integer>
</dict>
</plist>
"""
    # Write the plist content to the file
    with open(plist_name, 'w') as file:
        file.write(plist_content)
    
    print(f"LaunchAgent plist created at {plist_name}")

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 create_launch_agent.py path_to_your_script.scpt [--launch-agents]")
        sys.exit(1)
    
    script_path = sys.argv[1]
    if not os.path.isfile(script_path):
        print(f"Error: {script_path} does not exist or is not a file.")
        sys.exit(1)
    
    save_to_launch_agents = len(sys.argv) == 3 and sys.argv[2] == "--launch-agents"
    create_launch_agent(script_path, save_to_launch_agents)