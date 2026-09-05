#!/usr/bin/env python3
"""Generate YouKnow's original sounds and metadata."""

import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


PROJECT = Path(__file__).resolve().parent.parent
PUBLIC = PROJECT / "Resources" / "Public"
LEVELS_PATH = PROJECT / "Design" / "preset_levels.json"
PRODUCT_ID = "cz.protocodus.YouKnow"
CHORUS_NOISE_DEFAULT = 0.29858038
STEPPED = {
    "keyMode", "pwmMode", "range", "highPass", "envPolarity", "vcaMode",
    "chorus", "transpose", "polyphony",
}

# Original sounds retained from the initial Rack port; see Docs/ASSET_PROVENANCE.md.
FEATURED_PATCHES = {
    "Init.repatch",
    "Bass - Rubber Pulse.repatch",
    "Bass Short and Hard.repatch",
    "Brass - Bright Stab.repatch",
    "Brass - Soft Ensemble.repatch",
    "Effects - Rising Voltage.repatch",
    "Effects - Storm Signal.repatch",
    "Glass Pad.repatch",
    "Hollow Fifths.repatch",
    "Keys - Plucked Keys.repatch",
    "Keys - Velvet Electric.repatch",
    "Organ.repatch",
    "Pads - Lunar Drift.repatch",
    "Percussive Comb.repatch",
    "Self-Oscillating Sine.repatch",
    "Slow Sweep.repatch",
    "Strings - Dark Bowed.repatch",
    "Strings - PWM Ensemble.repatch",
    "Vibrato Lead.repatch",
}

