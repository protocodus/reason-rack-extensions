# YouKnow 1.0.0f9 release evidence

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
