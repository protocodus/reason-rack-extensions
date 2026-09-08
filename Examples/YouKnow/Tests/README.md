# Validation

Run commands from the YouKnow project directory. Set `JUKEBOX_SDK_DIR` to an
SDK 5 root in a standalone checkout; this SDK checkout defaults to `../..`.
Current results and remaining host acceptance are in
[release evidence](../Docs/RELEASE_EVIDENCE.md).

## Metadata and panels

```sh
python3 Tests/validate_patches.py
python3 Design/render_panels.py
```

The metadata check covers localization, all 93 authored patches, ranges,
versions, identity, level trims, permanent automation IDs, socket order, and CV
notifications. The renderer checks both GUI formats, property bindings,
widget geometry, stock sprites, asset inventory, and readable label spacing.
Review the resulting full, folded, and browser images at their displayed size.

## Wrapper, automation, and CV

```sh
clang++ -std=c++17 -O3 -Wall -Wextra -Wpedantic -Werror \
  -I"${JUKEBOX_SDK_DIR:-../..}/API" \
  Tests/WrapperHostContract.cpp YouKnow.cpp \
  DSP/YouKnowEngine.cpp DSP/YouKnowChorus.cpp \
  -o /tmp/youknow-wrapper-host-contract
/tmp/youknow-wrapper-host-contract
```

The SDK host shim exercises property snapshots, event timing, parameter
reachability, saved defaults, reset, tuning, quality transitions, silent-output
handling, Note/Gate CV, and the six modulation inputs. It checks automation
and CV together without writing modulation back into stored panel values.
For memory/undefined-behavior checks, build this same contract with
`-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer` in place of `-O3`.

## Engine and upstream parity

```sh
clang++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror \
  Tests/FrozenTableContract.cpp -o /tmp/youknow-frozen-tables
/tmp/youknow-frozen-tables

clang++ -std=c++17 -O3 -DNDEBUG -Wall -Wextra -Wpedantic -Werror \
  -I"${JUKEBOX_SDK_DIR:-../..}/API" Tests/EngineRenderContract.cpp \
  DSP/YouKnowEngine.cpp DSP/YouKnowChorus.cpp \
  -o /tmp/youknow-engine-port-contract
/tmp/youknow-engine-port-contract

clang++ -std=c++17 -O2 -I. Tests/rendercheck.cpp \
  DSP/YouKnowEngine.cpp DSP/YouKnowChorus.cpp -o /tmp/youknow-rendercheck
/tmp/youknow-rendercheck
```

These contracts cover frozen-table identity, deterministic quality/kernel
paths, voice retirement and wake-up, chorus state, notes/sustain/release,
parameter comparison, the 64 KiB memory ceiling, and fixed 41-sample latency.

## Automation artifacts

```sh
clang++ -std=c++17 -O3 -DNDEBUG -Wall -Wextra -Wpedantic -Werror -I. \
  Tests/AutomationArtifactContract.cpp \
  DSP/YouKnowEngine.cpp DSP/YouKnowChorus.cpp \
  -o /tmp/youknow-automation-artifacts
/tmp/youknow-automation-artifacts          # add --verbose for every measurement
```

Automates all 40 host-automatable parameters under a sounding note, each as a
single full-travel jump and as a fast sweep, dry and through the chorus, and
measures whether the change injects a discontinuity the signal was not already
producing. The reference is causal: a moving control is compared against the
same patch HELD STILL at values across its own travel. That matters, because a
self-referential threshold cannot tell a zipper step from a sawtooth edge -- as
the filter opens the waveform becomes a saw, whose derivative is one large step
per cycle. It also checks that notes held through a switch change survive it.

The run takes about six minutes: most of it is the held-still reference renders,
twelve per parameter, each long enough to span several LFO cycles.

Unit Character is the one parameter whose change rebuilds every voice card's
analogue trims at once, so the wrapper glides it over 30 ms
(`AdvanceCalibrationGlide` in YouKnow.cpp); the test reproduces that glide so it
measures the path the instrument ships rather than the bare engine.
[DSP/SYNC.md](../DSP/SYNC.md) identifies the exact upstream revision, source
hashes, Rack adaptations, and retained 26-program scalar parity evidence.
Recheck parity when shared DSP changes; retain labelled results when its bytes
are unchanged.

## Public patches

```sh
python3 Tests/run_all_patch_render.py
python3 Tests/run_all_patch_render.py --aging 0
python3 Tests/run_all_patch_render.py --stress-levels
```

The normal gate uses fresh-device Aging 50%, the shipped 1x/Poly/Cubic/Normal
policy, and a fixed three-note chord. Every patch must be audible, finite,
bounded, and deterministic. Peak limits are 0.04–0.185; RMS must not exceed
0.041. `--aging` accepts any finite percentage from 0 to 100. Stress mode
checks low/high six-note chords below full scale.

Only after an intentional sound or bank change, recalibrate and validate:

```sh
python3 Tests/run_all_patch_render.py --calibrate-levels --aging 0
python3 Design/generate_presets.py
python3 Tests/validate_patches.py
python3 Tests/run_all_patch_render.py
```

Calibration retains the historical Aging 0% reference unless `--aging` is
specified, records that value, and adjusts only the internal patch trim.
Do not recalibrate merely to hide a failed sound or compatibility check.

## Native timing and SDK builds

```sh
clang++ -std=c++17 -O3 -DNDEBUG -Wall -Wextra -Wpedantic -Werror \
  Tests/PerformanceProbe.cpp DSP/YouKnowEngine.cpp \
  DSP/YouKnowChorus.cpp -o /tmp/youknow-performance-probe
/tmp/youknow-performance-probe

python3 build45.py local45 Deployment
python3 build45.py universal45
unzip -t Output/Universal45/YouKnow.u45
```

Run timing without concurrent compilation or rendering. The default probe
records six voices, 1x, Poly/Cubic/Normal, Aging 50%, 48 kHz, and 64-frame
blocks. Non-stress runs fail on any wall-clock deadline miss. Optional modes
are `--quality-2x`, `--vcf-exact`, `--vcf-fast`, `--vcf-fast-cubic`, `--idle`,
`--idle-exact`, and the 16-voice/4x `--stress` diagnostic. Retain failed runs
and their workload instead of silently retrying until one passes.

Native timing excludes the Rack wrapper, Reason scheduling, and target
translation. Final acceptance requires the exact candidate in a confirmed
SDK 5 host and an authorized Deployment build. Inspect installed bytes and U45
contents, then record fresh host creation, routing, automation, and performance
results using the SDK acceptance checklist. A legacy-labelled Recon diagnostic
alone is not SDK 5 delivery acceptance.