# path, Reason category, Reason tags, overrides on Init
PRESETS = (
    (
        "Bass/Sub Current.repatch", ("Bass", "Synth"),
        ("Analog", "Deep", "Sub"),
        dict(volume=.66, benderDco=.24, benderVcf=.08, portamento=.03,
             keyMode=2, pwm=.46, range=0, saw=False, pulse=True, sub=.80,
             highPass=0, cutoff=.18, resonance=.08, vcfEnv=.36,
             keyFollow=.14, vcaLevel=.76, decay=.40, sustain=.72,
             release=.18, velocity=.20),
    ),
    (
        "Bass/Acid Lantern.repatch", ("Bass", "Synth"),
        ("Analog", "Dirty", "Punchy"),
        dict(volume=.56, benderDco=.32, benderVcf=.36, portamento=.08,
             keyMode=2, lfoRate=.34, pwm=.41, pwmMode=0, range=0,
             pulse=True, sub=.10, cutoff=.23, resonance=.76, vcfEnv=.82,
             keyFollow=.20, vcaLevel=.72, decay=.39, sustain=.03,
             release=.14, velocity=.25, calibration=.55),
    ),
    (
        "Bass/Wide Dub.repatch", ("Bass", "Synth"),
        ("Deep", "Mellow", "Wide"),
        dict(volume=.62, benderDco=.25, lfoRate=.16, pwm=.66, pwmMode=0,
             range=0, saw=False, pulse=True, sub=.50, highPass=0,
             cutoff=.30, resonance=.16, vcfEnv=.32, vcfLfo=.03,
             keyFollow=.28, vcaLevel=.74, attack=.03, decay=.55,
             sustain=.52, release=.45, chorus=1, velocity=.15,
             chorusNoise=.75),
    ),
    (
        "Bass/Wire Pluck.repatch", ("Bass", "Synth"),
        ("Bright", "Percussive", "Tight"),
        dict(volume=.64, benderDco=.28, benderVcf=.20, keyMode=1, pwm=.35,
             pulse=True, sub=.10, noise=.02, highPass=3, cutoff=.36,
             resonance=.48, vcfEnv=.74, keyFollow=.45, vcaLevel=.72,
             decay=.18, sustain=.00, release=.10, velocity=.55,
             calibration=.45),
    ),
    (
        "Leads/Neon Glide.repatch", ("Synth", "Leads"),
        ("Analog", "Glide", "Wide"),
        dict(volume=.62, benderDco=.42, benderVcf=.18, benderLfo=.30,
             portamento=.28, keyMode=2, lfoRate=.38, lfoDelay=.32,
             pwm=.55, pwmMode=0, pulse=True, sub=.04, cutoff=.46,
             resonance=.24, vcfEnv=.42, vcfLfo=.04, keyFollow=.68,
             vcaLevel=.76, attack=.02, decay=.42, sustain=.62, release=.28,
             chorus=1, calibration=.55, chorusNoise=.78),
    ),
    (
        "Leads/Pulse Whistle.repatch", ("Synth", "Leads"),
        ("Bright", "Glassy", "Monophonic"),
        dict(volume=.58, benderDco=.48, benderVcf=.20, portamento=.14,
             keyMode=2, lfoRate=.28, lfoDelay=.20, dcoLfo=.02, pwm=.84,
             range=2, saw=False, pulse=True, highPass=2, cutoff=.57,
             resonance=.66, vcfEnv=.30, vcfLfo=.02, keyFollow=.82,
             vcaLevel=.70, attack=.01, decay=.36, sustain=.74, release=.34,
             calibration=.45),
    ),
    (
        "Leads/Copper Reed.repatch", ("Synth", "Leads"),
        ("Analog", "Organic", "Warm"),
        dict(volume=.64, benderDco=.35, benderVcf=.16, benderLfo=.48,
             portamento=.07, keyMode=2, lfoRate=.44, lfoDelay=.38, pwm=.43,
             pulse=True, sub=.07, noise=.02, cutoff=.35, resonance=.36,
             vcfEnv=.60, keyFollow=.62, vcaLevel=.74, attack=.10,
             decay=.48, sustain=.58, release=.32, velocity=.12,
             calibration=.60),
    ),
    (
        "Leads/Laser Thread.repatch", ("Synth", "Leads"),
        ("Bright", "Fast", "Glide"),
        dict(volume=.65, benderDco=.50, benderVcf=.35, portamento=.18,
             keyMode=2, lfoRate=.78, lfoDelay=.05, dcoLfo=.12, pwm=.32,
             range=2, noise=.01, highPass=2, cutoff=.63, resonance=.40,
             envPolarity=0, vcfEnv=.45, vcfLfo=.22, keyFollow=.72,
             vcaLevel=.70, decay=.32, sustain=.68, release=.24, chorus=1,
             chorusNoise=.70),
    ),
    (
        "Keys/Midnight Tines.repatch", ("Keys", "Electric Piano"),
        ("Mellow", "Percussive", "Warm"),
        dict(volume=.66, benderDco=.18, benderVcf=.14, lfoRate=.30,
             lfoDelay=.20, pwm=.67, saw=False, pulse=True, sub=.12,
             noise=.01, highPass=2, cutoff=.50, resonance=.30, vcfEnv=.55,
             keyFollow=.78, vcaLevel=.74, decay=.37, sustain=.22,
             release=.30, chorus=2, velocity=.62, calibration=.45,
             chorusNoise=.70),
    ),
    (
        "Keys/Bell Current.repatch", ("Mallets", "Bells & Vibes"),
        ("Bright", "Glassy", "Percussive"),
        dict(volume=.58, benderDco=.16, benderVcf=.08, lfoRate=.52,
             pwm=.78, range=2, saw=False, pulse=True, noise=.05,
             highPass=3, cutoff=.61, resonance=.58, vcfEnv=.66,
             keyFollow=.92, vcaLevel=.68, decay=.20, sustain=.00,
             release=.38, chorus=1, velocity=.52, chorusNoise=.65),
    ),
    (
        "Keys/Warm Poly.repatch", ("Keys", "Misc"),
        ("Analog", "Warm", "Wide"),
        dict(volume=.66, benderDco=.18, benderVcf=.16, lfoRate=.22,
             lfoDelay=.32, dcoLfo=.01, pwm=.52, pwmMode=0, pulse=True,
             sub=.10, highPass=1, cutoff=.44, resonance=.12, vcfEnv=.34,
             vcfLfo=.02, keyFollow=.72, vcaLevel=.72, attack=.04,
             decay=.46, sustain=.62, release=.36, chorus=1, velocity=.42,
             chorusNoise=.76),
    ),
    (
        "Keys/Percussive Mallet.repatch", ("Mallets", "Misc"),
        ("Organic", "Percussive", "Short"),
        dict(volume=.58, benderDco=.16, benderVcf=.18, pwm=.38,
             pulse=True, noise=.05, highPass=2, cutoff=.40, resonance=.70,
             vcfEnv=.78, keyFollow=.50, vcaLevel=.68, decay=.15,
             sustain=.00, release=.14, velocity=.68, calibration=.42),
    ),
    (
        "Brass/Solo Copper.repatch", ("Wind", "Brass"),
        ("Analog", "Organic", "Warm"),
        dict(volume=.63, benderDco=.36, benderVcf=.18, benderLfo=.38,
             portamento=.06, keyMode=2, lfoRate=.36, lfoDelay=.42,
             pwm=.46, pulse=True, sub=.06, noise=.01, cutoff=.31,
             resonance=.18, vcfEnv=.50, vcfLfo=.02, keyFollow=.58,
             vcaLevel=.72, attack=.24, decay=.55, sustain=.80, release=.38,
             velocity=.20, calibration=.55),
    ),
    (
        "Brass/Muted Circuit.repatch", ("Wind", "Brass"),
        ("Mellow", "Soft", "Synthetic"),
        dict(volume=.64, benderDco=.25, benderVcf=.26, keyMode=1,
             lfoRate=.27, lfoDelay=.25, dcoLfo=.01, pwm=.39, saw=False,
             pulse=True, sub=.03, noise=.04, highPass=2, cutoff=.30,
             resonance=.44, vcfEnv=.72, keyFollow=.60, vcaLevel=.74,
             attack=.05, decay=.30, sustain=.32, release=.22, velocity=.58),
    ),
    (
        "Brass/Stadium Stack.repatch", ("Wind", "Brass"),
        ("Fat", "Punchy", "Wide"),
        dict(volume=.55, benderDco=.38, benderVcf=.20, benderLfo=.26,
             portamento=.04, keyMode=2, lfoRate=.33, lfoDelay=.28,
             dcoLfo=.01, pwm=.58, pwmMode=0, pulse=True, sub=.12,
             cutoff=.45, resonance=.10, vcfEnv=.60, vcfLfo=.03,
             keyFollow=.52, vcaLevel=.68, attack=.10, decay=.46,
             sustain=.70, release=.34, chorus=2, velocity=.18,
             calibration=.58, chorusNoise=.75),
    ),
    (
        "Brass/Slow Fanfare.repatch", ("Wind", "Brass"),
        ("Long", "Soft", "Warm"),
        dict(volume=.58, benderDco=.26, benderVcf=.18, benderLfo=.22,
             lfoRate=.21, lfoDelay=.35, dcoLfo=.01, pwm=.50, pwmMode=0,
             pulse=True, sub=.04, noise=.02, cutoff=.28, resonance=.16,
             vcfEnv=.62, keyFollow=.48, vcaLevel=.68, attack=.52,
             decay=.70, sustain=.84, release=.62, chorus=1, velocity=.25,
             calibration=.58, chorusNoise=.80),
    ),
    (
        "Pads/Aurora Veil.repatch", ("Synth", "Pads"),
        ("Airy", "Atmospheric", "Evolving"),
        dict(volume=.58, benderDco=.18, benderVcf=.20, benderLfo=.22,
             lfoRate=.12, lfoDelay=.45, dcoLfo=.03, pwm=.68, pwmMode=0,
             range=2, saw=False, pulse=True, noise=.08, highPass=2,
             cutoff=.46, resonance=.34, vcfEnv=.24, vcfLfo=.16,
             keyFollow=.38, vcaLevel=.66, attack=.68, decay=.74,
             sustain=.86, release=.80, chorus=2, velocity=.22,
             calibration=.62, chorusNoise=.68),
    ),
    (
        "Pads/Warm Horizon.repatch", ("Synth", "Pads"),
        ("Lush", "Spacious", "Warm"),
        dict(volume=.60, benderDco=.18, benderVcf=.14, benderLfo=.20,
             lfoRate=.09, lfoDelay=.36, dcoLfo=.03, pwm=.54, pwmMode=0,
             pulse=True, sub=.12, noise=.02, cutoff=.34, resonance=.12,
             vcfEnv=.28, vcfLfo=.10, keyFollow=.42, vcaLevel=.68,
             attack=.48, decay=.70, sustain=.80, release=.74, chorus=1,
             velocity=.20, calibration=.55, chorusNoise=.75),
    ),
    (
        "Pads/Moon Choir.repatch", ("Synth", "Pads"),
        ("Airy", "Long", "Spacious"),
        dict(volume=.55, benderDco=.20, benderVcf=.18, benderLfo=.24,
             lfoRate=.14, lfoDelay=.55, dcoLfo=.04, pwm=.80, pwmMode=0,
             range=2, saw=False, pulse=True, noise=.10, highPass=2,
             cutoff=.48, resonance=.28, vcfEnv=.18, vcfLfo=.18,
             keyFollow=.35, vcaLevel=.64, attack=.75, decay=.82,
             sustain=.90, release=.88, chorus=2, velocity=.16,
             calibration=.62, chorusNoise=.65),
    ),
    (
        "Pads/Drifting Organ.repatch", ("Synth", "Pads"),
        ("Analog", "Evolving", "Lush"),
        dict(volume=.58, benderDco=.18, benderVcf=.12, benderLfo=.18,
             lfoRate=.11, lfoDelay=.40, dcoLfo=.02, pwm=.60, pwmMode=0,
             pulse=True, sub=.35, cutoff=.52, resonance=.08, vcfEnv=.00,
             vcfLfo=.08, keyFollow=.70, vcaLevel=.68, attack=.32,
             decay=.68, sustain=1.00, release=.65, chorus=2, velocity=.15,
             chorusNoise=.72),
    ),
    (
        "Strings/Silk Section.repatch", ("Strings", "Ensemble"),
        ("Lush", "Soft", "Wide"),
        dict(volume=.64, benderDco=.22, benderVcf=.10, benderLfo=.18,
             lfoRate=.18, lfoDelay=.26, dcoLfo=.01, pwm=.60, pwmMode=0,
             pulse=True, sub=.04, noise=.01, highPass=2, cutoff=.56,
             resonance=.08, vcfEnv=.18, vcfLfo=.03, keyFollow=.52,
             vcaLevel=.72, attack=.24, decay=.56, sustain=.85, release=.50,
             chorus=2, velocity=.24, chorusNoise=.76),
    ),
    (
        "Strings/Cello Current.repatch", ("Strings", "Solo"),
        ("Dark", "Organic", "Warm"),
        dict(volume=.62, benderDco=.24, benderVcf=.12, benderLfo=.20,
             keyMode=1, lfoRate=.23, lfoDelay=.36, dcoLfo=.01, pwm=.45,
             range=0, pulse=True, sub=.18, noise=.02, cutoff=.30,
             resonance=.20, vcfEnv=.32, vcfLfo=.03, keyFollow=.62,
             vcaLevel=.70, attack=.42, decay=.64, sustain=.74, release=.58,
             chorus=1, velocity=.36, calibration=.55, chorusNoise=.82),
    ),
    (
        "Strings/Frozen Harmonics.repatch", ("Strings", "Synth"),
        ("Airy", "Glassy", "Long"),
        dict(volume=.56, benderDco=.18, benderVcf=.10, benderLfo=.24,
             lfoRate=.15, lfoDelay=.40, dcoLfo=.02, pwm=.78, range=2,
             saw=False, pulse=True, noise=.02, highPass=3, cutoff=.60,
             resonance=.40, vcfEnv=.22, vcfLfo=.07, keyFollow=.74,
             vcaLevel=.65, attack=.55, decay=.70, sustain=.74, release=.72,
             chorus=2, velocity=.18, calibration=.60, chorusNoise=.70),
    ),
    (
        "Strings/Short Bow.repatch", ("Strings", "Synth"),
        ("Analog", "Short", "Synthetic"),
        dict(volume=.64, benderDco=.24, benderVcf=.14, benderLfo=.18,
             lfoRate=.30, lfoDelay=.28, dcoLfo=.01, pwm=.42, pulse=True,
             sub=.07, noise=.03, cutoff=.41, resonance=.18, vcfEnv=.46,
             keyFollow=.58, vcaLevel=.70, attack=.12, decay=.40,
             sustain=.62, release=.35, chorus=1, velocity=.35,
             chorusNoise=.78),
    ),
    (
        "Effects/Broken Telemetry.repatch", ("FX", "Sound FX"),
        ("Glitchy", "Noisy", "Weird"),
        dict(volume=.60, benderDco=.45, benderVcf=.35, benderLfo=.30,
             portamento=.05, keyMode=2, lfoRate=.84, dcoLfo=.32, pwm=.73,
             pwmMode=0, range=2, saw=False, pulse=True, noise=.24,
             highPass=2, cutoff=.62, resonance=.55, envPolarity=1,
             vcfEnv=.34, vcfLfo=.55, keyFollow=.16, vcaLevel=.62,
             attack=.08, decay=.48, sustain=.46, release=.52, chorus=1,
             transpose=24, calibration=.64, chorusNoise=.86),
    ),
    (
        "Effects/Gravity Well.repatch", ("FX", "Synth FX"),
        ("Atmospheric", "Dark", "Glide"),
        dict(volume=.52, benderDco=.40, benderVcf=.30, benderLfo=.25,
             portamento=.62, keyMode=2, lfoRate=.05, dcoLfo=.18, pwm=.56,
             pwmMode=0, range=0, pulse=True, sub=.10, noise=.06,
             highPass=0, cutoff=.26, resonance=.80, envPolarity=1,
             vcfEnv=.72, vcfLfo=.38, keyFollow=.08, vcaLevel=.66,
             attack=.28, decay=.74, sustain=.50, release=.68, chorus=2,
             calibration=.65, chorusNoise=.85),
    ),
    (
        "Effects/Circuit Rain.repatch", ("FX", "Textures"),
        ("Atmospheric", "Evolving", "Noisy"),
        dict(volume=.50, benderDco=.18, benderVcf=.25, lfoRate=.55,
             dcoLfo=.04, saw=False, pulse=False, noise=.88, highPass=3,
             cutoff=.55, resonance=.38, vcfEnv=.30, vcfLfo=.68,
             keyFollow=.05, vcaLevel=.62, attack=.12, decay=.45,
             sustain=.30, release=.72, chorus=2, calibration=.60,
             chorusNoise=.80),
    ),
    (
        "Effects/Falling Star.repatch", ("FX", "Synth FX"),
        ("Evolving", "Glide", "Long"),
        dict(volume=.60, benderDco=.42, benderVcf=.35, benderLfo=.30,
             portamento=.35, keyMode=2, lfoRate=.08, dcoLfo=.12, pwm=.70,
             pwmMode=0, range=2, pulse=True, highPass=2, cutoff=.55,
             resonance=.55, envPolarity=0, vcfEnv=.65, vcfLfo=.22,
             keyFollow=.30, vcaLevel=.62, attack=.48, decay=.80,
             sustain=.55, release=.84, chorus=1, transpose=24,
             calibration=.62, chorusNoise=.78),
    ),
)


