# YouKnow 1.0.0f20 release checklist

Product ID: `cz.protocodus.YouKnow`
SDK: `JukeboxSDK_500_028`, `TargetVersion=5.0`
Product support: https://protocodus.cz/product/youknow/

This candidate synchronizes shared DSP to production upstream `c9d3c57`.
The noise, modulation, output-stage, thermal and chorus changes intentionally
update audio; all musical patch settings are preserved. Circuit Rain alone
needs a 1.402051 dB level-trim reduction at Aging 50%.

## Engineering

- [x] Verify SDK 5 and latest production upstream revision.
- [x] Preserve identity, saved controls, automation IDs, sockets and latency.
- [x] Pass strict engine, frozen-table and 16-group DSP regression contracts.
- [x] Compare all 26 scalar scenarios bit-for-bit with upstream.
- [x] Pass wrapper contracts, ASan/UBSan and randomized MIDI/CV lifecycle audit.
- [x] Measure the complete bank at Aging 0% and 50%; adjust only Circuit Rain.
- [x] Pass final calibrated-bank renders at Aging 0% and 50%.
- [ ] Complete low/high six-note stress renders.
- [ ] Complete automation artifact contract.
- [ ] Record native default-quality timing without concurrent task load.
- [ ] Build local45 Deployment and inspect installed payload.
- [ ] Build universal45 and verify ZIP, source bytes, four chips and SHA-256.
- [ ] Run fresh SDK 5 host creation with production writes denied.
- [x] Visually verify all six manual pages and three matching Shop images.
- [ ] Assemble versioned handoff, build manifest and verified SHA256SUMS.
- [ ] Pass remote CI and address PR feedback. Merge requires an explicit user request.

## Host and distribution

- [ ] Complete interactive SDK acceptance: automation record/playback,
  Remote/Combinator, CV, reset, patches, routing, full/folded UI and multiple instances.
- [ ] Measure the exact Deployment candidate in representative Reason songs.
- [x] Inspect current portal: f17 Deployment is successful, f15 remains failed.
- [ ] Upload f20 and archive its cloud build result.
- [ ] Complete product acceptance and select an accepted Shop Article and price.
- [ ] Publish matching Shop/support materials after acceptance and owner decisions.

The f15 cloud failure remains unexplained; the successful f17 build supersedes
historical notes that left its result unknown. Upload for validation is distinct
from publishing the product in the Shop.
