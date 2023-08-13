import os
from time import sleep

c_msg = "GitHub Action Workflow - Market Data Download (Default Config)"

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
    os.system("git push -f -u origin actions-data-download")

os.remove("msg.log")
sleep(5)

print("[+] === SQUASHING COMMITS : DONE ===")
