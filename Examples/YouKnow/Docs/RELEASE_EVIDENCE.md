# YouKnow 1.0.0f13 candidate

Validated 2026-09-08 with `JukeboxSDK_500_028`, target 5.0, for the refined
front panel and a distinct U45 build. The first two control rows gain space
below their labels, Bend and Mod move down six pixels, and group titles sit
closer to their left edges. All four faces omit decorative screws. The maker and instrument names share a
centerline in the header, with the blue maker lettering directly on the
plastic. QUALITY and the readouts sit in a subtle separate strip aligned with
the first control caption; tiny icons use a blue and yellow two-bar mark.
The lowest HPF legend becomes 0 while its bass-boost behavior remains.

The candidate updates version metadata and all 93 patch headers. All 28
baseline audio/property inputs match `1.0.0f12`; every patch is byte-identical
after normalizing its version attribute. Both native libraries and all four
universal chip binaries are identical to that candidate. The retained native
audio, automation, sanitizer, bank, and timing evidence below still applies.

Current records are under `Release/validation/1.0.0f13`.

| Check | Result |
| --- | --- |
| Metadata and GUI | PASS: full renderer spacing, mappings, and stock assets; portable validation covers 74 widgets across four panels, 78 nodes, 18 image paths, and 14 artwork twins; all 93 patches pass and regenerate byte-identically |
| Visual review | PASS: final shipped front/back artwork matches the reviewed previews pixel-for-pixel; small icons visually reviewed |
| Local45 Deployment | PASS: 118 source-file matches, 93 patches, and two valid Mach-O libraries matching the completed build |
| Universal45 | PASS: ZIP integrity, 143 members, 138 source-file matches, 93 patches, and four Testing/Deployment 32/64-bit binaries with valid LLVM bitcode headers |
| Compatibility | PASS: 28 unchanged audio/property files, 93 version-only patch changes, and unchanged native/universal audio binaries |

The final package is `Output/Universal45/YouKnow.u45`, with an identical
preserved copy at `Release/1.0.0f13/YouKnow-1.0.0f13.u45`.
Size: 19,829,510 bytes. SHA-256:
`edf44a7642bda9dda7228ad0c9888ad6078184d782e18e82e210cf97c0adc19e`.
`archive.json`, `installed.json`, and `compatibility.json` record the payload
comparisons and retained audio identity.

No fresh compatible SDK 5 host creation test or cloud acceptance was performed
for this iteration. The results above verify source, artwork, local payload,
and U45 packaging.

## Retained 1.0.0f12 candidate

Prepared 2026-09-08 for the `main` source update and a distinct U45 build.
The candidate carries the validated DSP and reference-based plastic artwork
described below. Relative to that iteration, only the version in metadata,
all 93 patch headers, current documentation, and rear silkscreen changes.
Patch musical values, level trims, property contracts, and DSP remain identical.

Current build and validation records are under `Release/validation/1.0.0f12`.
The package is `Output/Universal45/YouKnow.u45`; `archive.json` records its
size, SHA-256, SDK chip inventory, version, and source-file comparisons.
`installed.json` records the local45 payload comparison. Native audio,
automation, sanitizer, bank, and timing evidence is retained from the same
audio source below. A compatible SDK 5 host/cloud acceptance remains separate
from this source push and local U45 packaging.

## Retained 1.0.0f11 refinement validation

Validated 2026-09-08 with `JukeboxSDK_500_028`, target 5.0. This update syncs
the nominated upstream DSP, clears the header collapse button, softens the
plastic finish, unifies rear rules, and moves settings above the cable sockets.
Current records are under `Release/validation/1.0.0f11-refinement`.

The subsequent reference-based front finish uses the original synth's fine ABS
material, a warm charcoal surround, darker textured recesses, and softer edge
highlights. Its GUI checks, regenerated artwork, local45/universal45 builds,
and payload verification are recorded in `Release/validation/1.0.0f11-front-plastic`.
All 138 recorded DSP, metadata, patch, mapping, and rear-art inputs are unchanged;
the audio evidence below is retained. The reviewed 1x front preview exactly
matches the generated panel, and full/folded/browser artwork was inspected.

