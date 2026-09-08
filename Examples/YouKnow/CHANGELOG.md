# Changelog

Notable customer-facing changes to YouKnow are recorded here.

## 1.0.0f15 - Unreleased

- Balance the stacked PROTOCODUS/YOUKNOW logo with equal visible padding
  above and below the nameplate on both full panels.
- Extend the quality-strip separator to both panel edges, preserving the
  control-aligned readout inset.

## 1.0.0f14 - Earlier candidate

- Start simultaneous Note/Gate CV updates at the new pitch regardless of
  same-frame socket notification order, while preserving gate retriggers.
- Retry voice allocation when a held CV note was dropped by a full voice pool
  and its pitch changes after a slot becomes available.
- Preserve the first audio samples when a deferred voice-assignment scan
  activates held notes inside a processing interval.
- Restore the current Character value immediately on audio reset, including
  resets during an automated calibration glide.
- Repair the PDF/Shop-image builder to load the current colored fader assets,
  derive the manual's patch count from the shipped bank, and match the guide's
  labels to the current panel.
- Keep all 93 patch sound values and permanent control identities unchanged.

## 1.0.0f13 - Earlier candidate

- Added clearance below control labels in the first two front rows and moved
  the Bend and Mod wheels down six pixels.
- Moved front group titles closer to their left edges and removed decorative
  screws from the front, rear, and both folded panels.
- Centered the maker and instrument names on a shared header axis, with the
  blue maker lettering printed directly on the plastic.
- Gave QUALITY and the readouts a subtle separate strip aligned with the
  first control caption, and simplified tiny icons to blue and yellow bars.
- Relabelled the lowest HPF position as 0, retaining its existing bass-boost
  behavior.
- Updated the candidate version; DSP, control behavior, and all patch sound
  values remain unchanged.

## 1.0.0f12 - Earlier candidate

- Synced DSP from the original YouKnow project at `72e1d448`, including the
  updated VCA, SUB, filter calibration, PWM, and chorus models. Preserved Rack
  real-time safeguards, quality controls, and fixed latency.
- Reduced six preset level trims by 0.234–1.139 dB for the updated signal path;
  all 93 patches retain their musical settings.
- Refined the front with warm charcoal ABS, fine matte grain, faint wear,
  darker textured control recesses, and softer edge highlights.
- Increased the branding and QUALITY left inset to clear Reason's collapse
  triangle, with matching branding clearance on front, rear, and folded views.
- Unified rear section rules in neutral gray and placed settings above the
  CV and stereo output sockets so downward cables leave the controls clear.
- Assigned a distinct build version across metadata, patches, and rear artwork.

## 1.0.0f11 - Earlier candidate

Fixes the cloud `render_gui` failure in `1.0.0f10`. The folded front panel's
Note lamp had been moved to the full front panel's coordinates, `(724, 51)`,
which is off the bottom of a panel one rack unit tall. `Design/sync_panel_lua.py`
confined its offset-form rewrites to the front panel but not its helper-call
rewrites, and `S_note_on` is declared by both panels. `check_layout()` could not
see it: it read positions from the whole file, so the folded copy overwrote the
front one and the two identical wrong values matched.

`check_panel_bounds()` now asserts every widget in every panel fits the panel
that declares it, which fails this exact case locally instead of in the cloud.

Version bumped from `1.0.0f9`: that build exists as an installed Rack
Extension, and a product id may carry a given version only once, so the
panel, bank and automation work below could not keep sharing its number.
An installed `1.0.0f9` also shadows a development build declaring the same
version, which is why the reworked panel did not appear in Reason.

- Added rear Cutoff, Resonance, Volume, Amp, Sub, and Noise CV inputs beside
  Note and Gate, arranged in a labelled two-row grid. Cutoff and Resonance add
  to the panel values; the four level inputs scale their panel settings.
- Extended sequencer automation to Chorus Hiss, Unit Character, Aging, and
  all four quality controls. The original 34 automation IDs remain unchanged;
  seven appended IDs bring the total to 41, with rear automation indications.
