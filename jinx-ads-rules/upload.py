import base64, json, os, sys, urllib.request

TOKEN = os.environ["GH_TOKEN"]
REPO = "RiverFlowsInUUU/jinx-ads-rules"
API = "https://api.github.com"

def req(url, method="GET", data=None):
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", "token " + TOKEN)
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "readme-refresh")
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, body) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print("HTTP", e.code, e.read().decode("utf-8")[:600])
        raise

def put(path, local, message):
    content = open(local, "rb").read()
    payload = {
        "message": message,
        "content": base64.b64encode(content).decode("ascii"),
        "branch": "main",
    }
    info = req(f"{API}/repos/{REPO}/contents/{path}?ref=main")
    if isinstance(info, dict) and "sha" in info:
        payload["sha"] = info["sha"]
        print("updating", path, "sha", info["sha"][:8])
    else:
        print("creating", path)
    out = req(f"{API}/repos/{REPO}/contents/{path}", "PUT", payload)
    print("ok:", out["content"]["path"], "->", out["commit"]["sha"][:8])

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    put("README.md", os.path.join(base, "README.md"), "docs: README 改为统一模板风格（对齐 egern-anti-dns-leak）")
    put("custom-direct.list", os.path.join(base, "custom-direct.list"), "feat: 补回 custom-direct.list（白名单产物的 --extra-white 源文件）")
