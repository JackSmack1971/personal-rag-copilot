# codex_sandbox_audit.py
# Safe, read-only checks except for tiny temp files under a writable dir.

import os, sys, json, time, socket, platform, pathlib, traceback
from contextlib import closing

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def first_writable(paths):
    for p in paths:
        try:
            p = pathlib.Path(p)
            p.mkdir(parents=True, exist_ok=True)
            test = p / ".codex_write_test"
            test.write_text("ok", encoding="utf-8")
            test.unlink(missing_ok=True)
            return p
        except Exception:
            continue
    return pathlib.Path.cwd()

# Prefer repo root if present, else /workspace, else /tmp
candidate_roots = []
for cand in [os.getcwd(), "/workspace", "/tmp"]:
    if isinstance(cand, str):
        candidate_roots.append(cand)
root = first_writable(candidate_roots)

def try_write(path: pathlib.Path):
    f = path / ".codex_write_test"
    try:
        f.write_text("ok", encoding="utf-8")
        f.unlink(missing_ok=True)
        return True, "write ok"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def try_exec_python(tmpdir: pathlib.Path):
    s = tmpdir / "exec_check.py"
    s.write_text("print('exec-ok')\n", encoding="utf-8")
    try:
        import subprocess, sys as _sys
        cp = subprocess.run([_sys.executable, str(s)], capture_output=True, text=True, timeout=3)
        ok = (cp.returncode == 0 and "exec-ok" in (cp.stdout + cp.stderr))
        return ok, (cp.stdout or cp.stderr).strip()[:120]
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        s.unlink(missing_ok=True)

def ulimits():
    # cross-platform-ish using resource when available
    info = {}
    try:
        import resource
        limits = {
            "RLIMIT_CPU": resource.RLIMIT_CPU,
            "RLIMIT_FSIZE": resource.RLIMIT_FSIZE,
            "RLIMIT_DATA": resource.RLIMIT_DATA,
            "RLIMIT_STACK": resource.RLIMIT_STACK,
            "RLIMIT_CORE": resource.RLIMIT_CORE,
            "RLIMIT_RSS": getattr(resource, "RLIMIT_RSS", None),
            "RLIMIT_NPROC": getattr(resource, "RLIMIT_NPROC", None),
            "RLIMIT_NOFILE": getattr(resource, "RLIMIT_NOFILE", None),
            "RLIMIT_MEMLOCK": getattr(resource, "RLIMIT_MEMLOCK", None),
            "RLIMIT_AS": getattr(resource, "RLIMIT_AS", None),
        }
        for k, v in limits.items():
            if v is None:
                continue
            cur, mx = resource.getrlimit(v)
            info[k] = [cur, mx]
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"
    return info

def tcp_check(host, port, timeout=2.0):
    try:
        with closing(socket.create_connection((host, port), timeout=timeout)):
            return True, "connect ok"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def https_head(host, path="/", method="GET", timeout=2.0):
    try:
        import ssl, http.client
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(host, timeout=timeout, context=ctx)
        conn.request(method, path)
        r = conn.getresponse()
        return True, f"{r.status} {r.reason}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def local_status_probe():
    # scan a tiny set of localhost ports for /status
    results = []
    for port in (80, 3000, 5000, 8000, 8080, 9000):
        ok, ev = tcp_check("127.0.0.1", port)
        if ok:
            s, ev2 = None, None
            try:
                import http.client
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1.5)
                conn.request("GET", "/status")
                r = conn.getresponse()
                s = f"{r.status} {r.reason}"
                ev2 = s
            except Exception as e:
                ev2 = f"{type(e).__name__}: {e}"
            results.append({"port": port, "open": True, "status_get": ev2})
        else:
            results.append({"port": port, "open": False, "status_get": ev})
    return results

def guess_mode():
    # Heuristics only — not authoritative
    mode = {"cloud_task": None, "internet_maybe_on": None, "notes": []}
    # cloud-ish hints
    if os.path.exists("/.dockerenv") or "container" in open("/proc/1/cgroup", "r", errors="ignore").read():
        mode["cloud_task"] = True
    else:
        mode["cloud_task"] = None
    # internet hint: quick HEAD to example.com
    ok, ev = https_head("example.com", "/")
    mode["internet_maybe_on"] = bool(ok)
    if not ok:
        mode["notes"].append("HTTPS blocked or off-by-default (see Codex internet access docs).")
    return mode

env = {
    "timestamp_utc": NOW,
    "user": os.getenv("USER") or os.getenv("USERNAME"),
    "pwd": os.getcwd(),
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "uname": " ".join(platform.uname()),
    "env_keys_sample": sorted([k for k in os.environ.keys() if k.upper().startswith(("CODEX", "OPENAI", "GIT", "CI"))])[:20],
}

