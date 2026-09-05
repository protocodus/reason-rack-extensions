# YouKnow 1.0.0f9 release checklist

Current results and retained failures are recorded in
[RELEASE_EVIDENCE.md](RELEASE_EVIDENCE.md).
Product support: https://protocodus.cz/product/youknow/

## Engineering

- [x] Verify SDK 5 and latest nominated upstream DSP, preserving Rack adaptations.
- [x] Preserve product identity, saved properties, socket order, and automation IDs.
- [x] Add six modulation CV sockets and seven previously missing automation mappings.
- [x] Keep Aging 50%, all 77 patch states, and calibrated patch gains.
- [x] Remove unused design inputs and document current behavior and test commands.
- [x] Pass final localization/patch metadata and both GUI layout/asset checks.
- [x] Pass timed automation/CV, reset, disconnection, sample-rate, and sanitizer contracts.
- [x] Render all 77 patches at the shipped Aging 50% default.
- [x] Record the current native default timing pass (0/1875 misses), retaining earlier failures.
- [x] Build local45 Deployment and inspect installed source-backed payload bytes.
- [x] Build universal45 and verify ZIP, four chips, source bytes, and SHA-256.
- [x] Record a fresh Recon diagnostic and its exact host identity/capability limit.
- [x] Generate and visually inspect the matching PDF, Shop, and panel previews.
- [x] Assemble the source/artifact handoff with a verified SHA256SUMS manifest.

## Host and publication acceptance

- [ ] Confirm SDK 5 host support and create the exact candidate.
- [ ] Complete `Documentation/acceptance_testing_checklist.txt`: automation
  record/playback and Alt-click indicators, Remote/Combinator mapping, Note/Gate
  and six modulation CV inputs, reconnect/reset, tuning, patch switching,
  routing, full/folded UI, and multiple instances.
- [ ] Measure the authorized Deployment candidate in representative songs,
  including default and maximum-voice/quality workloads.
- [ ] Confirm the existing developer product/account and distribution requirements.
- [ ] Complete shipped-content, branding, and customer-terms review.
- [ ] Upload the reviewed U45 and archive Reason Studios validation/acceptance.
- [ ] Select accepted Article, price and Shop tags; submit matching copy/images/PDF.
- [ ] Update support materials and publish only after acceptance; tag accepted source.

Use the clean product export for source distribution; do not publish the enclosing
SDK repository or historical third-party factory content.
