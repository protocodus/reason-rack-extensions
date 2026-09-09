# Rack MIDI boundary fix — 2026-09-09

Source baseline: `746f888` (`main`, 1.0.0f17). The initial correction changed
only the Reason wrapper. The subsequently requested f18 candidate updates
version metadata and generated materials while preserving all musical patch
states and shared DSP. Its build and installation status is recorded in
[release evidence](RELEASE_EVIDENCE.md); host acceptance remains pending.

## Confirmed failures and correction

The engine balances overlapping presses of one pitch. Passing an equal-frame
successor on before its predecessor off temporarily changed the count from
1 to 2 to 1, so neither edge reached voice allocation or the envelope. A
previous envelope at zero sustain could therefore stay silent. At full
polyphony, starting a different pitch before freeing a slot could instead
drop the new assignment while leaving that pitch counted as held.

`CYouKnow::RenderBatch` now releases pre-existing MIDI holds first at each
supplied frame, completes CV edges, then starts incoming MIDI notes. It keeps
the incoming on order. Multiple offs beyond the old held count pair with the
earliest incoming ons as zero-duration notes; unmatched offs are ignored.
Without note-instance IDs, an unheld pitch's simultaneous on/off cannot be
distinguished from an unmatched off plus a new held note. The explicit
convention is a zero-duration pair.

MIDI has its own bounded hold counts, reset with the audio engine. This keeps
stray MIDI offs from releasing CV-owned notes. One engine counter position is
reserved for the monophonic CV source. Invalid pitch tags are ignored instead
of being redirected to note 127. Neither supplied event frames nor genuinely
overlapping note durations are adjusted.

The [hardware audit](NOTE_EVENT_HARDWARE_CONTRACT.md) establishes the original
per-voice envelopes, shared controls, residual-level retrigger and allocation
rules. These DSP rules remain unchanged. Touching repeats can inherit the
previous envelope level; a real gap may contain a release update. The fix does
not force identical amplitude for those musically different inputs.

## Validation

| Check | Result |
| --- | --- |
| SDK authority | `JukeboxSDK_500_028`, `TargetVersion=5.0` |
| Strict wrapper contract | PASS, including existing snapshot/automation/CV/reset/five-rate coverage |
| Regression sensitivity | All six initial new boundary test groups fail independently against the original wrapper |
| Boundary cases | Same-pitch silent retrigger, full six-voice POLY1/POLY2 replacements, multiple edge permutations, true overlaps, stale offs, MIDI/CV ownership and both handoff directions |
| Timing | Both tie orders at frames 0/17/63; 44.1/48 kHz, 240 ms attack, touching and 1/32-sample gaps against a direct one-sample engine oracle |
| Pedal/mode companions | PASS: POLY1/POLY2/Unison × ENV/GATE × pedal-down/up transitions; no stranded key or sustain latch; invalid tags leave note 127 untouched |
| Address/undefined-behavior sanitizers | PASS on the full wrapper suite with the six initial boundary groups; later pedal/invalid-tag companions were checked by the strict build |
| Strict engine contract | PASS; adds independent-voice envelope renders and exact B-2 residual retrigger vector |
| Shared DSP preservation | Every tracked DSP `.cpp`, `.h`, and `.inc` is byte-identical to `HEAD`; existing quality-render hashes unchanged |
| Memory | Engine 42,264 bytes; wrapper 43,624 bytes, below 64 KiB |
| Patch/localization validation | PASS: 100 unique patches and metadata entries, 184 text keys, deterministic trims, SDK/schema/ranges/identity |
| SDK universal build | PASS: Testing/Deployment × 32/64-bit chip inputs; 100 patches; archive integrity PASS |
| Default native performance | FAILED deadline gate: 3/1,875 wall-clock misses, maximum 4.031084 ms against 1.333333 ms; median thread CPU 0.104347 × real time |

The timing run used six voices, 1x, Poly/Cubic/RK4-single, Aging 50%, 48 kHz,
64 frames, without concurrent test compilation/rendering. It excludes the
Rack wrapper and Reason. The unchanged engine cannot validate the wrapper's
cost, and the failed run is retained, not replaced by a passing retry.

Initial build/strict-wrapper/timing logs and source hashes are in
`Output/Diagnostics/MidiBoundaryFix-20260909/`. The initial compile-validation
archive retained f17 metadata and had SHA-256
`20d0ca2e7bd94bbbb641881dcac820f4a714dcc454e56319f244cf9cb3efe67d`.
That unversioned output is superseded by the separately identified f18 build;
see its `Release/1.0.0f18` handoff and `Release/validation/1.0.0f18` records.

## Remaining host evidence

The user's recording also has a buffer-dependent amplitude pattern reproducible
with synthetic early note-offs. That experiment does not establish the events
Reason actually supplied. The installed f17 binary respects the supplied
frame for both on and off. An incoming-event trace and reproduction with the
fixed candidate in Reason are needed to establish whether these confirmed
boundary bugs explain the complete recording and the reported held A2.
The initial diagnosis did not modify a running Reason session or installed
Rack Extension. The later f18 local45 build uses the separate development
payload, while the user's production Reason session is left intact.
