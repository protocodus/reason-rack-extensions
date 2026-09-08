# YouKnow 1.0.0f16 release checklist

Current results and retained failures are recorded in
[RELEASE_EVIDENCE.md](RELEASE_EVIDENCE.md).
Product support: https://protocodus.cz/product/youknow/

The requested inline branding and balanced header row create a new f16 candidate.
Its local visual, package, and handoff gates pass. Completed DSP and
patch-state checks retain their historical scope; f15 local validation and its
byte-identical f14 audio evidence remain recorded separately.

The f15 upload consumed that version. Cloud build
`8d852fdd-c51b-419d-882a-e216c23b3228` ran from
`2026-09-08T20:42:41.299944Z` to `2026-09-08T20:48:32.015879Z` and ended with
status `error`. The server/UI supplied no diagnostic beyond “Unknown error.”
The cause is unresolved; the f16 UI refinement is not a verified cloud fix.

## Engineering

- [x] Verify SDK 5 and latest nominated upstream DSP, preserving Rack adaptations.
- [x] Preserve product identity, saved properties, socket order, and automation IDs.
- [x] Add six modulation CV sockets and seven previously missing automation mappings.
- [x] Keep Aging 50%, all 93 patch states, and calibrated patch gains.
- [x] Remove unused design inputs and document current behavior and test commands.
- [x] Pass final f16 localization/patch metadata and both GUI layout/asset checks.
- [x] Pass timed automation/CV, reset, disconnection, sample-rate, and sanitizer contracts.
- [x] Render all 93 patches at the shipped Aging 50% default.
- [ ] Qualify current wall-clock timing without background contention; paired
  native CPU results and deadline failures are recorded in the release evidence.
- [x] Build f16 local45 Deployment and inspect installed source-backed payload bytes.
- [x] Build f16 universal45 and verify ZIP, four chips, source bytes, and SHA-256.
- [ ] Create this candidate in a fresh SDK 5-compatible host and record its identity.
- [x] Generate and visually inspect matching f16 PDF and Shop materials.
- [x] Assemble the f16 handoff with a verified SHA256SUMS manifest.
- [x] Recheck all 93 shipped patch states and pin the material/source provenance.
- [x] Retain the prepared f14/f15 support-site bundles as historical handoff evidence.
- [ ] Update the support-site handoff for the final f16 materials.
- [x] Retain reviewed, version-neutral Shop text and tags in the saved unpublished draft.

## Host and publication acceptance

- [ ] Confirm SDK 5 host support and create the exact candidate.
- [ ] Complete `Documentation/acceptance_testing_checklist.txt`: automation
  record/playback and Alt-click indicators, Remote/Combinator mapping, Note/Gate
  and six modulation CV inputs, reconnect/reset, tuning, patch switching,
  routing, full/folded UI, and multiple instances.
- [ ] Measure the authorized Deployment candidate in representative songs,
  including default and maximum-voice/quality workloads.
- [x] Confirm the existing developer product identity and current submission requirements.
- [ ] Confirm owner-controlled distribution agreement, business/tax and payment details.
- [ ] Complete shipped-content, branding, and customer-terms review.
- [x] Record the f15 upload result and retain its unresolved cloud failure.
- [x] Review the final f16 U45 and attempt the authorized upload; Chrome rejects
  file selection with `Not allowed` before submission.
- [ ] Resolve browser file selection, upload f16 and archive its cloud result and acceptance.
- [ ] Select accepted Article, price and Shop tags; submit matching copy/images/PDF.
- [ ] Update support materials and publish only after acceptance; tag accepted source.

Use the clean product export for source distribution; do not publish the enclosing
SDK repository or historical third-party factory content.
