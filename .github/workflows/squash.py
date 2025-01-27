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
import os
from time import sleep

# .github/workflows/squash.py -b actions-data-download -m "GitHub-Action-Workflow-Market-Data-Download-(Default-Config)"
argParser = argparse.ArgumentParser()
required = True
argParser.add_argument(
    "-m", "--message", help="Commit message to look for", required=required
)
argParser.add_argument(
    "-b", "--branch", help="Origin branch name to push to", required=required
)
args = argParser.parse_args()

# args.message = "GitHub-Action-Workflow-Market-Data-Download-(Default-Config)"
# args.branch = "actions-data-download"

c_msg = args.message  # "GitHub Action Workflow - Market Data Download (Default Config)"

print(f"[+] === SQUASHING COMMITS : {args.branch} branch ===")
print("[+] Saving Commit messages log..")
os.system("git log --pretty=oneline > msg.log")

sleep(5)

lines = None
with open("msg.log", "r") as f:
    lines = f.readlines()

cnt = 0
commit_hash = ""
previousCommitFound = False
for line in lines:
    if c_msg in line:
        cnt += 1
        previousCommitFound = True
    else:
        if previousCommitFound:
            commit_hash = line.split(" ")[0]
            cnt -= 1
            break
        else:
            cnt += 1


print(f"[+] Reset at HEAD~{cnt}")
print(f"[+] Reset hash = {commit_hash}")
print(f"git reset --soft {commit_hash}")
print(f"git commit -m '{c_msg}'")

if cnt < 1:
    print("[+] No Need to Squash! Skipping...")
else:
    os.system(f"git reset --soft HEAD~{cnt}")
    os.system(f"git commit -m '{c_msg}'")
    os.system(f"git push -f -u origin {args.branch}")  # actions-data-download

os.remove("msg.log")
sleep(5)

print("[+] === SQUASHING COMMITS : DONE ===")
