import json
import base64
import os
import mimetypes
from datetime import datetime
from urllib.parse import urlparse
from tkinter import Tk
from tkinter.filedialog import askopenfilename

def save_base64_to_file(base64_str, output_dir, original_file_name, mime_type, formatted_index):
    if mime_type != "image/jpeg":
        return  # Only process JPEG files

    extension = '.jpeg'

    if original_file_name:
        file_name, extension = os.path.splitext(original_file_name)
        output_file_name = f"{formatted_index}_{file_name}{extension}"
    else:
        output_file_name = f"{formatted_index}_unknown.jpeg"  # Fallback if original file name is not provided

    # Check for non-ASCII characters in Base64 string
    try:
        base64_str.encode('ascii')
    except UnicodeEncodeError:
        log_skipped_entry(output_dir, output_file_name)
        return

    file_path = os.path.join(output_dir, output_file_name)

    # Decode and write the file
    with open(file_path, "wb") as file:
        file.write(base64.b64decode(base64_str))

def log_skipped_entry(output_dir, original_file_name):
    log_file_path = os.path.join(output_dir, 'skipped_entries.log')
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"Skipped entry {original_file_name} due to non-ASCII characters\n")

def extract_base64_from_har(har_path, output_dir):
    with open(har_path, 'r', encoding='utf-8') as har_file:  # Explicitly specify UTF-8 encoding
        har_data = json.load(har_file)

    entries = har_data.get("log", {}).get("entries", [])

    for index, entry in enumerate(entries):
        request = entry.get("request", {})
        url = request.get ("url")
        clean_url = urlparse(url)
        original_file_name = os.path.basename(clean_url.path)
        response = entry.get("response", {})
        content = response.get("content", {})
        encoding = content.get("encoding")
        mime_type = content.get("mimeType", "application/octet-stream")
        base64_str = content.get("text")
        formatted_index = str(index).zfill(5)

        if encoding == "base64" and base64_str:
            save_base64_to_file(base64_str, output_dir, original_file_name, mime_type, formatted_index)
            print(f"Processed entry {original_file_name} with MIME type {mime_type}")

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

# Set the output directory to the same directory as the .HAR file
output_directory = os.path.join(os.path.dirname(har_file_path), 'extracted_files')
os.makedirs(output_directory, exist_ok=True)

extract_base64_from_har(har_file_path, output_directory)
