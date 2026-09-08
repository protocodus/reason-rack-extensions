# YouKnow user guide

Version 1.0.0f16

YouKnow is a circuit-modelled analogue polysynth from Protocodus for Reason 14
and later. It combines subtractive synthesis, stereo chorus, up to 16 voices,
93 original patches, and eight rear CV inputs.

## Install and first sound

Install and update YouKnow through your Reason Studios account and the Reason
Rack Extension browser. After installation, find **YouKnow** under Instruments
in the device palette.

1. Create YouKnow and play MIDI notes. The Init patch loads by default, and
   Reason creates a sequencer track and routes stereo audio when a suitable
   destination is available.
2. Use the patch display and browse controls to explore the 93 original
   patches. Categories include Bass, Leads, Keys, Brass, Pads, Strings, and
   Effects.
3. Shape the sound on the front. Flip the rack to adjust processing quality,
   Unit Character, Aging, or CV connections.
4. Save sounds with Reason's normal patch command. Unit Character is saved
   with the patch; Aging and processing quality are saved with the song.

## Front panel

**LFO** sets modulation rate and delayed onset. **DCO** selects octave
range, PWM source and depth, and oscillator modulation. **MIXER** contains the
pulse/saw switches and sub/noise levels. **HPF** provides four positions;
the lowest, labelled 0, retains the bass-boost setting.

**VCF** controls cutoff (FREQ), resonance (RES), envelope polarity (POL, +/−)
and amount (ENV), LFO amount (LFO), and keyboard tracking (KYBD). At high
resonance the filter can self-oscillate. **VCA** chooses envelope or gate
behavior and sets the amplifier level. **ENV** supplies attack (A), decay
(D), sustain (S), and release (R). **CHORUS** offers Off, I, II, and a
dedicated narrow I+II combination; NOISE sets its hiss level.

**Performance** contains the pitch and modulation wheels, Volume, and
performance modulation depths. **Keyboard** contains glide, key mode,
transpose, master tune, velocity response (VEL), and the 1-16 voice limit.
Clicking the already-selected Poly 1, Poly 2, or Unison button repeats the
held-key reassignment gesture.

The six-cell status strip reports processing quality, Character, and Aging.
Their editable controls are on the rear.

## Rear panel and engine quality

The rear groups four Processing Quality selectors, two Unit Model controls,
eight CV inputs, and stereo audio outputs. Settings occupy the upper half;
connections sit below them so downward cable runs leave the settings clear.

**Unit Character** varies circuit tolerances across a 0-200% range. It is
stored with each patch.

**Aging** models service drift and noise changes across a 0-100% range. New
devices start at 50%; set it to 0% for the freshly serviced state. Aging is
stored with the song, so patch browsing leaves it unchanged and existing
songs recall their saved value.

- **Oversample (Quality): 1x, 2x, 4x.** The default is 1x. Higher settings
  request more internal processing and increase CPU use; an already-high host
  sample rate can limit the applied factor. Changes, including automation,
  wait for voices and output tails to become quiet, then use a short fade.
- **Saturation (VCF Tanh): Exact, Fast, Poly.** Poly is the efficient default.
  Fast and Exact provide alternative filter calculations at higher CPU cost.
- **Early Model (Fast Early): Hermite, Cubic.** Cubic is the default; Hermite
  provides an alternative interpolation for the fast filter path.
- **Filter Solver (VCF Solver): Max, High, Normal.** Normal is the efficient
  default. High and Max spend more processing on the filter.

All four quality settings are stored with the song and survive patch changes.
Start with 1x, Poly, Cubic, and Normal for a busy rack. The combination of
16 voices and 4x is the heaviest configuration.

## Automation and Remote

All 41 sound, performance, and quality controls support Reason sequencer
automation and Remote mapping. This includes Chorus Hiss, Unit Character,
Aging, and all four rear quality selectors. Existing automation lanes retain
their assignments. The pitch and modulation wheels and sustain use Reason's
standard performance automation.

Rear controls and their readouts show Reason's automation indication; the
front status strip remains read-only. Automating Quality follows the same
quiet-tail transition policy as changing it manually.

The held-key reassignment press is a transient gesture available to Remote.
It has no separate sequencer lane. The internal preset-level trim balances
the supplied bank and is not a performance control.

## CV, tuning, and timing

The rear CV sockets form two rows: NOTE, GATE, CUTOFF, RES above VOLUME, AMP,
SUB, NOISE. The Note/Gate pair plays a monophonic CV part; MIDI remains
polyphonic up to the selected voice limit.

- **NOTE and GATE:** Note sets pitch; Gate triggers and releases the note.
  Changing Note while Gate remains high retargets the held note legato.
- **CUTOFF and RES:** CV adds to the corresponding normalized panel value.
  The result is limited to the control's 0-100% range. For example, a 50%
  cutoff setting with +0.25 CV becomes 75%; -0.25 CV makes it 25%.
- **VOLUME, AMP, SUB, and NOISE:** CV scales Volume, VCA Level, Sub, and Noise
  respectively. CV is limited to 0-1 before multiplying the panel setting:
  1 leaves it unchanged, 0.5 halves it, and 0 sets the control value to zero.
  These inputs shape the instrument's control settings, with its envelope and
  circuit response still applying.

Disconnected modulation inputs leave their panel values unchanged. Panel
edits and automation remain the base values that CV modulates. CV responds to
Reason's control updates; these inputs are not an audio-rate modulation path.

YouKnow follows Reason's master tuning preference alongside its panel Tune
setting. It reports a fixed 41-sample latency at every Quality setting.

## Patches

The supplied bank contains 93 original Protocodus patches, including Init.
Internal level trims keep browsing levels balanced without moving the visible
Volume control. Reason's categories and tags help find sounds by type and
character.

Use Reason's patch browser and patch files to manage sounds. MIDI Program
Change and SysEx file import/export are not supported.

## Troubleshooting

- **Notes arrive but there is no sound:** load Init, verify Volume and VCA
  Level, check any connected level CV sources, and confirm the audio outputs
  are connected.
- **High CPU:** select 1x, Poly, Cubic, and Normal on the rear. Reduce Voices
  for dense arrangements.
- **A Quality change seems delayed:** release all notes and let the output
  tail settle so the requested change can take effect.
- **No CV response:** check the intended socket and the source range. A
  pitched CV sequence needs both Note and Gate connections; level CV scales
  the current panel setting, so it cannot raise a control already set to zero.
- **A problem persists:** visit
  [protocodus.cz/product/youknow](https://protocodus.cz/product/youknow/) or email
  [protocodus+support@proton.me](mailto:protocodus+support@proton.me). Include the YouKnow and
  Reason versions, operating system, computer model, audio sample rate, patch
  name, and steps to reproduce the problem.

## Privacy and legal

YouKnow performs audio processing offline and contains no telemetry or network
client. The PDF manual includes the MIT notice for Protocodus-authored source
and artwork, the privacy notice, and third-party provenance. Their maintained
source copies are `LICENSE`, `PRIVACY.md`, and `THIRD_PARTY_NOTICES.md`.
Reason Studios' applicable customer terms govern Shop delivery; the MIT notice
does not relicense Reason SDK material.

YouKnow is an independent Protocodus product. It is not affiliated with,
endorsed by, sponsored by, or licensed by Roland Corporation. Reason and Rack
Extension identify the compatible Reason Studios platform.
