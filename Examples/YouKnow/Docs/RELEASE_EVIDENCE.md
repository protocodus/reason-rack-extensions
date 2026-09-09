# YouKnow 1.0.0f18 candidate

This candidate fixes simultaneous note boundaries and MIDI/CV ownership in the
Reason wrapper. It retains the per-voice envelope and voice-allocation model;
no shared DSP or VST code changed. All 100 patches differ from f17 only in
their version attribute, and the generated rear artwork changes only around
the version digit. The full front, folded panels and metadata retain their bytes.

The [boundary-fix report](MIDI_BOUNDARY_FIX.md) records passing functional,
sanitizer and hardware-preservation regressions. It also retains the native
performance failure: 3 of 1,875 wall-clock blocks exceeded 1.333333 ms, with a
4.031084 ms maximum. That probe uses the unchanged engine and excludes the
wrapper. No clean native timing or host acceptance is claimed.

| Check | Result |
| --- | --- |
| Scope and sound preservation | PASS: only `YouKnow.cpp`/`.h` runtime changes; shared DSP, musical patch values, trims, metadata and permanent properties unchanged |
| Metadata and panels | PASS: 100 unique patches, 184 text keys, 74 widgets, 78 nodes, both GUI asset trees and f18 version consistency |
| Local45 Deployment | PASS: 125 source-backed byte matches, 100 patches and both completed native libraries |
| Universal45 | PASS: ZIP integrity, 150 members, 145 source-backed byte matches, 100 patches and four LLVM chips |
| Materials | PASS: all six manual pages rendered and visually reviewed; front/thumbnail byte-identical to f17, rear changes confined to the version glyph |

The handoff is `Release/1.0.0f18/YouKnow-1.0.0f18.u45`, 19,854,855 bytes,
SHA-256 `65b9e896206e9139e1c702bea65a68a71afb044220d60a8caeba69d972fbc4f9`.
The folder also contains the matching manual, three Shop images, a build
manifest and verified `SHA256SUMS`. Manual SHA-256:
`db948343d755bfeef28acd453f0c05a6883403318b69f8e1c0e4fa2b492ec0b3`.
Local45 installed the development payload under `RackExtensions_Dev/YouKnow`;
the production f17 library remains byte-identical to the initial investigation.

Fresh Reason reproduction of the user's touching-note recording remains open.
The available SDK 5-capable Recon shares a user profile involved in an earlier
extension-pruning incident. No verified complete isolation route is available;
the user's running production Reason session is left intact. Current build and
material records are under `Release/validation/1.0.0f18`.

# Retained YouKnow 1.0.0f17 candidate

The bank expands from 93 to exactly 100 original presets. Seven new recipes
explore pulse-width modulation, inverted filter envelopes, noise percussion,
portamento and the sub oscillator. Existing patch states, level trims, permanent
properties and DSP remain unchanged from f16. Local validation passes.

The f16 inline header and equal edge margins are retained. The f17 rear version
label and matching manual identify the expanded candidate. Fresh host qualification
and cloud acceptance remain open; earlier failures below retain their original scope.

The additions are Reverse Clav, Glass Loom, Resonant Woodblock, Steam Hat,
Amber Ribbon, Gated Undertow and Afterimage. [PRESETS.md](../PRESETS.md)
describes their signal paths and playing suggestions. Only these seven patches
were calibrated; the earlier gain measurements and manual adjustments are intact.

| Check | Result |
| --- | --- |
| Bank and metadata | PASS: exactly 100 unique patch states, 100 browser entries and 100 calibrated trims; schema, categories, tags, identity and both GUI formats valid |
| Default audio render | PASS: 100/100 audible, finite, bounded and deterministic at Aging 50%; reference-chord maximum peak 0.184990 and maximum RMS 0.040939 |
| Six-note stress | PASS: all 100 at low and high registers; maximum peaks 0.413066 and 0.435990, below full scale |
| New-patch calibration | PASS: only seven new measurements/trims; the additions pass at Aging 0% and 50% |
| Musical demos | PASS: seven unnormalized stereo WAVs with articulation, velocity and note-off tails; no clipping, nonfinite samples or lingering voices; maximum peak 0.219133 |
| Preservation | PASS: all 93 earlier patch files differ only in version; prior gain/measurement/adjustment and metadata entries unchanged; all 28 audio/property files unchanged |
| Local45 Deployment | PASS: 125 source-backed byte matches, 100 patches and both completed native libraries |
| Universal45 | PASS: ZIP integrity, 150 members, 145 source-backed byte matches, 100 patches and four LLVM chips |
| Audio binary identity | PASS: both native libraries and all four universal chips are byte-identical to f16 |
| Materials | PASS: six-page manual and three Shop PNGs reviewed; front/thumbnail unchanged, rear changes confined to the version glyph |

