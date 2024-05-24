import json
import base64
import os
import mimetypes
from datetime import datetime
from urllib.parse import urlparse
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import requests

def save_base64_to_file(base64_str, output_directory, output_file_name):
    file_path = os.path.join(output_directory, output_file_name)
    # Decode and write the file
    with open(file_path, "wb") as file:
        file.write(base64.b64decode(base64_str))

def log_skipped_entries(output_directory, original_file_name, url, headers):
    log_file_path = os.path.join(output_directory, 'skipped_entries.log')
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"Skipped entry {original_file_name} due to non-ASCII characters\n")
        log_file.write(f"URL: {url}\n")
        log_file.write(f"Headers: {json.dumps(headers, separators=(',', ':'))}\n\n")

def process_skipped_entries(output_directory):
    log_file_path = os.path.join(output_directory, 'skipped_entries.log')
    if not os.path.exists(log_file_path):
        return
    with open(log_file_path, 'r') as log_file: 
        lines = log_file.readlines()
    
    remaining_entries = []

    for i in range(0, len(lines), 4):
        retry_skipped_entries(output_directory, lines, remaining_entries, i)

    # Rewrite the log file with remaining entries
    with open(log_file_path, 'w') as log_file:
        log_file.writelines(remaining_entries)

def retry_skipped_entries(output_directory, lines, remaining_entries, i):
    output_file_name = lines[i].split()[2]
    url = lines[i + 1].split("URL: ")[1].strip()
    headers = json.loads(lines[i + 2].split("Headers: ")[1].strip())
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and 'image' in response.headers['Content-Type']:
        save_base64_to_file(base64.b64encode(response.content).decode(), output_directory, output_file_name)
        print(f"Retrieved entry {output_file_name} ")
    else:
        # If the retry was not successful, keep the entry in the log
        remaining_entries.extend(lines[i:i+4])
        print(f"Retrieval failed for {output_file_name} with status code {response.status_code}")

def process_har_entries(output_directory, index, entry):
    request = entry.get("request", {})
    url = request.get ("url")
    parsed_url = urlparse(url)
    original_file_name = os.path.basename(parsed_url.path)
    response = entry.get("response", {})
    content = response.get("content", {})
    encoding = content.get("encoding")
    mime_type = content.get("mimeType", "application/octet-stream")
    if mime_type != "image/jpeg":
        return  # Only process JPEG files
    base64_str = content.get("text")
    formatted_index = str(index).zfill(5)
    if original_file_name:
        file_name, extension = os.path.splitext(original_file_name)
        output_file_name = f"{formatted_index}_{file_name}.jpeg"
    else:
        output_file_name = f"{formatted_index}_unknown.jpeg"
    if encoding == "base64" and base64_str: 
        # Check for non-ASCII characters in Base64 string
        handle_base64_content(output_directory, entry, url, base64_str, output_file_name)

def handle_base64_content(output_directory, entry, url, base64_str, output_file_name):
    try:
        base64_str.encode('ascii')
    except UnicodeEncodeError:
        headers = {h["name"]: h["value"] for h in entry.get("request", {}).get("headers", [])}
        log_skipped_entries(output_directory, output_file_name, url, headers)
        return    
    save_base64_to_file(base64_str, output_directory, output_file_name)
    print(f"Processed entry {output_file_name}")

def extract_base64_from_har(har_file_path, output_directory):
    with open(har_file_path, 'r', encoding='utf-8') as har_file:  # Explicitly specify UTF-8 encoding
        har_data = json.load(har_file)

    entries = har_data.get("log", {}).get("entries", [])

    for index, entry in enumerate(entries):
        process_har_entries(output_directory, index, entry)

# Use tkinter to open a file dialog to select the .HAR file
def select_har_file():
    root = Tk()
    root.withdraw()  # Hide the root window
    har_file_path = askopenfilename(title="Select .HAR file", filetypes=[("HAR files", "*.har")])
    root.destroy()
    return har_file_path

# Main script execution
har_file_path = select_har_file()
if not har_file_path:
    print("No file selected. Exiting...")
    exit()

har_file_name = os.path.splitext(os.path.basename(har_file_path))[0]

# Set the output directory to the same directory as the .HAR file
output_directory = os.path.join(os.path.dirname(har_file_path), har_file_name)
os.makedirs(output_directory, exist_ok=True)

if __name__ == '__main__':
    try:
        extract_base64_from_har(har_file_path, output_directory)
        process_skipped_entries(output_directory)
    except BaseException:
        import sys
        print(sys.exc_info()[0])
        import traceback
        print(traceback.format_exc())

print("Press Enter to continue ...")
input()
