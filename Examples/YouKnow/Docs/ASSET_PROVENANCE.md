# YouKnow asset and SDK provenance inventory

Current candidate: YouKnow `1.0.0f17`, with local artifact validation passed;
host and Reason Studios acceptance remain pending.
The dated `1.0.0f14` audits and hashes below retain their historical scope.
This is an engineering traceability record, not a legal conclusion, ownership
opinion, or grant of rights. Commercial permission and distribution scope stay
subject to the open owner/legal and Reason Studios release gates.

## SDK authority

- Active SDK: `JukeboxSDK_500_028`, `TargetVersion=5.0`.
- SDK `version.txt` SHA-256:
  `81f10bc015321c5e4f7a9e8297426cebf92ced49de1dd1dd1be9d65a726011c4`.
- Bundled `Licenses/RE SDK License Agreement.txt` SHA-256:
  `f7e7dc4d40e83965eb6417a60ddb93e0c68c994a4842c50397ea8ee6e17e308c`.
- SDK-relative paths below resolve from that exact SDK root. The SDK and stock
  material are not relicensed under YouKnow's MIT license.

The full SDK agreement is retained in the SDK root, not copied into this clean
source. Whether and how it must accompany source, manual, support-site, or
other non-U45 copies remains an owner/Reason Studios distribution-scope gate.

## Direct SDK bitmap inputs

The panel renderer decodes the following SimpleInstrument PNGs, converts them
to RGBA, and writes optimized PNGs. Renderer validation requires pixel identity
with the SDK input even when PNG encoding makes the file hashes differ.

| SDK-relative input | Input SHA-256 | YouKnow output | Output SHA-256 |
|---|---|---|---|
| `Examples/SimpleInstrument/GUI2D/Reason_GUI_front_root_Wheel_Pitch.png` | `47a639cd3aa9b18e4785d9e286848f9cb97f1eaf33b9f8240e505a78e7ecaa89` | `GUI2D/PitchWheel.png` and byte-identical `GUI/Output/HD/PitchWheel.png` | `081a08caa4c7eea5a96cc97c89888a5fc05c5f718247a409e180ff00737721f1` |
| `Examples/SimpleInstrument/GUI2D/Reason_GUI_front_root_Wheel_Mod.png` | `50276aafd57dc4f8ed9c5d286dcc0140c5104e2ac5c9afdfa148c02ba7ec93be` | `GUI2D/ModWheel.png` and byte-identical `GUI/Output/HD/ModWheel.png` | `4d4adf394cdba8ddc8906880e283c53007374df47035e8acde3b160e47a965e1` |
| `Examples/SimpleInstrument/GUI2D/SharedAudioJack.png` | `bc024967ac459c65d3c45a8507999fe1f2d142d44290ae46686e81c4039c109b` | `GUI2D/AudioJack.png` | `ac755c83c26ad196f35ad1292eac7e73e9cffad475390d3bb9ee966a5531d153` |
| `Examples/SimpleInstrument/GUI2D/SharedCVJack.png` | `d93351267357109b8a329d9884968e7c785d8c09854e4cb06498a8d9d5f84bd4` | `GUI2D/CVJack.png` | `94b01bc1cd99d6db26965f25fa969e4418de754a31d2e2c3f369ee1db52ffd98` |
| `Examples/SimpleInstrument/GUI2D/TapeHorz.png` | `89cdc510e463e50817ea75d93548cdc5bc29aca7cdb8358a285e1f7a1ba32b79` | `GUI2D/TapeHorz.png` | `6144f34a6e755385b9d2e9a41653eb8338a07f4acf23cdf9267794638f98a71c` |
| `Examples/SimpleInstrument/GUI2D/TapeVert.png` | `f5ea7edbd8bc79a09cf3f332acc5381517d05a6daf2397788dcca60e130ea045` | `GUI2D/TapeVert.png` | `792b9c5d430fbf4a506baab984dfa4df5cc4025066cc1cfd621d536059d16cd1` |
| `Examples/SimpleInstrument/GUI2D/Placeholder.png` | `ba22d3cfe50bb2e81d8c301a22243f8b8909391893f9e8428b0c610aef57c4d7` | `GUI2D/Placeholder.png` | `33cfd34d870bf0fd8967c7f98017446e844422b55babd60dd7fabee4fc087262` |

Two additional files are retained byte-for-byte from the same SDK example and
are consumed directly by `GUI2D/device_2D.lua`:

