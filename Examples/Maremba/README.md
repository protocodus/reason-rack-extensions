# Maremba (`cz.protocodus.Maremba`)

**Maremba** is a flagship physical-modeled marimba instrument Rack Extension for Reason 14, engineered by **Protocodus**.

It uses **100% real-time mathematical physical modeling with zero samples**, faithfully simulating the vibration of undercut wooden bars, quarter-wave acoustic resonator tubes, vibrating calabash gourd mirliton membranes, non-linear Hertzian mallet contact dynamics, sympathetic bar resonance, and organic performance imperfections.

---

## The Three Instruments

Maremba features three distinct, acoustically modelled marimbas, each with unique materials, geometry, overtone structures, and visual art:

### 1. Imperial Rosewood 5.0 (Concert Grand)
- **Range**: 5.0 Octaves ($C_2$ to $C_7$, 61 keys).
- **Bar Material**: Aged Honduran Rosewood (*Dalbergia stevensonii*). Dense ($950\text{ kg/m}^3$), low internal friction, high elasticity.
- **Overtones**: Harmonic concert undercut tuning ($1.00 : 4.00 : 10.00 : 16.4 : 24.0$).
- **Acoustic Resonators**: Gold-finished drawn brass oval tubes with high acoustic Q ($Q \approx 28$).
- **Sound Character**: Majestic, dark, deep singing bass fundamental, crystalline highs, and long sustain.
- **Visual Art**: Elegant Art Deco gold geometric engravings and lustrous dark rosewood finish.

### 2. Mayan Padauk 4.3 (Artisan Mesoamerican Marimba)
- **Range**: 4.3 Octaves ($A_2$ to $C_7$, 52 keys).
- **Bar Material**: Quarter-sawn Mexican Padauk (*Hormiguillo* / *Pterocarpus soyauxii*). Medium density, punchy acoustic bark.
- **Overtones**: Artisan traditional tuning ($1.00 : 3.94 : 9.45 : 15.6 : 22.2$).
- **Acoustic Resonators**: Handcrafted square cedar wood soundboxes with natural beeswax tuning plugs ($Q \approx 18$).
- **Sound Character**: Warm, earthy, vocal midrange, immediate transient punch, and organic wood projection.
- **Visual Art**: Hand-carved Mayan stepped fretwork (*Xicalcoliuhqui*) and solar motifs.

### 3. Balafon Ancestral (West African Gourd & Mirliton Balafon)
- **Range**: Extended diatonic/chromatic balafon ($F_2$ to $C_6$).
- **Bar Material**: Fire-cured African Ironwood (*Kéne*). Hard, dry, raw percussive bark.
- **Overtones**: Inharmonic ancestral intervals ($1.00 : 3.80 : 8.65 : 14.1 : 20.0$).
- **Acoustic Resonators**: Dried calabash gourds fitted with vibrating spider-egg silk / bamboo paper mirliton membranes.
- **Sound Character**: Sizzling, raw, energetic village percussion with dynamic buzzing overtones and organic ping.
- **Visual Art**: West African mudcloth (*Bogolanfini*) tribal zig-zags and diamond patterns with leather-tied bamboo frame.

---

## Physical Modeling Engine Details

- **Modal Undercut Bar Synthesis**: 5 coupled modal resonators per voice calculating transverse bending, torsional modes, and longitudinal clack.
- **Hertzian Mallet Contact**: Dynamic non-linear contact duration $T_c \approx 0.6\text{ ms} \dots 4.2\text{ ms}$ that hardens with velocity ($F \propto v^{1.35}$), modeling soft yarn, medium cord, and hard rosewood/acrylic mallets.
- **Quarter-Wave Resonator Coupling**: Bidirectional acoustic impedance match between the bar and the air column beneath.
- **Vibrating Mirliton Buzz**: Non-linear membrane threshold modeling the iconic buzz of traditional African balafons.
- **Natural Random Artifacts**: Strike position jitter, human firmness variance, wood grain micro-detuning, and suspension cord rattle.

---

## Signal Flow & Effects

- **3-Microphone Mixer**:
  - **Close Mic**: Intimate mallet contact with keyboard stereo spread across panorama.
  - **Far Room Mic**: Recital hall acoustic reflections and diffuse resonator bloom.
  - **Piezo Pickup**: Direct contact transducer on frame rails for hyper-fast transient bite.
  - **Stereo Width**: Adjustable stereo soundstage width.
- **Analog-Modeled Preamp**:
  - Transformer and tube saturation warmth.
  - Baxandall tilt tone control: warm low-end body vs silky mallet sheen.
- **Percussion Compressor**:
  - Dynamic range compressor with fast auto-attack and program-dependent release.
- **Multi-Stage Oversampling Engine**:
  - **2x (Studio Standard - Default)**: Pristine anti-aliased non-linearities with low CPU.
  - **4x (High Resolution)**: Audiophile transient definition.
  - **8x (Pristine Archival)**: Ultra-high precision modeling.

---

## Building and Testing

```bash
# Build universal bundle (32-bit & 64-bit Testing and Deployment targets)
python3 build45.py universal45 4

# Run standalone DSP verification suite
clang++ -std=c++17 -O3 -I. -IDSP DSP/MarembaVoice.cpp DSP/MarembaEngine.cpp Tests/test_dsp.cpp -o Tests/test_dsp
./Tests/test_dsp
```
