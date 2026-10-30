# Horizon native mod template

A minimal **horizon-mixins** mod template based on
[Horizon Veinminer](https://github.com/levzzz5154/horizon-veinminer).
It declares one HEAD hook that logs a block-break attempt, then lets Horizon's
original method run unchanged. Runtime logic lives in one Rust file that also
builds as a standalone testable Cargo library.

This is the native source-mixin path: it builds a custom Horizon executable.
For content mods (data only, `.hmod`), use Horizon's `cargo horizon-mod new`
instead. This template does not install into a running game or the launcher's
ordinary `.hmod` folder.

## Start a mod

Use GitHub's **Use this template → Create a new repository**, then clone your
new repository. Requirements: Linux, Rust 1.95.0, Python 3.12+, Git and Cargo.
The staging script uses Linux file locks; Windows/macOS are not validated.

```sh
cargo fetch --locked
cargo test --workspace --locked --offline
```

The exact compatible revisions are in [compatibility.json](compatibility.json):

- Horizon: `ba6344a59cb9e755b730dcf02285fc0d33b97d3c` (Nightly 2026-10-30).
- Horizon Mixins: `d9c83d7` (0.6.0, plan schema 6).

Clone the tools beside your mod if you do not already have suitable checkouts:

```sh
git clone https://github.com/horizon-rust/horizon ../horizon
git clone https://github.com/horizon-rust/horizon-mixins ../horizon-mixins
git -C ../horizon-mixins checkout "$(python3 -c 'import json; print(json.load(open("compatibility.json"))["horizon_mixins_revision"])')"
cargo fetch --locked --manifest-path ../horizon-mixins/Cargo.toml
```

Horizon can stay on its existing branch: staging exports the committed pin with
`git archive` and never checks out or edits the original source. Its Git history
must contain the pinned commit. A shallow clone may need a fetch first.
The Mixins checkout must be at the exact recorded revision with clean tracked
engine sources. For an existing development checkout at another revision, use
a separate clone/worktree and set `HORIZON_MIXINS=/path/to/pinned/horizon-mixins`.

## Layout and customization

```text
Cargo.toml                         Standalone runtime library + source audit workspace
compatibility.json                 Exact upstream/tool revisions and source hashes
mixins/example_mod/
  horizon-mixin.toml                Module and HEAD declaration
  break.rs                         Small typed hook adapter
  runtime.rs                       Runtime implementation and unit tests (single source)
tools/horizon.py                   Export → plan → apply → check/build/test
tools/test_template.py             Tiny compiled fixture; no Horizon checkout/assets needed
tools/test_stage.py                Real pinned source audit and repeatability test
tools/audit/                      Rust AST comparison against the pristine export
```

To rename the example:

1. Change Cargo package name/description and the manifest's mod ID/version.
2. Rename `mixins/example_mod/` and update the Cargo `[lib].path`.
3. Change the manifest module name `example_mod` and its reference in `break.rs`.
4. Change the runtime log prefix, unit-test expectation and the native test filter
   `game::example_mod::tests` in `tools/horizon.py`.
5. Run `cargo generate-lockfile --offline` after renaming the Cargo package and
   run the checks below.

Add behavior to `runtime.rs`, then expose it through small typed helpers and
TOML declarations. No payload generation is necessary: Cargo and the injected
module read the same file. Module payloads cannot use inner file attributes
(including `//!` comments), external `mod` files or `include!`; use ordinary
comments and inline modules. Hooks compile in their target's crate/module, so
native-specific imports can be placed in the helper. To keep runtime tests
standalone, use ordinary Rust types or a small host interface there.

This example passes only `pos`. To access the native game, declare an explicit
helper binding for `&mut crate::game::Game<'_>` with value `&mut *self`, as
Veinminer does. Existing crate dependencies/privacy/borrowing remain enforced;
Cargo dependencies from this template are not automatically injected into Horizon.
See [Mixin contracts](https://github.com/horizon-rust/horizon-mixins/blob/main/README.md)
and [effects/state](https://github.com/horizon-rust/horizon-mixins/blob/main/docs/effects-and-state.md)
for cancellation, captures, value changes, bridges and state.

## Stage, compile and run

```sh
python3 tools/horizon.py stage --horizon ../horizon
```

This prints the generated stage path. It uses only committed pinned sources,
records original hashes, runs the real Mixins `plan`/`apply` CLI, and preserves
unchanged bytes/mtimes on repeated runs. The original checkout and player data
stay untouched. The plan is saved at `target/mixins/plan.json`.

If Horizon dependencies are not cached, fetch the staged lockfile once:

```sh
cargo fetch --locked --manifest-path target/mixins/modded/Cargo.toml
python3 tools/horizon.py check --horizon ../horizon
python3 tools/horizon.py test --horizon ../horizon
python3 tools/horizon.py build --horizon ../horizon
```

`check` checks the actual client binary. `test` compiles it and runs the embedded
runtime test module. `build` uses Horizon's `fast` profile and
`--no-default-features` (audio/controllers disabled), and prints its binary path.
These commands use offline, locked builds; raw logs are in `target/horizon-*.log`.
`--target-dir PATH` selects a reusable external Cargo target directory.

Launch the built client with your own **prepared resources for the pinned
Horizon version**, and explicitly pass their path:

```sh
./target/horizon-cargo/fast/horizon-client --resources /absolute/path/to/prepared/resources
```

Prepare those resources using the compatible Horizon launcher or
`horizon-prepare --prepare`; game resources are not supplied by this repository.
Use the binary's `--help` for world/server arguments. Breaking a block should
print `[example_mod] Breaking block at ...` to the host's stderr. The HEAD log
reports attempts, including attempts the original game later rejects.
Compilation tests do not establish interactive gameplay/resource compatibility.

## Pin to a Nightly, package, publish

A native mod builds on one exact Horizon commit, and every mod of a player's build must pin the same one, so
pin a **Nightly**: its release notes name the commit, and the tag `nightly-source/<date>-<short>` keeps that
commit's source downloadable after the Nightly is replaced. This template pins Nightly 2026-10-30
(`ba6344a`). The launcher also builds every mod of a build with one horizon-mixins revision, the one
they all name (`horizon_mixins_revision`), so keep it the same as the other mods your players combine yours with.
To move to a newer Nightly:

1. Put its commit in `compatibility.json` (`horizon_revision`) and in the manifest's
   `[compatibility] horizon_revision`.
2. Update `source_sha256` for each target file (`git -C ../horizon show <commit>:<path> | sha256sum`).
3. Run the checks below. When a target moved (the game is being split into crates), `plan` names the
   missing function: find its new path in that commit and fix `target` in the manifest.

Then `python3 tools/package.py` writes `target/<id>-<version>.hnmod`: `horizon-native.json` plus your
`mixins/<id>/` sources, byte-for-byte reproducible. The mod id must be lowercase letters, digits and `_` (the
registry's rule), and the bundle folder is named after it.

## List it once, then release by tagging

1. **List the project once** at [playhorizon.dev/mods/submit](https://playhorizon.dev/mods/submit) (or a pull request
   to [horizon-mods](https://github.com/horizon-rust/horizon-mods)): your repository's address, kind `native-mod`,
   and the page. A maintainer reads your repository and its source; that is the review.
2. **Release a version**: set `version` in `mixins/<id>/horizon-mixin.toml`, then push a tag with the same number.
   [`.github/workflows/release.yml`](.github/workflows/release.yml) runs `tools/package.py` and publishes a GitHub
   release holding the `.hnmod`. (By hand: publish a release yourself with `target/<id>-<version>.hnmod` as its
   asset; exactly one `.hnmod` per release, not a draft or a pre-release.)
3. Within the hour the registry downloads the asset, checks it as it checks a submission (it reads the source, it
   builds and runs nothing), and lists the version. **There is no pull request and no reviewer for a release:** later
   releases are checked automatically, not read by a person, and `revoked.toml` takes a bad one down. If a check fails
   the release is skipped and an issue in horizon-mods says why. The version, the game and the pins are the ones in
   your `.hnmod`; the changelog is the release's notes.

The Horizon launcher compiles the mod with its own Rust on the pinned commit, in an instance of its own.

## Validation

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets --locked --offline -- -D warnings
cargo test --workspace --locked --offline
python3 tools/test_template.py
# With a Horizon Git clone containing the pin:
python3 tools/test_stage.py --horizon ../horizon
python3 tools/horizon.py check --horizon ../horizon
python3 tools/horizon.py test --horizon ../horizon
```

The tiny fixture compiles the actual bundle, checks the original body executes
once with its result preserved, runs the shared runtime unit test, and verifies
repeated source bytes/mtimes. Wrong revisions and missing targets fail before
replacing the stage. The Rust audit checks the exact generated HEAD/helper and
module, removes only those planned additions, then compares the remaining AST
with pristine source. The same audit runs on a complete pinned Horizon export.
CI runs the standalone checks and tiny fixture; the full native checks require
the larger cached Horizon dependency set. See [VALIDATION.md](VALIDATION.md).

Build/staging tooling is adapted from the MIT-licensed Veinminer port. This
repository includes no Veinminer gameplay, Minecraft assets, game binaries or
exported Horizon sources. License: [MIT](LICENSE).