The verified package is `Release/1.0.0f17/YouKnow-1.0.0f17.u45`,
19,854,668 bytes. SHA-256:
`1bddf8240e11d7f9b2685e9bca93e4d7b1bc194e21984aa69844d1d37c447f9f`.
The manual SHA-256 is
`38b5e31d1d9c0223e6619feac160b917183dd82777c9ca10825c25ac52ac7861`.

The candidate folder includes the U45, manual, product images, seven WAV demos,
their playing guide, a build manifest and verified `SHA256SUMS`.
Detailed records, the seven-only calibration driver and native audition harness
are in `Release/validation/1.0.0f17`. Demo checks are measured native renders;
auditory listening and fresh Reason host qualification have not been performed.
No f17 cloud upload or acceptance is claimed. The prior browser file-selection
rejection remains recorded under f16 below.

# Retained YouKnow 1.0.0f16 candidate

The full-panel branding now reads YOUKNOW followed by a smaller blue
“by Protocodus” on one line. The full front balances that signature, the complete
preset selector, and the device-name tape as one row. Actual visible bounds
are x94.4–659.6 in the 754-pixel panel: both outer margins are 94.4 pixels.
The brand's glyph ink spans y13.2–30.8 within the 44-pixel nameplate, preserving
equal vertical padding. The full rear uses the same inline signature at its
protected x40 inset; the compact folded layout remains unchanged.

Both consumed GUI layouts use the measured front positions: patch name
(284,16), browse controls (502,13), and device name (580,17). The selector
retains 25.6 pixels after the maker byline and 20 pixels before the tape canvas.
Existing renderer checks enforce the actual ink margins and native-widget
clearances. The quality strip remains full width.

## Final local validation

| Check | Result |
| --- | --- |
| Independent code and visual review | PASS: final inline header, both GUI formats, full/folded panel composites; no actionable findings |
| GUI and patch validation | PASS: 74 widgets, 78 nodes, 18 image paths, 14 GUI asset twins, 184 text keys, and 93 patches with deterministic trims |
| Local45 Deployment | PASS: 118 source-backed byte matches, 93 patches, and both native libraries match the completed build |
| Universal45 | PASS: ZIP integrity, 143 members, 138 source-backed byte matches, 93 patches, and four LLVM chip binaries |
| Audio compatibility | PASS: all 28 audio/property inputs, both native libraries and four universal chips are byte-identical to f15; all 93 patches differ only in their version attribute |
| Release materials | PASS: matching six-page manual and all three Shop PNGs reviewed and copied into the candidate folder |

The verified package is `Release/1.0.0f16/YouKnow-1.0.0f16.u45`,
19,849,842 bytes. SHA-256:
`a8e838f1054c92a5f6d54ca4186d7b31daf3b1b053a600546a43d3c4f694291a`.
The manual SHA-256 is
`d426a0ab142b0cca912fcecc8fc1cf514f07ff461feab7a553e2e8a269d76bc2`.
Detailed build/payload records are under `Release/validation/1.0.0f16`;
final panel comparisons are under `Release/ui-review/1.0.0f16`.
The candidate folder includes a build manifest and verified `SHA256SUMS`.

The user authorized upload. The browser file chooser rejected the final f16
archive with `Not allowed` before submission, so no f16 cloud result is claimed.
The browser tool's troubleshooting guidance recommends enabling “Allow access
to file URLs” for the ChatGPT extension; the setting itself was not inspected.
This browser-side rejection is separate from the prior f15 server failure.

## Investigation of the f15 cloud failure

The Reason Studios portal confirms that f15 Deployment build
`8d852fdd-c51b-419d-882a-e216c23b3228` failed. The server timestamps are
`2026-09-08T20:42:41.299944+00:00` through
`2026-09-08T20:48:32.015879+00:00`. Expanding its log displays only
“Unknown error”; the portal's normal build-list response includes no failing
stage or technical diagnostic. No additional log request occurs on expansion.
The service does not expose the uploaded archive checksum in that response.

Targeted investigation records are in `Release/validation/cloud-f15-debug`:

- All four archived chips pass the SDK's forbidden-global check.
- The official optimized45 64-bit Deployment path successfully translates,
  links, and checks undefined symbols for both Mac Intel and Apple Silicon.
- The exact SDK Windows x64 optimization/code-generation sequence produces a
  valid AMD64 COFF object. Windows DLL linking and its dependency check were
  not tested because the required Windows linker, wrapper and CRT are absent.