| Check | Result |
| --- | --- |
| Upstream DSP | Local and fetched `origin/main` at `72e1d4482324465993c8e62609fa345e848d3b70`; 26 scalar comparison scenarios match bit-for-bit |
| Native contracts | Frozen data, expanded engine, wrapper/CV, and ASan/UBSan checks pass; engine 42,264 bytes, wrapper 43,368 bytes |
| Automation | 40 parameters, step/ramp, dry/chorused pass; held notes survive switches; worst continuous slew ratio 1.02 against limit 3.0 |
| Public bank | 93/93 pass at Aging 0% and 50% and low/high six-note stress; six level trims reduced 0.234–1.139 dB; musical settings unchanged |
| Default native CPU | Six voices, 1x/Poly/Cubic/Normal, Aging 50%, 48 kHz/64 frames: 0/1875 deadline misses; median CPU 0.101913 times realtime |
| Metadata and GUI | 184 text keys, 93 patches, 74 bounded widgets across four panels, 78 matching nodes, 14 GUI2D/HD artwork twins; both GUI mappings and socket bindings pass |
| Visual review | Front, rear, and folded previews reviewed at 1x; shared 40-pixel branding inset, neutral rear rules, settings above descending cable runs |
| Local45 Deployment | Intel and Apple Silicon libraries built and installed; 118 source-backed byte matches and all 93 patches verified |
| Universal45 | ZIP integrity and 138 source-backed byte matches pass; 93 patches and four Testing/Deployment 32/64-bit chip binaries verified |

The updated archive is `Output/Universal45/YouKnow.u45`, 19,779,380 bytes,
SHA-256 `c1024d8867f5903e96f86645fe3ca34ab1c0fe62487703fdedbbb7e6d4513c5f`.
Current 1x front previews are `Release/ui-review/front-plastic-reference/front.png`
and `folded-front.png`; rear previews remain in `Release/ui-review/refinement`.
`DSP/SYNC.md` records the exact upstream changes, Rack adaptations, and
comparison/performance evidence, including the retained baseline timing outlier.

The existing user-owned Reason process was left running. These results verify
native contracts, generated assets, installed payload, and SDK packaging;
a fresh Reason session has not been used to verify this update in the host.
Earlier manual/Shop/host records below are historical and were not regenerated
or repeated for this focused update.

## Historical 1.0.0f9 release evidence

Prepared 2026-09-05. This candidate adds modulation CV and corrects intra-block
automation timing. It has not been uploaded or published. Records for this
candidate are in `Release/validation/1.0.0f9`. Current local gates passed;
confirmed SDK 5 host and publication acceptance remain open.

## Changes and compatibility

- SDK `JukeboxSDK_500_028`, target 5.0; permanent product/module identity
  `cz.protocodus.YouKnow` / `YouKnow`; default patch `/Public/Init.repatch`.
- Existing automation IDs 256–289 and property types/persistence remain stable.
  IDs 290–296 add Chorus Hiss, Character, Aging, Quality, Saturation, Early
  Model, and Filter Solver. Native performance controllers keep their SDK roles.
- Existing Note/Gate sockets retain their identities and declaration order.
  Six appended sockets address cutoff, resonance, master volume, amplifier
  level, sub level, and noise level. Audio routing and 41-sample latency remain.
- The wrapper applies subscribed automation/CV changes at their supplied frame,
  including multiple changes per batch. CV changes effective engine values,
  never the document's parameter values. Oversampling retains its idle/fade rule.
- Aging remains 50% for new devices and song-persistent. All 77 patch states
  and their trims are unchanged apart from the candidate version.
- The approved front artwork remains; the rear uses an eight-socket CV grid.
  Groups retain 10px spacing and independent labels at least 16px separation.
- Removed five unused historical design inputs (5,068,645 bytes), condensed
  current documentation, and made Aging selection a supported patch-test option.

## Current checks

