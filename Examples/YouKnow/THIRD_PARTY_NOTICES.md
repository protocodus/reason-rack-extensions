# Third-party notices and provenance

Protocodus' original YouKnow source and panel artwork are covered by the
[MIT license](LICENSE). The Rack Extension is built with the separately
licensed Reason Rack Extension SDK and is intended for distribution through
the authorized Reason Studios channel. Reason SDK material is not relicensed
under YouKnow's MIT license.

SDK standard artwork supplies the pitch/mod wheels, audio/CV sockets,
device-name tape, placeholder, patch-browser group, and folded patch-name field.
These remain under SDK terms, not YouKnow's MIT license.
Panel labels and section titles are rasterized from the local
macOS Arial and Arial Bold fonts; the YouKnow wordmark uses DIN Condensed Bold.
Font files are not shipped. Reason supplies the native patch/status text.
Exact inputs, hashes, mappings, and adapted sample scaffolding are recorded in
`Docs/ASSET_PROVENANCE.md`.

## Modelling references

YouKnow is an independent implementation informed by published virtual-analog
research. It does not copy or include the reference implementations associated
with these publications.

- Vadim Zavalishin, *The Art of VA Filter Design* - topology-preserving
  transforms and ladder-filter analysis.
- Tim Stilson and Julius O. Smith, *Analyzing the Moog VCF with Considerations
  for Digital Implementation* (1996) - ladder root-locus analysis.
- Antti Huovilainen, *Non-linear digital implementation of the Moog ladder
  filter* (DAFx-04), and Stefano D'Angelo and Vesa Valimaki, *Generalized Moog
  Ladder Filter: Part II* - nonlinear delay-free-loop methods.
- Vesa Valimaki, Jussi Pekonen and Juhan Nam, *Perceptually informed synthesis
  of bandlimited classical waveforms using integrated polynomial
  interpolation* (JASA, 2012) - bandlimited waveform synthesis.
- Martin Holters and Julian Parker, *A Combined Model for a Bucket Brigade
  Device and its Input and Output Filters* (DAFx-18) - bucket-brigade delay
  modelling.

## Patches

The shipped bank contains 77 patch names and parameter states created for
YouKnow by Protocodus. No third-party factory tone-memory records or archival
factory labels are included.
The source-history and sound-state comparison behind this inventory are
recorded in [the patch provenance audit](Docs/ASSET_PROVENANCE.md#patch-bank-provenance).

No firmware, ROM image, sample, impulse response, captured audio, or separately
sold sound-bank data is included.

## Trademarks

YouKnow is an independent Protocodus product. It is not affiliated with,
endorsed by, sponsored by, or licensed by Roland Corporation. Roland and Juno
are Roland Corporation trademarks; development documentation uses them only to
identify the studied historical architecture.

Reason, Reason Studios, and Rack Extension are Reason Studios AB trademarks.
They identify compatibility and do not imply endorsement beyond the Rack
Extension program.