| SDK-relative input | YouKnow file | Shared SHA-256 |
|---|---|---|
| `Examples/SimpleInstrument/GUI2D/PatchBrowseGroup.png` | `GUI2D/PatchBrowseGroup.png` | `ad8fa95719e64ed438249528004ae267b45aad024c73f924ad0efe288b2d738b` |
| `Examples/SimpleInstrument/GUI2D/204x10_5x5.png` | `GUI2D/PatchName.png` | `576ec378c1ace3cd5b8e0a8ab8249f03d1ae4b20dd6c5cff6d5ed4ffdcca76d1` |

The patch-name bitmap now supplies only the folded front. The full front uses
a pathless 204-by-16 logical-pixel surface, following the SDK SimplePlayer
example. Reason supplies its native Arial medium patch and status text; the
folded patch field retains the native Bold LCD style.

## Adapted SDK sample scaffolding

The following YouKnow files are adapted, non-byte-identical descendants of the
corresponding `Examples/SimpleInstrument` sample or its SDK-facing structure.
This list distinguishes SDK-derived scaffolding from Protocodus DSP and panel
design; it does not characterize the legal scope of either category.

| YouKnow file | SDK sample baseline | Baseline SHA-256 |
|---|---|---|
| `build45.py` | `Examples/SimpleInstrument/build45.py` | `23cb7cea415b43d768ba2a1d2e2db47409a1adf67fa6dd20e79323c281888919` |
| `JukeboxExports.cpp` | `Examples/SimpleInstrument/JukeboxExports.cpp` | `92414283c5a780651a1e068d754ca55f69de51a21a1b240f76a8971aaed51449` |
| `info.lua` | `Examples/SimpleInstrument/info.lua` | `0af2f8ce3399f00653b30b6d084bb48a3427cf616fd2c5b119ae2c026a613128` |
| `motherboard_def.lua` | `Examples/SimpleInstrument/motherboard_def.lua` | `0e0461ddde087d6381ca99c84598cfdfa1031a65c5b65e4c98aa511baa296559` |
| `realtime_controller.lua` | `Examples/SimpleInstrument/realtime_controller.lua` | `2a52390a469e0a27f1b97ca7beab7003864669fa9d1d6e0bee4b19ba7c6371e2` |
| `GUI2D/device_2D.lua` | `Examples/SimpleInstrument/GUI2D/device_2D.lua` | `6f852270d29a135e48068c653b3b699cce4cec523297cbefcff350e244383cfb` |
| `GUI2D/hdgui_2D.lua` | `Examples/SimpleInstrument/GUI2D/hdgui_2D.lua` | `0c9bc830a656a6f725309ec51e87284057ae368d00b6caf0a0aa0eaff6aba6c3` |
| `GUI/Output/gui.lua` | `Examples/SimpleInstrument/GUI/Output/gui.lua` | `e6a1c189e4a9bd193e45ee68a9f95cfd8111d174cc03dfebd006adf1d3be2681` |

`Resources/English/texts.lua`, `YouKnow.rsmeta`, and the `.repatch` files use
SDK-defined data formats but contain YouKnow-specific text, metadata, and patch
states. SDK headers and build modules are referenced from the verified SDK root
and are not copied into the clean release source.

## Historical visual-reference lineage

The provenance record imported into `protocodus/reason-rack-extensions` at
`7995caaed859d8f8260e0f47e775331078e07b9d`, in
`Examples/YouKnow/Docs/ASSET_PROVENANCE.md`, reports a former SDK-tree commit
`5782a5a` containing a generated visual-direction reference in the device's
former Design/References directory, identified by SHA-256
`c28fc9315c2f735a04e05abcb2692a4f67efa974214bedfac50dd91195c94512`.
That imported record describes an adjacent prompt using an unnamed “current
panel” Image 1 as the layout input while avoiding exact Roland/Juno trade dress.
The earlier SDK-tree commit does not resolve in the current Rack repository;
the imported description is the available historical record, not a fresh
verification of the former image or prompt.

Neither file is shipped in the clean source or U45. The provider/model/date,
applicable generation terms, and the exact origin and permission record for
the unnamed input image are not present in the release source. Those missing
facts and the combined final panel remain within the open owner/legal
trade-dress and shipped-content review; this history is not treated as approval.

## Patch bank provenance

The production bank contains 100 Protocodus patches, including Init. These
source records resolve in the identified repositories:

- In `protocodus/reason-rack-extensions`, the source import
  `7995caaed859d8f8260e0f47e775331078e07b9d` contains
  `Examples/YouKnow/Design/generate_presets.py`: its 19-path featured catalog
  comprises Init and 18 sounds; its `PRESETS` and `UNIVERSAL_PRESETS` contain
  28 and 30 explicit parameter recipes. Commit
  `9068e27c5801e6f4850a06ff4cee240b4d98503c` then tracks the 77 patch files in
  `Examples/YouKnow/Resources/Public`. The audit report retains their paths,
  Git blob identifiers, and SHA-256 hashes.
