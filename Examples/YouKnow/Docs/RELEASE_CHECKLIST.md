# YouKnow 1.0.0f22 release checklist

Product ID: `cz.protocodus.YouKnow`
SDK: `JukeboxSDK_500_028`, `TargetVersion=5.0`
Product support: https://protocodus.cz/product/youknow/

This candidate rebuilds the never-uploaded f21 on the current source: the shared
DSP verified against upstream `f929eca` (production `main` `b5cd360` carries the
same engine sources), the 17 September hand-ported mechanism sets recorded in
`DSP/SYNC.md`, the rear routing symbols, the single-jack L/MONO fold, and the
eight patch level trims the chorus Mode I blend required. The source plug-in's
non-DSP fixes of the same day (an atomic POLY pair write, a NaN-safe SysEx
encoder, host program indexing) concern code the Rack does not carry: Reason
stores the assign mode as one property and the device has no SysEx or program
list.

## Engineering

- [x] Verify SDK 5 and the latest production upstream revision.
- [x] Preserve identity, saved controls, automation IDs, sockets and latency.
- [x] Pass strict engine, frozen-table, envelope-firmware and 19-group DSP regression contracts.
- [x] Compare all 43 scalar scenarios bit-for-bit with upstream, including the Rack product configuration.
- [x] Pass wrapper contracts under ASan/UBSan, including musical note phrases and malformed controls.
- [x] Fuzz engine and wrapper with exact press-count models, optimized and sanitized.
- [x] Pass final calibrated-bank renders at Aging 0% and 50%.
- [x] Complete low/high six-note stress renders.
- [x] Complete automation artifact contract on the product configuration.
- [x] Record native default-quality timing without concurrent task load; retain its failure.
- [ ] Qualify wall-clock deadlines and representative Reason playback performance.
- [x] Regenerate the panels for the f22 rear version label (Panels run
  `35276496140` on the macOS runner).
- [ ] Build universal45 and verify ZIP, version, source bytes, four chips and SHA-256.
- [ ] Generate and visually verify the manual and the front, back and 1:1 thumbnail Shop images.
- [ ] Assemble every artifact in `Release/1.0.0f22/` with a build manifest and verified SHA256SUMS,
  and commit the `.u45` and its `.sha256` the script copies to `dist/` at the repository root.
- [ ] Build local45 Deployment and inspect the installed payload; this also confirms the
  HD `gui.lua` static-decoration syntax for the routing symbols, which the cloud build
  does not read.
- [x] Pass source CI on the committed candidate (run `35279712541` on `b481256` in `main`).

## Host and distribution

- [ ] Complete interactive SDK acceptance: automation record/playback,
  Remote/Combinator, CV, reset, patches, routing, full/folded UI and multiple instances.
- [ ] Confirm the output cabling in Reason: auto-route to a mono channel and hear the
  whole chorus, pull one cable under a held note, and check the routing symbols read
  against the chorus switch.
- [ ] Measure the exact Deployment candidate in representative Reason songs.
- [ ] Resolve the pending submission the portal reported for f20, upload f22
  and archive its cloud build result.
- [ ] Complete product acceptance and select an accepted Shop Article and price.
- [ ] Publish matching Shop/support materials after acceptance and owner decisions.

The f15 cloud failure remains unexplained; f17 Deployment built successfully.
The f21 U45 was assembled from `f834459` and never uploaded; it does not carry
this candidate's source. Upload for validation is distinct from publishing the
product in the Shop.
