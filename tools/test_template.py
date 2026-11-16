#!/usr/bin/env python3
"""Lightweight projection tests. These do not claim SDK compilation or gameplay."""
from pathlib import Path
import shutil
import tempfile
import tomllib
import unittest

import horizon

# Synthetic data for TOML/projection unit tests only, never an SDK download or pin.
PIN = "a" * 40
MIXINS = "b" * 40
NATIVE = f'\n[native]\ngame = "26.3"\nhorizon = "{PIN}"\nmixins = "{MIXINS}"\n'
BASE = 'id = "example_mod"\nversion = "0.1.0"\napi = "0.2"\n'


class TemplateTests(unittest.TestCase):
    def test_exact_pins_required(self):
        for manifest in ({}, {"native": {}}, {"native": {"horizon": "nightly"}},
                         {"native": {"horizon": PIN, "mixins": "short"}}):
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                horizon.native_pin(manifest)
        self.assertEqual(horizon.native_pin(tomllib.loads(BASE + NATIVE))["horizon"], PIN)

    def test_projection_keeps_other_tables(self):
        dependencies = '\n[dependencies]\nhelper = "1.0.0"\n'
        text = BASE + NATIVE + dependencies
        result = horizon.without_native(text)
        self.assertEqual(tomllib.loads(result), tomllib.loads(BASE + dependencies))
        self.assertIn(dependencies, result)

    def test_native_mixin_is_supported_but_not_projected_to_wasm(self):
        text = BASE + NATIVE + '\n[[native.mixin]]\nid = "custom"\n'
        with self.assertRaisesRegex(ValueError, "native.mixin"):
            horizon.without_native(text)

    def test_projection_uses_actual_source_and_exact_build(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / "horizon-mod.toml").write_text(BASE + NATIVE, encoding="utf-8")
            shutil.copyfile(horizon.ROOT / "Cargo.toml", root / "Cargo.toml")
            shutil.copytree(horizon.ROOT / "src", root / "src")
            shutil.copytree(horizon.ROOT / "assets", root / "assets")
            before = (root / "horizon-mod.toml").read_bytes()
            project = horizon.prepare_wasm(root)
            self.assertNotIn("native", horizon.load(project / "horizon-mod.toml"))
            cargo = horizon.load(project / "Cargo.toml")
            self.assertEqual(cargo["package"]["metadata"]["horizon"]["sdk"], PIN)
            self.assertEqual(cargo["dependencies"]["horizon-mod-api"]["path"],
                             ".horizon/sdk/api/crates/horizon-mod-api")
            for directory in ("src", "assets"):
                for source in (root / directory).rglob("*"):
                    if source.is_file():
                        self.assertEqual(source.read_bytes(),
                                         (project / source.relative_to(root)).read_bytes())
            # Refresh removes stale generated sources, but preserves SDK/build caches.
            (project / "src/stale.rs").write_text("old", encoding="utf-8")
            (project / ".horizon").mkdir()
            (project / ".horizon/cache").write_text("keep", encoding="utf-8")
            horizon.prepare_wasm(root)
            self.assertFalse((project / "src/stale.rs").exists())
            self.assertTrue((project / ".horizon/cache").is_file())
            self.assertEqual((root / "horizon-mod.toml").read_bytes(), before)

    def test_projection_refuses_unowned_output(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / "horizon-mod.toml").write_text(BASE + NATIVE, encoding="utf-8")
            shutil.copyfile(horizon.ROOT / "Cargo.toml", root / "Cargo.toml")
            (root / "target/wasm-project").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "unowned"):
                horizon.prepare_wasm(root)


if __name__ == "__main__":
    unittest.main()