- The imported provenance record identifies ten featured sounds as original
  Rack designs and eight as adaptations of original VST sound-design recipes:
  Glass Pad, Bass Short and Hard, Hollow Fifths, Vibrato Lead, Slow Sweep,
  Organ, Percussive Comb, and Self-Oscillating Sine. The recipe document resolves
  in **`voho/vst-instruments`**, at commit
  `732bbf116145b5497e958e94901f7be6c4d4f840`, path
  `youknow106/Presets/README.md` (SHA-256
  `42b7d45908a733d5db217da2af00487d01891036a43aefb8b7e39cf369d753e4`).
  It distinguishes these original recipes from the historical program bank.
  This commit belongs to the earlier monorepo, not the standalone upstream.
- The 16 numbered additions resolve in Rack commit
  `a45fef7e81ae3433205b8de8f8d02e00ed165065`, in `CLASSIC_PRESETS` and
  `STRING_PRESETS` in `Examples/YouKnow/Design/generate_presets.py`.

Seven new f17 recipes are independently authored in the current generator,
with no imported patch data. Their descriptions and playing suggestions are
in [PRESETS.md](../PRESETS.md). The earlier 93 sound states and level trims
are retained; only the new patches receive new calibration measurements.
The following historical comparison remains scoped to its recorded 93 patches.

The imported record also cites earlier SDK-tree commits `5782a5a`, `3d9b284`,
and `662809a` for the initial port, categorized expansion, and universal
expansion/factory-bank removal. These short identifiers do not resolve in the
current Rack repository. They are retained as reported pre-import history;
the full commits above identify the source and bank that can be verified now.

The historical **2026-09-05 audit covered 77 patches** and reported no exact
matches against 128 removed factory states across 16 continuous parameters and
eight switches. The retained f14 audit below extended the comparison to its 93
shipped patches; it does not retroactively change that historical scope.

The **2026-09-08 audit of `1.0.0f14`** reads the 128-state reference corpus from
`protocodus/virtual-instrument-youknow` commit
`72e1d4482324465993c8e62609fa345e848d3b70`, path
`Source/DSP/YouKnowPresets.cpp`, and pins the switch mapping to that commit's
`Source/DSP/YouKnowSysEx.cpp` and `.h`. The 2,304 decoded bytes have SHA-256
`394ae874da33aa63fa4833932fbf415546d2ad66b1b6b9a36315601799eeec21`.
This comparison corpus remains external to the Rack source and U45.

- All 93 source patch files are byte-identical to their `Public/` members in
  the 143-member U45, SHA-256
  `e93bb2a07bed3b6571ca9272dbcc3355f86df4ee801550961fc7062bd891676a`.
- No patch matches any reference state across the 16 continuous tone controls
  and eight waveform/range/filter/envelope/VCA/chorus switches, either using
  exact normalized values or rounding continuous values to the nearest 7-bit
  step. Chorus I+II remains a distinct switch value. Every comparison differs
  in at least 10 of these 24 fields after quantization.
- Performance settings, extension controls, and level trims outside those
  24 tone fields are excluded from the comparison. The result establishes
  absence of exact tone-state copies under these two representations; it is
  not a perceptual-similarity or ownership conclusion.

The retained f14 audit can be reproduced against its recorded source and archive
from the YouKnow directory with
`python3 Release/validation/production-audit/audit_provenance.py`. The ignored
validation directory retains the script, `patch-material-provenance.json`,
and pinned authored recipe/material-notice extracts. The script accepts local
clone paths through `--upstream` and `--monorepo`, records immutable source
identifiers and hashes, checks the U45 against all 93 source files, and does
not write the factory corpus into the report.

The generator and patch validator require the exact authored 100-path catalog,
rejecting additional or renamed files even if the total patch count stays the
same. Revalidating these source records does not confer rights to unrelated
third-party banks or replace the remaining release approvals.

## Font inputs

Panel labels are rasterized during development from these local macOS 26.5.1
font files. The font binaries are not packaged; rendered glyph pixels are
present in panels and their downstream assets.

| Development input | SHA-256 | Renderer role |
|---|---|---|
| `/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf` | `36958182a424e1e8a1307b2636a615a6323ce1bbfadda136735ab4fb3bd26ceb` | YouKnow wordmark, section titles, Protocodus branding |
| `/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf` | `78e816b9938fc40dd5383f4a91b598494798e2fa1d526abbd9e7ff7e5b9bf0ee` | Control captions, scales, rear legends, and native-text preview approximations |

