# Horizon native mod template

A real Rust code mod using the **prebuilt, exact-build Horizon SDK**. It ships as
`.hmod`, not as a custom game-source bundle. The launcher compiles the mod and
links it against downloaded game libraries; it does **not** rebuild the game.

The example, **Stone Signal**, attaches a `BlockPart` to stone that makes it a
constant-strength comparator source (15). A `player_logged_in` hook resolves the
player's handle through `ServerHost` and sends a translated explanation. There
is no global tick loop, game-crate dependency, injection or source rewriting.
The same `src/lib.rs` and assets also build as sandboxed WebAssembly.

## Bootstrap

Use GitHub's **Use this template**, then clone your repository. Install Python
3.11+, Rust/rustup, a current Horizon launcher and the published mod tool:

```sh
cargo binstall --git https://github.com/horizon-rust/horizon cargo-horizon-mod
python3 tools/horizon.py bootstrap
```

Without cargo-binstall, build only the **tool**, not the game:

```sh
cargo install --locked --git https://github.com/horizon-rust/horizon cargo-horizon-mod
```

Get the launcher from [Horizon's releases](https://github.com/horizon-rust/horizon/releases).

Bootstrap preserves an existing committed pin. For an uninitialized template,
it delegates to `cargo horizon-mod new --template native`, resolving the current
published Nightly and verifying its SDK before writing exact `[native]` commits
into `horizon-mod.toml`. It never invents a commit or substitutes an older SDK.
If that Nightly has no SDK, the command fails; select a published build:

```sh
python3 tools/horizon.py bootstrap --horizon "$PUBLISHED_HORIZON_SHA"
```

Use an actual SDK-bearing Nightly or full commit from its release. An editor
can resolve `mod_api` after bootstrap downloads `.horizon/sdk/`. An already
pinned clone uses the same bootstrap command to restore that SDK.

## Build, package, run

```sh
# Type-check the actual source against the pinned SDK, for host and wasm.
cargo horizon-mod check --uses

# Pack the native source project and API-use table, then validate the .hmod.
cargo horizon-mod build
cargo horizon-mod check target/horizon-mod/example_mod.hmod --json

# Create a separate test instance in your launcher, then compile/link the mod.
horizon-launcher instance create "Stone Signal"
horizon-launcher native-build . --instance "Stone Signal" --trust-native-code
horizon-launcher play --instance "Stone Signal" --world stone-signal --creative
```

Use an installed game release matching `[native] horizon`; install that release
in the launcher first. `native-build --version TAG` selects an explicit installed
base. Native SDK downloads must match the build, host, side and compiler exactly.
The launcher manages the native compiler and linker. It never falls back to
compiling the game checkout. Native mods run with your rights: read their source
before granting trust. Playing requires your licensed Minecraft resources and
normal account sign-in, prepared by the launcher, not supplied here.

Join the world: the translated message appears in chat. Place stone, then a
comparator with its rear against the stone; it should output 15 without a
redstone input. Remove the stone; the output should stop. This is a useful
manual proof of Part dispatch, beyond merely loading/logging the mod.

The native artifact is `target/horizon-mod/example_mod.hmod`, containing the
flat manifest, Cargo project, source and assets. Share it as registry kind `mod`.
Downloaded SDKs, tooling and target directories are not the package.

## Build the same project as wasm

```sh
python3 tools/horizon.py wasm
```

This refreshes `target/wasm-project/` from the actual source, assets and data,
removes only the native pin table and pins the **same exact SDK** in
`[package.metadata.horizon] sdk`. It invokes `cargo horizon-mod build --wasm`,
then the official package validator. It writes
`target/horizon-mod/example_mod-wasm.hmod` without changing your native project.
The tool installs its pinned wasm Rust components and uses the game's shared
wasm runtime. Do not build or inject a standard library manually.

To run, use a **different, unmodified** instance of the matching game build:
place the wasm package in its game folder's `horizon-mods/`, and add
`mod.example_mod:true` to `horizon-mods.txt`. Start that instance and repeat the
chat/comparator proof above. Never enable the native and wasm variants together:
they have the same mod id and behavior. The wasm artifact filename differs only
to keep both outputs; its manifest id remains `example_mod`.

Wasm is sandboxed and needs neither a player compiler nor native-code consent.
It supports Hooks, Host handles and supported Parts, not arbitrary native Rust
or APIs marked **Not on wasm**. A compile refusal is not a reason to substitute
another SDK or a compatibility alias.

## Customize and extend

* `horizon-mod.toml`: mod identity, capabilities and exact native pins.
* `Cargo.toml`: the SDK dependency at `.horizon/sdk/api/crates/horizon-mod-api`.
* `src/lib.rs`: the one native/wasm implementation.
* `assets/example_mod/lang/en_us.json`: translated player-facing text.
* `tools/horizon.py`: published-SDK bootstrap and disposable wasm projection.

Rename the mod id, Cargo package, asset namespace and translation key together.
The mod id comes from `horizon-mod.toml`, not the Cargo name. Keep player-facing
strings in language files. Additional registry dependencies need a reviewed
lockfile (`horizon-launcher native-lock .`); the example has only the SDK API.

Prefer Hooks and Parts. If a required operation truly needs source patching,
`[[native.mixin]]` remains supported in the **same** `horizon-mod.toml`; the
launcher downloads pinned source, patches only the targeted functions and links
them against the SDK, without rebuilding game crates. Such native extensions
are exact-build-only and cannot use this wasm projection: it refuses them
rather than silently removing behavior. See the
[modding book](https://github.com/horizon-rust/horizon/tree/main/docs/modding/src),
especially `concepts/parts.md`, `concepts/native-route/2-mixins.md` and `reference/sdk/`.

## Release pins and CI

After a candidate SDK has actually been published, finalize its exact pin:

```sh
python3 tools/horizon.py bootstrap --horizon "$PUBLISHED_HORIZON_SHA"
cargo horizon-mod check --uses
cargo horizon-mod build
python3 tools/horizon.py wasm
git add horizon-mod.toml
git commit -m "Pin the published Horizon SDK"
```

On an existing pin, bootstrap uses the official `cargo horizon-mod update`
compatibility report instead of blindly editing commits. Review any API changes
and repeat native/wasm gameplay proofs before publishing either artifact.
Never commit an unavailable candidate as if it were downloadable.

CI runs the lightweight Python projection tests independently, then downloads a
normal published SDK, type-checks both targets and builds/validates both packages.
Its manual workflow additionally accepts an exact matching game release and a
published launcher tag, installs them in isolated homes and links the actual
packaged native source against normal SDK downloads. It needs no engine checkout
or resource injection. Gameplay proof still requires an owner account/resources;
CI linking alone is not a claim that a world was played.

See [VALIDATION.md](VALIDATION.md) for the distinction between tooling checks,
SDK builds, native links and live gameplay. License: [MIT](LICENSE).
