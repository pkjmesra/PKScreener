import argparse
import os
from time import sleep

argParser = argparse.ArgumentParser()
required = True
argParser.add_argument("-m", "--message", help="Commit message to look for", required=required)
argParser.add_argument(
    "-b", "--branch", help="Origin branch name to push to", required=required
)
args = argParser.parse_args()

c_msg = args.message #"GitHub Action Workflow - Market Data Download (Default Config)"

print("[+] === SQUASHING COMMITS : actions-data-download branch ===")
print("[+] Saving Commit messages log..")
os.system("git log --pretty=oneline > msg.log")

sleep(5)

lines = None
with open("msg.log", "r") as f:
    lines = f.readlines()

cnt = 0
commit_hash = ""
for line in lines:
    if c_msg in line:
        cnt += 1
    else:
        commit_hash = line.split(" ")[0]
        cnt -= 1
        break


print(f"[+] Reset at HEAD~{cnt}")
print(f"[+] Reset hash = {commit_hash}")
print(f"git reset --soft {commit_hash}")
print(f"git commit -m '{c_msg}'")

if cnt < 1:
    print("[+] No Need to Squash! Skipping...")
else:
    os.system(f"git reset --soft HEAD~{cnt}")
    os.system(f"git commit -m '{c_msg}'")
    os.system(f"git push -f -u origin {args.branch}") # actions-data-download

os.remove("msg.log")
sleep(5)

print("[+] === SQUASHING COMMITS : DONE ===")