- Preserved the quiet-tail transition for automated Quality changes and the
  patch/song persistence of Character, Aging, and processing quality.
- Simplified the build documentation and updated the user guide and Shop copy
  for the current controls. Removed unused historical artwork inputs.
- Verified that the nominated upstream checkout and current remote contain no
  newer shared DSP changes; the existing engine remains unchanged. The upstream
  checkout is now its own repository rather than a directory in the monorepo.
- Rebuilt the front and rear panels as a brushed-metal chassis with shallow
  machined section recesses, replacing the flat card groups. Every legend is
  now set in DIN, the lettering standard used on instrument panels, and is
  letterspaced; control captions grew from 10.5 to 12.5 pixels and scale
  legends from 9 to 10.5.
- Colour-coded the panel by signal stage. Fader caps and section rules share
  four accents -- tone sources, shaping, effects, and performance -- so a cap
  colour says which stage a control belongs to. The single grey cap strip is
  replaced by four.
- Derived control positions from each control's own caption, tick ladder and
  scale legend instead of hand-set coordinates, then shared each row's spare
  width between its sections. The filter row was over-subscribed by 93 pixels
  and is now positive throughout, with a guaranteed 17-pixel clearance between
  neighbouring controls.
- Renamed sections to the terms a hardware panel is silkscreened with -- DCO,
  VCF, VCA, ENV, HPF -- and moved Chorus to the end of the shaping row where it
  sits in the signal. Master Volume moved out of the bender group into
  Performance. The Key Mode caption is now MODE, and the two adjacent PWM
  captions read PWM and SOURCE.
- Aligned the Note lamp caption to the engine readout baseline it had been
  sitting four pixels above, and enlarged the readout captions to 10 pixels.
- Reworked the header. The six engine readouts used to stack a caption over
  its value in the sliver between the patch window and the bottom of the
  header, six abreast; each caption now sits beside its own value on one line
  spread across the panel's full width, with the Note lamp at its end. The
  maker mark and wordmark are placed identically on the front and the rear, so
  a flipped rack shows the same nameplate in the same spot.
- Dropped the group boxes from the rear and titled its areas with a rule
  instead: the rear is a wiring diagram, and boxing sockets only fences them
  off. The rear nameplate now carries the version number below the wordmark.
- Glided Unit Character over 30 ms when a host automates it. It is the one
  parameter whose change rebuilds every voice card's analogue trims at once,
  and jumped across its full travel under a sounding note that rebuild was
  audible as a ~15 dB burst through the chorus. Patch loads and resets still
  adopt the new unit outright, so no stored sound is altered, and the glide
  costs about 27 us per batch only while the control is moving.
- Added an automation artifact contract covering all 40 host-automatable
  parameters as single jumps and as fast sweeps, dry and chorused, plus a
  held-note survival check across every switch. Nothing else in the panel
  injects a discontinuity beyond what the voice already produces standing
  still; the worst continuous control measures 1.01x.
- Added six more numbered string patches -- the brass-and-strings layer, a
  16'-plus-sub octave section, delayed vibrato, a marcato bowed attack, a full
  I+II chorus wash and filter tremolo -- taking the public bank to 93.
- Added ten patches in the numbered-bank idiom (8411 Brass through 8474 Sweep),
  filed across the existing categories and level-calibrated with the rest of
  the bank; the public bank is now 87 patches.

## 1.0.0f8 - Superseded before publication

- Kept front captions at a uniform 10.5 pixels, with at least 16 pixels between
  independent labels and the existing 10-pixel group padding and gutters.
- Separated Key Mode from Shift and widened the status strip spacing; shortened
  Velocity to VEL while retaining the full TRACK label.
- DSP, patch states, control behavior, and the 50% Aging default are unchanged.

## 1.0.0f7 - Superseded before publication

- Simplified panel groups to quiet flat backgrounds, removing outlined borders,
  header dividers, accent tabs, and redundant captions.
