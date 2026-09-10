# DSP synchronization

Upstream now lives in its own repository. YouKnow left the `vst-instruments`
monorepo in `3a5d0e399a973f974d73638912555980ccb3038f` ("Move Electry, Taikor
and YouKnow into their own repositories", 2026-09-06) and arrived at
`8ab52dc2473261d0227fa4742c28c2fda9249ea4` ("Import YouKnow from the
vst-instruments monorepo") in
`git@github.com:protocodus/virtual-instrument-youknow.git`. **The nominated
checkout is `/Users/vojta/Dev/virtual-instrument-youknow/Source/DSP`**; the
former monorepo path in earlier revisions of this file no longer exists.

Synchronized on 2026-09-10 from freshly fetched production `origin/main` at
`c9d3c571c6d8586fbb19c8e821e66f68607dfdff` ("Merge pull request #4 from
protocodus/claude/juno-plugin-realism-cxycuk"). The shared DSP's latest change
is `a163cd8` ("Sample the jack-board temperature on the converter pass, not the
callback"). Source was read from a `git archive` of that exact revision. The
nominated checkout remains on its existing `codex/fix-builds-distribution`
branch; its unrelated untracked `Assets/store` files were left untouched.

This is an intentional sound-model and bug-fix update from the previous
`013b25702145b72d67965665c701f59e105c52b7` synchronization. Only
`YouKnowEngine.h`, `YouKnowEngine.cpp`, and `YouKnowChorus.cpp` changed upstream:

- The main noise source now draws bounded Gaussian avalanche noise at the
  previous RMS coordinate, preventing quality-dependent amplitude statistics.
- VCF LFO and bend follow the recovered integer control words, including their
  low-depth truncation and bend centre dead zone. LFO delay follows running
  voices, including sustain, instead of only physical key presses. Envelope
  attack hands over on the pass that exceeds the peak.
- The jack output includes its host-rate R64/R65-C22/C21 pole. Common VCA gain
  follows jack-board temperature, sampled on converter passes so output does
  not depend on callback partitioning.
- Correction steps at an interval's left boundary retain the prior sample's
  side of the event. Reported pulse duty follows each card's actual comparator
  threshold. Quality fades reach exact zero at their scheduled sample; the
  latency calculation now matches the measured decimator delay. The declared
  41-sample latency and existing 1x/2x pads remain unchanged.
- Unknown/nonpositive sample rates use 48 kHz. Chorus wet mute reaches exact
  zero without relying on host flush-to-zero behavior; corrected circuit
  provenance remains in the source comments.

No properties, stored ordinals, parameter fields, tables, or Rack wrapper
contracts were added or removed. All intentional Rack adaptations below remain.

The preceding sound-model sync was on 2026-09-08 at
`72e1d4482324465993c8e62609fa345e848d3b70` ("Document fixed filter
calibration and reference-card comparisons").

The prior port recorded `7ed16c42046ed0c2966096ca4c4b8664cf64dcc2`.
This update brings across the actual intervening DSP changes: coupled voice-VCA
control, the measured SUB diode law, fixed full-resonance VCF service trim,
corrected PWM feedback/output smoothing, coupled chorus mute capacitors, and
reconstruction of the chorus's held noise before numerical sampling. These
upstream model changes intentionally change audio relative to the previous
Rack port. Measured reference-card/noise/chorus profiles, firmware DCO timing,
the coupled mixer, and the finite-resistance HPF circuit remain opt-in native
comparison paths with upstream defaults; they add no host properties.

| Upstream source | SHA-256 |
| --- | --- |
| `YouKnowEngine.h` | `11d18c0543f19649685c75ad9a45cc0eb6c81124008d4340feae26d79d4652da` |
| `YouKnowEngine.cpp` | `53435a755ed789f4bbe3a6f2aa9f6769508fb80f0ad3e639d5c5e5876f2f1b61` |
| `YouKnowChorus.h` | `aafd8b3a62c0879a45bcffe5a40e9bf02ec3b6d04b3d80237c2eefcdf07c056b` |
| `YouKnowChorus.cpp` | `df757abc4242e0842d976b76effcb90e05e34c71ed862a7278745b7d0bdcb600` |
| `YouKnowCoupledMixer.h` | `66e4bb603fb926c071e9654d03461052c636f758a35fcc30daf87e70a90a9d06` |
| `YouKnowHighPassSwitch.h` | `4ae45325506bd0590ca05b5ead51bc69a30e16bc4dcc9ea78540910548a96d84` |
| `YouKnowNoiseCalibration.h` | `a6fe97a772df0c633a0c90a0fba06ce9466a8e5ca4f6a75f8e966353a9b5654a` |
| `YouKnowPwmControl.h` | `3b661483146cd701b33bd349525c3de00720114c128e9b219f85dfbb27705eb2` |
| `YouKnowReferenceVcf.h` | `3f4c422d72b3dbb695847989be0cfb5c7ab4fb635f9dd94e36c5d623660ba1a9` |
| `YouKnowSubLevel.h` | `2a2a877619103c6870513df4753147da19d9bb28425437f1e667b880c4479d99` |
| `YouKnowVcaControl.h` | `15d689be6823ab53ee2d184054ff00629148fd40a1c0b60608f7cb2aede1a385` |

The port includes the exact voice-VCA junction/control law and signal
saturation, C59 coupling constrained by its drawn series resistance, input-side
VCA service trim, sub half-wave coupling and level correction, stepped
DCO/noise/resonance holds, circuit-derived noise/resonance onset, differential
resonance input and its reconstructed compensation bracket, card Johnson noise
and common-VCA noise, capacitor/service-frequency calibration, departing HPF
cut/Boost charge states, chorus mute-drive charge and bypass evolution,
per-line chorus insertion spread, and the upstream +2.5 dB output policy. It
also carries the newer Merson kernel source changes; Rack uses the scalar
kernel until SDK target SIMD support has been qualified.

The shared engine sources are merged deliberately with the following Rack
adaptations:

- C++17 equivalents replace C++20 bit-casts, defaulted parameter equality,
  templated lambdas, and branch-likelihood attributes. All 70 parameter fields,
  including comparison-only switches, participate in equality.
- Oscillator correction, BBD/VCF transfer, resonance-frequency trim,
  harmonic describing, voice-VCA gain, SUB diode gain, and coupled VCA
  charge/differential tables are immutable hexadecimal chip data. The service calibration's nominal droop is the exact hexadecimal
  result of the upstream solve. The card Johnson-noise amplitude is the exact
  upstream binary32 value `0x1.a0b024p-13f`, frozen and bit-compared against its
  source calculation: native constant folding of its square-root initializer
  was insufficient for the SDK global-constant analyzer. This avoids guarded initialization, table
  construction during rendering, and writable runtime-initialized globals.
  Per-card service calibration retains the upstream bounded solve at a
  Character/model change; it does not run on settled blocks.
- New table copies were generated from the nominated C++ builders. The
  standalone table contract rebuilds and bit-compares 513 BBD nodes, 216 VCF
  intervals, 129 resonance trims, 6,146 oscillator-correction samples,
  513 describing nodes, 4,097 voice-VCA gain entries, 8,194 coupled VCA
  charge/differential entries, 4,097 SUB diode gain entries, and the card-noise
  constant. The new VCA circuit object and SUB table are constant-initialized;
  no static guard or first-note table construction is introduced.
- Fixed hexadecimal/literal chassis gradients and C++17 dispatch preserve the
  existing SDK adaptations. Paired/quad SIMD is disabled; reference and fast
  scalar kernels retain all upstream physics. Upstream work-audit instrumentation
  is not enabled or shipped as a runtime dependency.
- `setInitialOversamplingFactor()` restores a song's initial quality before its
  first note without starting a live-change fade. Later quality changes wait
  for silence and complete the safety fade before reporting readiness.
- `retargetHeldNoteLegato()` supports the Rack Note/Gate CV adapter;
  `hasPendingVoiceAssignment()` lets the wrapper advance deferred assignment
  scans while Reason elides silent output. The f14 release review added a
  keyed-source check before a legato retarget: a CV note dropped by a full
  voice pool must fall back to allocation when its pitch later changes.
  Wrapper regressions cover this recovery, simultaneous pitch/gate ordering,
  and preserving the onset when a deferred scan assigns a voice mid-block.
- Cold `reset()` meets Reason's audio-reset contract and clears the chorus's
  pending bypass flush. Reason transport-stop behavior is wrapper-owned.
- Master tune accepts +/-150 cents to combine Reason global tuning with the
  panel trim. Its pitch conversion preserves the source's signed-byte
  quantization for every value within +/-50 cents, including the +127-unit
  positive endpoint, then adds a rounded remainder outside that segment.
  A native regression verifies the complete original range, extended endpoints,
  malformed input, and live oscillator-divider changes beyond +/-50 cents.
  Declared host latency stays fixed at 41 samples.
- Fresh Rack devices retain 1x/Poly/Cubic/RK4-single as the release CPU policy;
  source standalone defaults may differ. Stored quality ordinals and complete
  1x/2x/4x, Exact/Fast/Poly, Hermite/Cubic and three-solver choices are retained.
  Chorus Off/I/II/I+II keeps ordinals 0/1/2/3 and Chorus Noise defaults to
  `0.29858038`. The shared engine's Aging reference default stays zero; fresh
  Rack devices start at 50% through the song-persistent motherboard property,
  while existing songs restore their stored value. New physical-model comparison switches
  use source defaults without adding host controls.
- Source panel, preset and SysEx adapters are not DSP dependencies of the Rack
  engine. Reason owns those host surfaces. No upstream preset payload is copied;
  the independent public Rack bank retains every musical parameter. Six
  existing level trims are attenuated by 0.234–1.139 dB to keep the updated
  DSP within its existing peak/RMS limits at Aging 0% and 50%; the measurement
  and adjustment evidence lives in `Design/preset_levels.json`.
- Files, C++ types, namespaces, and macros retain YouKnow identity. Circuit
  documentation retains original manufacturer/model names where needed to
  identify the cited physical source.

## 2026-09-08 sound-model validation

The updated C++17 frozen-table and engine-render contracts pass under Apple
Clang with warnings treated as errors. All earlier frozen data remain unchanged;
the three added tables are bit-compared with the nominated source builders.
The native engine occupies 42,264 bytes, below the 64 KiB contract; the Rack
wrapper occupies 43,368 bytes. Engine coverage includes all quality paths,
finite/deterministic note/sustain/release output, idle transitions, fixed
41-sample latency, all six new equality fields, reference noise-profile block
invariance, and VCF service-profile/cache round trips across all six cards.
The wrapper/CV contract passes both optimized and AddressSanitizer plus
UndefinedBehaviorSanitizer builds.
The automation-artifact contract passes all 40 parameters in step/ramp,
dry/chorused renders, with held notes surviving switch changes. All 93 public
patches pass the calibration gate at Aging 0% and 50%. Low/high six-note bank
stress also passes all 93 patches; maximum peaks are 0.413066 and 0.435990.

A same-source comparison compiles the nominated engine as C++20 with SIMD
disabled (`-U__ARM_NEON -U__SSE2__`) and the Rack engine as C++17, both at
`-O3 -DNDEBUG`. All 26 deterministic 480-block, 64-frame, 48 kHz stereo
scenarios are bit-identical. The original fourteen cover all three rates,
tanh/early/solver paths, all HPF legs, chorus transitions, Character/Aging,
pitch/modulation, sustain/release and reset. Twelve additional scenarios cover
new reference profiles, legacy comparison switches, firmware DCO timing, the
finite-resistance HPF and coupled mixer. The two complete hash logs share
SHA-256 `75783a28ee631b6ce3f28f22ce82a005d8609fcb71b75a5ecc6145d4b4b90067`.

Default native performance uses six voices, 1x/Poly/Cubic/RK4-single,
Aging 50%, 48 kHz and 64-frame blocks. The updated engine passes with zero
misses in 1,875 timed blocks, median CPU 0.101913 times realtime, p99 block
0.161666 ms and maximum 0.240792 ms against a 1.333333 ms deadline. The
unchanged prior engine's median was 0.101621 times realtime; its one
1.340792 ms scheduling outlier is retained as a failed baseline run rather
than discarded. These measurements exclude the wrapper, Reason scheduling,
and target translation.

Current source hashes, build commands, frozen-table generation driver, native
contract results, full parity driver/logs, performance results, and bank
measurements are retained under
`Release/validation/1.0.0f11-refinement/dsp-sync/`. Earlier `f9` source-audit
artifacts describe the previous snapshot and remain historical evidence.
SDK chip translation, compatible host creation/CPU acceptance, and final
archive checks are recorded separately in `Docs/RELEASE_EVIDENCE.md`.

## 2026-09-09 Rack note-boundary correction

At the time of the f18 boundary fix, shared DSP source bytes remained unchanged
from the `72e1d448` snapshot. The
wrapper now releases pre-existing MIDI holds at an equal-frame boundary before
starting replacement notes, and completes CV edges before those MIDI attacks.
Excess offs pair with incoming ons as zero-duration notes; separate MIDI hold
counts keep unmatched MIDI offs from releasing a CV-owned pitch. Genuinely
separated events retain their supplied frames. No release interval, envelope
reset or new voice-stealing rule is introduced.

The expanded wrapper contract covers arrival-order equivalence, full pools,
balanced overlaps, source ownership and exact sample timing. Engine regressions
protect independent envelopes and the firmware's residual retrigger law; see
the [hardware contract](../Docs/NOTE_EVENT_HARDWARE_CONTRACT.md) for primary
references and measurement limits. The native engine is still 42,264 bytes;
the wrapper is now 43,624 bytes. Earlier shared-DSP parity evidence remains
applicable because the engine, chorus and support-source files did not change.

## 2026-09-09 VST MIDI follow-up synchronization

Upstream `013b257` adds a bounds-checked `isNoteHeld(int)` audio-thread query.
It reports outstanding presses, including overlaps and notes dropped by a full
assigner; a sustain or release tail alone does not count as a held key. The
query is copied verbatim. No other shared engine, chorus or support source
changed upstream since `72e1d448`.

Both VST and Rack corrections release old holds before replacement attacks to
prevent swallowed retriggers and full-pool dropped notes. Both preserve actual
overlaps and insert no release interval. Their host contracts differ:

- VST normalizes contiguous note runs at one original timestamp. Controllers,
  program changes and SysEx end a run. Rack completes the frame's parameter and
  CV changes before starting its MIDI attacks, as its property-diff contract
  and pedal-order regressions require.
- VST preserves the arrival order of releases beyond pre-existing holds. Rack
  pairs these excess offs with the earliest incoming ons as zero-duration
  notes. An initially unheld same-frame `OFF, ON` therefore leaves a key held
  in VST and makes a zero-duration note in Rack.
- VST queries engine-held keys. Rack keeps separate MIDI hold counts so a MIDI
  release cannot consume a CV-owned press. The new shared query deliberately
  does not replace that source-ownership accounting.
- VST keeps distinct original timestamps apart after defensive clamping. Rack
  retains the SDK's fixed 64-frame batches and documented frame-63 fallback.

The existing Rack wrapper already implements its correction and remains
unchanged by this sync. Upstream details are in
[`Docs/midi-event-ordering.md`](https://github.com/protocodus/virtual-instrument-youknow/blob/013b25702145b72d67965665c701f59e105c52b7/Docs/midi-event-ordering.md);
Rack behavior and the outstanding actual-host reproduction are recorded in
[the boundary-fix evidence](../Docs/MIDI_BOUNDARY_FIX.md). The upstream fix
corroborates the confirmed scheduling defect; it does not establish that the
complete Reason recording's amplitude pattern has been resolved.

Current verification passes the strict C++17 engine and wrapper contracts,
the engine contract under AddressSanitizer/UndefinedBehaviorSanitizer, and
patch/localization validation (100 patches). Added query regressions cover
invalid bounds, overlaps, full-pool dropped notes, sustain/release tails and
all reset/release entry points. Engine and wrapper sizes remain 42,264 and
43,624 bytes. All 26 scalar parity scenarios are bit-identical to upstream
`013b257` and the preceding sync; both logs retain SHA-256
`75783a28ee631b6ce3f28f22ce82a005d8609fcb71b75a5ecc6145d4b4b90067`.

The default native performance run failed its wall-clock deadline gate:
4/1,875 misses, maximum 17.574958 ms against 1.333333 ms. Median thread CPU
was 0.108670 times realtime with six voices, 1x/Poly/Cubic/RK4-single,
Aging 50%, 48 kHz and 64-frame blocks. It ran after this task's other
compilation/rendering jobs finished; the failure is retained without retry.
These timings exclude the wrapper, Reason scheduling and target translation.
Source audit, exact commands and logs are retained locally under
`Output/Diagnostics/DspSync-20260909/`. This source synchronization did not
build/install a new package or run a Reason host test.

## 2026-09-10 firmware and output-stage synchronization

The strict C++17 engine and frozen-table contracts pass. Frozen `.inc` data
are unchanged and all upstream builder identity checks still pass. The engine
occupies 42,296 bytes and the Rack native object 43,656 bytes, both below their
64 KiB limits. Parameter equality still covers the same 70 fields.

`Tests/UpstreamDspRegressionContract.cpp` passes 16 focused groups, adapted
from the new upstream engine/circuit regressions. These measure rendered pulse
duty against each card's comparator state; correction continuity at the exact
interval boundary; integer VCF LFO/bend behavior; LFO delay across sustain,
unison and dropped-key cases; attack peak handover; unknown sample rates;
quality-fade sample timing; decimator impulse centroid and the unchanged
41-sample report; Gaussian noise statistics across quality rates; the output
jack pole and its rendered high-frequency response; and temperature-dependent
VCA gain. Additional regressions require bit-identical output across irregular
callback partitions at 1x/2x/4x and three warm-up positions, and exact chorus
wet-mute settling without a host flush-to-zero policy.

All 26 deterministic scalar parity scenarios are bit-identical between the
exact `c9d3c57` archive built as C++20 with SIMD disabled and the Rack port built
as C++17, both at `-O3 -DNDEBUG`. These are 480-block, 64-frame, 48 kHz stereo
renders covering all quality and solver paths, reference/comparison profiles,
physical circuit switches, notes, controllers, transitions, and reset. Both
hash logs have SHA-256
`1f38d34c90eb65dc1e22ddac7ed34d8cd04bb97f9b4ddcd204d8454461ad3e0d`.
The changed hashes relative to f19 are expected for this upstream sound update;
they are not a claim that the prior audio is unchanged.

Exact source hashes, the parity driver and logs, engine/frozen/regression logs,
and commands are retained under `Output/Diagnostics/DspSync-20260910/`.
Wrapper, automation, public-bank levels, native timing, SDK builds and actual
host/release acceptance are recorded separately in
[release evidence](../Docs/RELEASE_EVIDENCE.md).
