"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
import argparse
import re

argParser = argparse.ArgumentParser()
required = True
argParser.add_argument("-f", "--find", help="Find this item", required=required)
argParser.add_argument(
    "-r", "--replace", help="Replace with this item", required=required
)
argParser.add_argument(
    "-t", "--type", help='Type: One of "link" or "text" type', required=required
)
argParser.add_argument(
    "-p", "--path", help="Relative file path for the file", required=required
)
args = argParser.parse_args()

def update_file_content():
    """Update the file content directly with simple string replacement"""
    with open(args.path, "r", encoding='utf-8') as f:
        content = f.read()
    
    if args.type == "link":
        # For links, we want to replace the version in URLs
        print(f"Looking for '{args.find}' in URLs to replace with '{args.replace}'")
        
        # Pattern to match URLs that contain the find text
        # This will match both inline links and reference definitions
        url_pattern = r'(https?://[^\s<>"{}|\\^`[\]]*)'
        
        def replace_in_url(match):
            url = match.group(1)
            if args.find in url:
                old_url = url
                new_url = url.replace(args.find, args.replace)
                print(f"Replacing URL: {old_url} -> {new_url}")
                return new_url
            return url
        
        # Replace in all URLs
        updated_content = re.sub(url_pattern, replace_in_url, content)
        
    elif args.type == "text":
        # For text, simple replacement throughout the content
        print(f"Replacing text '{args.find}' with '{args.replace}'")
        if args.find in content:
            updated_content = content.replace(args.find, args.replace)
        else:
            updated_content = content
            print(f"Text '{args.find}' not found in content")
    else:
        print(f"Unknown type: {args.type}")
        updated_content = content
    
    # Write the updated content back
    with open(args.path, "w", encoding='utf-8') as f:
        f.write(updated_content)
    
    print("Update completed successfully!")

if __name__ == "__main__":
    update_file_content()