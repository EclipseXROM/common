"""Manikineko Store publisher (runs on the dev machine; the SIGNING KEY NEVER LEAVES IT).

  python -I scripts/80-store-publish.py init                   create the catalog signing key (once) + store/store-pubkey.b64
  python -I scripts/80-store-publish.py add <app.apk> [...]    add/replace apps, rewrite + sign the catalog, upload
  python -I scripts/80-store-publish.py remove <package>       drop an app from the catalog (APK files are removed on the server too)
  python -I scripts/80-store-publish.py list                   show the local catalog
  python -I scripts/80-store-publish.py refresh                recompute compatibility fields (abis, glEs) of every app from store/site/apk, re-sign, upload
  extra option for `add`: --devices "kanas3gnfc,other"   limit an app to these Build.DEVICE codenames (default: every device)
  options: --no-upload (only write store/site/*), --summary "text" (for `add`, one-line description)

Layout produced (served by the nginx container on 10.10.10.7:8097 = https://apps.zyghosting.online):
  catalog.json  {"v":1,"updated":"...","apps":[{package,name,versionCode,versionName,minSdk,apk,sha256,size,cert,summary}]}
  catalog.sig   base64( RSA-2048 PKCS#1 v1.5 SHA-256 signature over the exact bytes of catalog.json )
  apk/<package>-<versionCode>.apk
The phone's Store app embeds the public key (X.509 DER, base64), checks the signature, then sha256 of every APK it downloads.
RSA, not Ed25519: Android 6 has no Ed25519 in java.security."""
import base64, datetime, hashlib, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "store", "site")
PUBKEY = os.path.join(ROOT, "store", "store-pubkey.b64")
KEYDIR = os.environ.get("MK_SIGNING", "C:/mkbuild/store-signing")
KEY = KEYDIR + "/catalog-key.pem"
BT = os.path.join(ROOT, "tools", "sdk", "build-tools", "30.0.3")
JAVA = os.path.join(ROOT, "tools", "jdk-17.0.21.1+2", "bin")
REMOTE = "root@10.10.10.7"
REMOTE_SITE = "/opt/manikineko-store/site"


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", **kw)
    if r.returncode != 0:
        raise SystemExit("command failed: %s\n%s%s" % (" ".join(map(str, cmd)), r.stdout, r.stderr))
    return r.stdout


def init():
    os.makedirs(KEYDIR, exist_ok=True)
    if os.path.exists(KEY):
        print("key already exists:", KEY)
    else:
        run(["openssl", "genrsa", "-out", KEY, "2048"])
        print("created", KEY, "(back this file up; losing it means every phone needs a new Store build)")
    der = subprocess.run(["openssl", "pkey", "-in", KEY, "-pubout", "-outform", "DER"], capture_output=True, check=True).stdout
    open(PUBKEY, "w").write(base64.b64encode(der).decode() + "\n")
    print("public key ->", PUBKEY, "sha256", hashlib.sha256(der).hexdigest()[:16])


def badging(apk):
    out = run([os.path.join(BT, "aapt2.exe"), "dump", "badging", apk])
    m = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']*)'", out)
    if not m: raise SystemExit("cannot read package info from " + apk)
    pkg, vcode, vname = m.group(1), int(m.group(2)), m.group(3)
    label = re.search(r"application-label:'([^']*)'", out)
    label_lt = re.search(r"application-label-lt:'([^']*)'", out)
    sdk = re.search(r"sdkVersion:'(\d+)'", out)
    native = re.search(r"^native-code: (.*)$", out, re.M)
    abis = re.findall(r"'([^']+)'", native.group(1)) if native else []
    return dict(package=pkg, versionCode=vcode, versionName=vname, name=(label.group(1) if label else pkg),
                minSdk=int(sdk.group(1)) if sdk else 1, abis=abis, glEs=gl_es(apk)), (label_lt.group(1) if label_lt else None)


def gl_es(apk):
    """OpenGL ES version the manifest REQUIRES (e.g. 0x00020000), 0 if it does not say."""
    out = run([os.path.join(BT, "aapt2.exe"), "dump", "xmltree", "--file", "AndroidManifest.xml", apk])
    m = re.search(r"glEsVersion\(0x[0-9a-f]+\)=0x([0-9a-f]+)", out)
    return int(m.group(1), 16) if m else 0


def signer_cert(apk):
    out = run([os.path.join(BT, "apksigner.bat"), "verify", "--print-certs", "--min-sdk-version", "19", apk],
              env=dict(os.environ, JAVA_HOME=os.path.dirname(JAVA)))
    m = re.search(r"certificate SHA-256 digest: ([0-9a-f]+)", out)
    return m.group(1) if m else ""


