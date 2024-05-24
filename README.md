# .har-jpeg-extraction
Extracts image/jpeg entries from a .har file and saves them. 
Tested with Python 3.11.

Does the following: 
- Creates an output folder with the same name as the .har file, and in the same folder as well. 
- Tries to extract every image/jpeg file and save them as individual files by decoding the base64 value. 
    - If for some reason the base64 of an image is corrupt (which makes them contain non-ASCII characters), the file will be skipped and the incident will be logged in the output folder. 
- Tries to retrieve the image once for each skipped entry from the url w/ the original request headers.
- Rewrites the log so that only information about the files that are ultimately NOT saved on the disk remains in the log file. 
- The status of retrieval will be printed in a console as well, which will not disappear until you have pressed a button. 

This script will attatch the entries' index numbers as 5-digit prefix. They might not be consecutive, since the only reason they are there is for the sake of file sorting. 
