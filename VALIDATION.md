# Validation

The SDK cutover replaces the old source-staging fixture and its unrelated
full-game compilation claims. Those checks do not establish compatibility
with the current API and are no longer this template's validation.

## Lightweight tooling

`python3 tools/test_template.py` checks exact-pin syntax, TOML table conversion,
native-extension refusal, byte-identical source/asset projection, stale-source
removal, retained build caches and refusal to overwrite unowned directories.
These are unit tests with explicitly synthetic TOML pins; they neither download
an SDK nor substitute a fake SDK for compilation.

Source-cutover checks on 2026-11-16: **5 Python unit tests passed**; both Python
tools compiled with `py_compile`; the Cargo/mod manifests, language JSON and
workflow YAML parsed successfully. No Rust build or formatter was run in this
isolated source task.

## Published-SDK and live proofs

Run these only after the exact candidate SDK is published, through ordinary
downloads (no checkout SDK injection, game rebuild or manual wasm stdlib):

```sh
python3 tools/horizon.py bootstrap --horizon "$PUBLISHED_HORIZON_SHA"
cargo horizon-mod check --uses
cargo horizon-mod build
cargo horizon-mod check target/horizon-mod/example_mod.hmod --json
python3 tools/horizon.py wasm
horizon-launcher native-build . --instance "Stone Signal" --version "$GAME_TAG" --trust-native-code
horizon-launcher play --instance "Stone Signal" --world stone-signal --creative
```

The packaged native source must also build after unpacking the `.hmod`, not
only from this developer checkout. CI's manual native job exercises that path.
The wasm package must run in a separate unmodified instance of the same build,
with the same mod id enabled; do not load native and wasm variants together.

For both variants record: exact SDK commit, launcher/game release, host/side,
package hashes, successful join message, stone comparator output 15 and output
removal after breaking the stone. Keep native build logs showing SDK downloads
and mod compilation, not game-crate compilation. The README has install/run
instructions and the workflow has actual SDK/package/native-link jobs.

No public SDK build, native link, wasm compilation or live gameplay has been
claimed by the source-only cutover. A release pin is finalized only after
bootstrap succeeds against its actual signed publication; that publication and
the end-to-end canary are release gates, not simulated successes.