- All 38 archived PNGs pass format, CRC, decompression and decode checks;
  their formats/dimensions match the retained f11 source. SDK Lua evaluation
  finds all 86 rendered leaves within their panels. The exact successfully
  uploaded f11 bytes are unavailable, so that source comparison is not a
  cloud-payload identity claim.

No concrete local GUI, DSP, or package defect was reproduced. This investigation
does not establish the cause of the service failure or a fix. The requested
f16 UI revision uses a new version because the f15 upload consumed that version.
A support-request draft with the build ID is preserved but has not been sent.
Actual host/performance qualification and Reason Studios acceptance remain open.

## Retained 1.0.0f15 candidate

Validated on 2026-09-08 for the requested header refinement. Actual
PROTOCODUS/YOUKNOW glyph ink spans y6–38 in the 44-pixel nameplate, giving
six pixels of visible plastic above and below on both full panels. The quality
background and its separator reach both panel edges, while the readouts keep
their established alignment with the first control caption.

Independent code and visual reviews found no defects. The full-panel bodies
below y70, both folded panels, and the tiny blue/yellow icons remain unchanged.
Larger browser previews reflect the new nameplate. The current-version validator
now checks each document's current declaration while allowing dated historical
evidence; 16 focused fixtures verify stale and missing declarations are rejected.

| Check | Result |
| --- | --- |
| GUI and patch validation | PASS: 74 widgets, 78 nodes, 18 image paths, 14 GUI asset twins, 184 text keys, and 93 patches with deterministic trims |
| Visual review | PASS: both full panels, folded panels, header geometry, and edge-to-edge quality strip; records under `Release/ui-review/1.0.0f15` |
| Local45 Deployment | PASS: 118 source-backed byte matches, 93 patches, and both native libraries match the completed build |
| Universal45 | PASS: ZIP integrity, 143 members, 138 source-backed byte matches, 93 patches, and four valid LLVM chip binaries |
| Audio compatibility | PASS: all 28 audio/property inputs, both native libraries, and all four universal chips are byte-identical to f14; all 93 patches differ only in their version attribute |

The verified package is `Release/1.0.0f15/YouKnow-1.0.0f15.u45`,
19,851,411 bytes. SHA-256:
`5668207cdea7adbed1a047a98004c2b53eedf1cf035342fce9a9dfe0733936f3`.
Detailed build, source, binary, and payload records are under
`Release/validation/1.0.0f15`.

The matching six-page manual, three Shop PNGs, and support-site WebPs pass
fresh visual review. The candidate folder contains these files, a verified
recursive `SHA256SUMS`, the build manifest, and a host acceptance worksheet.
Its seven-file support-site patch applies cleanly to the retained deployed
source `d36663e4311427a5914fd9d3efb932d32b4d7610`; the website checkout and
live site remain unchanged. Historical f14 evidence is labelled separately.

The retained f14 engine, wrapper, and sanitizer results apply to the identical
audio binaries. Its wall-clock timing qualification remains open. At the initial
local handoff, no fresh host creation test, cloud upload, or publication had been
performed. The user subsequently authorized upload; the resulting f15 cloud
failure and investigation are recorded above.

## Retained 1.0.0f14 candidate

Final code review on 2026-09-08 corrected four reproduced playback/reset bugs:

- Simultaneous Note/Gate CV updates could start the old pitch and glide to the
  new one when Gate arrived first. The wrapper now resolves the frame's pitch
  before replaying gate edges, including retriggers and reconnections.
- A CV note dropped by a full voice pool could stay silent on later pitch
  changes. Legato retargeting now requires a keyed source voice; otherwise the
  wrapper retries normal allocation without corrupting the held-note counts.
- Deferred voice-assignment scans could create audio that was discarded in a
  scratch buffer. Newly assigned voices now retain their onset and output tail.
- Audio reset could preserve an in-flight Character glide. Reset now restores
  the current control image immediately, while later-frame automation retains
  its event timing.

Focused before/after reproducers and expanded engine/wrapper regressions cover
all four cases. The strict engine and wrapper contracts pass; the wrapper also
passes AddressSanitizer, UndefinedBehaviorSanitizer, and float-cast-overflow
checks. Leak detection is unavailable in this macOS sanitizer runtime. All
three normal quality fingerprints match f13, and object sizes remain 42,264
bytes for the engine and 43,368 bytes for the wrapper.

The release-material builder now loads all four colored fader assets and derives
the manual cover's patch count from the shipped bank. The guide, patch catalog,
and notices match the current panel and 93-patch bank. The six-page f14 PDF and
all three Shop images pass visual review. Full renderer and portable GUI/patch
validators pass; front, folded-front, and icon artwork are byte-identical to
f13, with only the rear version silkscreen and its previews regenerated.
All 93 patch sound values, property identities, and socket mappings remain.

