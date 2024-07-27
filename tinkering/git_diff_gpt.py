import os
import sys
import json
import subprocess
import hashlib
import concurrent.futures

# Import the virtual environment setup module
path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shared_utils")
sys.path.append(path)
import venv_setup

# Ensure required packages and virtual environment
venv_setup.ensure_packages_and_relaunch(required_packages=['openai', 'tqdm'])
import openai
from tqdm import tqdm

# Load configuration data from the JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Extract values from config
api_key = config['api_key']
organization_id = config['organization_id']
project_id = config['project_id']

# Initialize OpenAI client
openai.api_key = api_key

CACHE_FILE = 'commit_message_cache.json'
MAX_DIFF_LENGTH = 1500  # Set a maximum length for each diff part

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as cache_file:
            return json.load(cache_file)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as cache_file:
        json.dump(cache, cache_file)

def run_openai_query(query, model="gpt-4o-mini", max_tokens=1000, temperature=0.7, top_p=1.0):
    """
    Execute a query to the OpenAI model and retrieve the response.
    """
    try:
        response = openai.chat.completions.create(
            messages=[{"role": "user", "content": query}],
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )

        full_response = response.choices[0].message.content

        return full_response
    except Exception as e:
        print(f"An error occurred while querying OpenAI: {e}")
        return None, 0

def get_git_diff(path="."):
    """
    Get the git diff for the specified path, including staged and unstaged changes.
    """
    try:
        # Verify if the path is a git repository
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Get the unstaged changes
        unstaged_diff = subprocess.run(["git", "diff"], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        unstaged_diff.check_returncode()
        
        # Get the staged changes
        staged_diff = subprocess.run(["git", "diff", "--cached"], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        staged_diff.check_returncode()

        # Combine both diffs
        combined_diff = unstaged_diff.stdout + "\n" + staged_diff.stdout
        return combined_diff.strip()
    except subprocess.CalledProcessError:
        print(f"The path '{path}' is not a valid git repository.")
        return None
    except Exception as e:
        print(f"An error occurred while getting git diff: {e}")
        return None

def split_diff(diff, max_length=MAX_DIFF_LENGTH):
    """
    Split the diff into parts of a specified maximum length.
    """
    return [diff[i:i+max_length] for i in range(0, len(diff), max_length)]

def main():
    try:
        path = input("Enter path for git diff (default: current directory): ") or "."
        # Remove leading and trailing quotes
        path = path.strip('\'"')
        absolute_path = os.path.abspath(path)
        git_diff = get_git_diff(absolute_path)
        if git_diff:
            diff_hash = hashlib.sha256(git_diff.encode()).hexdigest()
            cache = load_cache()
            
            if diff_hash in cache:
                final_commit_message = cache[diff_hash]
            else:
                diff_parts = split_diff(git_diff)
                commit_message = ""

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for part in diff_parts:
                        part_hash = hashlib.sha256(part.encode()).hexdigest()
                        if part_hash in cache:
                            commit_message += cache[part_hash] + "\n"
                        else:
                            query = f"Please generate a detailed commit message for the following git diff:\n{part}"
                            futures.append((executor.submit(run_openai_query, query), part_hash))
                    
                    for future, part_hash in tqdm(futures, desc="Processing diff parts"):
                        part_commit_message = future.result()
                        if part_commit_message:
                            commit_message += part_commit_message + "\n"
                            cache[part_hash] = part_commit_message
                        else:
                            print("Failed to generate commit message for part.")
                            return

                save_cache(cache)
                
                # Send the combined commit message back to OpenAI for summarization
                final_query = f"Please summarize the following commit messages into a single commit message:\n{commit_message}"
                final_commit_message = run_openai_query(final_query, max_tokens=3000)
                
                cache[diff_hash] = final_commit_message
                save_cache(cache)

            print("\nCommit Message:")
            print(final_commit_message)
        else:
            print("No git diff available or an error occurred.")
    except KeyboardInterrupt:
        print("\nReceived KeyboardInterrupt")
        sys.exit()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()