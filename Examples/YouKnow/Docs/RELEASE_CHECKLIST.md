# YouKnow 1.0.0f19 release checklist

Current results and retained failures are recorded in
[RELEASE_EVIDENCE.md](RELEASE_EVIDENCE.md).
Product support: https://protocodus.cz/product/youknow/

The f19 candidate packages the shared-DSP sync from upstream `013b257`, adding
the `isNoteHeld()` query and retaining the f18 equal-frame note handling and
MIDI/CV ownership corrections in the Reason wrapper. Audio algorithms, all 100
sound states and level trims are unchanged. Source-sync engine, wrapper,
sanitizer and 26-scenario audio-parity checks pass. Both f19 builds pass metadata,
panel and payload checks; the native libraries and all four chips are
byte-identical to f18. PDF/Shop regeneration, host acceptance and the retained
native wall-clock deadline failure remain open.

The f15 upload consumed that version. Cloud build
`8d852fdd-c51b-419d-882a-e216c23b3228` ran from
`2026-09-08T20:42:41.299944Z` to `2026-09-08T20:48:32.015879Z` and ended with
status `error`. The server/UI supplied no diagnostic beyond “Unknown error.”
The cause is unresolved; neither the f18 note-boundary correction nor the f19
DSP query sync is a verified cloud fix.

## Engineering

- [x] Verify SDK 5 and pin the upstream DSP sync to `013b257`.
- [x] Preserve product identity, saved properties, socket order, and automation IDs.
- [x] Add six modulation CV sockets and seven previously missing automation mappings.
- [x] Keep Aging 50%, all 100 patch states, and calibrated patch gains.
- [x] Remove unused design inputs and document current behavior and test commands.
- [x] Pass final f19 localization/patch metadata and both GUI layout/asset checks.
- [x] Retain passing timed automation/CV, reset, disconnection, sample-rate,
  and sanitizer evidence; source-sync engine, wrapper and engine sanitizers pass.
- [x] Retain f17's 100-patch Aging 50% and low/high six-note render results;
  audio algorithms and all musical patch inputs remain unchanged, and the
  source-sync 26-scenario audio comparison is bit-identical.
- [x] Verify all 100 f19 patches differ only in version; keep every level trim.
- [x] Pass equal-frame retrigger, full-pool, MIDI/CV ownership, pedal/mode,
  exact-timing and original per-voice envelope regressions.
- [ ] Qualify current wall-clock timing without background contention; paired
  native CPU results and deadline failures are recorded in the release evidence.
- [x] Build f19 local45 Deployment and inspect installed source-backed payload bytes.
- [x] Build f19 universal45 and verify ZIP, four chips, source bytes, and SHA-256.
- [ ] Create this candidate in a fresh SDK 5-compatible host and record its identity.
- [ ] Generate and visually inspect matching f19 PDF and Shop materials.
- [x] Assemble the f19 U45 handoff with a verified SHA256SUMS manifest.
- [x] Retain the prior 93-patch provenance and record the seven new original recipes.
- [x] Retain the prepared f14/f15 support-site bundles as historical handoff evidence.
- [ ] Update the support-site handoff for the final f19 materials.
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
- [ ] Resolve browser file selection, upload f19 and archive its cloud result and acceptance.
- [ ] Select accepted Article, price and Shop tags; submit matching copy/images/PDF.
- [ ] Update support materials and publish only after acceptance; tag accepted source.

Use the clean product export for source distribution; do not publish the enclosing
SDK repository or historical third-party factory content.
