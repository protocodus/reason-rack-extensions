# DSP synchronization

Candidate `1.0.0f9` was rechecked on 2026-09-05 against the nominated checkout
`/Users/vojta/Dev/vst-instruments/youknow/Source/DSP`. Local `main` is at
`1e20b3191bd1bd18d25dafcc143f75f1809a07fe`; YouKnow has no local changes,
although other products in the monorepo have unrelated edits.

An authorized `git fetch --no-tags origin` verified `origin/main` at
`412347383290f3a7d998754ac5946f4372716933`. Local `main` is one commit behind;
that demo-audio commit changes no YouKnow files. Both local and fetched remote
shared DSP match the original synchronization from
`14615838b90e1a6edd2a9e6d91d4f62ea38e418d` byte for byte. No source port,
checkout, upstream edits, or DSP implementation cleanup was needed.

| Upstream source | SHA-256 |
| --- | --- |
| `YouKnowEngine.h` | `b1e06dd74ff5ca7fee78397ff5f7fdb1d446569863293231f321c8364532b901` |
| `YouKnowEngine.cpp` | `af4ab683b12a73d72e9fbde973d447957be855e290ae5a3555378a832dcaa026` |
| `YouKnowChorus.h` | `ca18f940aa4adf13ef88ce9856710080eaecd442923f1aae5d8a40776814a65d` |
| `YouKnowChorus.cpp` | `0f214d7fdcbd3fc6a4b4c9a388b8c55eb7a9b163c3670cd7d0fad58eed721417` |

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
  templated lambdas, and branch-likelihood attributes. All 64 parameter fields,
  including comparison-only switches, participate in equality.
- Oscillator correction, BBD/VCF transfer, resonance-frequency trim,
  harmonic describing, and voice-VCA gain tables are immutable hexadecimal
  chip data. The service calibration's nominal droop is the exact hexadecimal
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
  513 describing nodes, 4,097 voice-VCA gain entries, and the card-noise constant.
- Fixed hexadecimal/literal chassis gradients and C++17 dispatch preserve the
  existing SDK adaptations. Paired/quad SIMD is disabled; reference and fast
  scalar kernels retain all upstream physics. Upstream work-audit instrumentation
  is not enabled or shipped as a runtime dependency.
- `setInitialOversamplingFactor()` restores a song's initial quality before its
  first note without starting a live-change fade. Later quality changes wait
  for silence and complete the safety fade before reporting readiness.
- `retargetHeldNoteLegato()` supports the Rack Note/Gate CV adapter;
  `hasPendingVoiceAssignment()` lets the wrapper advance deferred assignment
  scans while Reason elides silent output.
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
  the independent public Rack bank is recalibrated for the new signal path.
- Files, C++ types, namespaces, macros, and documentation use YouKnow identity.
  Former model-number branding and references are removed without changing
  numerical DSP coefficients.

## Validation

All 13 Rack engine, chorus, and frozen-data files match the validated `f6`
audio-source manifest byte for byte. The unchanged source retains its passing
C++17 frozen-table, engine-render and behavioral contracts under Apple Clang
with warnings treated as errors. The native engine occupies 38,864 bytes,
below the 64 KiB contract. Candidate wrapper/CV checks are recorded separately.
The behavioral render verifies finite note/sustain/release output, the three
quality rungs, completed idle transitions, and fixed 41-sample latency.

A same-source comparison compiled the nominated engine as C++20 with SIMD
disabled and this Rack engine as C++17, both at `-O3 -DNDEBUG`. Fourteen deterministic
480-block, 64-frame, 48 kHz stereo scenarios are bit-identical. Coverage includes
all three rates, all tanh/early/solver paths, switching all four HPF legs,
chorus Off/I/I+II/II transitions, live Character/Aging changes, pitch/modulation,
sustain/release, and reset. The comparison driver and per-scenario hashes are
recorded with the release validation artifacts.

The `f9` revision, branch/tracking state, local and remote SHA-256 comparisons,
Rack source hashes, and exact verification commands are recorded under
`Release/validation/1.0.0f9/dsp-sync-*`. Since both implementations are unchanged,
the identical broad render suites were not repeated for this source audit.

Native tests establish source parity and local engine behavior; SDK chip
translation, compatible host creation/CPU acceptance, and final archive checks
are recorded separately in `Docs/RELEASE_EVIDENCE.md`.