| Check | Result |
| --- | --- |
| Latest upstream DSP | PASS: fetched origin/main `412347383290f3a7d998754ac5946f4372716933`; shared DSP matches local `1e20b3191bd1bd18d25dafcc143f75f1809a07fe` and the recorded port source |
| DSP identity | PASS: all 13 Rack DSP/data files match the validated baseline; no algorithm changes or repeated parity claim |
| Song/patch compatibility | PASS: SDK motherboard comparison against f8; 77 version-only patch changes; existing automation and socket identities retained |
| Metadata/GUI | PASS: 184 text keys, 77 patches/trims, both GUI formats and eight socket mappings; front/folded artwork unchanged, rear label minimum 30.9px |
| Automation/CV wrapper | PASS: strict contract, timed control reachability, same-frame retriggers, reset/disconnect, five declared sample rates, allocation guards, ASan/UBSan/float-cast-overflow |
| Unconnected audio compatibility | PASS: f8/f9 stereo fingerprints match bit-for-bit at 1x/2x/4x for the same two-chord program, linked against identical DSP |
| Public bank at Aging 50% | PASS: 77/77 audible, finite, bounded, deterministic; peak 0.055343–0.183660, maximum RMS 0.040589 |
| Native default timing | PASS: first current run after builds/renders completed; 0/1875 wall misses, maximum 0.249291ms against 1.333333ms, median thread CPU 0.104049 times realtime |
| Local45 Deployment | PASS: Intel/ARM libraries; 99 installed source-backed byte matches and 77 patches |
| Universal45 | PASS: 124 archive members, 119 source-backed byte matches, 77 patches, eight CV inputs, four Testing/Deployment 32/64-bit chips; ZIP/bitcode/SDK analyzer checks |
| Recon | PASS diagnostic: fresh Create RE and nonlinear conversions, exit 0, on the legacy-labelled host recorded below |
| Manual/Shop | PASS: six PDF pages, three Shop images, matching current version/CV/automation/defaults, and clean pagination |
| Handoff | PASS: 180 source files, current artifacts and labelled retained evidence; source ZIP and SHA256SUMS verified |

The MIDI range used for added automation is defined by the
[SDK 5 scripting specification](https://developer.reasonstudios.com/documentation/rack-extension-sdk/5.0.0/jukebox-scripting-specification).
Timed-diff handling follows the installed SDK's `API/Jukebox.h` notification
contract and `TJBox_PropertyDiff` in `API/JukeboxTypes.h`. The bundled
`Tools/Build/motherboard_diff.lua` verifies update compatibility.

## Retained evidence

`DSP/SYNC.md` records exact source hashes and intentional Rack adaptations.
Unchanged engine/table code retains its f4 deterministic engine, frozen-table,
14-program upstream parity, reset/event, and stress evidence. Current wrapper
results are required independently because its event handling changed.

The f6 patch renders at Aging 0% and 50%, including Circuit Rain's recorded trim,
remain preserved. The f6 native default probe reported 4/1875 wall-clock misses,
a 6.438042ms maximum against a 1.333333ms deadline, and 0.104131 median CPU times
realtime. It was not retried and its cause was not established. Current timing
results are recorded separately and passed on the first f9 run after task-owned
builds and rendering finished. Workload: six voices, 1x/Poly/Cubic/Normal,
Aging 50%, 48kHz, 64-frame blocks. Native timing excludes the Rack wrapper,
Reason scheduling, and target translation; it does not replace host acceptance.

## Release artifacts and acceptance

- U45: `Output/Universal45/YouKnow.u45`, 9,296,243 bytes.
- U45 SHA-256: `2b53212bab8e0be21f6016d46a0a9c4280c64643fd044f10baedb707956e0574`.
- Manual: `Release/pdf/YouKnow_User_Manual.pdf`, six pages.
- Manual SHA-256: `fd71813dd2f80017f8f989f8e673c073f57a786e2394eb001db73367c7eefca2`.
- Shop artwork: `Release/shop`; actual-size panels: `Release/ui-review`.
- Handoff: `Release/1.0.0f9`; clean source export and SHA256SUMS verified.

The installed Recon is labelled RESDK4; its identity was rechecked as
14.0.2d7 build 20275 TESTING VERSION in `host-inventory.json`. It provides a diagnostic, but its SDK 5
capability has not been confirmed. Native contracts and U45 validation do not
establish real-host automation, CV routing, or Deployment performance acceptance.

Before publication, exercise the exact candidate in a confirmed SDK 5 host and
an authorized Deployment build using the SDK acceptance checklist, including
record/playback automation, Combinator/Remote mapping, live CV cabling, routing,
multiple instances, and maximum-voice/quality workloads. Archive Portal/Shop
acceptance and the existing product-account/content review. No upload,
support-site change, or publication is performed by this preparation run.