UNIVERSAL_PRESETS = (
    (
        "Bass/Solid Saw Bass.repatch", ("Bass", "Synth"),
        ("Analog", "Punchy", "Tight"),
        dict(volume=.64, benderDco=.32, benderVcf=.18, keyMode=1, range=0,
             saw=True, pulse=False, sub=.38, highPass=0, cutoff=.27,
             resonance=.18, vcfEnv=.58, keyFollow=.24, vcaLevel=.74,
             decay=.32, sustain=.18, release=.12, velocity=.28),
    ),
    (
        "Bass/Rounded Sub Bass.repatch", ("Bass", "Synth"),
        ("Deep", "Mellow", "Sub"),
        dict(volume=.62, benderDco=.26, benderVcf=.10, keyMode=0, pwm=.54,
             range=0, saw=False, pulse=True, sub=.74, highPass=0,
             cutoff=.22, resonance=.10, vcfEnv=.34, keyFollow=.16,
             vcaLevel=.76, attack=.01, decay=.48, sustain=.58, release=.20,
             velocity=.20),
    ),
    (
        "Bass/Picked Pulse Bass.repatch", ("Bass", "Synth"),
        ("Percussive", "Punchy", "Tight"),
        dict(volume=.60, benderDco=.30, benderVcf=.22, keyMode=1, pwm=.38,
             range=0, saw=False, pulse=True, sub=.22, noise=.02,
             highPass=1, cutoff=.36, resonance=.32, vcfEnv=.72,
             keyFollow=.38, vcaLevel=.72, decay=.19, sustain=.00,
             release=.10, velocity=.62),
    ),
    (
        "Bass/Soft Mono Bass.repatch", ("Bass", "Synth"),
        ("Mellow", "Soft", "Warm"),
        dict(volume=.62, benderDco=.34, benderVcf=.14, portamento=.05,
             keyMode=2, pwm=.48, range=0, saw=True, pulse=True, sub=.18,
             highPass=1, cutoff=.25, resonance=.12, vcfEnv=.30,
             keyFollow=.30, vcaLevel=.71, attack=.04, decay=.56,
             sustain=.66, release=.25, velocity=.30),
    ),
    (
        "Bass/Punchy Dual Bass.repatch", ("Bass", "Synth"),
        ("Analog", "Fat", "Punchy"),
        dict(volume=.58, benderDco=.36, benderVcf=.24, keyMode=2, pwm=.43,
             range=0, saw=True, pulse=True, sub=.28, highPass=1, cutoff=.31,
             resonance=.26, vcfEnv=.68, keyFollow=.26, vcaLevel=.70,
             decay=.24, sustain=.06, release=.10, velocity=.45),
    ),
    (
        "Bass/Octave Floor Bass.repatch", ("Bass", "Synth"),
        ("Deep", "Fat", "Sub"),
        dict(volume=.60, benderDco=.28, benderVcf=.12, keyMode=0, range=1,
             saw=True, pulse=False, sub=.82, highPass=0, cutoff=.34,
             resonance=.08, vcfEnv=.38, keyFollow=.34, vcaLevel=.68,
             decay=.40, sustain=.50, release=.18, velocity=.22),
    ),
    (
        "Bass/Clean Pulse Bass.repatch", ("Bass", "Synth"),
        ("Clean", "Mellow", "Tight"),
        dict(volume=.63, benderDco=.28, benderVcf=.14, keyMode=1, pwm=.61,
             range=0, saw=False, pulse=True, sub=.30, highPass=1,
             cutoff=.30, resonance=.12, vcfEnv=.44, keyFollow=.30,
             vcaLevel=.74, decay=.38, sustain=.42, release=.15,
             velocity=.35),
    ),
    (
        "Bass/Steady Poly Bass.repatch", ("Bass", "Synth"),
        ("Analog", "Deep", "Warm"),
        dict(volume=.61, benderDco=.24, benderVcf=.12, keyMode=0,
             lfoRate=.18, lfoDelay=.30, dcoLfo=.01, pwm=.50, pwmMode=0,
             range=0, saw=True, pulse=True, sub=.12, highPass=1, cutoff=.35,
             resonance=.10, vcfEnv=.32, keyFollow=.42, vcaLevel=.70,
             attack=.02, decay=.50, sustain=.72, release=.24, velocity=.25),
    ),
    (
        "Brass/Classic Poly Brass.repatch", ("Wind", "Brass"),
        ("Analog", "Punchy", "Warm"),
        dict(volume=.62, benderDco=.28, benderVcf=.18, benderLfo=.20,
             keyMode=1, pwm=.44, saw=True, pulse=True, cutoff=.40,
             resonance=.12, vcfEnv=.60, keyFollow=.52, vcaLevel=.70,
             attack=.08, decay=.42, sustain=.62, release=.28, velocity=.32),
    ),
    (
        "Brass/Soft Brass.repatch", ("Wind", "Brass"),
        ("Soft", "Warm", "Wide"),
        dict(volume=.60, benderDco=.24, benderVcf=.14, benderLfo=.18,
             lfoRate=.18, lfoDelay=.30, dcoLfo=.01, pwm=.52, pwmMode=0,
             saw=True, pulse=True, cutoff=.32, resonance=.10, vcfEnv=.48,
             keyFollow=.50, vcaLevel=.70, attack=.20, decay=.56,
             sustain=.76, release=.42, chorus=1, velocity=.28),
    ),
    (
        "Brass/Open Brass.repatch", ("Wind", "Brass"),
        ("Bright", "Punchy", "Synthetic"),
        dict(volume=.60, benderDco=.28, benderVcf=.20, benderLfo=.18,
             keyMode=1, pwm=.39, saw=True, pulse=True, highPass=2,
             cutoff=.52, resonance=.15, vcfEnv=.70, keyFollow=.60,
             vcaLevel=.70, attack=.03, decay=.32, sustain=.38, release=.20,
             velocity=.45),
    ),
    (
        "Brass/Mono Brass.repatch", ("Wind", "Brass"),
        ("Analog", "Monophonic", "Warm"),
        dict(volume=.60, benderDco=.38, benderVcf=.20, benderLfo=.30,
             portamento=.05, keyMode=2, lfoRate=.32, lfoDelay=.34,
             dcoLfo=.01, pwm=.46, saw=True, pulse=True, sub=.05,
             cutoff=.35, resonance=.22, vcfEnv=.57, keyFollow=.58,
             vcaLevel=.71, attack=.14, decay=.48, sustain=.70, release=.34,
             velocity=.18),
    ),
    (
        "Brass/Short Brass Stab.repatch", ("Wind", "Brass"),
        ("Bright", "Punchy", "Short"),
        dict(volume=.59, benderDco=.26, benderVcf=.24, keyMode=1, pwm=.42,
             saw=True, pulse=True, noise=.01, highPass=2, cutoff=.45,
             resonance=.18, vcfEnv=.76, keyFollow=.54, vcaLevel=.70,
             decay=.21, sustain=.08, release=.12, velocity=.52),
    ),
    (
        "Brass/Rounded Brass.repatch", ("Wind", "Brass"),
        ("Mellow", "Soft", "Warm"),
        dict(volume=.62, benderDco=.24, benderVcf=.14, benderLfo=.16,
             pwm=.50, saw=True, pulse=True, sub=.04, cutoff=.33,
             resonance=.08, vcfEnv=.42, keyFollow=.48, vcaLevel=.72,
             attack=.12, decay=.58, sustain=.68, release=.38, velocity=.30),
    ),
    (
        "Brass/Wide Brass Ensemble.repatch", ("Wind", "Brass"),
        ("Fat", "Lush", "Wide"),
        dict(volume=.57, benderDco=.24, benderVcf=.16, benderLfo=.18,
             lfoRate=.21, lfoDelay=.28, dcoLfo=.01, pwm=.57, pwmMode=0,
             saw=True, pulse=True, sub=.06, cutoff=.43, resonance=.09,
             vcfEnv=.50, vcfLfo=.02, keyFollow=.54, vcaLevel=.68,
             attack=.16, decay=.50, sustain=.72, release=.40, chorus=2,
             velocity=.24),
    ),
    (
        "Strings/Warm String Ensemble.repatch", ("Strings", "Ensemble"),
        ("Lush", "Warm", "Wide"),
        dict(volume=.60, benderDco=.20, benderVcf=.10, benderLfo=.18,
             lfoRate=.16, lfoDelay=.32, dcoLfo=.01, pwm=.58, pwmMode=0,
             saw=True, pulse=True, sub=.04, noise=.01, highPass=2,
             cutoff=.44, resonance=.08, vcfEnv=.20, keyFollow=.55,
             vcaLevel=.70, attack=.32, decay=.60, sustain=.84, release=.58,
             chorus=2, velocity=.22),
    ),
    (
        "Strings/Bright String Ensemble.repatch", ("Strings", "Ensemble"),
        ("Bright", "Lush", "Wide"),
        dict(volume=.58, benderDco=.20, benderVcf=.12, benderLfo=.18,
             lfoRate=.20, lfoDelay=.26, dcoLfo=.02, pwm=.64, pwmMode=0,
             saw=True, pulse=True, highPass=2, cutoff=.58, resonance=.10,
             vcfEnv=.18, vcfLfo=.02, keyFollow=.62, vcaLevel=.69,
             attack=.25, decay=.52, sustain=.82, release=.48, chorus=1,
             velocity=.26),
    ),
    (
        "Strings/Soft String Section.repatch", ("Strings", "Ensemble"),
        ("Lush", "Soft", "Warm"),
        dict(volume=.60, benderDco=.18, benderVcf=.10, benderLfo=.18,
             lfoRate=.13, lfoDelay=.28, dcoLfo=.01, pwm=.70, pwmMode=0,
             saw=False, pulse=True, sub=.06, cutoff=.36, resonance=.12,
             vcfEnv=.22, keyFollow=.46, vcaLevel=.70, attack=.42,
             decay=.68, sustain=.88, release=.66, chorus=2, velocity=.30),
    ),
    (
        "Strings/Slow String Section.repatch", ("Strings", "Ensemble"),
        ("Long", "Soft", "Wide"),
        dict(volume=.58, benderDco=.18, benderVcf=.12, benderLfo=.20,
             lfoRate=.10, lfoDelay=.40, dcoLfo=.02, pwm=.56, pwmMode=0,
             saw=True, pulse=True, noise=.02, cutoff=.40, resonance=.14,
             vcfEnv=.30, keyFollow=.48, vcaLevel=.68, attack=.62,
             decay=.76, sustain=.90, release=.80, chorus=1, velocity=.18),
    ),
    (
        "Strings/Short String Section.repatch", ("Strings", "Ensemble"),
        ("Analog", "Short", "Tight"),
        dict(volume=.61, benderDco=.22, benderVcf=.12, benderLfo=.16,
             lfoRate=.24, lfoDelay=.20, dcoLfo=.01, pwm=.45, saw=True,
             pulse=True, noise=.01, highPass=2, cutoff=.48, resonance=.10,
             vcfEnv=.32, keyFollow=.58, vcaLevel=.70, attack=.14,
             decay=.46, sustain=.68, release=.34, chorus=1, velocity=.38),
    ),
    (
        "Strings/Dark String Ensemble.repatch", ("Strings", "Ensemble"),
        ("Dark", "Lush", "Warm"),
        dict(volume=.59, benderDco=.20, benderVcf=.14, benderLfo=.20,
             lfoRate=.15, lfoDelay=.34, dcoLfo=.01, pwm=.54, pwmMode=0,
             saw=True, pulse=True, sub=.10, noise=.02, cutoff=.30,
             resonance=.16, vcfEnv=.24, vcfLfo=.03, keyFollow=.44,
             vcaLevel=.69, attack=.38, decay=.66, sustain=.80, release=.62,
             chorus=2, velocity=.24),
    ),
    (
        "Strings/Shimmer String Ensemble.repatch", ("Strings", "Ensemble"),
        ("Airy", "Bright", "Wide"),
        dict(volume=.57, benderDco=.18, benderVcf=.12, benderLfo=.18,
             lfoRate=.23, lfoDelay=.25, dcoLfo=.01, pwm=.78, pwmMode=0,
             saw=False, pulse=True, highPass=2, cutoff=.55, resonance=.14,
             vcfEnv=.16, vcfLfo=.04, keyFollow=.58, vcaLevel=.67,
             attack=.28, decay=.58, sustain=.84, release=.55, chorus=1,
             velocity=.20),
    ),
    (
        "Strings/Solo Low Strings.repatch", ("Strings", "Solo"),
        ("Dark", "Organic", "Warm"),
        dict(volume=.61, benderDco=.24, benderVcf=.12, benderLfo=.22,
             keyMode=1, lfoRate=.20, lfoDelay=.36, dcoLfo=.01, pwm=.43,
             range=0, saw=True, pulse=True, sub=.12, noise=.02, cutoff=.31,
             resonance=.18, vcfEnv=.28, vcfLfo=.02, keyFollow=.64,
             vcaLevel=.70, attack=.36, decay=.62, sustain=.76, release=.55,
             chorus=1, velocity=.42),
    ),
    (
        "Pads/Warm Analog Pad.repatch", ("Synth", "Pads"),
        ("Analog", "Lush", "Warm"),
        dict(volume=.60, benderDco=.18, benderVcf=.12, benderLfo=.18,
             lfoRate=.12, lfoDelay=.38, dcoLfo=.02, pwm=.55, pwmMode=0,
             saw=True, pulse=True, sub=.08, noise=.01, cutoff=.39,
             resonance=.10, vcfEnv=.24, vcfLfo=.05, keyFollow=.46,
             vcaLevel=.68, attack=.48, decay=.68, sustain=.82, release=.70,
             chorus=1, velocity=.20),
    ),
    (
        "Pads/Soft PWM Pad.repatch", ("Synth", "Pads"),
        ("Lush", "Soft", "Wide"),
        dict(volume=.58, benderDco=.18, benderVcf=.12, benderLfo=.20,
             lfoRate=.10, lfoDelay=.42, dcoLfo=.02, pwm=.72, pwmMode=0,
             saw=False, pulse=True, cutoff=.46, resonance=.15, vcfEnv=.20,
             vcfLfo=.07, keyFollow=.55, vcaLevel=.69, attack=.58,
             decay=.74, sustain=.86, release=.78, chorus=2, velocity=.25),
    ),
    (
        "Pads/Bright Air Pad.repatch", ("Synth", "Pads"),
        ("Airy", "Bright", "Spacious"),
        dict(volume=.56, benderDco=.16, benderVcf=.14, benderLfo=.20,
             lfoRate=.13, lfoDelay=.44, dcoLfo=.02, pwm=.67, pwmMode=0,
             saw=False, pulse=True, noise=.06, highPass=2, cutoff=.60,
             resonance=.24, vcfEnv=.18, vcfLfo=.10, keyFollow=.62,
             vcaLevel=.66, attack=.66, decay=.70, sustain=.78, release=.76,
             chorus=2, velocity=.18),
    ),
    (
        "Pads/Slow String Pad.repatch", ("Synth", "Pads"),
        ("Long", "Lush", "Soft"),
        dict(volume=.58, benderDco=.18, benderVcf=.10, benderLfo=.18,
             lfoRate=.14, lfoDelay=.30, dcoLfo=.01, pwm=.60, pwmMode=0,
             saw=True, pulse=True, noise=.02, highPass=2, cutoff=.50,
             resonance=.08, vcfEnv=.26, vcfLfo=.03, keyFollow=.54,
             vcaLevel=.68, attack=.70, decay=.72, sustain=.88, release=.82,
             chorus=2, velocity=.20),
    ),
    (
        "Pads/Dark Motion Pad.repatch", ("Synth", "Pads"),
        ("Dark", "Evolving", "Spacious"),
        dict(volume=.58, benderDco=.18, benderVcf=.16, benderLfo=.22,
             lfoRate=.08, lfoDelay=.40, dcoLfo=.02, pwm=.64, pwmMode=0,
             saw=True, pulse=True, sub=.10, cutoff=.29, resonance=.30,
             vcfEnv=.22, vcfLfo=.14, keyFollow=.35, vcaLevel=.67,
             attack=.62, decay=.80, sustain=.76, release=.84, chorus=1,
             velocity=.18),
    ),
    (
        "Pads/Simple Saw Pad.repatch", ("Synth", "Pads"),
        ("Analog", "Clean", "Warm"),
        dict(volume=.61, benderDco=.16, benderVcf=.10, benderLfo=.18,
             lfoRate=.16, lfoDelay=.34, dcoLfo=.01, range=1, saw=True,
             pulse=False, sub=.06, cutoff=.44, resonance=.08, vcfEnv=.22,
             vcfLfo=.03, keyFollow=.50, vcaLevel=.70, attack=.40,
             decay=.62, sustain=.80, release=.64, chorus=1, velocity=.20),
    ),
    (
        "Pads/Soft Choir Pad.repatch", ("Synth", "Pads"),
        ("Airy", "Long", "Soft"),
        dict(volume=.56, benderDco=.16, benderVcf=.12, benderLfo=.20,
             lfoRate=.11, lfoDelay=.46, dcoLfo=.02, pwm=.74, pwmMode=0,
             saw=False, pulse=True, noise=.05, highPass=2, cutoff=.42,
             resonance=.26, vcfEnv=.15, vcfLfo=.06, keyFollow=.40,
             vcaLevel=.66, attack=.72, decay=.80, sustain=.90, release=.88,
             chorus=2, velocity=.18),
    ),
)


