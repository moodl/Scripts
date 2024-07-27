import subprocess

def cprint(input):
    print(input)

def main():
    while (True):
        subpixel_rendering_level = input("")

def set_subpixel_rendering(level):
    execute_bash_command(f"defaults -currentHost write -globalDomain AppleFontSmoothing {level}")

def execute_bash_command(command):
    """
    Executes a Bash command and returns the output.

    Parameters:
    command (str): The Bash command to execute.

    Returns:
    str: The output of the command.
    """
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

if __name__ == "__main__":
    pass