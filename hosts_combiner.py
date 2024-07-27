import os
import aiohttp
import asyncio

async def download_hosts_file(session, url):
    """
    Asynchronously download the hosts file from the given URL.
    """
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientError as e:
        print(f"Error downloading {url}: {e}")
        return None

async def combine_hosts_files(urls_file_path, combined_hosts_file_path):
    """
    Combine hosts files from URLs specified in the given text file and save to the combined hosts file.
    """
    if not os.path.exists(urls_file_path):
        print(f"The file {urls_file_path} does not exist.")
        return

    try:
        with open(urls_file_path, 'r') as urls_file:
            urls = [url.strip() for url in urls_file.readlines() if url.strip()]
    except IOError as e:
        print(f"Error reading {urls_file_path}: {e}")
        return

    combined_hosts_content = ""

    async with aiohttp.ClientSession() as session:
        tasks = [download_hosts_file(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

        for url, hosts_content in zip(urls, results):
            if hosts_content:
                combined_hosts_content += f"# Start of hosts from {url}\n"
                combined_hosts_content += hosts_content
                combined_hosts_content += f"\n# End of hosts from {url}\n\n"

    try:
        with open(combined_hosts_file_path, 'w') as combined_hosts_file:
            combined_hosts_file.write(combined_hosts_content)
        print(f"Combined hosts file saved to {combined_hosts_file_path}")
    except IOError as e:
        print(f"Error writing to {combined_hosts_file_path}: {e}")

def main():
    urls_file_path = input("Enter the path to the text file containing the URLs of the hosts files: ").strip()
    combined_hosts_file_path = input("Enter the path where the combined hosts file should be saved: ").strip()
    asyncio.run(combine_hosts_files(urls_file_path, combined_hosts_file_path))

if __name__ == "__main__":
    main()