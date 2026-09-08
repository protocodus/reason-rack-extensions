---
name: rack-extension
description: Use when creating or modifying a Reason Rack Extension (RE) in this repo — new instrument/effect device, adding parameters or knobs, writing DSP in JBox_Export_RenderRealtime, editing motherboard_def.lua / realtime_controller.lua / info.lua / device_2D.lua, or building and installing with build45.py.
---

# Rack Extension development (Jukebox SDK 5.0)

This repo masters **only the extension source**. The SDK is a download: unzip the release named
in `version.txt` (`JukeboxSDK_500_028`) over this checkout and `API/`, `Tools/`, `Documentation/`
and `Examples/` appear alongside it — everything below assumes that tree is present.
`Examples/` holds 11 working devices — they are the reference, read them before writing anything.
Docs:
[SDK overview](https://developer.reasonstudios.com/discover/rack-extension-sdk) ·
[Jukebox readme](https://developer.reasonstudios.com/documentation/rack-extension-sdk/5.0.0/jukebox-readme) ·
[Get started](https://developer.reasonstudios.com/learning-and-support/get-started)

## Starting a new device

Copy an example, then adjust. `Examples/SimpleInstrument` for instruments,
`Examples/RE2DAllWidgets` for a widget catalog, `Examples/SilenceDetectionEffect` for effects.

```bash
cp -R Examples/SimpleInstrument Examples/MyDevice
```

Then, in order:

1. **`info.lua`** — `product_id` must be unique reverse-DNS. **The last segment becomes the
   build/install name**, so `cz.protocodus.MyDevice` → `MyDevice`. Also set `long_name`/`medium_name`/
   `short_name` (40/20/10 char limits), `device_type`, `device_height_ru`.
   Changing this file requires restarting Reason/Recon.
2. **`build45.py`** — only `JUKEBOX_SDK_DIR` and `SOURCE_FILES`. It defaults to `"../.."`
   (correct inside `Examples/*`) but honours a `JUKEBOX_SDK_DIR` env var, which is how you build a
   standalone extension repo against an SDK checkout elsewhere. It hard-asserts the SDK release —
   `version.txt` must start `JukeboxSDK_500_` and contain `TargetVersion=5.0`.
3. **`Resources/Public/*.repatch`** — these are XML and hard-code the _original_ device's identity:
   `deviceProductID` and `<DeviceNameInEnglish>`. Leave them and Reason refuses the device with
   **"Patch/song format error: The patch and the Rack Extension have different product IDs"**.
   Either rewrite them or delete them _and_ drop `default_patch` from info.lua:
   ```bash
   sed -i '' 's|se.propellerheads.SimpleInstrument|cz.protocodus.MyDevice|g; s|Simple Instrument|MyDevice|g' \
     Resources/Public/*.repatch
   ```
4. Rename the `.cpp/.h`, the class, and the include guards; drop the stale
   `.sln/.vcxproj*/.xcodeproj` unless you use those IDEs. Delete inherited `Intermediate-llvm/`
   and `Output/` — they contain the old device's build.
5. `Resources/English/texts.lua` — every `jbox.ui_text("key")` in motherboard_def.lua resolves here.
   A missing key is a load error.

Finish with an identity sweep — the old name hides in more places than you expect:

```bash
grep -rn "SimpleInstrument\|Simple Instrument" --include="*.cpp" --include="*.h" \
  --include="*.lua" --include="*.repatch" .
```

## The five files that define a device

| File                                         | Role                                                                                                   |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `info.lua`                                   | identity, device type, height, patch support                                                           |
| `motherboard_def.lua`                        | properties (params, audio/CV ins & outs, native objects) — the contract between Lua and C++            |
| `realtime_controller.lua`                    | non-realtime glue: `rtc_bindings`, `global_rtc` handlers, `rt_input_setup.notify`, `sample_rate_setup` |
| `GUI2D/device_2D.lua` + `GUI2D/hdgui_2D.lua` | 2D panel: image offsets, then widgets bound to property paths                                          |
| `JukeboxExports.cpp`                         | C++ entry points                                                                                       |

A parameter is not one edit — it is three: property in `motherboard_def.lua`, widget in
`hdgui_2D.lua` (+ its `device_2D.lua` node and a PNG in `GUI2D/`), and DSP that reads it.
Miss one and it silently does nothing.

## What to version-control

Master what you author plus everything the build consumes; only the SDK and true build outputs
are droppable. For YouKnow that is 182 files / ~14 MB.

| Ignore | Why |
| --- | --- |
| `/Tools/`, `/API/`, `/Documentation/`, `/Licenses/`, `/version.txt`, other `Examples/*` | the SDK download |
| `Output/`, `Intermediate-llvm/`, `Release/`, `*.plist`, `validatere-*.log` | build outputs |
| `Examples/*/Output/` | the build's own tree — anchor it, see the `GUI/Output` trap below |

**Never commit the SDK.** `Tools/LLVM/Mac` alone is 1.3 GB, and `clang`, `clang++`, `opt`, `llc`
and `lli` each exceed GitHub's 100 MB per-file hard limit, so the push is rejected outright.
`.gitignore` cannot fix it once the blobs are committed — they must come out of history with
`git filter-branch --index-filter 'git rm -r --cached --ignore-unmatch Tools/LLVM'` (or
`git-filter-repo`), and note `filter-branch` also deletes the path from the working tree, so copy
the toolchain aside first (`cp -Rc` is instant on APFS). `Tools/LLVM/Jukebox` is only 4.4 MB of
target libc/libc++ bitcode, but it still ships with the SDK — ignore it too.

**`GUI/Output` is a build _input_, despite the name.** `Tools/Build/build.py` reads it at the end
of a `local45` build and copies it into the install dir, warning `No HD GUI folder called
'GUI/Output'` when it is missing. A blanket `Output/` rule silently swallows the HD art and the
device installs without a panel. Re-include what you author:

```gitignore
Output/
!GUI/Output/
GUI/Output/*
!GUI/Output/gui.lua
```

**Do not assume an asset script is a clean-room generator.** It is tempting to ignore anything a
`Design/` script emits, but YouKnow's scripts are in-place *refiners*: they read the existing
files back and re-emit them, so those files hold source state that exists nowhere else.

- `generate_presets.py` writes the presets defined inline, then loops
  `for path in PUBLIC.rglob("*.repatch"): values, types = read_values(path)` — re-emitting the
  original sounds from their own stored parameter values. Delete them and they are gone.
- `Resources/Public/Init.repatch` is the seed: `read_values()` takes the property name→type table
  from it and every other patch is written using that table. Both scripts fail without it.
- `render_panels.py` composites `GUI2D/PatchBrowseGroup.png`, which nothing generates.

So master `GUI2D/`, `GUI/Output/` and `Resources/Public/` wholesale. Verify the claim rather than
trusting it — clone to a temp dir, run the scripts, and check `git status` is empty:

```bash
git clone <repo> /tmp/fresh && cd /tmp/fresh/Examples/YouKnow
JUKEBOX_SDK_DIR=/path/to/SDK python3 Design/render_panels.py && python3 Design/generate_presets.py
git status --porcelain    # empty = committed assets match a regeneration
```

The renderer also needs Pillow, the SDK's `Examples/SimpleInstrument/GUI2D` stock art, and three
macOS system fonts whose SHA-256 hashes are pinned in `Docs/ASSET_PROVENANCE.md` — a Linux CI box
cannot reproduce the panels, which is a second reason to keep them committed.

The exception is a frozen artifact whose generator lives **outside** the repo: `DSP/*.inc` holds
host-built lookup tables as hex doubles, is not reproducible here, and stays committed under
`Tests/FrozenTableContract.cpp`.

## C++ entry points (`API/Jukebox.h`)

- `JBox_Export_CreateNativeObject` — construct your C++ state; called from
  `jbox.make_native_object_rw/ro` in RTC. **Do allocation and heavy setup here.**
- `JBox_Export_RenderRealtime(void* state, diffs, count)` — the audio callback.
- `JBox_Export_Draw` / `Gesture` / `DisplaySetup` / `Notify` — custom display + UI.

### Realtime rules — non-negotiable

`RenderRealtime` gets ~1.5 ms for the _entire rack_ per batch.

- No allocation, no locks, no file/sample loading, no long math.
- Only a subset of the Jukebox Toolbox is legal there — an illegal call **aborts the call and
  disables the device instance**. Check the per-function notes in `API/Jukebox.h`.
- Writing an audio output means writing **every** frame of that DSP buffer. Not writing it at all
  marks the output silent (a host optimization) — that's the correct way to output silence.
- NaN/Inf in a DSP buffer is not allowed.
- CV outputs hold their last value if unwritten.
- Property diffs are ordered by frame position and already applied to the MOM. Subscribe via
  `rt_input_setup.notify` when you'd otherwise miss multiple changes within one batch (e.g. a
  gate toggling twice).

Move anything expensive into a native object created in `CreateNativeObject`, triggered from
`realtime_controller.lua` (see `SimpleInstrument`'s async sample load on sample-rate change).

## Build & install

```bash
cd Examples/MyDevice                      # must run from the project dir
python3 build45.py local45 Debugging      # Debugging | Testing | Deployment
python3 build45.py universal45            # store submission; requires development_version=false
```

The build installs into `~/Library/Application Support/...`, which is **outside the agent
sandbox** — compilation succeeds and then `getInstallDir()` dies with
`PermissionError: Operation not permitted`. Run builds with the sandbox disabled.
`Debugging` also copies `.dSYM` bundles into the installed RE folder; harmless.

`local45` compiles native and installs into
`~/Library/Application Support/Propellerhead Software/RackExtensions_Dev/<REName>`
(`%APPDATA%\Propellerhead Software\RackExtensions_Dev\<REName>` on Windows).
Clang static analysis is on by default — leave it on.

## Shipping — the `.u45` is the product

`python3 build45.py universal45` emits **`Output/Universal45/<Name>.u45`**, a zip of
`info.lua` + `motherboard_def.lua` + `realtime_controller.lua` + `version.txt` + `GUI2D/` +
`Resources/` + `chip_binaries/{Testing,Deployment}/<Name>{32,64}.ll`.

The chip binaries are **LLVM IR, not machine code** — Reason Studios compiles them per-platform
in the cloud. That upload, at [developer.reasonstudios.com](https://developer.reasonstudios.com),
is the real build-and-validate gate; local `local45` builds are only for iteration and never ship.
So a clean local build proves nothing about acceptance — keep `universal45` working as you go
rather than discovering it at submission time.

Requirements the local build enforces: `development_version` must be false or absent in
`info.lua`, and `texts.lua` must be final (it ships as-is). Keep the archive clean — the
acceptance checklist has an explicit "no unnecessary files in U45 archive" item, and public
samples must be wav or aif.

## Testing

**Retail Reason does not load `RackExtensions_Dev`.** Verified on 2026-09-08: with the
cloud-built RE uninstalled, a `local45` build in that folder is invisible to
`/Applications/Reason 14.app` (14.1d100). That folder is read by the RESDK *testing* builds
only — which is what Recon is for. A YouKnow appearing in retail Reason's browser is the
signed RE in `RackExtensions/`, not your `local45` output.

So `local45` is for iteration under a matching RESDK host. **To put a build in front of a
retail Reason, upload the `.u45`** at [developer.reasonstudios.com](https://developer.reasonstudios.com/developer-area/builds),
let it cloud-build, and install it — that is how any previously installed version got there.

A same-identity collision is silent and costs hours: an installed RE with the *same*
`product_id` **and** `version_number` as a development build wins, so the dev build never
appears no matter how often the device is recreated. Bump `version_number` for every build you
intend to see. `info.lua` changes need a restart; `.lua`-only changes need only the song
reloaded.

Automated validation in Recon:

```bash
python3 Tools/Build/validatere.py "/Applications/Reason Recon 14 RESDK4 Logging.app" \
  cz.protocodus.MyDevice ~/Library/Application\ Support/Propellerhead\ Software/RackExtensions_Dev
```

That prints the real command; run it, then **always read both logs afterwards** — Recon exits 0
and prints nothing on failure, so the console tells you nothing:

```bash
cat validatere-re.log                          # per-RE results; one line only = it never got started
grep -iE "error|fail|exception|not a rack" validatere-test.log | head -30
```

> **Do not run the installed Recon in this shared user profile.**
> On 2026-09-08 a Recon run after moving the installed-RE index aside was
> associated with deletion of `RackExtensions/cz.protocodus.YouKnow.1.0.0f9`.
> Preserve that observed failure; its cause was not established. Never move
> or delete the installed-RE index or broad Reason cache folders for validation.
>
> The earlier attribution to an SDK 4-only host was incorrect. Read-only
> inspection of `Reason Recon 14 RESDK4 Logging` (14.0.2d7 build 20275) found
> SDK 5 native drawing APIs and an explicit `kJukeboxTargetVersion50` assertion.
> It is signed by Reason Studios AB. The official SDK 5 readme still uses
> RESDK4-labelled example paths, so the filename does not establish capability.
> `Examples/YouKnow/Release/validation/production-audit/host-inventory.json`
> records binary hashes, versions, signature identity, and the observed signals.
>
> SDK 5 hosting code is present, but exact-candidate creation and runtime
> acceptance remain unverified. Use an authorized cloud-built candidate in
> retail Reason, or establish a separate test profile/VM before local Recon
> validation. Do not treat copying the app or changing its name as isolation.
> A previous broken GraphicsCache symlink also interrupted startup; inspect
> exact failures without clearing the user's caches as a shortcut.

Manual acceptance: **[`Documentation/acceptance_testing_checklist.txt`](../../../Documentation/acceptance_testing_checklist.txt)**.
Read it and walk the boxes — don't paraphrase it from memory. Two checklists in that file:

- **Full** — any graphics, parameter, or behavior change. Sections: Reason versions, archive,
  graphics, general behavior, device-type-specific (Instruments / FX / Players), then
  feature-specific (patches, audio sockets, patterns, sample loading).
- **DSP checklist** (bottom of file) — the reduced pass, valid _only_ when nothing but DSP changed:
  no graphics files added or removed, and only the version number touched in `info.lua`.

Design-affecting items worth knowing before you build, not after:

- Test in both latest Reason **Testing** and **Deployment**.
- Instruments: respect master tuning; Note On indicator on folded _and_ unfolded front panels;
  polyphonic CV Gate/Note (test through RPG-8).
- FX: On/Off/Bypass fader on front and folded front; mono in → mono out auto-routing;
  Combinator "Bypass All FX" must bypass the device.
- Any device with audio sockets: implement `request_reset_audio`; silent input
  (`<kAvoidZeroOffset`) must produce silent output.
- Automation: every parameter remotable (Custom Display widgets may not be), flat parameter list
  max 20 items, no single-entry groups, sane hit boxes.
- Patches: patch display on front and folded front, a default patch, 5–20 examples in the root.

## Iterating

Reason/Recon holds the dylib open while an instance exists. Fast loop: "Delete devices and tracks"
in Recon → rebuild/install → Undo. Lua edits reload without a rebuild; `info.lua` needs a restart.

When a Lua parse-error popup offers **Retry**, don't — it's unstable. Fix the file and reload the song.

## Debugging

`JBOX_TRACE("...")`, `JBOX_TRACEVALUES("x=^0", values, n)`, `JBOX_ASSERT(...)` from C++;
`jbox.trace(...)` from Lua.

In a `Debugging` build, Reason surfaces device problems in a **"Debug Info"** dialog — that dialog
text is the actual diagnosis, so read it before guessing. Build `Deployment` to silence it.

## The distribution agreement governs release

**<https://developer.reasonstudios.com/agreements/distribution-agreement>** — *General
Terms and Conditions, Distribution, Version 2, updated 14 August 2020.* Read it before any
release and steer development toward it by default. A human may override a call it implies;
you may not, and you may not settle a question by guessing at what it says. Do not commit
its text to this repo — §14 reserves Reason Studios' material and this is their document,
not ours. Cite the clause and link.

Clauses that actually shape the work:

- **§2 — nothing ships that we do not own.** "Any musical compositions, sound samples or
  other content incorporated in the RSPP must either be fully owned by the Developer or the
  Developer must have acquired a sub licensable right", such that neither Reason Studios nor
  any End User owes a royalty to a third party. §2 also forbids infringing "copyrights,
  trademarks, patents or design rights". `Docs/ASSET_PROVENANCE.md` is the traceability
  record and says outright it is *not* a legal conclusion or grant of rights; the open owner
  gate lives in `Docs/RELEASE_CHECKLIST.md`. **A green provenance table is not permission.**
- **§2 — no copyleft.** No "open source software, free software or other third party
  products which may create an obligation ... to disclose or distribute the RSPP (or any
  part thereof), any software or source code on open source license terms". Permissive
  licences are fine; anything reciprocal is not. Check this before adding a dependency, not
  at release.
- **§2 — no personal data.** An RSPP "may not process any personal data" of End Users. No
  telemetry, no analytics, no phone-home.
- **§3 — every change needs re-approval.** "If the Developer makes any changes to the RSPPs
  (during or after the approval procedure), the Developer shall resubmit ... Such changes
  include, but are not limited to, bug fixes, patches or updates." There is no such thing as
  a quiet hotfix. Budget the review: Reason Studios aims to decide within thirty days, and
  an appeal to the review board takes a further fifteen and is final.
- **§3 — do not misrepresent the device.** "The Developer shall not hide or misrepresent any
  feature or functionality of the RSPPs during the approval process." What the panel, the
  copy and the submission notes claim must be what the device does.
- **§4 — distribution is exclusive to the Marketplace.** The waiver for "unlicensed,
  non-executable product content" explicitly "does not apply to Rack Extensions". Do not
  plan a side channel for the built RE.
- **§16 — we carry the indemnity.** The Developer indemnifies Reason Studios for third-party
  claims, including IP infringement, for the term plus five years. That is why an unresolved
  ownership question is a blocker to raise, never a risk to absorb.

Downstream of the above, and enforceable here:

- **The SDK is never redistributed** — not in the repo, a release asset, a CI cache, or a
  bucket. `.github/workflows/ci.yml` gates this: no SDK path tracked, only `Examples/YouKnow`
  under `Examples/`, nothing tracked over 50 MB.
- **No factory patch payload from the modelled instrument.** `Design/generate_presets.py`
  enforces it in code: `main()` refuses to ship an `A/`, `B/` or `Factory Bank/` directory and
  the metadata step strips those URLs. Sounds in the same musical territory are authored here;
  someone else's stored parameter data is not copied.
- **Identity is our own.** No other manufacturer's marque, model number or trademark in the
  product id, names, panel art, patch names or copy — §2 covers trademarks and design rights,
  and §16 is who pays if we get it wrong.
- **One upload per product id and version.** Bump `version_number` for every upload; a failed
  cloud build still consumes the version it was uploaded as.

## Build and Release

On the website, you upload a Rack Extension .u45 for testing and deployment. If the uploaded Rack Extension passes basic validation tests, it will be scheduled for building. As soon as it is built, it will be available for testing.

https://developer.reasonstudios.com/developer-area/builds

The submission format for Rack Extensions is as a "universal 45", which contains everything needed to transform the Rack Extension to the correct format for the currently targeted Reason version. It is important to set the correct product_id and version_number fields in info.lua before uploading.

The product_id is your registered reverse domain developer id followed by a dot and a product specific suffix, for example 'se.propellerhead.Subtractor'.

The version_number must be in the following format: 1.2.3d4, where '1' = major, '2' = minor, '3' = revision and 'd4' is the stage number. " Supported stages are 'd' for developer, 'b' for beta and 'f' for final builds. Reason Studios recommends using 'developer' for internal developer builds and 'final' for release candidates.

Uploading a Rack Extension with a non-existent product id will create the corresponding product entry.

It is only allowed to use the same product id and version number combination for one upload. Please refer to the SDK documentation for more details.
