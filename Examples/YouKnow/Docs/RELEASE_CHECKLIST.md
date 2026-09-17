# YouKnow 1.0.0f21 release checklist

Product ID: `cz.protocodus.YouKnow`
SDK: `JukeboxSDK_500_028`, `TargetVersion=5.0`
Product support: https://protocodus.cz/product/youknow/

This candidate synchronizes shared DSP to production upstream `5d9390d` plus the
nominated checkout's enum-sanitising hunk and the two 17 September hand-ported
mechanism sets recorded in `DSP/SYNC.md`, and renders with the source
instrument's complete product configuration. The circuit, firmware and product
changes intentionally update audio, so every patch level trim is recalibrated;
Storm Signal's volume rises from 0.62 to 0.72, and Broken Telemetry and Circuit
Rain are attenuated at Aging 50%. All other musical settings are preserved.

After the items below were ticked, the rear gained Reason's routing symbols
and a single cabled output began carrying the L/MONO fold of both channels.
The panels, previews, Shop images, universal build, assembled artifacts and
source CI must therefore be redone on the current source; those items are
unticked again below.

## Engineering

- [x] Verify SDK 5 and the latest production upstream revision.
- [x] Preserve identity, saved controls, automation IDs, sockets and latency.
- [x] Pass strict engine, frozen-table, envelope-firmware and 19-group DSP regression contracts.
- [x] Compare all 42 scalar scenarios bit-for-bit with upstream, including the Rack product configuration.
- [x] Pass wrapper contracts under ASan/UBSan, including musical note phrases and malformed controls.
- [x] Fuzz engine and wrapper with exact press-count models, optimized and sanitized.
- [x] Recalibrate the complete bank against the product configuration at Aging 0% and 50%.
- [x] Pass final calibrated-bank renders at Aging 0% and 50%.
- [x] Complete low/high six-note stress renders.
- [x] Complete automation artifact contract on the product configuration.
- [x] Record native default-quality timing without concurrent task load; retain its failure.
- [ ] Qualify wall-clock deadlines and representative Reason playback performance.
- [ ] Regenerate the panels and previews after the rear routing symbols: run the
  Panels workflow by hand on the branch (it renders on a macOS runner and commits
  the result), or `python3 Design/render_panels.py` on a Mac.
- [ ] Build universal45 and verify ZIP, version, source bytes, four chips and SHA-256.
- [ ] Generate and visually verify the manual and the front, back and 1:1 thumbnail Shop images.
- [ ] Assemble every artifact in `Release/1.0.0f21/` with a build manifest and verified SHA256SUMS.
- [ ] Build local45 Deployment and inspect the installed payload; this also confirms the
  HD `gui.lua` static-decoration syntax for the routing symbols, which the cloud build
  does not read.
- [ ] Pass source CI on the committed candidate (last passed: run `35133083217` on
  `f834459` in `main`, before the routing symbols and the output fold).

## Host and distribution

- [ ] Complete interactive SDK acceptance: automation record/playback,
  Remote/Combinator, CV, reset, patches, routing, full/folded UI and multiple instances.
- [ ] Confirm the output cabling in Reason: auto-route to a mono channel and hear the
  whole chorus, pull one cable under a held note, and check the routing symbols read
  against the chorus switch.
- [ ] Measure the exact Deployment candidate in representative Reason songs.
- [ ] Resolve the pending submission the portal reported for f20, upload f21
  and archive its cloud build result.
- [ ] Complete product acceptance and select an accepted Shop Article and price.
- [ ] Publish matching Shop/support materials after acceptance and owner decisions.

The f15 cloud failure remains unexplained; f17 Deployment built successfully.
Upload for validation is distinct from publishing the product in the Shop.
