# DSP synchronization

Upstream now lives in its own repository. YouKnow left the `vst-instruments`
monorepo in `3a5d0e399a973f974d73638912555980ccb3038f` ("Move Electry, Taikor
and YouKnow into their own repositories", 2026-09-06) and arrived at
`8ab52dc2473261d0227fa4742c28c2fda9249ea4` ("Import YouKnow from the
vst-instruments monorepo") in
`git@github.com:protocodus/virtual-instrument-youknow.git`. **The nominated
checkout is `/Users/vojta/Dev/virtual-instrument-youknow/Source/DSP`**; the
former monorepo path in earlier revisions of this file no longer exists.

Synchronized on 2026-09-08 from the nominated checkout at
`72e1d4482324465993c8e62609fa345e848d3b70` ("Document fixed filter
calibration and reference-card comparisons"). Local `main` and fetched
`origin/main` both resolve to that revision after `git fetch --no-tags origin`;
the upstream worktree is clean. No upstream checkout or source edits were made.

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
| `YouKnowEngine.h` | `3d1c800866d923cb63bd846797fdb16c96363cb27e24c5a79a27bb51f122c4ca` |
| `YouKnowEngine.cpp` | `544b0c5e741e424d4f7441fe3abc34b63a487d97b4bb39fe665f265f223acae4` |
| `YouKnowChorus.h` | `aafd8b3a62c0879a45bcffe5a40e9bf02ec3b6d04b3d80237c2eefcdf07c056b` |
| `YouKnowChorus.cpp` | `57dbb4fcdad6056c9f1219652bb50e77a2ab572bfe9c7874fe6131c7bdca9c6c` |
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

## Validation

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
