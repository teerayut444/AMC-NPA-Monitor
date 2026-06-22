import os
import json
import base64
import urllib.request
import urllib.error
import ssl

# Configuration file name
CONFIG_FILE = "github_config.json"
GITIGNORE_FILE = ".gitignore"

DEFAULT_IGNORE_PATTERNS = [
    "github_config.json",  # Keep token private!
    "__pycache__",
    ".git",
    ".env",
    ".vscode",
    "node_modules",
    ".streamlit"
]

def create_default_gitignore():
    """Creates a .gitignore file if it doesn't exist to ensure token is not committed."""
    patterns_to_add = ["github_config.json", ".env", "__pycache__/", "*.pyc"]
    existing_patterns = set()
    
    if os.path.exists(GITIGNORE_FILE):
        try:
            with open(GITIGNORE_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    existing_patterns.add(line.strip())
        except Exception:
            pass
            
    new_patterns = [p for p in patterns_to_add if p not in existing_patterns]
    if new_patterns:
        mode = "a" if os.path.exists(GITIGNORE_FILE) else "w"
        try:
            with open(GITIGNORE_FILE, mode, encoding="utf-8") as f:
                if mode == "a" and not existing_patterns:
                    f.write("\n")
                for p in new_patterns:
                    f.write(f"{p}\n")
            print(f"✅ Added {new_patterns} to {GITIGNORE_FILE}")
        except Exception as e:
            print(f"⚠️ Could not write to {GITIGNORE_FILE}: {e}")

def load_config():
    """Loads configuration from github_config.json."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Ensure all required keys exist
                required_keys = ["token", "repo_owner", "repo_name", "branch"]
                if all(k in config for k in required_keys):
                    return config
        except Exception as e:
            print(f"⚠️ Error reading config file: {e}")
    return None

def save_config(config):
    """Saves configuration to github_config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"💾 Configuration saved to {CONFIG_FILE}")
        create_default_gitignore()
    except Exception as e:
        print(f"⚠️ Error saving config file: {e}")

def setup_config():
    """Prompts user for configuration details."""
    print("=== GitHub Auto Uploader Setup ===")
    print("กรุณากรอกข้อมูลสำหรับเชื่อมต่อ GitHub API:")
    
    # Try to load existing partial config
    existing = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except:
            pass

    token = input(f"GitHub Personal Access Token (PAT) [{existing.get('token', 'ไม่มีบันทึกไว้')}]: ").strip()
    if not token and 'token' in existing:
        token = existing['token']
        
    owner = input(f"GitHub Owner/Username [{existing.get('repo_owner', '')}]: ").strip()
    if not owner and 'repo_owner' in existing:
        owner = existing['repo_owner']
        
    repo = input(f"GitHub Repository Name [{existing.get('repo_name', '')}]: ").strip()
    if not repo and 'repo_name' in existing:
        repo = existing['repo_name']
        
    branch = input(f"Branch [{existing.get('branch', 'main')}]: ").strip()
    if not branch:
        branch = existing.get('branch', 'main')

    if not token or not owner or not repo:
        print("❌ ข้อมูลไม่ครบถ้วน! ไม่สามารถดำเนินการต่อได้")
        return None

    config = {
        "token": token,
        "repo_owner": owner,
        "repo_name": repo,
        "branch": branch
    }
    save_config(config)
    return config

def make_github_request(url, method, headers, data=None):
    """Helper to make HTTP request to GitHub API using urllib."""
    req = urllib.request.Request(url, method=method, headers=headers)
    if data:
        req.data = json.dumps(data).encode("utf-8")
    
    # Create SSL context that tolerates different environments
    ctx = ssl.create_default_context()
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            res_data = response.read()
            if res_data:
                return json.loads(res_data.decode("utf-8")), response.status
            return None, response.status
    except urllib.error.HTTPError as e:
        # Read the error body for more info
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            return err_json, e.code
        except:
            return {"message": err_body}, e.code
    except Exception as e:
        return {"message": str(e)}, 500

def get_file_sha(owner, repo, path, branch, token):
    """Gets the SHA of an existing file in the repository (needed for updates)."""
    # GitHub paths should use forward slashes
    path = path.replace("\\", "/")
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Python-GitHub-Uploader",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    res, status = make_github_request(url, "GET", headers)
    if status == 200 and isinstance(res, dict) and "sha" in res:
        return res["sha"]
    return None

