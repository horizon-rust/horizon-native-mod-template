# Working on a native Horizon mod

Read README.md and horizon-mod.toml before editing. Build against the exact
published SDK, never by staging or recompiling the game. Keep this repository
separate from Horizon and horizon-mixins; do not commit downloaded SDKs,
binaries, generated wasm projects or Minecraft assets.

src/lib.rs is the native and wasm implementation. Prefer typed Hooks, Host
handles and Parts. Use [[native.mixin]] only when the API cannot express the
behavior; such projects are native-only and require an exact build.

Run python3 tools/test_template.py for the lightweight tooling checks.
SDK compilation, package validation, native linking and gameplay checks are
separate: follow README.md and record only checks actually run in VALIDATION.md.
Never claim a candidate SDK is published before bootstrap downloads it normally.