DIN is the industrial lettering standard instrument panels are silkscreened in,
so both faces of the device are set in one family. Arial and Arial Bold were
the previous label and title faces and are no longer a renderer input.

The exact OS/font hashes make the renderer input reproducible. They do not by
themselves establish commercial permission; that remains within the shipped-
content ownership blocker in `Docs/RELEASE_CHECKLIST.md`.

### Separate support site

The support-site repository uses Space Grotesk under the SIL Open Font License
1.1, retained there as `assets/fonts/OFL-Space-Grotesk.txt`. Those self-hosted
font files are separate from the U45 and this release's panel inputs. Their
recorded licensing and deployment evidence belongs to the support-site history.

## Project-created and generated bitmap lineage

- `Design/render_panels.py` code-renders four signal-stage `Fader` cap strips
  (`FaderSource`, `FaderShape`, `FaderEffect`, `FaderPlay`), `Knob`, `Toggle`,
  `MomentaryOverlay`, `Lamp`, and `EngineDisplay`, then assembles front, rear,
  folded, navigator, palette, icon, and track-list images in both consumed GUI
  trees. The rear chassis uses seeded, non-directional grain at several scales.
  The front uses the original YouKnow ABS material below, with a warm charcoal
  surround, darker textured recesses, and subdued edge highlights, following
  the supplied plastic references. Front sections carry a stage-coloured rule;
  rear rules share one neutral ink. Decorative screws are omitted on all
  faces, and the blue maker mark is printed directly on the plastic. Maker and
  instrument names share a header centerline; a subtle separate readout strip
  starts at the first control caption. Tiny icons use a blue and yellow two-bar
  mark. The front controls leave more space below their labels, with tighter
  group-title insets. Rear settings sit above the sockets to keep downward
  cable runs clear. Control positions are derived from each control's caption,
  tick ladder and scale legend. `Design/sync_panel_lua.py` stamps those
  coordinates and cap-art paths
  into `GUI2D/device_2D.lua` and `GUI/Output/gui.lua`.
- `Design/Assets/used-charcoal-plastic.png` is copied byte-for-byte from
  `protocodus/virtual-instrument-youknow` commit
  `72e1d4482324465993c8e62609fa345e848d3b70`, path
  `Assets/used-charcoal-plastic.png`, also verified against the nominated local
  checkout at `/Users/vojta/Dev/virtual-instrument-youknow`.
  SHA-256: `cfcdd00f5d885eff061ebee8e3b120dd619a704849e128999bf08ac5feb6b920`.
  At the same commit, `THIRD_PARTY_NOTICES.md` (SHA-256
  `17d3aba48f0abbaa53b8f2f2a29e5015dd979b56bf1a92ace30c1959e4246549`),
  under “Generated UI assets / Faceplate material tile,” records the full
  prompt and generation mode: OpenAI built-in image generation, new image
  rather than an edit. It describes a 1024-by-1024 material with fine mould
  pores, soft satin wear, and sparse hairline scuffs on maintained charcoal ABS.
  The notice does not give a generation date for this material; repository
  dates are not substituted for one. The production audit retains the exact
  notice section as `upstream-faceplate-material-notice.md` and verifies the
  image dimensions and byte identity.
  The Rack renderer fits one continuous, aspect-preserved piece across the
  front, softly filters it, and composites it at low contrast. The loose input
  is a build asset; only the resulting panel/browser images ship in the U45.
- The single `Fader` strip that preceded the four stage-coloured strips is no
  longer generated or shipped.
- The `1.0.0f14` rear CV grid and automation indications are implemented in the
  project renderer and GUI Lua sources. All eight CV sockets reuse the listed
  SDK CV jack input; this change introduces no new external artwork or fonts.
  CV behavior and control metadata are defined in the Rack adapter and
  `motherboard_def.lua`.
- `Docs/build_release_materials.py` derives `Release/shop/*.png` and the PDF
  manual from the assembled panels and maintained Markdown notices. `Release/`
  is ignored build output; final artifact hashes belong in
  `Docs/RELEASE_EVIDENCE.md` and the versioned handoff manifest.
- Pillow `11.0.0` and ReportLab `5.0.1` are pinned build-only dependencies in
  `Docs/build_release_materials.py`; their code is not embedded in the U45.

Any change to an input hash, renderer, font, SDK version, or panel composition
requires regeneration and a fresh release-evidence/handoff hash set. This
inventory must be updated before those new hashes are treated as final.
