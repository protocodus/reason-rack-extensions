# DSP synchronization

Upstream now lives in its own repository. YouKnow left the `vst-instruments`
monorepo in `3a5d0e399a973f974d73638912555980ccb3038f` ("Move Electry, Taikor
and YouKnow into their own repositories", 2026-09-06) and arrived at
`8ab52dc2473261d0227fa4742c28c2fda9249ea4` ("Import YouKnow from the
vst-instruments monorepo") in
`git@github.com:protocodus/virtual-instrument-youknow.git`. **The nominated
checkout is `/Users/vojta/Dev/virtual-instrument-youknow/Source/DSP`**; the
former monorepo path in earlier revisions of this file no longer exists.

Synchronized on 2026-09-16 from the nominated checkout, whose `main` equals
freshly fetched production `origin/main` at
`5d9390daaa518e91e64ad454736b011dfd05168c` ("CI: refresh screenshot and audio
demos"). Its shared DSP is identical to `1e9522a` ("fix(dsp): adopt
circuit-derived input coupling"), the latest DSP commit. The checkout also holds
one uncommitted DSP change, taken deliberately: `YouKnowEngine::sanitise()` maps
out-of-range enumerations (key mode, PWM source, range, HPF, envelope polarity,
VCA mode, chorus, noise-calibration and chorus-timing profiles) to their
defaults. The working-tree diff of `Source/DSP` against `5d9390d` is that single
35-line hunk (diff SHA-256
`80ae130d24ca6f153cf62489cd97f3e23bce1ae64dc24574bf264c8c04846792`). The
checkout's other uncommitted changes are plug-in, CMake and demo tooling, not
DSP dependencies, and were left untouched.

This is an intentional sound-model and bug-fix update from the previous
`c9d3c571c6d8586fbb19c8e821e66f68607dfdff` synchronization; 31 upstream commits
touched `Source/DSP`:

- DCO: the configurable clock is coupled to audio and to the accelerated
  thermal model; held control current integrates causally; joint capacitor and
  range-resistor variation is preserved; RANGE switches C54's charging resistor
  at its PF write; a configurable retained-charge reset is integrated; and
  portamento advances before DCO writes. New helpers `YouKnowDcoComponents.h`,
  `YouKnowDcoReset.h` and `YouKnowDcoTemperature.h` carry that circuit.
- Firmware: filter control precision, envelope update ordering and phase
  latches follow B-2; a nominal control-pass trace (`YouKnowFirmwareProgram.h`,
  `YouKnowFirmwareTrace.*`) and voice-board command replay exist as comparison
  paths.
- Converters and VCAs: the envelope DAC span, common VCA buffer gain and loaded
  DAC bias network are derived (`YouKnowControlDac.h`); the voice VCA response
  follows temperature, its service calibration and HOLD state match hardware,
  and finite envelope-hold acquisition is modelled (`YouKnowEnvelopeHold.h`).
- Noise: VCF resistor noise is distributed across the four stages and card
  resistor noise scales with temperature.
- Chorus: coupled input loading, finite mute discharge resistance, an optional
  clock-mute circuit and four renderable timing candidates (the shipping profile
  stays the default).
- Output and input: the analog output-jack rolloff is a magnitude-matched pole
  (`YouKnowOutputJack.h`), and the product adopts circuit-derived C56 input
  coupling.
- `YouKnowProductFidelity.h` centralizes the product's circuit selections: the
  110-ohm HPF switch, the thermal DCO clock proxy, C56 input coupling and the
  serviced VCF calibration.

No Reason properties, stored ordinals or automation identities were added or
removed. `EngineParameters` gains `enableVoiceVcaServiceGain`,
`enableVoiceVcaTemperature`, `enableChorusClockMuteCircuit` and
`chorusTimingProfile` (replacing `useA11EffectiveChorusTimingProfile`); they
keep source defaults and add no host controls.

The Rack product now renders with the source plug-in's complete product
configuration, shared by the wrapper and every product-measuring harness in
`ProductConfiguration.h`: `ProductFidelityProfile` before the first `prepare()`
and on every parameter snapshot, plus the `MeasuredChartGeometry` converter
timing that the plug-in's `prepareToPlay()` and its product renderers select
(an upstream listening decision of 2026-09-04). Earlier Rack candidates never
selected that timing, so this closes a product-parity gap as well as adopting
the new selections.

| Upstream source (nominated checkout) | SHA-256 |
| --- | --- |
| `YouKnowEngine.h` | `8c3d099d28593bb5ca1b466548c41681ee33e517f07f718d53db39da63853d84` |
| `YouKnowEngine.cpp` | `1d7d9278ffedd1d300c310ebcf2fffdd9f44e72d3d30403bdb031ebda1a587e2` |
| `YouKnowChorus.h` | `5f86b79a6cf74f22f74309a928fd51023249e342182bf0f630894073dcaaa01a` |
| `YouKnowChorus.cpp` | `1317903cd62c9ccd713c5969a83438b4dc8d0cf2e2c54788e7c6495ff994350d` |
| `YouKnowControlDac.h` | `5dc6f68e2b93c50975feb1e94b90c3f198239451071cd0ac080833b8638aa60e` |
| `YouKnowCoupledMixer.h` | `b66c33b2731e340393e9e58910e310ce0e603ad0ed94fa1ee1ffbc34b65ed2c4` |
| `YouKnowDcoComponents.h` | `aad6cb567e93f76c5ffc84b115df65004b5276343b542f071890d2b31748b788` |
| `YouKnowDcoReset.h` | `f9eea3cf4f196f485272cf0be04bb6f21c9e1a7e53a2f08289a9faf73032094a` |
| `YouKnowDcoTemperature.h` | `0e52db39e51810be461c36558276fc7c450a6d02d4d4d80c7a449e7f18301c70` |
| `YouKnowEnvelopeHold.h` | `799b7abe4123b497a3de2d0be022e0d57406adeb3169f5ed8e823f70f9fb0c33` |
| `YouKnowFirmwareProgram.h` | `2109da6a369998f8c6327eb6124b773ba5309d9251ae6e0218c6d4875b5d1007` |
| `YouKnowFirmwareTrace.h` | `ddd690de8ca696af170e186d1fd7ce2403c5af433f0c28e28b8be0b94af5253d` |
| `YouKnowFirmwareTrace.cpp` | `106cdde9d32d3a88f32db9161e6888309fd271be5f9837de663e0b5598deda27` |
| `YouKnowHighPassSwitch.h` | `33cc1311635ca3c6b850e952b5f0592db86c47b0bd93adfd07d960f7f1dd2eb8` |
| `YouKnowNoiseCalibration.h` | `a6fe97a772df0c633a0c90a0fba06ce9466a8e5ca4f6a75f8e966353a9b5654a` |
| `YouKnowOutputJack.h` | `b2eb43e45a0dfec0442679b144b5b11ffcef2f6153a9372ac7fe7747b37eb0e5` |
| `YouKnowProductFidelity.h` | `0ff45e77b4ead10bd53567a08e1bbd4d725690382d3b514cfae0fb5d92fdde98` |
| `YouKnowPwmControl.h` | `3b661483146cd701b33bd349525c3de00720114c128e9b219f85dfbb27705eb2` |
| `YouKnowReferenceVcf.h` | `3f4c422d72b3dbb695847989be0cfb5c7ab4fb635f9dd94e36c5d623660ba1a9` |
| `YouKnowSubLevel.h` | `2a2a877619103c6870513df4753147da19d9bb28425437f1e667b880c4479d99` |
| `YouKnowVcaControl.h` | `1c59ded44bef6dc19bad3231f567baeb0fc4413ac8062f48be90f618197f71db` |

Only `YouKnowEngine.cpp` differs from the `5d9390d` blob
(`46328bf1b4810dce5bf0dfd4f46342e1cccb2d1fd0b1b54675a51e0188f0e9a7`), by the
sanitising hunk above. `YouKnowControlDac.h`, `YouKnowCoupledMixer.h`,
`YouKnowDco*.h`, `YouKnowEnvelopeHold.h`, `YouKnowFirmwareProgram.h`,
`YouKnowFirmwareTrace.h`, `YouKnowHighPassSwitch.h`,
`YouKnowNoiseCalibration.h`, `YouKnowPwmControl.h` and `YouKnowReferenceVcf.h`
are byte-identical copies.

The port includes the exact voice-VCA junction/control law and signal
saturation, C59 coupling constrained by its drawn series resistance, input-side
VCA service trim, sub half-wave coupling and level correction, stepped
DCO/noise/resonance holds, circuit-derived noise/resonance onset, differential
resonance input and its reconstructed compensation bracket, card Johnson noise
and common-VCA noise, capacitor/service-frequency calibration, departing HPF
cut/Boost charge states, chorus mute-drive charge and bypass evolution,
per-line chorus insertion spread, and the upstream +2.5 dB output policy, now
with the circuit-level DCO, firmware, converter, envelope-hold, noise, chorus and
output/input changes above. It also carries the Merson kernel source; Rack uses
the scalar kernel until SDK target SIMD support has been qualified.

The shared engine sources are merged deliberately with the following Rack
adaptations:

- C++17 equivalents replace C++20 bit-casts, defaulted parameter equality,
  templated lambdas, `std::numbers::pi`, a constexpr `std::array::fill` and
  branch-likelihood attributes. All 73 parameter fields, including
  comparison-only switches, participate in equality.
- Oscillator correction, BBD/VCF transfer, resonance-frequency trim,
  harmonic describing, voice-VCA gain, SUB diode gain, and coupled VCA
  charge/differential tables are immutable hexadecimal chip data. The service
  calibration's nominal droop and the voice VCA's service gain
  (`0x1.47715cp+0f`) are the exact hexadecimal results of the upstream solves;
  the coupled VCA circuit's knee coordinates are constant-folded and
  `static_assert`ed against the source constructor. The card Johnson-noise
  amplitude is the exact upstream binary32 value `0x1.a0b024p-13f`, frozen and
  bit-compared against its source calculation: native constant folding of its
  square-root initializer was insufficient for the SDK global-constant analyzer.
  This avoids guarded initialization, table construction during rendering, and
  writable runtime-initialized globals. Per-card service calibration retains the
  upstream bounded solve at a Character/model change; it does not run on settled
  blocks.
- The firmware control-trace coefficient tables, a function-local static in the
  source, are an engine member filled by the constructor.
- The three voice-VCA tables were regenerated from the exact upstream builders
  on the corrected `ControlDac` full-scale span. The standalone table contract
  rebuilds and bit-compares 513 BBD nodes, 216 VCF intervals, 129 resonance
  trims, 6,146 oscillator-correction samples, 513 describing nodes, 4,097
  voice-VCA gain entries, 8,194 coupled VCA charge/differential entries, 4,097
  SUB diode gain entries, the nominal service droop and the card-noise constant;
  the regression contract bit-compares the frozen service gain with the live laws.
- `ProductFidelityProfile::configureBeforePrepare()` reports a refused circuit
  configuration instead of throwing: a Rack native object has no exception path,
  so the wrapper asserts on the result during `JBox_Export_CreateNativeObject`.
  The selections are identical.
- Fixed hexadecimal/literal chassis gradients and C++17 dispatch preserve the
  existing SDK adaptations. Paired/quad SIMD is disabled; reference and fast
  scalar kernels retain all upstream physics. Upstream work-audit instrumentation
  is not enabled or shipped as a runtime dependency.
- `noteOn()` gives a nonfinite velocity the velocity extension's neutral full
  scale. `std::clamp` passes NaN through, and the source would carry it into the
  coupled VCA control law, silencing the card and reaching an undefined
  float-to-integer table index. Finite velocities are unchanged. The Rack wrapper
  never produces such a velocity; the engine contract and fuzz hold the API to it.
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
  while existing songs restore their stored value. New physical-model comparison
  switches use source defaults without adding host controls.
- The engine object is 70,168 bytes and the Rack native object 71,528 bytes.
  The former 64 KiB contract predates the firmware trace, per-voice reset
  correction and per-stage filter noise; the SDK documents no native-object
  ceiling, so the contracts now hold a 96 KiB growth guard.
- Source panel, preset and SysEx adapters are not DSP dependencies of the Rack
  engine. Reason owns those host surfaces. No upstream preset payload is copied;
  the independent public Rack bank is recalibrated to the updated product sound
  (see the dated section below); its measurement and adjustment evidence lives
  in `Design/preset_levels.json`.
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
contracts were added or removed by that synchronization.

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

## 2026-09-16 upstream synchronization, product configuration and hardening

This section validates the synchronization described at the top of this file.
All native results below use Apple Clang with warnings treated as errors.

**Parity.** A deterministic scalar driver renders 42 scenarios of 480 64-frame
48 kHz stereo blocks through the nominated checkout's sources (C++20, `-O3
-DNDEBUG -U__ARM_NEON -U__SSE2__`) and through this port (C++17, `-O3 -DNDEBUG`).
All 42 are bit-identical; both hash logs share SHA-256
`4074833387e91700c2b8ea2be1b2b0276a2cac23b5ab7ae183645359bb91037d`. Scenarios
0-38 cover every quality, tanh and solver path, reference and comparison
profiles, the four chorus timings, firmware DCO and control-trace timing, the
DCO reset circuit, envelope holds, the coupled mixer, finite HPF resistances and
the product-fidelity selections; their hashes equal those of the first merge of
this synchronization, so the sanitising and velocity changes leave valid input
untouched. Scenarios 39-40 render the complete Rack product configuration at
1x and 2x, and 41 feeds out-of-range enumerations to both `sanitise()` paths.

**Contracts.** The frozen-table contract, the engine-render contract (engine
70,168 bytes, native object 71,528 bytes, quality/kernel hashes unchanged by the
hardening), the upstream regression contract (19 groups; the common-VCA law's
expected levels follow upstream `583e2f3`), the verbatim envelope-firmware oracle
and the behavioural render pass. The wrapper contract passes optimized and
under AddressSanitizer plus UndefinedBehaviorSanitizer, including its new
product-configuration, musical-phrase (two rates, three key modes, pedal up and
down, seven phrases) and malformed-control checks. The automation-artifact
contract passes all 40 parameters on the product configuration; the worst
continuous slew is 1.02x its held reference.

**Robustness.** Before these fixes the sanitized fuzzers found two undefined
float-to-integer conversions: a NaN note velocity reaching the coupled VCA
control table, and hostile stepped property values in the wrapper (for example
`1e300` for Transpose). Both are fixed at their source and pinned by focused
regressions. The wrapper now reads every nonfinite property as its declared
default from one table that `Tests/validate_patches.py` checks against
`motherboard_def.lua`, and clamps finite values before any conversion or CV
modulation. With programs drawn portably from raw
`std::mt19937` words, the engine fuzz then passed 48 seeds x 600 blocks, a
200-seed x 1,000-block campaign (about 400,000 API events) and 36 sanitized
seeds; the wrapper fuzz passed 24 seeds x 400 batches, a 120-seed x
1,000-batch campaign (about 720,000 host events) and 16 sanitized seeds. Each checker was shown to
catch a deliberately injected defect: a retriggering duplicate press (in every
key mode), a silently dropped Poly pitch, an overlap press-count error, an
initial-quality call that always resets, and a wrapper that no longer pairs
excess same-frame releases.

**Bank.** Retaining the f20 trims would fail 64 patches against the updated
product sound (median level +0.5 dB, extremes -3.3 to +3.2 dB), so all 100
trims were recalibrated at Aging 0% on the product configuration. The median
trim moves -0.559 dB (-2.826 dB for Falling Star to +2.485 dB for Hollow Fifths;
three trims stay at the +18 dB ceiling). Storm Signal could no longer reach the
0.04 audibility floor even at that ceiling, so its volume rises from 0.62 to
0.72 (+1.3 dB); no other musical value changes. At Aging 50%, Broken Telemetry
(0.185034 peak) and Circuit Rain (0.220611) exceeded the ceiling; their trims
fall by 0.2397 dB and 1.7672 dB by the established maximum-of-both-agings method,
recorded in `Design/preset_levels.json`. All 100 patches then pass at Aging 50%
(maximum peak 0.180120, maximum RMS 0.040013) and 0% (0.180001, 0.040002); the
low/high six-note stress peaks are 0.388021 and 0.416929.

**Open parity note.** Reason's audio reset remains a cold `reset()`, which
restarts the modelled chassis warm-up; the source plug-in keeps warm-up across
host stops (`resetForHostStop()`). With the new clock and VCA temperature
couplings, a reset therefore replays up to about 1 cent of DCO warm-up drift and
the temperature-dependent VCA level change while notes play. The cold reset
keeps Reason's "as if no sound was ever sent" audio-reset contract literal; the
alternative is a product decision, not taken here.

The parity driver and both hash logs, the contract, sanitizer, fuzz-campaign,
bank, metadata, build and timing logs are retained with the candidate under
`Release/1.0.0f21/validation/`; release results are in
[release evidence](../Docs/RELEASE_EVIDENCE.md).

## 2026-09-17 resonance BA662 input offset

Ported from the upstream working branch `claude/admiring-allen-tgtxg2`
(virtual-instrument-youknow, "feat(dsp): carry the resonance BA662 input
offset into the loop"), applied to this C++17 port by hand rather than by
copying files, so the port's `memcpy` bit-cast, frozen `.inc` tables and the
2026-09-16 `sanitise()` hunk are untouched. The change is confined to
`YouKnowEngine.h`/`.cpp`:

- `EngineParameters::enableResonanceOtaOffset` (default true) beside the
  stage-offset switch; `OtaCascade::resonanceOffsetVolts` in node volts;
  `VoiceCard::resonanceOtaOffset`, a signed ±1.5 mV draw at the pair
  (`hashBipolar(seed + 14u)`), inside the Rohm BA6110 sibling sheet's
  "VIO = 3 mV max" (URL and SHA-256 beside the field).
- `refreshVoiceCardStageTrims()` refers the draw to the node through
  `VoicedResonanceCompatibilityProfile::loopDividerRatio` (100k/1.5k) and
  scales it by Unit Character; the parameter-change test that triggers the
  refresh includes the new switch.
- The scalar, PolyZoned, both pair and the quad VCF kernels add the offset to
  the resonance pair's differential input before its tanh, so the gm·V_os
  feedthrough scales with the loop gain and is exactly zero with the loop
  open. Adding 0.0 leaves the Character-0 and switch-off paths bit-identical.
- A sibling reading of the JUNO-6 CPU-board DCO reset (TL082 integrator, TR5
  with 2.2 Ω, 270 pF/10 kΩ drive) is recorded beside `rampResetSeconds`; no
  value changes.
- Port fix, found on review: the hand-written `EngineParameters::operator==`
  (upstream defaults it) had not been extended with `enableResonanceOtaOffset`,
  so a change of that switch alone would not have registered as a parameter
  change. It now compares the switch; nothing in the product toggles it.

**Contracts (Linux, clang 18).** The behavioural render, the upstream regression
contract (19 groups), the envelope-firmware oracle, the engine fuzz
(48 seeds × 600 blocks; the fuzzed switch set now includes
`enableResonanceOtaOffset`) and all 100 public patches (audible, finite,
bounded, deterministic) pass. The frozen-table contract reports its documented
Linux libm mismatch in the BBD table (`BBD table mismatch at 50`); it compiles
no engine source and is unaffected by this change, and CI runs it on macOS.
The wrapper contract needs the SDK and did not run here. Patch trims were not
recalibrated: at Aging 50% the mechanism changes only resonance-dependent DC
and per-voice self-oscillation settling, and the bank check above passes with
the existing trims; a level pass belongs with the next release candidate.

## 2026-09-17 one-temperature resonance return, RES adjustment, gradient warm-up, jack-board floor, sub storage skew

Ported from the same upstream working branch `claude/admiring-allen-tgtxg2`
(virtual-instrument-youknow), again by hand into this C++17 port; the port's
`memcpy` bit-cast, frozen `.inc` tables and the `sanitise()` hunk are
untouched. Confined to `YouKnowEngine.h`/`.cpp`, `EngineParameters::operator==`
and the fuzz contract's switch list:

- `EngineParameters::enableResonanceHeadroomTemperature` (default true):
  `YouKnowEngine::resonanceHeadroomFor()` gives the resonance return's headroom
  as the stage headroom through the return's own 100k/1.5k divider (both are
  2 Vt in one module), written as a ratio to the nominal so a 25 C card
  reproduces `loopHeadroomVolts` bit for bit. All five VCF kernels (scalar,
  PolyZoned, both SIMD pairs, the quad) take the return's headroom per node or
  per lane from `OtaCascade::resonanceHeadroomFollowsStage`, set per voice from
  the switch.
- `EngineParameters::enableResonanceServiceTrim` (default true):
  `VoiceCard::vcfServiceResonanceScale`, the p. 19 RES adjustment, is the
  harmonic-balance loop gain that sustains 2.4 V peak on that card at its
  settled temperature as a ratio to the nominal card's solve; `resonanceFeedbackFor()`
  scales the whole return by it. The port freezes the nominal solve's loop
  gain beside its droop (`nominalLoopGain = 0x1.1ff370af4313ap+2`, the
  macOS value the frozen-table contract's own solve gives on the CI host
  that owns these constants; Linux/clang 18 reads one ULP higher,
  `...313b`, exactly as it does for the droop constant. The contract checks
  the loop gain and prints the actual bits on a mismatch).
- The FREQ solve carries the adjustment's shift of the loop gain the
  frequency-trim table is read at (`correctionRatio`) and reads the gradient's
  cutoff factor at the service reference; the voiced post-trim residual stays
  out of it as before.
- `voiceCardCelsius()` develops both rises on the warm-up clock;
  `thermalFilterOmegaScaleFor()` gives the gradient's cutoff factor at a
  warm-up fraction; `refreshVoiceCardThermalScales()` runs on the drift
  cadence with the Johnson scales and on every settle path.
- `refreshJackBoardTemperature()` resamples `jackBoardCelsius_` together with
  `jackBoardJohnsonScale_`, applied to the summer and wiper floors.
- `EngineParameters::enableSubStorageSkew` (default true) and
  `subSwitchStorageSeconds` (0.2 us, a borrowed class value): the sub track's
  rising edge is placed late by the storage time in `beginDcoDischarge()`.

**Contracts (Linux, clang 18).** The behavioural render, the upstream
regression contract, the engine port contract, the wrapper host contract
(against the SDK API stub) and the engine fuzz (48 seeds x 600 blocks; the
fuzzed switch set now includes the three new switches) pass. The frozen-table
contract still reports its documented Linux libm mismatch in the BBD table and
is verified on macOS in CI. Patch trims were not recalibrated: at Aging 50% the
changes move the settled self-oscillation amplitude by under 2 % and the
resistor floor by 0.2 dB, and the bank check passes with the existing trims.
