import subprocess
import sys
import os
import logging

# Logger konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REQUIRED_PACKAGES = []

def check_virtual_environment():
    """
    Check if the script is running inside a virtual environment.

    Returns:
        bool: True if the script is running inside a virtual environment, False otherwise.
    """
    return sys.prefix != sys.base_prefix

def install_packages(venv_dir):
    """
    Install required packages in the virtual environment.

    Args:
        venv_dir (str): Path to the virtual environment directory.
    """
    logging.info("Installing required packages...")
    subprocess.check_call([os.path.join(venv_dir, "bin", "pip"), "install"] + REQUIRED_PACKAGES)

def setup_virtual_environment(venv_dir=".venv"):
    """
    Create and set up a virtual environment if it does not already exist.

    Args:
        venv_dir (str, optional): Path to the virtual environment directory. Defaults to ".venv".

    Returns:
        str: Path to the virtual environment directory.
    """
    if not os.path.exists(venv_dir):
        logging.info("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        logging.info("Upgrading pip...")
        subprocess.check_call([os.path.join(venv_dir, "bin", "pip"), "install", "--upgrade", "pip"])
    return venv_dir

def check_and_install_packages(required_packages):
    """
    Check if required packages are installed and install them if they are not.

    Args:
        required_packages (list): List of required package names.

    Returns:
        bool: True if all required packages are installed, False otherwise.
    """
    global REQUIRED_PACKAGES
    REQUIRED_PACKAGES = required_packages
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        return False
    return True

def ensure_packages_and_relaunch(venv_dir=".venv", required_packages=[]):
    """
    Ensure that the script is running in a virtual environment with all required packages installed.
    If not, create the virtual environment, install the packages, and relaunch the script inside the virtual environment.

    Args:
        venv_dir (str, optional): Path to the virtual environment directory. Defaults to ".venv".
        required_packages (list, optional): List of required package names. Defaults to [].

    Usage:
        1. Import this module in your script.
        2. Call `ensure_packages_and_relaunch(venv_dir, required_packages)` at the beginning of your script.
        3. Continue with your script's main functionality after ensuring all packages are installed.

    Example:
        ```python
        import venv_setup

        if __name__ == "__main__":
            venv_setup.ensure_packages_and_relaunch(venv_dir=".venv_create_formula", required_packages=['requests', 'tqdm'])

            # Your main script functionality goes here
        ```
    """
    if not check_virtual_environment():
        venv_dir = setup_virtual_environment(venv_dir)
        logging.info("Re-running script in virtual environment...")
        subprocess.check_call([os.path.join(venv_dir, "bin", "python")] + sys.argv)
        sys.exit()

    if not check_and_install_packages(required_packages):
        install_packages(venv_dir)
        logging.info("Re-running script after installing packages...")
        subprocess.check_call([sys.executable] + sys.argv)
        sys.exit()