def upload_file(owner, repo, local_path, repo_path, branch, token, commit_message="Auto upload via Python"):
    """Uploads a file to GitHub repository (creates or updates)."""
    repo_path = repo_path.replace("\\", "/")
    
    # Read and encode file content to base64
    try:
        with open(local_path, "rb") as f:
            file_bytes = f.read()
        content_b64 = base64.b64encode(file_bytes).decode("utf-8")
    except Exception as e:
        print(f"❌ Error reading file {local_path}: {e}")
        return False

    # Check if file exists to get its SHA (required for updating)
    sha = get_file_sha(owner, repo, repo_path, branch, token)
    
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{repo_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Python-GitHub-Uploader",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    }
    
    data = {
        "message": commit_message,
        "content": content_b64,
        "branch": branch
    }
    
    if sha:
        data["sha"] = sha
        action_str = "Update"
    else:
        action_str = "Create"
        
    res, status = make_github_request(url, "PUT", headers, data)
    
    if status in (200, 201):
        print(f"✅ [{action_str}] อัพโหลด {repo_path} สำเร็จ")
        return True
    else:
        err_msg = res.get("message", "Unknown error")
        print(f"❌ [{action_str}] อัพโหลด {repo_path} ล้มเหลว (Status: {status}): {err_msg}")
        return False

def get_all_files(root_dir):
    """Walks the directory and gathers all files that shouldn't be ignored."""
    files_to_upload = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter directories in-place to avoid walking ignored ones
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_IGNORE_PATTERNS]
        
        for file in filenames:
            if file in DEFAULT_IGNORE_PATTERNS:
                continue
            
            # Also ignore some common large files/formats or script files if needed
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.pyc', '.pyo', '.git']:
                continue
                
            full_path = os.path.join(dirpath, file)
            # Relative path from the root_dir
            rel_path = os.path.relpath(full_path, root_dir)
            files_to_upload.append((full_path, rel_path))
            
    return files_to_upload

def main():
    print("=========================================")
    print("    🚀 GitHub Auto File Uploader        ")
    print("=========================================")
    
    config = load_config()
    if not config:
        config = setup_config()
        if not config:
            return
            
    # Check if config is complete
    required = ["token", "repo_owner", "repo_name", "branch"]
    if not all(k in config for k in required):
        config = setup_config()
        if not config:
            return

    # Option menu
    print(f"\nRepository ปัจจุบัน: {config['repo_owner']}/{config['repo_name']} (Branch: {config['branch']})")
    print("1. อัพโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้")
    print("2. เลือกไฟล์เฉพาะเจาะจงที่จะอัพโหลด")
    print("3. ตั้งค่าการเชื่อมต่อ GitHub ใหม่")
    print("4. ออกจากโปรแกรม")
    
    choice = input("กรุณาเลือกเมนู (1-4): ").strip()
    
    if choice == "3":
        setup_config()
        return main()
    elif choice == "4":
        print("ปิดโปรแกรม")
        return
        
    root_dir = os.path.dirname(os.path.abspath(__file__))
    all_files = get_all_files(root_dir)
    
    if not all_files:
        print("⚠️ ไม่พบไฟล์ที่สามารถอัพโหลดได้ในโฟลเดอร์นี้")
        return
        
    selected_files = []
    
    if choice == "1":
        selected_files = all_files
    elif choice == "2":
        print("\nรายการไฟล์ที่พบ:")
        for idx, (full, rel) in enumerate(all_files, 1):
            print(f"{idx}. {rel}")
            
        indices_str = input("\nกรอกหมายเลขไฟล์ที่ต้องการอัพโหลด (คั่นด้วยเครื่องหมายจุลภาค , เช่น 1,3,4): ").strip()
        try:
            indices = [int(i.strip()) - 1 for i in indices_str.split(",") if i.strip()]
            selected_files = [all_files[i] for i in indices if 0 <= i < len(all_files)]
        except Exception:
            print("❌ กรอกข้อมูลไม่ถูกต้อง")
            return
    else:
        print("❌ เลือกเมนูไม่ถูกต้อง")
        return
        
    if not selected_files:
        print("⚠️ ไม่มีไฟล์ที่ถูกเลือก")
        return
        
    print(f"\nไฟล์ที่จะอัพโหลด ({len(selected_files)} ไฟล์):")
    for _, rel in selected_files:
        print(f" - {rel}")
        
    commit_msg = input("\n Commit Message [Auto upload via Python]: ").strip()
    if not commit_msg:
        commit_msg = "Auto upload via Python"
        
    confirm = input("ยืนยันการอัพโหลดหรือไม่? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ ยกเลิกการอัพโหลด")
        return
        
    print("\nกำลังเริ่มอัพโหลดไฟล์...")
    success_count = 0
    for local_path, rel_path in selected_files:
        success = upload_file(
            owner=config["repo_owner"],
            repo=config["repo_name"],
            local_path=local_path,
            repo_path=rel_path,
            branch=config["branch"],
            token=config["token"],
            commit_message=commit_msg
        )
        if success:
            success_count += 1
            
    print(f"\n📊 สรุปผล: อัพโหลดสำเร็จ {success_count}/{len(selected_files)} ไฟล์")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 สิ้นสุดการทำงาน")
