# Validation

Validated on Linux with Rust 1.95.0 on 2026-10-30, using the exact revisions in
`compatibility.json` and the real bundle committed here.

| Check | Result |
|---|---|
| `cargo fmt --all --check` | Pass |
| `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` | Pass |
| `cargo test --workspace --locked --offline` | Runtime unit test passes |
| `python3 tools/test_template.py` | Actual bundle compiles in the tiny fixture; original method calls/result, shared runtime, AST audit, unchanged bytes/mtimes and incompatible revision/target rejection pass |
| `python3 tools/test_stage.py` | Complete pinned Horizon export stages deterministically; original checkout unchanged; exact HEAD/module audit passes |
| `python3 tools/horizon.py check` | Actual `horizon-client` binary checks successfully with `--no-default-features` |
| `python3 tools/horizon.py test` | The runtime's embedded test passes inside the actual Horizon library test target (1 test run) |

The native check reported 69.55 seconds in Cargo, and the native test passed.
Both reused an existing external Cargo target directory with cached
Horizon dependencies. These are compilation/test checks, not a fresh-build
benchmark. Staging the full export took about 24 seconds per command on this
machine; a repeated application preserved the stage.

No game was launched and no Minecraft resources or player data were read or
changed. Interactive logging/gameplay remains a manual check with the compatible
prepared resources. The source audit verifies only the declared HEAD statement
and support module differ from pristine Rust ASTs; it does not claim compatibility
with other Horizon revisions or arbitrary third-party mods.

CI reproduces the formatting, clippy, standalone runtime and tiny-fixture tests.
The full native checks additionally need a Horizon Git history containing the
pin and its cached dependencies; use the commands in README.md to reproduce them.
