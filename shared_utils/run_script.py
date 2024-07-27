import os
import sys
import venv
import subprocess
import ast
import importlib.util
import shlex
import atexit
import shutil

VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.hidden_venv')

def create_venv():
    print("Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True)

def get_venv_python():
    if sys.platform.startswith('win'):
        return os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    return os.path.join(VENV_DIR, 'bin', 'python')

def get_imports(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:  # absolute import
                imports.add(node.module.split('.')[0])
    return imports

def is_package_installed(package):
    venv_python = get_venv_python()
    result = subprocess.run([venv_python, '-c', f'import {package}'], capture_output=True, text=True)
    return result.returncode == 0

def install_package(package):
    venv_python = get_venv_python()
    print(f"Installing {package}...")
    subprocess.check_call([venv_python, '-m', 'pip', 'install', package])

def ensure_packages(packages):
    for package in packages:
        if not is_package_installed(package):
            install_package(package)

def run_main_script(main_script, args):
    venv_python = get_venv_python()
    print(f"Running the main script: {main_script}")
    quoted_args = [shlex.quote(arg) for arg in args]
    cmd = [venv_python, main_script] + quoted_args
    subprocess.run(cmd, check=True)

def cleanup_venv():
    if os.path.exists(VENV_DIR):
        print("Cleaning up virtual environment...")
        shutil.rmtree(VENV_DIR)

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_python_file>")
        sys.exit(1)

    main_script = os.path.abspath(sys.argv[1])
    if not os.path.exists(main_script):
        print(f"Error: The file {main_script} does not exist.")
        sys.exit(1)

    # Cleanup any existing venv
    cleanup_venv()

    # Create new venv
    create_venv()

    # Register cleanup function
    atexit.register(cleanup_venv)

    # Get imports from the main script
    imports = get_imports(main_script)

    # Filter out standard library modules
    stdlib_modules = set(sys.stdlib_module_names)
    third_party_imports = imports - stdlib_modules

    # Ensure all required packages are installed
    ensure_packages(third_party_imports)

    try:
        # Run the main script
        run_main_script(main_script, sys.argv[2:])
    except subprocess.CalledProcessError as e:
        print(f"Error running the main script: {e}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Cleanup will be done by atexit
        pass

if __name__ == "__main__":
    main()