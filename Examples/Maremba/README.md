# Maremba (`cz.protocodus.Maremba`)

**Maremba** is a physically modelled mallet-percussion instrument Rack Extension for Reason, by **Protocodus**.

It uses no samples. Every note is synthesised in real time from a modal model of a struck bar (or a plucked kalimba tine), with a resonator tube or gourd, a mirliton buzz membrane, a mallet contact model, sympathetic resonance between the bars, a frame body and a three-microphone mixer.

---

## The Four Instruments

The Model selector switches between four instruments. Each one has its own overtone ratios, damping, resonator, clack and frame-body tuning (`DSP/MarimbaModel.h`). None of them limits the playable key range.

### 1. Imperial Rosewood 5.0 (concert marimba)
- **Bars**: rosewood with low internal damping and long sustain (base fundamental decay 3.0 s).
- **Overtones**: concert undercut tuning, 1 : 4 : 10 : 16 : 22.4 (first five modes).
- **Resonators**: brass tubes, Q ≈ 13.

### 2. Mayan Padauk 4.3 (Mesoamerican marimba)
- **Bars**: padauk. Damping is higher, so the decay is tighter and punchier (base 2.0 s).
- **Overtones**: 1 : 4 : 9.8 : 15.6 : 21.4.
- **Resonators**: cedar soundboxes, Q ≈ 10.5.

### 3. Balafon Ancestral (West African balafon)
- **Bars**: fire-cured hardwood with high internal friction (base 1.6 s).
- **Overtones**: 1 : 4 : 9.6 : 14.1 : 19.5.
- **Resonators**: calabash gourds (Q ≈ 9), each with a vibrating mirliton membrane that buzzes on strong strokes.

### 4. Kalimba Artisan (thumb piano)
- **Tines**: steel cantilever tines with clamped-free beam overtones, 1 : 6.27 : 17.6 : 34.4 : 56.8, and long sustain (base 4.0 s).
- **Body**: acacia soundbox (Q ≈ 10).
- With this model the Striker selector picks thumb techniques instead of mallets: flesh, natural thumb, thumbnail, thumb pick.

---

## Sound Engine

- **Modal bar**: 8 transverse modes per voice, plus a slightly detuned twin of the fundamental that gives the slow beating of real wood grain. Above middle C the overtone ratios of the marimba models move gradually toward those of an un-undercut free bar. Decay depends on the register, and higher modes are damped by radiation and internal loss. The modal bank runs in double precision, so tuning stays accurate at every sample rate and oversampling factor.
- **Mallet contact**: a pulse whose contact time and shape depend on the striker type, Mallet Hardness and velocity. It adds a short shock spike, a small rebound, yarn friction noise and a band-passed clack noise burst. Strike Position shapes which modes are excited.
- **Resonator**: a tube or gourd driven by the bar's fundamental. The drive is one-way: the resonator colours and extends the sound but does not feed back into the bar. Resonator Tune detunes it by ±50 cents and Resonator Coupling sets how strongly it is driven.
- **Mirliton buzz**: on the Balafon the membrane buzzes above a displacement threshold. The other models get a gentler membrane only when Mirliton Buzz is above 0.2.
- **Sympathetic halo**: 24 resonators (C3–B5) pick up the notes being played, but only at consonant intervals (unison, octave, fifth, fourth, major third).
- **Frame body bloom**: a low-frequency resonance of the frame, excited by the bars.
- **Acoustic artifacts / Strike Variance**: random variation of strike position, hardness, micro-tuning, friction and cord rattle from stroke to stroke.

## Playing

- **Bars ring freely.** Note-off does not damp a bar, just as on a real marimba. When Reason's transport stops, every sounding bar is damped by hand with a gentle, model-specific decay of roughly 0.3–0.6 s.
- **Pitch bend** covers ±2 semitones and also bends bars that are already ringing. The **mod wheel** adds up to 0.35 of mallet hardness.
- **Master Tune** is ±100 cents, and Reason's global master tune is always respected. **Key Detune Drift** detunes each key by a fixed per-key amount, up to ±100 cents.
- **Polyphony** is 8, 16 or 24 voices. When a voice is stolen it fades out over a few milliseconds instead of being cut, and lowering the polyphony fades out the excess voices.
- **Velocity curves**: Soft (√v, a light touch plays loud), Linear, Hard (v^1.55, needs a firm touch), Expressive (smoothstep).
- **CV inputs**: Note and Gate (sample-accurate, auto-routed; Gate CV sets the velocity), plus Mallet Hardness, Strike Position, Resonator Coupling, Sympathetic Halo and Master Volume modulation. Modulation CV is added to the knob value and clamped.
- The **Note On lamp** on the front and folded front flashes on every strike.

## Signal Flow

1. **Three microphones**: Close (keyboard-panned), Far Room (through a small wooden-room reverb) and a mono Piezo contact pickup, mixed by their level knobs.
2. **Stereo Width**: mid/side width on the summed main bus. 0 is mono, 1 is natural and 2 is wide.
3. **Compressor**: gentle bus glue with an effective ratio of about 1.2:1–1.33:1 and a user-set attack (1–50 ms) and release (20–500 ms).
4. **Preamp**: soft saturation above −4.4 dBFS (Drive) with a tilt EQ (Warmth).
5. **Master Volume**, followed by the **Main L/R** outputs. If only one main jack is connected, it carries the mono sum.
6. **Direct outputs**: Close L/R, Far L/R (including the room) and Piezo. They are tapped before the level knobs, compressor and preamp, then scaled by the main mix gain and the master volume.

**Oversampling**: 2x, 4x or 8x at every host sample rate. Rendered level, pitch and decay are the same at every setting. Changing the setting fades out the sound for about 5 ms and restarts the engine at the new rate. 8x at 96/192 kHz is very CPU-heavy.

---

## Building and Testing

```bash
# Full verification suite: Lua/metadata, patches, panel geometry, DSP engine,
# the Rack wrapper through a JBox host shim, and all factory patches
bash Tests/run_all_tests.sh

# Store build (runs the suite first). Outside this SDK checkout, point JUKEBOX_SDK_DIR at an SDK 5 root.
python3 build45.py universal45

# Re-render the panels (needs Pillow, numpy, scipy and the macOS DIN fonts)
python3 Design/render_panels.py
```
