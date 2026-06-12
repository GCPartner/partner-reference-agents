import os
import shutil

src = "/usr/local/google/home/veermuchandi/.gemini/jetski/skills"
dst = "/usr/local/google/home/veermuchandi/code/rad-skills"

def sync():
    if not os.path.exists(src):
        print(f"Source does not exist: {src}")
        return
    
    print(f"Syncing from {src} to {dst}")
    
    # We use dirs_exist_ok=True to merge directories
    try:
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print("Sync completed successfully.")
    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    sync()
