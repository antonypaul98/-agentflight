#!/usr/bin/env python3
"""Build and smoke-test a bounded, source-pinned offline AgentFlight demo bundle."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
import venv

ROOT = Path(__file__).resolve().parents[1]
INCLUDED = (
    "src/agentflight", "examples/offline-crash-test-demo.json", "docs/DEMO.md",
    "pyproject.toml", "README.md", "tests/test_demo.py", "scripts/package_offline_demo.py",
)

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def command(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)

def smoke(root, scratch):
    """Execute actual CLI from extracted sources in a fresh stdlib-only venv."""
    scratch.mkdir(parents=True, exist_ok=True)
    venv_dir = scratch / "venv"
    venv.EnvBuilder(with_pip=False, clear=True).create(venv_dir)
    python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    env = dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONNOUSERSITE="1")
    fixture = root / "examples/offline-crash-test-demo.json"
    def demo(path):
        return subprocess.run([str(python), "-m", "agentflight.demo", str(path)],
                              cwd=root, env=env, capture_output=True, text=True, check=False)
    first, second = demo(fixture), demo(fixture)
    if first.returncode != 0 or second.returncode != 0 or first.stdout != second.stdout:
        raise RuntimeError("positive exit/determinism smoke failed")
    report = json.loads(first.stdout)
    if report.get("status") != "passed":
        raise RuntimeError("positive demo verdict failed")
    if report["recorded_calls"]["summary"] != {"total": 2, "passed": 2, "failed": 0, "error": 0}:
        raise RuntimeError("recorded-call acceptance failed")
    if report["injection_probes"]["summary"] != {"total": 2, "passed": 2, "failed": 0}:
        raise RuntimeError("injection-probe acceptance failed")
    digest = report.pop("report_hash")
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if digest != hashlib.sha256(canonical.encode("utf-8")).hexdigest():
        raise RuntimeError("report hash failed")
    for marker in ("synthetic-42", "Ignore all previous instructions", "Please check the status"):
        if marker in first.stdout:
            raise RuntimeError("recorded payload leaked")
    mismatch = json.loads(fixture.read_text(encoding="utf-8"))
    mismatch["injection_probes"][0]["expected_detected"] = not mismatch["injection_probes"][0]["expected_detected"]
    mismatch_file = scratch / "mismatch.json"
    mismatch_file.write_text(json.dumps(mismatch), encoding="utf-8")
    mismatch_result = demo(mismatch_file)
    if mismatch_result.returncode != 1 or json.loads(mismatch_result.stdout).get("status") != "failed":
        raise RuntimeError("exit 1 mismatch contract failed")
    invalid_file = scratch / "invalid.json"
    invalid_file.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    invalid_result = demo(invalid_file)
    if invalid_result.returncode != 2 or json.loads(invalid_result.stdout).get("status") != "invalid_fixture":
        raise RuntimeError("exit 2 invalid fixture contract failed")
    return {"exit_codes": [0, 1, 2], "deterministic_runs": 2,
            "report_hash": digest, "redacted": True, "recorded_cases": 2, "injection_probes": 2}

def extract_checked(archive, destination):
    with tarfile.open(archive, "r:*") as stream:
        for member in stream.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
                raise RuntimeError("unsafe archive entry")
        stream.extractall(destination)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="dist")
    args = parser.parse_args()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    sha = command("git", "rev-parse", "HEAD", cwd=ROOT).stdout.strip()
    version = "agentflight-offline-demo-" + sha[:12]
    with tempfile.TemporaryDirectory(prefix="agentflight-bundle-") as temp:
        tmp = Path(temp)
        stage = tmp / version
        stage.mkdir()
        source_tar = tmp / "source.tar"
        command("git", "archive", "--format=tar", "-o", str(source_tar), sha, "--", *INCLUDED, cwd=ROOT)
        extract_checked(source_tar, stage)
        (stage / "RUNTIME_DEPENDENCIES.lock").write_text(
            "# Python 3.11; zero third-party runtime dependencies.\n"
            "# This bundle runs via PYTHONPATH=src in a fresh stdlib-only venv.\n"
            "# No pip/build-backend installation is needed for the demo.\n", encoding="utf-8")
        (stage / "BUNDLE_README.md").write_text(
            "# AgentFlight bounded offline demo\n\nSource commit: " + sha + "\n\n"
            "Requires Python 3.11 (stdlib only). From the extracted directory:\n\n"
            "python3.11 -m venv .venv\n"
            "PYTHONPATH=src .venv/bin/python -m agentflight.demo examples/offline-crash-test-demo.json\n\n"
            "Expected: JSON status passed, 2 matching recorded-call verdicts, "
            "2 matching injection-probe verdicts, stable report_hash, exit 0. "
            "An expectation mismatch exits 1; an invalid fixture exits 2. "
            "Run twice and compare stdout bytes for determinism. "
            "Recorded-only, model-free checks do NOT prove live agent execution or sandbox safety.\n\n"
            "Verify SHA256SUMS beside the archive with: sha256sum -c SHA256SUMS\n"
            "For rollback, check out the pinned source SHA. See docs/DEMO.md.\n",
            encoding="utf-8")
        receipt = smoke(stage, tmp / "first-smoke")
        receipt.update({"source_sha": sha, "python": sys.version.split()[0],
                        "tested_at_utc": datetime.now(timezone.utc).isoformat()})
        (stage / "SMOKE_RECEIPT.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        files = sorted(p for p in stage.rglob("*") if p.is_file())
        manifest = {"version": version, "source_sha": sha, "python_minor": "3.11",
                    "runtime_dependencies": [], "files": [
                        {"path": str(p.relative_to(stage)), "sha256": sha256(p), "bytes": p.stat().st_size}
                        for p in files]}
        (stage / "BUNDLE_MANIFEST.json").write_text(
            json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        archive = output / (version + ".tar.gz")
        with tarfile.open(archive, "w:gz") as stream:
            stream.add(stage, arcname=version)
        checksum = sha256(archive)
        (output / "SHA256SUMS").write_text(checksum + "  " + archive.name + "\n", encoding="utf-8")
        extracted = tmp / "extracted"
        extracted.mkdir()
        extract_checked(archive, extracted)
        unpacked = extracted / version
        for item in manifest["files"]:
            if sha256(unpacked / item["path"]) != item["sha256"]:
                raise RuntimeError("bundle manifest checksum mismatch")
        second_receipt = smoke(unpacked, tmp / "second-smoke")
        for key, value in second_receipt.items():
            if receipt[key] != value:
                raise RuntimeError("extracted clean-room smoke differs")
        print(json.dumps({"version": version, "source_sha": sha, "archive": str(archive),
                          "sha256": checksum, "clean_room_smoke": "passed"}, sort_keys=True))

if __name__ == "__main__":
    main()