## Native timing qualification remains open

A default six-voice, 1x/Poly/Cubic/Normal, Aging 50%, 48 kHz/64-frame timing
run encountered 4/1875 wall-clock misses on a machine with unrelated background
work. One controlled f13/f14 comparison followed, without concurrent builds or
renders from this task: median thread CPU was 0.114177 times realtime for f13
and 0.114014 for f14. Both failed the wall-clock deadline gate (14/1875 and
7/1875 misses; maxima 9.435291 ms and 31.505458 ms against a 1.333333 ms budget).
The earlier candidate's failure and essentially equal CPU cost point to
scheduling contention rather than an observed DSP CPU regression. All three
runs are retained; no current wall-clock timing pass is claimed. Qualification
in a quiet, compatible SDK 5 host remains required.

## Build and package records

Records are under `Release/validation/final-review`. SDK 5 local45 Deployment
and universal45 builds pass. Installed payload verification finds 118 matching
source-backed files, 93 patches, and both native libraries matching the completed
Intel/Apple Silicon builds. The U45 passes ZIP integrity with 143 members,
138 source-backed byte matches, 93 patches, and four Testing/Deployment 32/64-bit
LLVM chip binaries. Patch regeneration preserves all 93 patches and metadata
byte-for-byte. The source audit permits only the two reviewed runtime files;
25 other audio/property inputs remain unchanged.

The preserved package is `Release/1.0.0f14/YouKnow-1.0.0f14.u45`,
19,852,536 bytes. SHA-256:
`e93bb2a07bed3b6571ca9272dbcc3355f86df4ee801550961fc7062bd891676a`.
The same folder contains the reviewed PDF, three Shop images, build manifest,
and a verified `SHA256SUMS`. `archive.json`, `installed.json`, and
`compatibility.json` record the detailed source and payload comparisons.
No fresh compatible SDK 5 host creation test or cloud acceptance was performed.

## Production host and portal audit

Read-only inspection on 2026-09-08 found SDK 5 hosting code in the installed
Recon 14.0.2d7, build 20275, despite its legacy RESDK4 filename. Its binary
contains the SDK 5 native drawing APIs and an explicit target-version-5.0
assertion. Retail Reason 14.1d100, build 20457, also contains those APIs;
both are signed by Reason Studios AB. Binary hashes and identity evidence
are in `Release/validation/production-audit/host-inventory.json`.
The [official SDK 5 readme](https://developer.reasonstudios.com/documentation/rack-extension-sdk/5.0.0/jukebox-readme)
still uses RESDK4-labelled Recon paths. Earlier claims that the filename
proved SDK 4-only support were incorrect.

This establishes available SDK 5 code, not f14 runtime acceptance. The prior
shared-profile pruning incident remains a separate reason not to launch
Recon in the current user profile. No host was launched for this audit.

The authenticated Developer Portal confirms the existing
`cz.protocodus.YouKnow` product. Its latest listed build is f11 Deployment,
with a successful cloud build and product status `testing`; f14 is not yet
uploaded or accepted. The reviewed f14 archive is ready for an authorized
cloud build. Acceptance, representative-song timing, and publication remain
open for this exact candidate.

An unpublished Shop text draft was saved and reopened at page `33752`, with
reviewed copy, support links, and the available Synth / Analog / Vintage /
Hardware emulation tags. The Product selector offered no accepted product;
association, images/PDF, price, acceptance, and publication remain incomplete.
The public support URL loads successfully, but its downloadable manual is
f3 with 77 patches. A separate website update is prepared against deployed commit
`d36663e4311427a5914fd9d3efb932d32b4d7610`; neither website checkout nor the
live page has been changed. The candidate folder includes the seven-file
support-site patch and an exact-candidate host acceptance worksheet.

The fresh provenance audit covers all 93 source/U45 patch states against the
hash-pinned 128-state reference corpus. It finds zero exact or quantized
matches across 24 tone fields, with at least 10 fields differing in every
quantized comparison. This is an exact-state comparison, not an ownership
or perceptual-similarity conclusion. The material's source, generation mode,
and prompt are pinned to resolvable upstream history. The manual includes
the generated-material notice and remains six pages; pages 1-5 are pixel-
identical to the earlier reviewed f14 manual, and revised page 6 passes visual
review. These documentation changes leave the U45 and all runtime assets
unchanged.

## Retained 1.0.0f13 candidate

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

### Changes and compatibility

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

### Current checks

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

### Retained evidence

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

### Release artifacts and acceptance

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
