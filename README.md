# Reason Rack Extensions

Protocodus Rack Extensions for Reason 14 and later. Only the extension source
is mastered here; the Jukebox SDK is not in the repository and is unzipped over
a checkout to build (see `.gitignore`). The one tracked device is
[YouKnow](Examples/YouKnow/README.md), a native circuit-modelled polysynth.

## Where the binaries are

Nothing in this repository's CI builds a Rack Extension binary: the SDK is
licensed material and cannot be committed, so CI runs only the SDK-free
checks (metadata, panels, patches, sanitizers and the DSP contracts). The
distributables come from local builds against the SDK:

| Distributable | Produced by | Location |
| --- | --- | --- |
| Universal `.u45` for the Reason Studios build service | `python3 build45.py universal45` in `Examples/YouKnow/` | `Examples/YouKnow/Output/Universal45/YouKnow.u45` |
| Local development install for Reason | `python3 build45.py local45 Deployment` | `~/Library/Application Support/Propellerhead Software/RackExtensions_Dev/YouKnow` |
| Assembled release set: versioned `.u45`, Shop images, PDF manual, changelog, release evidence, build manifest and `SHA256SUMS` | `python3 Docs/assemble_release.py` after the universal build | `Examples/YouKnow/Release/<version>/` |

`Output/` and `Release/` are ignored by Git, so a fresh checkout contains no
binaries. The published product comes from the Reason Studios build service
and Shop after the `.u45` is uploaded there; each candidate's validation and
upload state is recorded in
[release evidence](Examples/YouKnow/Docs/RELEASE_EVIDENCE.md) and the
[release checklist](Examples/YouKnow/Docs/RELEASE_CHECKLIST.md).

## Layout

- [`Examples/YouKnow/`](Examples/YouKnow/README.md) — the device: wrapper,
  DSP port, panels, patches, tests and release tooling.
- [`Examples/YouKnow/DSP/SYNC.md`](Examples/YouKnow/DSP/SYNC.md) — the log of
  every synchronization from the upstream YouKnow plug-in engine.
- [`.github/workflows/`](.github/workflows/) — the SDK-free CI and nightly
  checks.
