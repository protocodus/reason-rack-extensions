# Note events and the original hardware

Reviewed 2026-09-09 for the touching-note / nonzero-attack fix. The reference
instrument is the original six-voice Roland JUNO-106. Higher voice counts and
Reason's timestamped event stream are product extensions.

## Manufacturer evidence

The original [Owner's Manual, opening page and pp. 20-22](https://cdn.roland.com/assets/media/pdf/JUNO-106_OM.pdf)
establishes six envelopes, six filters and six amplifiers. Each note's envelope
controls its filter and, in ENV mode, its amplifier. GATE selects a gate signal
for the amplifier instead; it does not remove filter envelope modulation.
POLY 1 and POLY 2 allocate one voice per key. POLY 2 reuses voices so that only
the latest note or group keeps its complete release. Six held keys exhaust
the polyphonic capacity. Pressing both POLY buttons selects a six-voice
monophonic stack.

The [Service Notes, pp. 7-8](https://www.kiwitechnics.com/downloads/Kiwi-106/Roland%20Juno-106%20Service%20Manual.pdf#page=7)
show a common module-board CPU and 12-bit converter with separate per-voice
control holds and a nominal 4.2 ms converter pass. This is shared computation,
not one global envelope state. The assigner combines local-keyboard and MIDI
key bitmaps and reacts to their changes. A second press of a pitch already
held on the other keyboard does not retrigger it. Key-up releases the assigned
voice. These scanned pages were visually checked; the text extraction of the
service scan is empty.

## Digital-law and allocation audit

The nominated upstream claims B-2 voice firmware and A-5 assigner behavior.
The following audit also reads the pinned recovered listings directly; their
unofficial annotations are corroboration, not manufacturer documentation.

The [B-2 Voice On path, addresses $010D-$014C](https://github.com/ErroneousBosh/j106roms/blob/26926a04ff1939106820313e71e34b4ca2f67070/ic29.txt#L195)
sets the addressed voice's gate and attack flags without clearing its envelope
accumulator. The [envelope loop, $0503-$0590](https://github.com/ErroneousBosh/j106roms/blob/26926a04ff1939106820313e71e34b4ca2f67070/ic29.txt#L780)
adds an attack increment to the current level, saturates at the peak, and
multiplies falling segments. Decay approaches sustain; release approaches
zero. Raising sustain past the current level takes effect at the next update.
The accumulator has 14 bits, with two low bits discarded at the converter.
Reusing a still-releasing voice consequently attacks from its residual level.
The Rack implementation preserves this in `Envelope::noteOn`,
`Envelope::tick` and `updateVoiceEnvelopeAndPitch`; `Voice` owns its own
`Envelope`. The existing upstream circuit vector expects a retrigger at
`0x1800` followed by increment `0x007f` to yield `0x187f`.

The [A-5 allocation and release paths, $0A76-$0B2F](https://github.com/ErroneousBosh/j106roms/blob/26926a04ff1939106820313e71e34b4ca2f67070/ic1.txt#L1555)
support POLY 2's first-free-slot rule and POLY 1's preference for a free slot
that last played the same key, otherwise the longest-released free slot.
Held slots are not stolen; released slots become eligible even while their
sound continues. Note-off searches the assignment's key identity, rather than
blindly releasing a previously used slot number. The Rack `allocateVoice`
and `noteOffInternal` retain these relationships.

## Rack boundary policy

An equal-frame end/start pair needs a deterministic host convention. Releasing
notes already held before starting their successors makes an adjacent note
available for assignment and produces a new attack edge. This convention is
not a claim about simultaneous serial MIDI messages on the original unit.
Preserve supplied frame positions and the order of genuinely separated events.

Do not manufacture a release interval or clear an envelope to make every
attack start at zero. With no intervening envelope update, a touching repeat
can legitimately inherit substantial level. The hardware's voice history and
release law can therefore make touching and gapped notes sound different.
Balanced overlap counts in the shared engine protect hosted repeated-pitch
notes; they are an adaptation of keyboard gate semantics, not a literal
hardware MIDI counter.

Regression expectations for this boundary include:

- Both event orders produce the same successor assignment at an equal-frame
  boundary, including a decayed-to-zero envelope and an exhausted voice pool.
- A release for another key, an unmatched release, and an old key's release
  after its slot was reused for a different key cannot release that assignment.
- Genuine repeated-pitch overlaps retain their gate until the matching final
  release; a zero-duration pair cannot leave a held note behind.
- Unaffected voices retain their independent envelope state, and changing a
  key does not restart a global amplitude envelope.
- POLY 1, POLY 2, Unison, sustain, ENV/GATE, frame-zero/block-end boundaries,
  and relevant host sample rates preserve the same semantic rules.

## Evidence limits

The upstream [hardware validation](../../../../../virtual-instrument-youknow/Docs/hardware-validation.md)
uses steady source measurements and explicitly does not qualify hardware
onset timing. Its [research protocol](../../../../../virtual-instrument-youknow/Docs/modeling-research-2026-09.md)
calls for independent envelope onset, segment-time and sustain captures.
The engine's intra-pass offsets are model choices; exact original-unit
converter timing and firmware-revision coverage remain unmeasured. Software
regressions establish preservation of this documented model, not universal
sample-exact agreement with every physical JUNO-106. The recording's separate
buffer-dependent timing pattern still requires an actual Reason event trace
before its full cause can be attributed.
