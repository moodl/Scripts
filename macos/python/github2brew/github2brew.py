import subprocess
import sys
import os
import hashlib
import re
import argparse
import logging
import shutil

# print(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "shared_utils"))  # Import-Pfad anpassen
import venv_setup  # Import der generischen Bibliothek

# Logger konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_sha256(url):
    import requests
    from tqdm import tqdm
    logging.info(f"Calculating SHA256 for URL: {url}")
    response = requests.get(url, stream=True)
    sha256_hash = hashlib.sha256()
    total_size = int(response.headers.get('content-length', 0))
    with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading", ncols=75) as pbar:
        for byte_block in response.iter_content(4096):
            sha256_hash.update(byte_block)
            pbar.update(len(byte_block))
    logging.info("SHA256 calculation completed.")
    return sha256_hash.hexdigest()

def generate_formula(name, description, homepage, url, sha256, license_type):
    logging.info("Generating Homebrew formula...")
    formula_content = f"""class {name.capitalize()} < Formula
  desc "{description}"
  homepage "{homepage}"
  url "{url}"
  sha256 "{sha256}"
  license "{license_type}"

  def install
    bin.install "{name}"
  end

  test do
    system "#{{bin}}/{name}", "--version"
  end
end
"""
    logging.info("Formula generation completed.")
    return formula_content

def create_homebrew_formula(github_url):
    import requests
    logging.info(f"Fetching release information from GitHub URL: {github_url}")
    repo_name = re.search(r'github.com/(.*?)/(.*?)(/|$)', github_url).groups()
    api_url = f"https://api.github.com/repos/{repo_name[0]}/{repo_name[1]}/releases/latest"

    response = requests.get(api_url)
    release_info = response.json()

    name = repo_name[1]
    description = release_info['name']
    homepage = f"https://github.com/{repo_name[0]}/{repo_name[1]}"
    tarball_url = release_info['tarball_url']
    sha256 = calculate_sha256(tarball_url)
    license_type = "MIT"  # Beispiel-Lizenz, passe dies bei Bedarf an

    formula = generate_formula(name, description, homepage, tarball_url, sha256, license_type)

    formula_path = os.path.join('Formula', f"{name}.rb")
    os.makedirs(os.path.dirname(formula_path), exist_ok=True)
    with open(formula_path, 'w') as file:
        file.write(formula)

    logging.info(f"Formula successfully created: {formula_path}")
    return formula_path, name

def clone_tap_repository(tap_url, tap_dir):
    if not os.path.exists(tap_dir):
        logging.info(f"Cloning tap repository from {tap_url}...")
        subprocess.check_call(['git', 'clone', tap_url, tap_dir])
    else:
        logging.info("Tap repository already exists. Pulling latest changes...")
        subprocess.check_call(['git', '-C', tap_dir, 'pull'])

def commit_and_push_formula(tap_dir, formula_path):
    logging.info("Copying formula to tap repository...")
    shutil.copy(formula_path, tap_dir)

    logging.info("Committing and pushing changes to tap repository...")
    subprocess.check_call(['git', '-C', tap_dir, 'add', '.'])
    subprocess.check_call(['git', '-C', tap_dir, 'commit', '-m', 'Add new formula'])
    subprocess.check_call(['git', '-C', tap_dir, 'push'])

def install_package(formula_name):
    logging.info(f"Installing {formula_name} package via Homebrew...")
    subprocess.check_call(['brew', 'install', '--build-from-source', formula_name])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub URL für Homebrew-Formel übergeben")
    parser.add_argument("github_url", help="Die URL des GitHub-Repositories")
    parser.add_argument("tap_url", help="Die URL des Homebrew-Tap-Repositories")
    args = parser.parse_args()

    # Sicherstellen, dass das Skript im virtuellen Umfeld läuft und alle Pakete installiert sind
    venv_setup.ensure_packages_and_relaunch(venv_dir=".venv_create_formula", required_packages=['requests', 'tqdm'])

    formula_path, formula_name = create_homebrew_formula(args.github_url)

    tap_dir = os.path.join(os.getcwd(), "homebrew-tap")
    clone_tap_repository(args.tap_url, tap_dir)
    commit_and_push_formula(tap_dir, formula_path)
    install_package(formula_name)