# Filesystem checks
fs = []
paths = [
    (root, "write"),
    ("/tmp", "write"),
    ("/etc", "write-forbidden"),
    ("/", "write-forbidden"),
]
for p, kind in paths:
    pth = pathlib.Path(p)
    ok, ev = try_write(pth)
    fs.append({"path": str(p), "expected": kind, "result": "ALLOWED" if ok else "DENIED", "evidence": ev})

# Exec check in writable root
exec_ok, exec_ev = try_exec_python(root)

# Network checks (short timeouts)
net = {
    "dns_example_com": socket.gethostbyname_ex("example.com")[2][0:1] if True else [],
    "tcp_443_example": tcp_check("example.com", 443)[0],
    "https_get_example": https_head("example.com", "/")[1],
    "https_post_httpbin": https_head("httpbin.org", "/post", method="POST")[1],
    # optional: check metadata IP (should fail in sane sandboxes)
    "tcp_169_254_169_254_80": tcp_check("169.254.169.254", 80)[0],
}

# Local /status scans
status_scan = local_status_probe()
mode_guess = guess_mode()

report = {
    "env": env,
    "writable_root": str(root),
    "ulimits": ulimits(),
    "fs_tests": fs,
    "exec_test_python": {"allowed": exec_ok, "evidence": exec_ev},
    "network": net,
    "local_status_scan": status_scan,
    "mode_guess_unverified": mode_guess,  # heuristic only
    "notes": [
        "Network behavior depends on your Codex environment’s internet-access setting (default OFF).",
        "Method restrictions (e.g., POST blocked) may be enforced even if GET is allowed.",
        "Results are specific to this task container and time.",
    ],
}

# Write JSON report
json_out = root / "report.json"
json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")

# Emit Markdown matrix
def to_markdown(r):
    md = []
    md.append(f"# Codex Sandbox Report — {r['env']['timestamp_utc']}\n")
    md.append("## Environment\n")
    md.append("| Key | Value |\n|---|---|\n")
    for k in ["user", "pwd", "python", "platform", "uname"]:
        md.append(f"| {k} | {r['env'].get(k, '')} |\n")
    md.append("\n## Filesystem Capability Matrix\n")
    md.append("| Path | Expected | Result | Evidence |\n|---|---|---|---|\n")
    for row in r["fs_tests"]:
        md.append(f"| `{row['path']}` | {row['expected']} | **{row['result']}** | {row['evidence']} |\n")
    md.append("\n## Execution\n")
    md.append(
        f"- Create & run Python script in `{r['writable_root']}`: **{'ALLOWED' if r['exec_test_python']['allowed'] else 'DENIED'}** — {r['exec_test_python']['evidence']}\n"
    )
    md.append("\n## Network Probes\n")
    md.append("| Probe | Result |\n|---|---|\n")
    md.append(f"| DNS resolve example.com | {r['network'].get('dns_example_com')} |\n")
    md.append(f"| TCP connect example.com:443 | {r['network'].get('tcp_443_example')} |\n")
    md.append(f"| HTTPS GET example.com/ | {r['network'].get('https_get_example')} |\n")
    md.append(f"| HTTPS POST httpbin.org/post | {r['network'].get('https_post_httpbin')} |\n")
    md.append(f"| TCP 169.254.169.254:80 (metadata) | {r['network'].get('tcp_169_254_169_254_80')} |\n")
    md.append("\n## Local /status Scan (localhost)\n")
    md.append("| Port | Open | /status GET |\n|---|---|---|\n")
    for s in r["local_status_scan"]:
        md.append(f"| {s['port']} | {s['open']} | {str(s['status_get']).replace('|', '/')} |\n")
    md.append("\n## Mode (Heuristic, [Unverified])\n")
    md.append(f"- cloud_task: {r['mode_guess_unverified'].get('cloud_task')}\n")
    md.append(f"- internet_maybe_on: {r['mode_guess_unverified'].get('internet_maybe_on')}\n")
    if r["mode_guess_unverified"].get("notes"):
        for n in r["mode_guess_unverified"]["notes"]:
            md.append(f"  - {n}\n")
    md.append("\n## Notes\n")
    for n in r["notes"]:
        md.append(f"- {n}\n")
    return "".join(md)

md = to_markdown(report)
out = root / f"codex_sandbox_report-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}.md"
out.write_text(md, encoding="utf-8")
print(f"Wrote report: {out}")
print(md)