- Replaced generic 0/5/10 fader numerals with sparse ticks; kept meaningful
  units, bipolar values, selector labels, 10-pixel spacing, and large branding.
- Carries forward the `1.0.0f6` sound, Aging default, patch trims, and controls.

## 1.0.0f6 - Superseded before publication

- Gave control groups at least 10 logical pixels of internal padding and
  10-pixel gutters, with shorter filter and envelope labels and aligned widgets.
- Removed the printed product descriptor from the front and rear panels and
  removed the rear support URL for a cleaner layout.
- New devices start with Aging at 50%; 0% remains the freshly serviced state,
  and existing songs retain their stored value.
- Reduced Circuit Rain's stored preset level by 1.56 dB to keep its peaks
  within the bank's target at the new Aging default.
- Carries forward the `1.0.0f5` readability improvements and full DSP update,
  with the original patch bank, control ranges, Remote, and automation intact.

## 1.0.0f5 - Superseded before publication

- Enlarged the Protocodus branding on full and folded panels and switched
  operational labels and section titles to clear Arial faces.
- Rebalanced the front control groups, enlarged the native patch and status
  text, and simplified the panel surfaces to a clean matte finish.
- Aligned the rear processing-quality and unit-model controls in wider bays,
  with clearer labels and patch/song persistence captions.
- Carries forward the complete `1.0.0f4` DSP update, original patch bank,
  calibrated levels, and existing Remote and automation mappings.

## 1.0.0f4 - Superseded before publication

- Synchronized the full engine and chorus with the nominated YouKnow source,
  including voice VCA saturation/control response, resonance and scanned-control
  behavior, HPF switching memory, chorus gain/mute/noise, and service drift.
- Removed the former model suffix from C++ names, filenames, tests, and docs;
  the permanent `cz.protocodus.YouKnow` song/patch identity is unchanged.
- Refined the front/rear panels and kept all processing-quality and unit-model
  controls on the rear, with existing Remote and automation contracts preserved.
- Rechecked the original patch bank and regenerated release metadata and assets.
- Fixed the LFO-delay readout and extended combined Reason/panel tuning through
  its full +/-150-cent range while preserving the original panel tuning grid.

## 1.0.0f3 - Superseded before publication

- Ported the latest loaded MN3009 chorus output network: both finite-source BBD
  outputs, the shared tap capacitor, and the first reconstruction section now
  advance as one coupled six-state system. The wet path is about 0.87 dB darker
  at 10 kHz, with its measured hiss normalization and patch trims refreshed.
- Carries forward the complete `1.0.0f2` release-candidate feature set below.

## 1.0.0f2 - Superseded before publication

- Added 30 independently authored universal sounds focused on bass, brass,
  strings, and pads, bringing the original Protocodus bank to 77
  level-calibrated patches.
- Added permanent Reason automation-only IDs for all 34 musical front-panel
  controls. Preset Level, Unit Character, Aging, Chorus Hiss, and rear engine
  policies remain intentionally outside sequencer automation.
- Tightened front-panel legends, stacked Pulse/Saw vertically, moved Chorus
  Hiss into the Chorus bay, and retained the dedicated I+II chorus mode.
- Grouped Glide and Key Mode with the Keyboard controls, then widened the dense
  Performance bay and tightened Keyboard spacing while preserving all
  automation lanes and Remote mappings.
- Moved the patch-persistent 0-200% Unit Character control beside Engine Quality
  on the rear and exposed a distinct rear-only Aging control. Aging is
  song-persistent, ranges from 0-100%, defaults to 0% (freshly serviced), and is
  Remote-mappable but intentionally outside sequencer automation alongside
  Character.
- Vertically aligned the Protocodus/YouKnow lockup with the synth descriptor,
  removed the full-width front-header rule, strengthened the section accent
  rules, switched section titles to the regular panel face, centered visible
  legend ink, normalized panel gutters, and refined the corner-screw shading.
- Added a documented, project-generated low-gloss molded-plastic texture with
  restrained surface scratches across the chassis and complete control islands,
  plus lightly worn bevel edges.
