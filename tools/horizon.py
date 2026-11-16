#!/usr/bin/env python3
"""Bootstrap a published native SDK pin, or build the same project as wasm."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
NATIVE_FIELDS = {"game", "horizon", "mixins"}


def load(path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


def run(*args, cwd=ROOT):
    subprocess.run(args, cwd=cwd, check=True)


def native_pin(manifest):
    native = manifest.get("native")
    if not isinstance(native, dict):
        raise ValueError("run python3 tools/horizon.py bootstrap before building")
    for field in ("horizon", "mixins"):
        if not re.fullmatch(r"[0-9a-f]{40}", native.get(field, "")):
            raise ValueError(f"[native] {field} must be an exact lowercase commit")
    return native


def without_native(text):
    """Remove the single plain native pin table; retain all other manifest text."""
    manifest = tomllib.loads(text)
    native = native_pin(manifest)
    if set(native) != NATIVE_FIELDS:
        raise ValueError("native extensions (including native.mixin) cannot be built as wasm")
    header = re.search(r"(?m)^\[native\]\s*(?:#.*)?$", text)
    if header is None:
        raise ValueError("write the native pins in a standalone [native] table")
    following = re.search(r"(?m)^\s*\[", text[header.end():])
    end = header.end() + following.start() if following else len(text)
    return text[:header.start()] + text[end:]


def bootstrap(root, horizon):
    manifest_path = root / "horizon-mod.toml"
    manifest = load(manifest_path)
    if "wasm" in manifest:
        raise ValueError("bootstrap expects the native source project, not a built wasm project")
    if "native" in manifest:
        native_pin(manifest)
        if horizon:
            # The official update checks API changes instead of blindly replacing a pin.
            run("cargo", "horizon-mod", "update", "--horizon", horizon, cwd=root)
    else:
        target = root / "target"
        target.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="bootstrap-", dir=target) as scratch:
            project = Path(scratch) / "sdk-pin"
            # new verifies the resolved SDK's signature/checksums before returning.
            run("cargo", "horizon-mod", "new", str(project), "--template", "native",
                "--horizon", horizon or "nightly", cwd=root)
            native = native_pin(load(project / "horizon-mod.toml"))
            downloaded = project / ".horizon/sdk"
            if (downloaded / "build").read_text(encoding="utf-8").strip() != native["horizon"]:
                raise ValueError("the downloaded SDK does not match the generated pin")
            sdk = root / ".horizon/sdk"
            if not sdk.exists():
                sdk.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(downloaded), sdk)
            text = manifest_path.read_text(encoding="utf-8").rstrip() + "\n\n[native]\n"
            text += "".join(f"{key} = {json.dumps(native[key])}\n"
                            for key in ("game", "horizon", "mixins"))
            partial = manifest_path.with_suffix(".toml.partial")
            partial.write_text(text, encoding="utf-8")
            partial.replace(manifest_path)
    # Restores the verified API after a fresh clone of an already pinned project, too.
    run("cargo", "horizon-mod", "hooks", "player_logged_in", cwd=root)
    print(f"Native build: {native_pin(load(manifest_path))['horizon']}", flush=True)


def prepare_wasm(root):
    text = (root / "horizon-mod.toml").read_text(encoding="utf-8")
    manifest = tomllib.loads(text)
    native = native_pin(manifest)
    wasm_manifest = without_native(text)
    cargo = (root / "Cargo.toml").read_text(encoding="utf-8")
    metadata = tomllib.loads(cargo)["package"].get("metadata", {})
    if "horizon" in metadata:
        raise ValueError("keep the native project's SDK pin only in horizon-mod.toml")
    cargo += f'\n[package.metadata.horizon]\nsdk = "{native["horizon"]}"\n'
    project = root / "target/wasm-project"
    marker = project / ".template-projection"
    if project.exists() and not marker.is_file():
        raise ValueError(f"refusing to overwrite an unowned directory: {project}")
    project.mkdir(parents=True, exist_ok=True)
    marker.write_text("Generated from the native project; edit the original sources.\n",
                      encoding="utf-8")
    for directory in ("src", "assets", "data"):
        destination = project / directory
        if destination.exists():
            shutil.rmtree(destination)
        if (root / directory).exists():
            shutil.copytree(root / directory, destination, symlinks=True)
    (project / "horizon-mod.toml").write_text(wasm_manifest, encoding="utf-8")
    (project / "Cargo.toml").write_text(cargo, encoding="utf-8")
    if (root / "Cargo.lock").exists():
        shutil.copyfile(root / "Cargo.lock", project / "Cargo.lock")
    return project


def build_wasm(root):
    project = prepare_wasm(root)
    # The official command fetches the exact SDK and builds the shared-runtime module.
    run("cargo", "horizon-mod", "build", "--wasm", cwd=project)
    mod_id = load(root / "horizon-mod.toml")["id"]
    package = project / "target/horizon-mod" / f"{mod_id}.hmod"
    run("cargo", "horizon-mod", "check", str(package), cwd=project)
    destination = root / "target/horizon-mod" / f"{mod_id}-wasm.hmod"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(package, destination)
    print(f"Wasm package: {destination}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    bootstrap_parser = actions.add_parser("bootstrap", help="fetch and pin a published SDK")
    bootstrap_parser.add_argument("--horizon", help="published build SHA or Nightly name")
    actions.add_parser("wasm", help="build/package the same sources as a wasm-only .hmod")
    args = parser.parse_args()
    if args.action == "bootstrap":
        bootstrap(ROOT, args.horizon)
    else:
        build_wasm(ROOT)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Template: {error}", file=sys.stderr)
        raise SystemExit(1)
