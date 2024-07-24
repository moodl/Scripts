import os
import sys
import venv
import subprocess
import ast
import importlib.util

def create_venv(venv_path):
    print("Creating virtual environment...")
    venv.create(venv_path, with_pip=True)

def get_venv_python(venv_path):
    if sys.platform.startswith('win'):
        return os.path.join(venv_path, 'Scripts', 'python.exe')
    return os.path.join(venv_path, 'bin', 'python')

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

def is_package_installed(venv_python, package):
    result = subprocess.run([venv_python, '-c', f'import {package}'], capture_output=True, text=True)
    return result.returncode == 0

def install_package(venv_python, package):
    print(f"Installing {package}...")
    subprocess.check_call([venv_python, '-m', 'pip', 'install', package])

def ensure_packages(venv_python, packages):
    for package in packages:
        if not is_package_installed(venv_python, package):
            install_package(venv_python, package)

def run_main_script(venv_python, main_script, args):
    print(f"Running the main script: {main_script}")
    cmd = [venv_python, main_script] + args
    subprocess.check_call(cmd)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_python_file>")
        sys.exit(1)

    main_script = os.path.abspath(sys.argv[1])
    if not os.path.exists(main_script):
        print(f"Error: The file {main_script} does not exist.")
        sys.exit(1)

    script_name = os.path.basename(main_script)
    script_dir = os.path.dirname(main_script)
    venv_name = f"venv_{os.path.splitext(script_name)[0]}"
    venv_path = os.path.join(script_dir, venv_name)

    if not os.path.exists(venv_path):
        create_venv(venv_path)

    venv_python = get_venv_python(venv_path)

    # Get imports from the main script
    imports = get_imports(main_script)

    # Filter out standard library modules
    stdlib_modules = set(sys.stdlib_module_names)
    third_party_imports = imports - stdlib_modules

    # Ensure all required packages are installed
    ensure_packages(venv_python, third_party_imports)

    # Run the main script
    run_main_script(venv_python, main_script, sys.argv[2:])