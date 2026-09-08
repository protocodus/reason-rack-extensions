# YouKnow asset and SDK provenance inventory

Updated 2026-09-05 CEST for the YouKnow `1.0.0f11` production candidate. This
is an engineering traceability record, not a legal conclusion, ownership
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

The prior SDK-tree engineering history at commit `5782a5a` records a generated
visual-direction reference in the device's former Design/References directory,
identified by SHA-256
`c28fc9315c2f735a04e05abcb2692a4f67efa974214bedfac50dd91195c94512`.
Its adjacent prompt calls an unnamed “current panel” Image 1 the layout input
and asks to retain the same sections and approximate geometry while avoiding
exact Roland/Juno trade dress.

Neither file is shipped in the clean source or U45. The provider/model/date,
applicable generation terms, and the exact origin and permission record for
the unnamed input image are not present in the release source. Those missing
facts and the combined final panel remain within the open owner/legal
trade-dress and shipped-content review; this history is not treated as approval.

## Patch bank provenance

The production bank contains 93 Protocodus patches, including Init:

- Init and 18 featured sounds entered the Rack source in commit `5782a5a`,
  before the historical factory-bank importer was introduced. Their established
  musical parameters remain unchanged; Init's chorus-noise default and the
  subsequent panel-less preset level trims are separately maintained. The
  featured plucked-keys patch later received its current descriptive name.
  The initial Rack catalog identifies ten featured patches as original Rack
  designs. The other eight follow the VST's original sound-design recipes:
  Glass Pad, Bass Short and Hard, Hollow Fifths, Vibrato Lead, Slow Sweep,
  Organ, Percussive Comb, and Self-Oscillating Sine. Those recipes are recorded
  in the VST device's `Presets/README.md` at upstream commit
  `732bbf116145b5497e958e94901f7be6c4d4f840` and explicitly distinguished there
  from its historical program bank.
- The 28 categorized patches are explicit parameter overrides authored in
  `Design/generate_presets.py` at commit `3d9b284`.
- The 30 universal expansion patches are explicit parameter overrides added
  in commit `662809a`. That commit also removed all 128 historical A/B factory
  patches, their source tone corpus, and the importer.

The 2026-09-05 audit compared all 93 current patch states with the 128 deleted
factory states from commit `3d9b284`. None matched across the 16 continuous
tone parameters and eight waveform, range, filter, envelope, VCA, and chorus
switches. The deleted tone corpus has SHA-256
`394ae874da33aa63fa4833932fbf415546d2ad66b1b6b9a36315601799eeec21`,
which also identifies the factory corpus still present in the nominated VST
checkout. That corpus and its archival labels are excluded from this Rack
release. The comparison establishes absence of exact tone-state copies;
source history supplies the separate authorship record.

The generator and patch validator require the exact reviewed 77-path catalog,
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
  trees. The chassis is a brushed-grain plate with an edge falloff; sections are
  shallow recesses titled with a stage-coloured rule. Control positions are
  derived from each control's own caption, tick ladder and scale legend, and
  `Design/sync_panel_lua.py` stamps the resulting coordinates and cap-art paths
  into `GUI2D/device_2D.lua` and `GUI/Output/gui.lua`.
- The single `Fader` strip that preceded the four stage-coloured strips is no
  longer generated or shipped.
- The `1.0.0f11` rear CV grid and automation indications are implemented in the
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
