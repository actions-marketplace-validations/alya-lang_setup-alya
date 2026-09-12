#!/usr/bin/env python3
"""
setup_alya.py
Core installer for the alya-lang/setup-alya GitHub Action.

Downloads, verifies, extracts, and configures the Alya compiler (alyac)
for Linux, macOS, and Windows runners.
"""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# Ensure UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def log(msg):
    print(f"[setup-alya] {msg}", flush=True)


def log_error(msg):
    print(f"::error::[setup-alya] {msg}", flush=True)


def detect_target():
    """Detect runner OS and architecture matching Alya release artifacts."""
    sys_plat = sys.platform
    mach = platform.machine().lower()

    if sys_plat.startswith("linux"):
        # Linux releases: x86_64-linux
        arch = "x86_64"
        platform_id = "x86_64-linux"
        ext = "tar.gz"
        bin_name = "alyac"
    elif sys_plat == "darwin":
        # macOS releases: arm64-macos or x86_64-macos
        if mach in ("arm64", "aarch64"):
            arch = "arm64"
            platform_id = "arm64-macos"
        else:
            arch = "x86_64"
            platform_id = "x86_64-macos"
        ext = "tar.gz"
        bin_name = "alyac"
    elif sys_plat == "win32":
        # Windows releases: x86_64-windows
        arch = "x86_64"
        platform_id = "x86_64-windows"
        ext = "zip"
        bin_name = "alyac.exe"
    else:
        raise RuntimeError(f"Unsupported operating system: {sys_plat} ({mach})")

    return platform_id, ext, bin_name


def resolve_version(requested_version, token=""):
    """Resolve version string to an actual release tag (e.g. 'latest' -> 'v0.0.5')."""
    version_input = (requested_version or "latest").strip()

    if version_input.lower() == "latest":
        log("Resolving latest Alya release tag from GitHub...")
        url = "https://api.github.com/repos/alya-lang/alya/releases?per_page=1"
        headers = {"User-Agent": "alya-lang-setup-alya"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data and isinstance(data, list) and len(data) > 0:
                    tag = data[0].get("tag_name", "").strip()
                    if tag:
                        log(f"Resolved latest release to: {tag}")
                        return tag
        except Exception as e:
            log(f"Warning: Failed to fetch releases from GitHub API: {e}")
            log("Falling back to default stable release 'v0.0.9'")
            return "v0.0.9"

        return "v0.0.9"

    # Specific version given (e.g. "0.0.5" -> "v0.0.5")
    if not version_input.startswith("v"):
        return f"v{version_input}"
    return version_input


def download_file(url, dest_path, token=""):
    """Download a remote URL to dest_path with optional GitHub authentication."""
    headers = {"User-Agent": "alya-lang-setup-alya"}
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as f:
        shutil.copyfileobj(resp, f)


def verify_sha256(file_path, expected_hash):
    """Verify SHA-256 hash of a local file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    actual_hash = sha256.hexdigest().lower()
    return actual_hash == expected_hash.lower(), actual_hash


def main():
    requested_version = os.environ.get("INPUT_VERSION", "latest")
    check_checksum = os.environ.get("INPUT_CHECK_CHECKSUM", "true").lower() in ("true", "1", "yes")
    token = os.environ.get("INPUT_TOKEN", "").strip()

    try:
        platform_id, ext, bin_name = detect_target()
    except RuntimeError as e:
        log_error(str(e))
        sys.exit(1)

    tag = resolve_version(requested_version, token)
    clean_version = tag.lstrip("v")
    package_name = f"alyac-{tag}-{platform_id}"
    archive_name = f"{package_name}.{ext}"

    # Determine installation / cache directory
    tool_cache = os.environ.get("RUNNER_TOOL_CACHE", "")
    if tool_cache and Path(tool_cache).is_dir():
        install_root = Path(tool_cache) / "alyac" / clean_version / platform_id
    else:
        install_root = Path.home() / ".alyac" / clean_version / platform_id

    install_root.mkdir(parents=True, exist_ok=True)

    # Check if already installed in cache
    existing_bin = list(install_root.glob(f"**/{bin_name}"))
    if existing_bin:
        bin_path = existing_bin[0]
        bin_dir = bin_path.parent
        log(f"Alya compiler found in tool cache: {bin_path}")
    else:
        # Download archive and checksum
        base_url = f"https://github.com/alya-lang/alya/releases/download/{tag}"
        archive_url = f"{base_url}/{archive_name}"
        sha_url = f"{base_url}/{archive_name}.sha256"

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            archive_path = tmp_path / archive_name
            sha_path = tmp_path / f"{archive_name}.sha256"

            log(f"Downloading Alya compiler from: {archive_url}")
            try:
                download_file(archive_url, archive_path, token)
            except Exception as e:
                log_error(f"Failed to download archive '{archive_url}': {e}")
                sys.exit(1)

            # Checksum verification
            if check_checksum:
                log(f"Fetching SHA-256 checksum: {sha_url}")
                try:
                    download_file(sha_url, sha_path, token)
                    expected_sha = sha_path.read_text(encoding="utf-8").strip().split()[0]
                    valid, actual_sha = verify_sha256(archive_path, expected_sha)
                    if not valid:
                        log_error(
                            f"SHA-256 checksum mismatch!\n"
                            f"  Expected: {expected_sha}\n"
                            f"  Actual:   {actual_sha}"
                        )
                        sys.exit(1)
                    log(f"SHA-256 checksum verified: {actual_sha[:12]}...")
                except Exception as e:
                    log(f"Warning: Could not verify checksum ({e}). Proceeding...")

            # Extract archive
            log(f"Extracting {archive_name} into {install_root}...")
            if ext == "tar.gz":
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=install_root)
            elif ext == "zip":
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(path=install_root)

        # Locate binary in extracted directory
        found_bins = list(install_root.glob(f"**/{bin_name}"))
        if not found_bins:
            log_error(f"Failed to locate '{bin_name}' after extraction in {install_root}")
            sys.exit(1)

        bin_path = found_bins[0]
        bin_dir = bin_path.parent

    # Ensure binary is executable on Unix
    if sys.platform != "win32":
        current_mode = os.stat(bin_path).st_mode
        os.chmod(bin_path, current_mode | 0o755)

    # Export to $GITHUB_PATH
    github_path = os.environ.get("GITHUB_PATH", "")
    if github_path:
        with open(github_path, "a", encoding="utf-8") as f:
            f.write(f"{bin_dir}\n")
        log(f"Added {bin_dir} to GITHUB_PATH")
    else:
        # If running outside GitHub Actions (e.g. locally)
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    # Export outputs to $GITHUB_OUTPUT
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"version={clean_version}\n")
            f.write(f"alyac-path={bin_dir}\n")

    # Verify installation
    try:
        ver_output = subprocess.check_output([str(bin_path), "--version"], text=True).strip()
        log(f"Successfully installed Alya compiler: {ver_output}")
    except Exception as e:
        log_error(f"Failed to execute '{bin_path} --version': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
