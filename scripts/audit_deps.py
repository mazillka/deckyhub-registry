"""Bounded inventory of identifiable installed packages and OSV lookups.

A successful lookup is not evidence that an archive is free of vulnerabilities.
Lock files and project manifests do not establish what was shipped.
"""
import json
import re
import urllib.error
import urllib.request
import zipfile
import zlib

MAX_MEMBERS = 20000
MAX_METADATA = 128 * 1024
MAX_PACKAGES = 100
MAX_FINDINGS = 100
MAX_BINARIES = 100
MAX_BINARY_HEADER = 4096
MAX_RESPONSE = 2 * 1024 * 1024
BATCH_SIZE = 100
_NAME = re.compile(r"^(?:@[a-z0-9][a-z0-9._~-]*/)?[a-z0-9][a-z0-9._~-]*$", re.I)
_PY_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_VERSION = re.compile(r"^[0-9][A-Za-z0-9.+!_-]{0,99}$")
_NPM_VERSION = re.compile(r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_BINARY = re.compile(r"(?:\.so(?:\.\d+)*|\.dll|\.dylib|\.exe|\.node|\.wasm|\.a|\.o)$", re.I)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused", headers, fp)


def _osv_query(queries):
    data = json.dumps({"queries": queries}, separators=(",", ":")).encode()
    req = urllib.request.Request("https://api.osv.dev/v1/querybatch", data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(req, timeout=15) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("OSV response exceeded limit")
    return json.loads(raw)


def _metadata(zf, info):
    if info.file_size > MAX_METADATA or info.compress_size > MAX_METADATA:
        raise ValueError("metadata exceeded limit")
    with zf.open(info) as f:
        raw = f.read(MAX_METADATA + 1)
    if len(raw) > MAX_METADATA:
        raise ValueError("metadata exceeded limit")
    return raw.decode("utf-8")



def _binary_format(zf, info):
    """Read at most MAX_BINARY_HEADER uncompressed bytes; never execute the member."""
    with zf.open(info) as member:
        head = member.read(min(info.file_size, 64))
        if head.startswith(b"\x7fELF"):
            if len(head) < 16:
                raise ValueError("truncated ELF header")
            return "ELF"
        if head[:4] in (b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe",
                        b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe",
                        b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca",
                        b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"):
            if len(head) < 8:
                raise ValueError("truncated Mach-O header")
            return "Mach-O"
        if head.startswith(b"MZ"):
            if len(head) < 64:
                raise ValueError("truncated DOS header")
            offset = int.from_bytes(head[60:64], "little")
            if offset < 64 or offset + 4 > MAX_BINARY_HEADER:
                raise ValueError("PE header outside inspection limit")
            rest = member.read(offset + 4 - len(head))
            if len(rest) < offset + 4 - len(head):
                raise ValueError("truncated PE header")
            if (head + rest)[offset:offset + 4] == b"PE\0\0":
                return "PE"
        return None

def _package(zf, info):
    path = info.filename.replace("\\", "/")
    parts = path.split("/")
    if any(p in (".", "..") for p in parts):
        return None
    if len(parts) >= 2 and parts[-1] == "METADATA" and parts[-2].endswith(".dist-info"):
        # Only actual installed distribution metadata, not package manifests or locks.
        from email.parser import Parser
        message = Parser().parsestr(_metadata(zf, info), headersonly=True)
        names, versions = message.get_all("Name", []), message.get_all("Version", [])
        if len(names) != 1 or len(versions) != 1:
            raise ValueError("invalid distribution metadata")
        name, version = str(names[0]).strip(), str(versions[0]).strip()
        if len(name) > 200 or not _PY_NAME.fullmatch(name) or not _VERSION.fullmatch(version):
            raise ValueError("invalid distribution identity")
        return "PyPI", name, version
    if len(parts) >= 3 and parts[-1] == "package.json" and "node_modules" in parts[:-1]:
        idx = len(parts) - 1 - parts[-2::-1].index("node_modules") - 1
        relative = parts[idx + 1:-1]
        if len(relative) not in (1, 2) or (len(relative) == 2 and not relative[0].startswith("@")):
            return None
        obj = json.loads(_metadata(zf, info))
        name, version = obj.get("name"), obj.get("version")
        if (not isinstance(name, str) or not isinstance(version, str) or
                len(name) > 214 or len(version) > 100 or not _NAME.fullmatch(name) or not _NPM_VERSION.fullmatch(version) or
                name.lower() != "/".join(relative).lower()):
            raise ValueError("invalid installed npm identity")
        return "npm", name, version
    return None


def audit_dependencies(zip_path, query=None):
    """Inventory identifiable installed packages and query OSV without executing code.

    query takes a list of OSV query objects and returns a querybatch response.
    """
    out = {"result": "complete", "packages": [], "findings": [], "binaries": [], "issues": []}
    issues = out["issues"]
    def issue(message):
        if message not in issues and len(issues) < 20:
            issues.append(message)
        out["result"] = "incomplete"
    try:
        with zipfile.ZipFile(zip_path) as zf:
            infos = zf.infolist()
            if len(infos) > MAX_MEMBERS:
                issue("Archive member limit exceeded; inventory truncated.")
                infos = infos[:MAX_MEMBERS]
            seen = set()
            for info in infos:
                if info.is_dir():
                    continue
                if _BINARY.search(info.filename):
                    issue("Native or binary components could not be identified reliably.")
                try:
                    binary_format = _binary_format(zf, info)
                    if binary_format:
                        issue("Native or binary components could not be identified reliably.")
                        if len(out["binaries"]) < MAX_BINARIES:
                            out["binaries"].append({"path": info.filename[:300],
                                                    "size": info.file_size, "format": binary_format})
                        else:
                            issue("Binary inventory limit exceeded; inventory truncated.")
                except (ValueError, OSError, RuntimeError, EOFError, NotImplementedError, zipfile.BadZipFile, zlib.error):
                    issue("A binary header could not be read or was truncated.")
                try:
                    pkg = _package(zf, info)
                except (ValueError, TypeError, UnicodeError, KeyError, OSError, RuntimeError, zipfile.BadZipFile):
                    issue("Some installed package metadata could not be read or identified.")
                    continue
                if pkg and pkg not in seen:
                    if len(seen) >= MAX_PACKAGES:
                        issue("Package inventory limit exceeded; inventory truncated.")
                        continue
                    seen.add(pkg)
                    ecosystem, name, version = pkg
                    out["packages"].append({"ecosystem": ecosystem, "name": name,
                                            "version": version, "source": info.filename[:300]})
    except (OSError, zipfile.BadZipFile, ValueError):
        return {"result": "error", "packages": [], "findings": [], "binaries": [],
                "issues": ["Archive could not be read."]}
    # Minified/bundled code and vendored source cannot be identified from manifests alone.
    issue("Bundled or vendored code without installed package metadata is not identified.")
    lookup = query or _osv_query
    packages = out["packages"]
    for start in range(0, len(packages), BATCH_SIZE):
        batch = packages[start:start + BATCH_SIZE]
        requests = [{"package": {"ecosystem": p["ecosystem"], "name": p["name"]},
                     "version": p["version"]} for p in batch]
        try:
            response = lookup(requests)
            results = response["results"]
            if not isinstance(results, list) or len(results) != len(batch):
                raise ValueError("invalid OSV response")
            for package, result in zip(batch, results):
                if not isinstance(result, dict):
                    raise ValueError("invalid OSV response")
                if result.get("next_page_token"):
                    issue("A vulnerability lookup has additional pages; results are incomplete.")
                vulns = result.get("vulns", [])
                if not isinstance(vulns, list):
                    raise ValueError("invalid OSV response")
                for vuln in vulns:
                    if not isinstance(vuln, dict) or not isinstance(vuln.get("id"), str):
                        raise ValueError("invalid OSV response")
                    if len(out["findings"]) >= MAX_FINDINGS:
                        issue("Vulnerability findings limit exceeded; results truncated.")
                        break
                    out["findings"].append({"ecosystem": package["ecosystem"], "name": package["name"],
                        "version": package["version"], "id": vuln["id"][:200]})
        except Exception:
            issue("A vulnerability lookup failed or returned an invalid response.")
    return out
