import os
import logging

# Configure logging
logging.basicConfig(filename='rename_log.txt', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def replace_spaces_in_filenames(directory):
    logging.info(f"Starting to scan directory: {directory}")
    
    # First, rename directories to avoid issues with nested renames
    for root, dirs, _ in os.walk(directory, topdown=False):
        for name in dirs:
            if ' ' in name:
                old_path = os.path.join(root, name)
                new_name = name.replace(" ", "_")
                new_path = os.path.join(root, new_name)
                try:
                    os.rename(old_path, new_path)
                    logging.info(f"Renamed directory: {old_path} -> {new_path}")
                    update_references_in_text_files(directory, old_path, new_path)
                except Exception as e:
                    logging.error(f"Failed to rename directory: {old_path} -> {new_path}, Error: {e}")

    # Then, rename files
    for root, _, files in os.walk(directory, topdown=False):
        logging.info(f"Scanning directory: {root}")
        
        for name in files:
            if ' ' in name:
                old_path = os.path.join(root, name)
                new_name = name.replace(" ", "_")
                new_path = os.path.join(root, new_name)
                try:
                    os.rename(old_path, new_path)
                    logging.info(f"Renamed file: {old_path} -> {new_path}")
                    update_references_in_text_files(directory, old_path, new_path)
                except Exception as e:
                    logging.error(f"Failed to rename file: {old_path} -> {new_path}, Error: {e}")

def update_references_in_text_files(directory, old_path, new_path):
    text_file_extensions = [
        '.txt', '.csv', '.md', '.py', '.json', '.xml', '.html', '.htm',
        '.yaml', '.yml', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', 
        '.h', '.hpp', '.cs', '.rb', '.go', '.rs', '.php', '.pl', '.sh', 
        '.bat', '.ps1', '.r', '.jl', '.scala', '.swift', '.kt', '.kts',
        '.m', '.mm', '.groovy', '.sql', '.ini', '.conf', '.cfg', '.log',
        '.properties', '.gradle', '.makefile', '.mk', '.dockerfile', '.toml',
        '.env', '.tex', '.rmd', '.lhs'
    ]

    logging.info(f"Updating references in text files for: {old_path} -> {new_path}")
    for root, _, files in os.walk(directory):
        for name in files:
            if any(name.endswith(ext) for ext in text_file_extensions):
                file_path = os.path.join(root, name)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                    updated_content = content.replace(old_path, new_path)
                    if updated_content != content:
                        with open(file_path, 'w', encoding='utf-8', errors='ignore') as file:
                            file.write(updated_content)
                        logging.info(f"Updated references in file: {file_path}")
                except Exception as e:
                    logging.error(f"Failed to update file: {file_path}, Error: {e}")

def main():
    directory = input("Please enter the directory path: ")
    if os.path.isdir(directory):
        replace_spaces_in_filenames(directory)
        print("All done! Check rename_log.txt for details.")
    else:
        print("Invalid directory path!")

if __name__ == "__main__":
    main()