def load():
    p = os.path.join(SITE, "catalog.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"v": 1, "apps": []}


def write_and_sign(cat):
    if not os.path.exists(KEY): raise SystemExit("no signing key: run `init` first")
    cat["v"] = 1
    cat["store"] = "Manikineko Store"
    cat["updated"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cat["apps"].sort(key=lambda a: a["name"].lower())
    data = json.dumps(cat, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "catalog.json"), "wb").write(data)
    sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", KEY], input=data, capture_output=True, check=True).stdout
    open(os.path.join(SITE, "catalog.sig"), "w").write(base64.b64encode(sig).decode() + "\n")
    # self-check with the public key so a broken signature is never uploaded
    pub = subprocess.run(["openssl", "pkey", "-in", KEY, "-pubout"], capture_output=True, check=True).stdout
    pf = os.path.join(KEYDIR, "pub.pem"); open(pf, "wb").write(pub)
    sf = os.path.join(KEYDIR, "tmp.sig"); open(sf, "wb").write(sig)
    chk = subprocess.run(["openssl", "dgst", "-sha256", "-verify", pf, "-signature", sf], input=data, capture_output=True)
    os.remove(sf)
    if b"Verified OK" not in chk.stdout: raise SystemExit("signature self-check FAILED")
    print("catalog.json signed (%d apps), self-check OK" % len(cat["apps"]))


def upload(extra_remove=()):
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", REMOTE]
    keep = {a["apk"].split("/")[-1] for a in load()["apps"]}
    apk_dir = os.path.join(SITE, "apk")
    os.makedirs(apk_dir, exist_ok=True)
    for f in os.listdir(apk_dir):                                  # local copies of removed/superseded versions
        if f not in keep: os.remove(os.path.join(apk_dir, f))
    # only send APKs the server does not already have (same name and size): a publish must not re-upload ~200 MB every time
    have = {}
    for line in run(ssh + ["cd %s/apk 2>/dev/null && stat -c '%%n %%s' * 2>/dev/null; true" % REMOTE_SITE]).splitlines():
        parts = line.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].isdigit(): have[parts[0]] = int(parts[1])
    todo = [os.path.join(apk_dir, f) for f in keep if have.get(f) != os.path.getsize(os.path.join(apk_dir, f))]
    if todo: run(["scp", "-q", "-o", "BatchMode=yes"] + todo + ["%s:%s/apk/" % (REMOTE, REMOTE_SITE)])
    # catalog last, so clients never see a catalog that points to a missing APK
    run(["scp", "-q", "-o", "BatchMode=yes", os.path.join(SITE, "catalog.sig"), os.path.join(SITE, "catalog.json"), "%s:%s/" % (REMOTE, REMOTE_SITE)])
    for f in have:
        if f not in keep: run(ssh + ["rm -f %s/apk/%s" % (REMOTE_SITE, f)])
    print("uploaded to %s (%d apk(s) sent) -> https://apps.zyghosting.online/catalog.json" % (REMOTE, len(todo)))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = sys.argv[1:]
    if not args: print(__doc__); return 2
    cmd, rest = args[0], args[1:]
    summary = flags[flags.index("--summary") + 1] if "--summary" in flags else ""
    if summary in rest: rest.remove(summary)
    devices = flags[flags.index("--devices") + 1] if "--devices" in flags else ""
    if devices and devices in rest: rest.remove(devices)
    if cmd == "init": init(); return 0
    cat = load()
    if cmd == "list":
        for a in cat["apps"]: print("%-45s %-8s v%-3s %s" % (a["package"], a["versionName"], a["versionCode"], a["sha256"][:12]))
        return 0
    if cmd == "add":
        os.makedirs(os.path.join(SITE, "apk"), exist_ok=True)
        for apk in rest:
            info, _ = badging(apk)
            cert = signer_cert(apk)
            name = "%s-%d.apk" % (info["package"], info["versionCode"])
            shutil.copyfile(apk, os.path.join(SITE, "apk", name))
            sha = hashlib.sha256(open(apk, "rb").read()).hexdigest()
            old = next((a for a in cat["apps"] if a["package"] == info["package"]), None)
            if old and old["versionCode"] > info["versionCode"]:
                raise SystemExit("%s: catalog already has newer versionCode %d" % (info["package"], old["versionCode"]))
            entry = dict(info, apk="apk/" + name, sha256=sha, size=os.path.getsize(apk), cert=cert,
                         summary=summary or (old or {}).get("summary", ""))
            devs = [d for d in devices.split(",") if d] or (old or {}).get("devices", [])
            if devs: entry["devices"] = devs
            cat["apps"] = [a for a in cat["apps"] if a["package"] != info["package"]] + [entry]
            print("added %s %s (code %d) cert %s" % (info["package"], info["versionName"], info["versionCode"], cert[:12]))
        write_and_sign(cat)
        if "--no-upload" not in flags: upload()
        return 0
    if cmd == "refresh":
        for a in cat["apps"]:
            path = os.path.join(SITE, a["apk"])
            if not os.path.exists(path): raise SystemExit("missing local APK for " + a["package"])
            info, _ = badging(path)
            a["abis"], a["glEs"], a["minSdk"] = info["abis"], info["glEs"], info["minSdk"]
            print("%-45s abis=%s glEs=%#x minSdk=%d" % (a["package"], ",".join(a["abis"]) or "any", a["glEs"], a["minSdk"]))
        write_and_sign(cat)
        if "--no-upload" not in flags: upload()
        return 0
    if cmd == "remove":
        gone = [a for a in cat["apps"] if a["package"] in rest]
        cat["apps"] = [a for a in cat["apps"] if a["package"] not in rest]
        for a in gone:
            p = os.path.join(SITE, a["apk"]);  os.path.exists(p) and os.remove(p)
        write_and_sign(cat)
        if "--no-upload" not in flags: upload()
        return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main())
