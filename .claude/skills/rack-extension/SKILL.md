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

Master what you author; the SDK is a download and generated assets are reproducible. For YouKnow
that is 54 files / 1.5 MB.

| Ignore | Why |
| --- | --- |
| `/Tools/`, `/API/`, `/Documentation/`, `/Licenses/`, `/version.txt`, other `Examples/*` | the SDK download |
| `Output/`, `Intermediate-llvm/`, `Release/`, `*.plist`, `validatere-*.log` | build outputs |
| whatever a script in the project regenerates | see below |

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

**Generated assets: ignore them, but pin the generator's inputs.** YouKnow renders every
`GUI2D/*.png` and `GUI/Output/HD/*.png` from `Design/render_panels.py`, and all
`Resources/Public/*.repatch` from `Design/generate_presets.py`. That renderer needs Pillow, the
SDK's `Examples/SimpleInstrument/GUI2D` stock art, and three macOS system fonts — whose exact
SHA-256 hashes are recorded in `Docs/ASSET_PROVENANCE.md` so the render reproduces. Without that
pinning the panels drift between machines, so either record it or keep the art mastered.

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

**Load the device in Reason** (`/Applications/Reason 14.app`) — it reads `RackExtensions_Dev`
just like Recon, and its error dialogs are the fastest real signal. `info.lua` changes need a
restart; `.lua`-only changes need only the song reloaded.

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

> Known blocker on this machine: **headless `--validate_re` is broken**, though Recon itself
> launches and runs fine interactively (`open -a "Reason Recon 14 RESDK4 Logging"` — use it
> normally, Create menu, same as Reason). In validate mode it aborts with
> `Dir is not a rack-extension` at `JukeboxDeviceFileSystem.cpp:3674`, then
> `Stopping the NSApplication due to error returned from IGUILibRunBehavior_OnInitialize`.
> Unrelated to the device under test: reproduces with `--re_dir` pointing at an empty directory
> and with both `RackExtensions` and `RackExtensions_Dev` emptied. Test interactively in Recon
> or Reason and work the manual checklist.

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

## Build and Release

On the website, you upload a Rack Extension .u45 for testing and deployment. If the uploaded Rack Extension passes basic validation tests, it will be scheduled for building. As soon as it is built, it will be available for testing.

https://developer.reasonstudios.com/developer-area/builds

The submission format for Rack Extensions is as a "universal 45", which contains everything needed to transform the Rack Extension to the correct format for the currently targeted Reason version. It is important to set the correct product_id and version_number fields in info.lua before uploading.

The product_id is your registered reverse domain developer id followed by a dot and a product specific suffix, for example 'se.propellerhead.Subtractor'.

The version_number must be in the following format: 1.2.3d4, where '1' = major, '2' = minor, '3' = revision and 'd4' is the stage number. " Supported stages are 'd' for developer, 'b' for beta and 'f' for final builds. Reason Studios recommends using 'developer' for internal developer builds and 'final' for release candidates.

Uploading a Rack Extension with a non-existent product id will create the corresponding product entry.

It is only allowed to use the same product id and version number combination for one upload. Please refer to the SDK documentation for more details.
