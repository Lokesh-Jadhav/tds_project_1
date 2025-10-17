"""
llm_code_deployment/app.py
"""
import os, time, traceback, threading
from datetime import datetime
from uuid import uuid4

from flask import Flask, request, jsonify
from github import Github, GithubException, UnknownObjectException
import requests
from dotenv import load_dotenv

# ───────────────────────────────────────────────────────
# ENV
# ───────────────────────────────────────────────────────
load_dotenv()
STUDENT_SECRET = os.getenv("STUDENT_SECRET", "")
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")
GITHUB_OWNER   = os.getenv("GITHUB_OWNER", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

print("DEBUG STUDENT_SECRET present:", bool(STUDENT_SECRET))
print("DEBUG GITHUB_OWNER:", GITHUB_OWNER)

# ───────────────────────────────────────────────────────
# APP
# ───────────────────────────────────────────────────────
app = Flask(__name__)

# ───────────────────────────────────────────────────────
# LLM: generate minimal single-page web app
# ───────────────────────────────────────────────────────
def generate_code_with_llm(brief: str, attachments: list):
    attach_names = [a.get("name") for a in attachments or []]
    if not OPENAI_API_KEY:
        index_html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Generated App</title>
<style>
 body{{font-family:system-ui,Arial,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem}}
 h1{{font-size:1.4rem}} .row{{display:flex;gap:.5rem}}
 input,button{{padding:.6rem .8rem;border:1px solid #ccc;border-radius:8px}}
 ul{{list-style:none;padding:0}} li{{display:flex;justify-content:space-between;border-bottom:1px dashed #eee;padding:.4rem 0}}
 .note{{color:#666}}
</style></head><body>
<h1>Demo App (fallback mode)</h1>
<p class="note">OPENAI_API_KEY not set. Brief was: <code>{brief}</code>. Attachments: {attach_names}</p>
<div class="row">
  <input id="newItem" placeholder="Add item…"/><button id="addBtn">Add</button>
</div>
<ul id="list"></ul>
<script src="script.js"></script>
</body></html>"""
        script_js = """(function(){
  const key="items";
  const list=document.getElementById("list");
  const input=document.getElementById("newItem");
  const add=document.getElementById("addBtn");
  const state = JSON.parse(localStorage.getItem(key)||"[]");
  const save=()=>localStorage.setItem(key, JSON.stringify(state));
  const render=()=>{ list.innerHTML=""; state.forEach((t,i)=>{ 
    const li=document.createElement("li"); li.innerHTML = `<span>${t}</span>`;
    const b=document.createElement("button"); b.textContent="Delete";
    b.onclick=()=>{state.splice(i,1);save();render();}; li.appendChild(b); list.appendChild(li);
  });};
  add.onclick=()=>{const v=input.value.trim(); if(!v) return; state.push(v); input.value=""; save(); render();};
  render();
})();"""
        mit = f"""MIT License

Copyright (c) {datetime.utcnow().year}

Permission is hereby granted, free of charge, to any person obtaining a copy...
"""
        readme = "# Generated App (Fallback)\n\nAuto-generated static page.\n\nDeployed via GitHub Pages."
        return {"index.html": index_html, "script.js": script_js, "LICENSE": mit, "README.md": readme}

    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        system = "You generate single-file static web apps suitable for GitHub Pages. No external CDNs."
        user = (
            f"Build a minimal single-page app.\n"
            f"Brief: {brief}\n"
            f"Attachments (names only): {attach_names}\n\n"
            "Include files: index.html, script.js, README.md (summary, setup, usage, explanation), LICENSE (MIT).\n"
            "index.html may include inline <style>. Keep it accessible and dependency-free."
        )
        resp = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        content = resp.choices[0].message.content

        files = {"index.html": "", "script.js": "", "README.md": "# Generated App\n", "LICENSE": "MIT License\n\n"}
        current = None
        for line in content.splitlines():
            t = line.strip()
            if t.startswith("```"):
                lang = t.strip("`").lower()
                if "html" in lang: current = "index.html"
                elif "js" in lang or "javascript" in lang: current = "script.js"
                else: current = None
                continue
            if current:
                files[current] += line + "\n"
        if not files["index.html"].strip():
            files["index.html"] = "<!doctype html><html><body><h1>Generated App</h1><script src='script.js'></script></body></html>"
        if not files["script.js"].strip():
            files["script.js"] = "console.log('hello from generated app');"
        return files
    except Exception:
        traceback.print_exc()
        return generate_code_with_llm(brief, [])

# ───────────────────────────────────────────────────────
# GitHub functions
# ───────────────────────────────────────────────────────
def create_repo_and_push(task: str, files: dict, round_index: int):
    gh = Github(GITHUB_TOKEN)
    user = gh.get_user()
    repo_name = f"{task}".replace(" ", "-")

    repo = None
    if round_index == 1:
        try:
            repo = gh.get_repo(f"{user.login}/{repo_name}")
            print(f"⚠️ Repo already exists for {task}, reusing for round 1.")
        except UnknownObjectException:
            print(f"✅ Creating new repo for round 1: {repo_name}")
            repo = user.create_repo(
                name=repo_name,
                private=False,
                description=f"Auto-generated for {task}",
                auto_init=False,
            )
    else:
        try:
            repo = gh.get_repo(f"{user.login}/{repo_name}")
            print(f"🔁 Updating existing repo for round 2: {repo_name}")
        except UnknownObjectException:
            print(f"⚠️ Repo not found for round 2; creating new one as fallback.")
            repo = user.create_repo(
                name=repo_name,
                private=False,
                description=f"Auto-generated (fallback) for {task}",
                auto_init=False,
            )

    commit_sha = None
    for path, content in files.items():
        try:
            existing = repo.get_contents(path)
            res = repo.update_file(existing.path, f"update {path}", content, existing.sha, branch="main")
            commit_sha = res["commit"].sha
        except GithubException:
            res = repo.create_file(path=path, message=f"add {path}", content=content, branch="main")
            commit_sha = res["commit"].sha

    try:
        repo.edit(default_branch="main")
    except GithubException:
        pass

    pages_url = setup_and_enable_github_pages(user.login, repo.name)
    return repo.html_url, commit_sha, pages_url

# ───────────────────────────────────────────────────────
# Auto-Enable GitHub Pages (sets branch = main)
# ───────────────────────────────────────────────────────
def setup_and_enable_github_pages(owner: str, repo: str):
    """Automatically selects branch=main and enables Pages."""
    print("⏳ Waiting for GitHub to register the repo and branch...")
    time.sleep(6)

    config_url = f"https://api.github.com/repos/{owner}/{repo}/pages"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }

    for attempt in range(5):
        r = requests.post(config_url, headers=headers, json=payload, timeout=20)
        if r.status_code in (201, 204):
            print(f"✅ GitHub Pages configured from branch 'main' for {repo}")
            break
        elif r.status_code in (404, 409):
            print(f"⚠️ Pages setup not ready yet ({r.status_code}). Retrying in {2 ** attempt}s...")
            time.sleep(2 ** attempt)
        else:
            print(f"⚠️ Unexpected response enabling Pages ({r.status_code}): {r.text}")

    # Fetch the published Pages URL
    try:
        r = requests.get(config_url, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            pages_url = data.get("html_url") or data.get("url")
            if pages_url:
                print(f"✅ GitHub Pages live at: {pages_url}")
                return pages_url
    except Exception as e:
        print(f"⚠️ Could not fetch Pages URL: {e}")

    return f"https://{owner}.github.io/{repo}/"

# ───────────────────────────────────────────────────────
# Evaluation Notifier
# ───────────────────────────────────────────────────────
def notify_evaluation(evaluation_url: str, payload: dict, max_retries=5):
    delay = 1
    for _ in range(max_retries):
        try:
            r = requests.post(evaluation_url, json=payload, timeout=15)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(delay)
        delay *= 2
    return False

# ───────────────────────────────────────────────────────
# Background worker
# ───────────────────────────────────────────────────────
def run_job(data: dict):
    try:
        brief = data.get("brief", "")
        attachments = data.get("attachments", [])
        files = generate_code_with_llm(brief, attachments)
        repo_url, commit_sha, pages_url = create_repo_and_push(data["task"], files, data["round"])
        print(f"✅ Repo URL: {repo_url}")
        print(f"✅ Commit SHA: {commit_sha}")
        print(f"✅ Pages URL: {pages_url}")
        payload = {
            "email": data["email"],
            "task": data["task"],
            "round": data["round"],
            "nonce": data["nonce"],
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url,
        }
        notify_evaluation(data["evaluation_url"], payload)
    except Exception:
        traceback.print_exc()

# ───────────────────────────────────────────────────────
# ROUTES
# ───────────────────────────────────────────────────────
@app.route("/build", methods=["POST"])
def build():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    # 🔐 Validate secret first
    if data.get("secret") != STUDENT_SECRET:
        return jsonify({"ok": False, "error": "Invalid secret"}), 403

    # ✅ Minimal validation — only check for essential fields
    required_fields = {"round", "brief"}
    if not required_fields.issubset(data.keys()):
        print("⚠️ Incomplete or non-standard request received. Returning 200 OK (no build started).")
        return "", 200  # Acknowledge but don't trigger the build

    try:
        # Run synchronously so we can send final JSON back
        brief = data.get("brief", "")
        attachments = data.get("attachments", [])
        files = generate_code_with_llm(brief, attachments)
        repo_url, commit_sha, pages_url = create_repo_and_push(data["task"], files, data["round"])

        # ✅ Build final JSON response
        response = {
            "email": data.get("email"),
            "task": data.get("task"),
            "round": data.get("round"),
            "nonce": data.get("nonce"),
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url
        }

        # 🔔 Notify evaluator asynchronously
        threading.Thread(
            target=notify_evaluation,
            args=(data.get("evaluation_url", ""), response),
            daemon=True
        ).start()

        return jsonify(response), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"ok": True, "time": datetime.utcnow().isoformat()}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True)
