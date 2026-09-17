# YouKnow Rack Extension

YouKnow is a native circuit-modelled polysynth for Reason 14 and later.
Production candidate `1.0.0f21` includes 100 original Protocodus patches, up to
16 voices, stereo chorus, eight CV inputs, and 41 automatable custom controls
alongside Reason's pitch wheel, modulation wheel, and sustain support.

This candidate synchronizes DSP from Protocodus YouKnow upstream `5d9390d` and
renders with the source instrument's product circuit selections. It includes
circuit-level DCO clock, temperature and reset behavior, firmware envelope and
control fixes, envelope-hold acquisition, DAC and VCA calibration, chorus
loading, output-stage and input-coupling corrections. These intentionally update
the sound model; every control also now resolves malformed values to defined
settings. Reason-specific real-time safeguards, fixed 41-sample latency, saved
control identities, and MIDI/CV ownership remain intact.
[DSP synchronization](DSP/SYNC.md) records the exact source and adaptations;
[release evidence](Docs/RELEASE_EVIDENCE.md) records validation and the
remaining release gates.

Start with the [user guide](Docs/USER_GUIDE.md) and
[patch catalog](PRESETS.md). Support:
[protocodus.cz/product/youknow](https://protocodus.cz/product/youknow/) or
[protocodus+support@proton.me](mailto:protocodus+support@proton.me).

## Where the binaries are

CI never builds a binary (the SDK is not in the repository). Local builds
against the SDK produce, from this directory:

- `python3 build45.py universal45` → `Output/Universal45/YouKnow.u45`, the
  file uploaded to the Reason Studios build service;
- `python3 build45.py local45 Deployment` → an installed development device
  under `~/Library/Application Support/Propellerhead Software/RackExtensions_Dev`;
- `python3 Docs/assemble_release.py` → the complete release set of a version
  under `Release/<version>/` (versioned `.u45`, Shop images, manual,
  changelog, release evidence, build manifest, verified `SHA256SUMS`).

`Output/` and `Release/` are ignored by Git. See [Build](#build) for the
prerequisites and the panel and release generators.

## Build

Use Jukebox SDK 5.0 (`JukeboxSDK_500_028`). From this directory:

```sh
python3 build45.py local45 Deployment
python3 build45.py universal45
```

`JUKEBOX_SDK_DIR` selects an absolute SDK directory; otherwise the build uses
`../..`. The local build installs `YouKnow` under
`~/Library/Application Support/Propellerhead Software/RackExtensions_Dev`.
The universal build writes `Output/Universal45/YouKnow.u45` for the Reason
Studios build service. Use Deployment builds for representative performance
checks; Debugging intentionally disables target DSP optimization.

Regenerate panels after changing their sources, and assemble a version's
release after the universal build:

```sh
python3 Design/render_panels.py
uv run Docs/build_release_materials.py
python3 Docs/assemble_release.py
```

`Design/render_panels.py` owns the layout and checks widget alignment in both
GUI trees. Every artifact of a version goes into one target directory,
`Release/<version>/`: the release generator writes the Shop front and back
panel views, the 1:1 product thumbnail and the PDF manual there, and the
assembler adds the versioned U45, changelog, release evidence, a build manifest
and verified `SHA256SUMS`. Build and release outputs are ignored by Git.

## Development contracts

The JUCE-free C++17 engine uses frozen lookup tables and reports a fixed
41-sample latency. [DSP/SYNC.md](DSP/SYNC.md) records the upstream revision,
source hashes, parity evidence, and Rack-specific adaptations.

The permanent product ID is `cz.protocodus.YouKnow`. Existing automation IDs
256-289 remain unchanged; the seven additional controls use 290-296.
`motherboard_def.lua` defines the property, persistence, and automation maps.
Musical settings and Unit Character belong to patches; Aging and all four
processing-quality choices belong to songs. Fresh devices use Aging 50% and
1x / Poly / Cubic / Normal processing. Quality changes wait for quiet voices
and tails before a short transition fade.

Run the metadata, engine, wrapper, patch-render, and performance checks in
[Tests/README.md](Tests/README.md). Candidate results and unresolved release
gates are maintained in [release evidence](Docs/RELEASE_EVIDENCE.md) and the
[release checklist](Docs/RELEASE_CHECKLIST.md). Native tests do not replace
Reason host validation or Reason Studios acceptance.

## Source and rights

The bank contains only original Protocodus patches; third-party factory banks
are excluded. Protocodus-authored source and artwork use the [MIT license](LICENSE).
SDK material has separate terms; see [third-party notices](THIRD_PARTY_NOTICES.md)
and the [asset provenance inventory](Docs/ASSET_PROVENANCE.md).
See also [privacy](PRIVACY.md) and the [changelog](CHANGELOG.md).