- Moved product support to `protocodus.cz/product/youknow` and printed that
  product-specific address on the rear panel.
- Carries forward the complete `1.0.0f1` DSP synchronization and Rack-specific
  safety, latency, CV, reset, and performance behavior.

## 1.0.0f1 - Superseded before publication

- Prepared the first production release candidate for Reason 14 and later.
- Synchronized Protocodus DSP through upstream `ff1aa2f4`, including corrected
  PIT and B-2 control timing, Pulse-Off coupling, noise-OTA memory, TA75558
  slew/bandwidth/noise behavior, and refreshed oscillator correction tables,
  while preserving the Rack-specific C++17, wrapper, fixed-latency, CV, reset,
  and real-time-safety adaptations.
- Added the source instrument's dedicated narrow Chorus I+II mode as appended
  selector ordinal 3, preserving existing Off/I/II song values.
- Ships 47 original Protocodus patches with independently calibrated browsing
  levels; no third-party factory tone-memory records or archival labels are
  included.
- Removed the unpublished beta's A/B patches, metadata, and retained factory
  tone corpus from the production source tree; renamed or selected copies are
  not used as a substitute for redistribution permission.
- Carried forward the circuit-modelled response, CPU-efficient defaults,
  calibrated browsing levels, polished 8RU interface, and SDK 5 integration
  developed during the unpublished beta cycle.

## 0.1.0b18 - Superseded before publication

- Synchronized the latest Protocodus engine from 2026-08-28, making the
  circuit-derived resonance response the shipped default while retaining the
  previous voiced curve internally for comparison.
- Refined the MN3009 chorus-line saturation curve against its typical
  distortion data and changed Init, factory-bank, and inherited Chorus Noise
  defaults to the inferred typical-S/N level. Previously saved songs and
  authored patches with explicit hiss settings retain their stored value.
- Recalibrated the hidden per-patch output trims for the new response without
  altering historical tone bytes or visible Volume controls.
- Hardened release generation against mixed-version guide and Shop copy, and
  made non-stress native performance probes fail on deadline misses.

## 0.1.0b17 - Superseded before publication

- Prepared the first public beta candidate for Reason 14 and later.
- Ported the latest CPU-efficient Protocodus engine defaults: 1x quality, Poly
  VCF saturation, Cubic early interpolation, and the Normal VCF solver.
- Added inactive-voice freewheel and settled Chorus-Off bypass for much lower
  idle and playing CPU use while retaining Exact, Fast, 2x, 4x, High, and Max
  choices on the rear panel.
- Fixed a state-reassertion edge case that could accept notes but remain silent
  after changing patches.
- Added a polished 8RU front, folded views, browser imagery, and a rear Engine
  Quality bay with readable Reason-native controls.
- Added Note/Gate CV, stereo outputs, patch browsing, performance automation,
  master tuning, audio reset, and fixed 41-sample latency behavior.
- Added 28 categorized sounds to the original featured bank: four each in
  Bass, Leads, Keys, Brass, Pads, Strings, and Effects, bringing the
  Protocodus-original bank to 47 patches.
- Added the 128-program historical factory tone bank in top-level `A` and `B`
  folders, with slot-prefixed names such as `A11 - Brass Set 1`,
  exact tone-memory round-trip validation, and searchable Reason metadata.
- Added deterministic, smoothed per-patch output calibration so preset browsing
  stays level while factory tone bytes and the front-panel Volume remain intact.
- Prevented a quiet patch's high makeup trim from carrying into a louder patch
  when Reason changes presets without an audio reset; attenuation now applies
  immediately while safe upward makeup changes retain their short smoothing.
- Added deterministic metadata/category validation and an all-patch minimum
  level gate for the categorized bank.
- Standardized every consumer-facing product surface on the YouKnow name.

Replace `Unreleased` with the publication date only after the exact Universal
45 has passed Reason Studios acceptance and its release commit has been tagged.
