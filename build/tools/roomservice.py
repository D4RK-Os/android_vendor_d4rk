#!/usr/bin/env python3
# D4RK Os roomservice: "breakfast <device>" fetches the device tree and its
# lineage.dependencies from the D4RK-Os GitHub org (no LineageOS lookup).
import json, os, subprocess, sys, urllib.request
import xml.etree.ElementTree as ET

ORG = os.environ.get("D4RK_ORG", "D4RK-Os")
BRANCH = os.environ.get("D4RK_DEVICE_BRANCH", "thirteen")
LOCAL = ".repo/local_manifests/roomservice.xml"


def tree_root():
    d = os.getcwd()
    while d != "/":
        if os.path.isdir(os.path.join(d, ".repo")):
            return d
        d = os.path.dirname(d)
    sys.exit("roomservice: .repo not found")


def api(url):
    req = urllib.request.Request(url)
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        req.add_header("Authorization", "token " + tok)
    return json.load(urllib.request.urlopen(req))


def org_repos():
    out, page = [], 1
    while True:
        r = api("https://api.github.com/orgs/%s/repos?per_page=100&page=%d" % (ORG, page))
        if not r:
            return out
        out += [x["name"] for x in r]
        page += 1


def manifest_paths():
    try:
        xml = subprocess.check_output(["repo", "manifest"], stderr=subprocess.DEVNULL).decode()
        return {p.get("path") or p.get("name") for p in ET.fromstring(xml).iter("project")}
    except Exception:
        return set()


def add_project(name, path, remote, revision):
    os.makedirs(os.path.dirname(LOCAL), exist_ok=True)
    root = ET.parse(LOCAL).getroot() if os.path.exists(LOCAL) else ET.Element("manifest")
    if any(p.get("path") == path for p in root.iter("project")):
        return
    ET.SubElement(root, "project", {"name": name, "path": path, "remote": remote, "revision": revision})
    try:
        ET.indent(root)
    except AttributeError:
        pass
    ET.ElementTree(root).write(LOCAL, encoding="utf-8", xml_declaration=True)
    print("roomservice: added %s -> %s (%s)" % (name, path, revision))


def sync(paths):
    if paths:
        subprocess.call(["repo", "sync", "-c", "--no-tags", "--no-clone-bundle",
                         "--force-sync", "-j8"] + paths)


def fetch_deps(path):
    f = os.path.join(path, "lineage.dependencies")
    if not os.path.isfile(f):
        return
    deps = json.load(open(f))
    known = manifest_paths()
    todo = []
    for d in deps:
        repo, tp = d["repository"], d["target_path"]
        remote = d.get("remote") or ("d4rk-github" if "/" in repo else "d4rk")
        if tp not in known:
            add_project(repo, tp, remote, d.get("branch", BRANCH))
        if not os.path.isdir(tp):
            todo.append(tp)
    sync(todo)
    for d in deps:
        fetch_deps(d["target_path"])


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: roomservice.py <device>")
    device = sys.argv[1]
    for pre in ("lineage_", "havoc_", "d4rk_"):
        if device.startswith(pre):
            device = device[len(pre):]
    device = device.split("-")[0]
    os.chdir(tree_root())

    path = None
    for p in manifest_paths():
        if p.startswith("device/") and p.count("/") == 2 and p.endswith("/" + device):
            path = p
    if path is None:
        pre, suf = "android_device_", "_" + device
        match = [r for r in org_repos() if r.startswith(pre) and r.endswith(suf)]
        if not match:
            print("Repository for %s not found in github.com/%s" % (device, ORG))
            sys.exit(1)
        name = match[0]
        vendor = name[len(pre):-len(suf)]
        path = "device/%s/%s" % (vendor, device)
        add_project(name, path, "d4rk", BRANCH)
        sync([path])
    fetch_deps(path)


main()