ORIGINAL_PATCH_PATHS = FEATURED_PATCHES | {
    relative for relative, _, _, _ in PRESETS + UNIVERSAL_PRESETS
}


def info_value(name):
    info = (PROJECT / "info.lua").read_text(encoding="utf-8")
    match = re.search(rf'^{re.escape(name)}\s*=\s*"([^"]+)"', info, re.MULTILINE)
    assert match, f"info.lua has no {name}"
    return match.group(1)


def read_values(path):
    values = {}
    types = {}
    for value in ET.parse(path).getroot().findall("./Properties/Object/Value"):
        name = value.get("property")
        kind = value.get("type")
        text = (value.text or "").strip()
        assert name and kind in {"number", "boolean"}
        values[name] = text == "true" if kind == "boolean" else float(text)
        types[name] = kind
    return values, types


def write_patch(path, values, types, version):
    lines = [
        '<?xml version="1.0"?>',
        '<JukeboxPatch version="1.0">',
        f"    <DeviceNameInEnglish>{info_value('long_name')}</DeviceNameInEnglish>",
        f'    <Properties deviceProductID="{PRODUCT_ID}" deviceVersion="{version}">',
        '        <Object name="custom_properties">',
    ]
    for name, value in values.items():
        kind = types[name]
        if kind == "boolean":
            text = "true" if value else "false"
        elif name in STEPPED:
            text = str(int(value))
        elif (name == "presetGain"
              or (name == "chorusNoise" and value == CHORUS_NOISE_DEFAULT)):
            text = f"{float(value):.9f}".rstrip("0").rstrip(".")
        else:
            text = f"{float(value):.2f}"
        lines.append(f'            <Value property="{name}" type="{kind}">{text}</Value>')
    lines.extend((
        "        </Object>",
        "    </Properties>",
        "</JukeboxPatch>",
    ))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    version = info_value("version_number")
    init_values, init_types = read_values(PUBLIC / "Init.repatch")
    assert not any(
        (PUBLIC / name).exists() for name in ("A", "B", "Factory Bank")
    ), "historical factory patches must not be shipped"
    unexpected = {
        path.relative_to(PUBLIC).as_posix() for path in PUBLIC.rglob("*.repatch")
    } - ORIGINAL_PATCH_PATHS
    assert not unexpected, f"unreviewed public patches: {sorted(unexpected)}"
    for relative, _, _, overrides in PRESETS + UNIVERSAL_PRESETS:
        assert relative.isascii() and set(overrides) <= set(init_values)
        values = init_values | overrides
        write_patch(PUBLIC / relative, values, init_types, version)

    # Re-emit the original sounds with the current identity/version while
    # retaining their established parameter states.
    for path in sorted(PUBLIC.rglob("*.repatch")):
        values, types = read_values(path)
        if "presetGain" not in values:
            values["presetGain"] = init_values["presetGain"]
            types["presetGain"] = init_types["presetGain"]
        assert values.keys() == init_values.keys(), f"{path}: property set drift"
        assert types == init_types, f"{path}: property type drift"
        ordered = {name: values[name] for name in init_values}
        write_patch(path, ordered, init_types, version)

    all_patches = sorted(PUBLIC.rglob("*.repatch"))
    assert {
        path.relative_to(PUBLIC).as_posix() for path in all_patches
    } == ORIGINAL_PATCH_PATHS, "public bank differs from the original patch catalog"
    if LEVELS_PATH.exists():
        level_data = json.loads(LEVELS_PATH.read_text(encoding="utf-8"))
        assert level_data["format"] == 1
        trims = level_data["preset_gain"]
        expected_paths = {
            path.relative_to(PUBLIC).as_posix() for path in all_patches
        }
        assert set(trims) == expected_paths, "preset level table differs from bank"
        for path in all_patches:
            relative = path.relative_to(PUBLIC).as_posix()
            values, types = read_values(path)
            values["presetGain"] = float(trims[relative])
            ordered = {name: values[name] for name in init_values}
            write_patch(path, ordered, init_types, version)

    metadata_path = PROJECT / "YouKnow.rsmeta"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    by_url = {entry["URL"]: entry for entry in metadata["Files"]}
    prefix = f"rackext:/{PRODUCT_ID}/Public/"
    by_url = {
        url: entry for url, entry in by_url.items()
        if not any(url.startswith(prefix + root) for root in ("A/", "B/", "Factory Bank/"))
    }
    for relative, (primary, sub), tags, _ in PRESETS + UNIVERSAL_PRESETS:
        by_url[prefix + relative] = {
            "URL": prefix + relative,
            "Tags": list(tags),
            "Categories": [{
                "ContentType": "instrument_patch",
                "Primary": primary,
                "Sub": sub,
            }],
            "Excluded": False,
            "Author": "Protocodus",
        }
    expected = {
        prefix + path.relative_to(PUBLIC).as_posix()
        for path in PUBLIC.rglob("*.repatch")
    }
    assert set(by_url) == expected, "metadata contains a stale or missing patch URL"
    metadata_path.write_text(
        json.dumps({"Files": [by_url[url] for url in sorted(by_url)]}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Generated {len(PRESETS) + len(UNIVERSAL_PRESETS)} categorized "
        f"originals; {len(expected)} total"
    )


if __name__ == "__main__":
    main()
