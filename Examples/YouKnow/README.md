# YouKnow Rack Extension

YouKnow is a native circuit-modelled polysynth for Reason 14 and later.
Production candidate `1.0.0f15` includes 93 original Protocodus patches, up to
16 voices, stereo chorus, eight CV inputs, and 41 automatable custom controls
alongside Reason's pitch wheel, modulation wheel, and sustain support.

The refined header and both SDK 5 packages pass local review and validation.
Reason Studios upload and host acceptance remain pending. The unchanged audio
binaries retain the recorded `1.0.0f14` runtime evidence.

Start with the [user guide](Docs/USER_GUIDE.md) and
[patch catalog](PRESETS.md). Support:
[protocodus.cz/product/youknow](https://protocodus.cz/product/youknow/) or
[protocodus+support@proton.me](mailto:protocodus+support@proton.me).

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

Regenerate panels and release materials after changing their sources:

```sh
python3 Design/render_panels.py
uv run Docs/build_release_materials.py
```

`Design/render_panels.py` owns the layout and checks widget alignment in both
GUI trees. The release generator writes Shop images and the PDF manual under
`Release/`. Build and release outputs are ignored by Git.

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
