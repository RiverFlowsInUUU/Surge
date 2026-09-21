"""用 Git Data API 把本地目录发布到 GitHub 仓库（单 commit）。
token 从环境变量 GHP 读，不写进任何文件。
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.error

SLUG = "RiverFlowsInUUU/surge-anti-dns-leak"
BRANCH = "main"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOKEN = os.environ["GHP"]

# 要忽略的路径（相对 ROOT，用 / 分隔）
SKIP_PREFIXES = (".git/", ".tmp-", "outputs/")
SKIP_FILES = {".tmp-min.py", ".DS_Store"}


def api(method, path, body=None):
    url = "https://api.github.com" + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "publish-script")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP %d on %s %s" % (e.code, method, path), file=sys.stderr)
        print(e.read().decode()[:600], file=sys.stderr)
        raise


def collect():
    out = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            if rel in SKIP_FILES:
                continue
            if any(rel.startswith(p) for p in SKIP_PREFIXES):
                continue
            with open(full, "rb") as f:
                raw = f.read()
            try:
                text = raw.decode("utf-8")
                is_text = True
            except UnicodeDecodeError:
                is_text = False
            if is_text and "\r\n" in text:
                # 强制 LF
                text = text.replace("\r\n", "\n")
                raw = text.encode("utf-8")
            out[rel] = raw
    return out


def main():
    files = collect()
    print("待发布 %d 个文件" % len(files))

    # 当前 HEAD
    try:
        ref = api("GET", "/repos/%s/git/ref/heads/%s" % (SLUG, BRANCH))
        parent = ref["object"]["sha"]
    except urllib.error.HTTPError:
        parent = None
        ref = None
    print("父 commit:", parent)

    if parent:
        pc = api("GET", "/repos/%s/git/commits/%s" % (SLUG, parent))
        parent_tree = pc["tree"]["sha"]
    else:
        parent_tree = None

    # 建 blobs
    tree_items = []
    for i, (rel, raw) in enumerate(sorted(files.items()), 1):
        blob = api("POST", "/repos/%s/git/blobs" % SLUG, {
            "content": base64.b64encode(raw).decode(),
            "encoding": "base64",
        })
        mode = "100755" if rel.endswith(".sh") else "100644"
        tree_items.append({"path": rel, "mode": mode, "type": "blob",
                           "sha": blob["sha"]})
        if i % 20 == 0:
            print("  ...%d/%d" % (i, len(files)))

    # tree（不带 base_tree ⇒ 整树覆盖）
    tree = api("POST", "/repos/%s/git/trees" % SLUG, {"tree": tree_items})
    print("tree:", tree["sha"])

    msg = os.environ.get("COMMIT_MSG", "chore: update")
    commit_body = {"message": msg, "tree": tree["sha"]}
    if parent:
        commit_body["parents"] = [parent]
    commit = api("POST", "/repos/%s/git/commits" % SLUG, commit_body)
    print("commit:", commit["sha"])

    if parent:
        try:
            api("PATCH", "/repos/%s/git/refs/heads/%s" % (SLUG, BRANCH),
                {"sha": commit["sha"], "force": True})
        except urllib.error.HTTPError:
            api("POST", "/repos/%s/git/refs" % SLUG,
                {"ref": "refs/heads/" + BRANCH, "sha": commit["sha"]})
    else:
        api("POST", "/repos/%s/git/refs" % SLUG,
            {"ref": "refs/heads/" + BRANCH, "sha": commit["sha"]})
    print("✅ 已推送到 %s@%s" % (BRANCH, commit["sha"][:8]))


if __name__ == "__main__":
    main()
