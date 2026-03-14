#!/usr/bin/env python3
"""
Generate placeholder sound effects for a match-3 puzzle game.
Uses only Python standard library (wave, struct, math, random).
All generated files are original creations - no copyright concerns.
"""

import wave
import struct
import math
import random
import os

SAMPLE_RATE = 44100
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def write_wav(filename, samples, sample_rate=SAMPLE_RATE, channels=1):
    """Write samples (list of floats -1.0 to 1.0) to a WAV file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with wave.open(filepath, 'w') as w:
        w.setnchannels(channels)
        w.setsampwidth(2)  # 16-bit
        w.setframerate(sample_rate)
        for s in samples:
            s = max(-1.0, min(1.0, s))
            w.writeframes(struct.pack('<h', int(s * 32767)))
    print(f"  Created: {filepath} ({len(samples)} samples, {len(samples)/sample_rate:.2f}s)")


def sine(freq, t):
    return math.sin(2 * math.pi * freq * t)


def envelope_adsr(t, duration, attack=0.01, decay=0.05, sustain_level=0.7, release=0.1):
    """Simple ADSR envelope."""
    release_start = duration - release
    if t < attack:
        return t / attack
    elif t < attack + decay:
        return 1.0 - (1.0 - sustain_level) * ((t - attack) / decay)
    elif t < release_start:
        return sustain_level
    elif t < duration:
        return sustain_level * (1.0 - (t - release_start) / release)
    return 0.0


def envelope_exp_decay(t, decay_rate=5.0):
    """Exponential decay envelope."""
    return math.exp(-decay_rate * t)


def noise():
    """White noise sample."""
    return random.uniform(-1.0, 1.0)


def generate_swap():
    """Short pop/click for gem swap - quick pitch sweep."""
    duration = 0.12
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Quick downward pitch sweep
        freq = 1200 - 800 * (t / duration)
        env = envelope_exp_decay(t, 25.0)
        s = sine(freq, t) * env * 0.7
        # Add a tiny click at the start
        if t < 0.005:
            s += noise() * (1.0 - t / 0.005) * 0.3
        samples.append(s)
    write_wav("sfx_swap.wav", samples)


def generate_match3():
    """Satisfying ding/chime for match-3 - two harmonious tones."""
    duration = 0.4
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = envelope_exp_decay(t, 6.0)
        # C5 + E5 (major third - pleasant)
        s = sine(523.25, t) * 0.5 + sine(659.25, t) * 0.35 + sine(1046.5, t) * 0.15
        samples.append(s * env * 0.7)
    write_wav("sfx_match3.wav", samples)


def generate_match4():
    """Bigger ding for match-4 - richer chord with slight upward sweep."""
    duration = 0.55
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = envelope_exp_decay(t, 4.5)
        # C5 + E5 + G5 (major chord) with slight pitch rise
        pitch_mult = 1.0 + 0.02 * (t / duration)
        s = (sine(523.25 * pitch_mult, t) * 0.4 +
             sine(659.25 * pitch_mult, t) * 0.3 +
             sine(783.99 * pitch_mult, t) * 0.2 +
             sine(1046.5 * pitch_mult, t) * 0.1)
        samples.append(s * env * 0.75)
    write_wav("sfx_match4.wav", samples)


def generate_match5():
    """Even bigger sound for match-5 - full arpeggio sweep up."""
    duration = 0.75
    n = int(SAMPLE_RATE * duration)
    samples = []
    # Quick arpeggio: C5 -> E5 -> G5 -> C6
    notes = [523.25, 659.25, 783.99, 1046.5]
    note_dur = 0.08
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        # Arpeggio notes
        for j, freq in enumerate(notes):
            note_start = j * note_dur
            if t >= note_start:
                nt = t - note_start
                note_env = envelope_exp_decay(nt, 3.0)
                s += sine(freq, t) * note_env * 0.35
        # Add shimmer
        if t > note_dur * len(notes):
            shimmer_t = t - note_dur * len(notes)
            shimmer_env = envelope_exp_decay(shimmer_t, 3.0)
            s += sine(1046.5, t) * 0.15 * shimmer_env
            s += sine(1318.5, t) * 0.1 * shimmer_env
        env_global = envelope_adsr(t, duration, 0.001, 0.1, 0.6, 0.3)
        samples.append(s * env_global * 0.7)
    write_wav("sfx_match5.wav", samples)


def generate_combo():
    """Rising combo sound - ascending notes with energy."""
    duration = 0.6
    n = int(SAMPLE_RATE * duration)
    samples = []
    # Rising scale: C5 D5 E5 F5 G5 A5 B5 C6
    freqs = [523.25, 587.33, 659.25, 698.46, 783.99, 880.0, 987.77, 1046.5]
    note_dur = duration / len(freqs)
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        note_idx = min(int(t / note_dur), len(freqs) - 1)
        for j in range(note_idx + 1):
            nt = t - j * note_dur
            if nt >= 0:
                env = envelope_exp_decay(nt, 8.0)
                s += sine(freqs[j], t) * env * 0.3
        # Global envelope
        env_global = envelope_adsr(t, duration, 0.005, 0.05, 0.8, 0.15)
        # Rising volume
        vol_rise = 0.5 + 0.5 * (t / duration)
        samples.append(s * env_global * vol_rise * 0.7)
    write_wav("sfx_combo.wav", samples)


def generate_special_create():
    """Sparkle/magic sound - shimmering high frequencies with randomized tones."""
    duration = 0.65
    n = int(SAMPLE_RATE * duration)
    samples = []
    # Pre-generate sparkle events
    random.seed(42)
    sparkles = []
    for _ in range(15):
        spark_t = random.uniform(0, duration * 0.7)
        spark_freq = random.uniform(2000, 5000)
        sparkles.append((spark_t, spark_freq))

    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        # Base magical tone (rising)
        base_freq = 800 + 600 * (t / duration)
        env_base = envelope_adsr(t, duration, 0.02, 0.1, 0.4, 0.2)
        s += sine(base_freq, t) * env_base * 0.3
        s += sine(base_freq * 1.5, t) * env_base * 0.15  # fifth harmonic
        # Sparkle pings
        for spark_t, spark_freq in sparkles:
            if t >= spark_t:
                st = t - spark_t
                spark_env = envelope_exp_decay(st, 20.0)
                s += sine(spark_freq, t) * spark_env * 0.15
        # Subtle noise shimmer
        s += noise() * 0.02 * envelope_adsr(t, duration, 0.1, 0.1, 0.5, 0.2)
        samples.append(max(-1.0, min(1.0, s * 0.7)))
    write_wav("sfx_special_create.wav", samples)


def generate_special_explode():
    """Explosion for special gem - noise burst with low rumble."""
    duration = 0.6
    n = int(SAMPLE_RATE * duration)
    samples = []
    random.seed(43)
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        # Initial burst of noise
        burst_env = envelope_exp_decay(t, 8.0)
        s += noise() * burst_env * 0.5
        # Low frequency rumble
        rumble_freq = 80 - 30 * (t / duration)
        rumble_env = envelope_exp_decay(t, 4.0)
        s += sine(rumble_freq, t) * rumble_env * 0.5
        # Mid crackle
        if t < 0.15:
            s += sine(200 + noise() * 100, t) * (1.0 - t / 0.15) * 0.3
        # Impact thud at start
        if t < 0.03:
            s += sine(60, t) * (1.0 - t / 0.03) * 0.6
        # Some distortion for punch
        if abs(s) > 0.7:
            s = 0.7 * (1 if s > 0 else -1) + (s - 0.7 * (1 if s > 0 else -1)) * 0.3
        samples.append(max(-1.0, min(1.0, s * 0.8)))
    write_wav("sfx_special_explode.wav", samples)


def generate_level_complete():
    """Victory fanfare - ascending major chord arpeggio with sustain."""
    duration = 1.5
    n = int(SAMPLE_RATE * duration)
    samples = []
    # Fanfare: C4-E4-G4-C5 with sustain on final chord
    fanfare_notes = [
        (0.0, 261.63, 0.3),    # C4
        (0.15, 329.63, 0.3),   # E4
        (0.30, 392.00, 0.3),   # G4
        (0.45, 523.25, 0.8),   # C5 (longer)
    ]
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        for note_start, freq, note_len in fanfare_notes:
            if t >= note_start:
                nt = t - note_start
                if nt < note_len:
                    env = envelope_adsr(nt, note_len, 0.01, 0.05, 0.7, 0.15)
                else:
                    env = envelope_exp_decay(nt - note_len + 0.15, 3.0) * 0.3
                s += sine(freq, t) * env * 0.3
                s += sine(freq * 2, t) * env * 0.1  # octave harmonic
        # Final sustained chord (all notes ring together)
        if t > 0.5:
            chord_t = t - 0.5
            chord_env = envelope_adsr(chord_t, 1.0, 0.05, 0.1, 0.5, 0.4)
            s += sine(523.25, t) * chord_env * 0.2
            s += sine(659.25, t) * chord_env * 0.15
            s += sine(783.99, t) * chord_env * 0.1
        # Global envelope for fade out
        if t > duration - 0.3:
            s *= (duration - t) / 0.3
        samples.append(max(-1.0, min(1.0, s * 0.75)))
    write_wav("sfx_level_complete.wav", samples)


def generate_level_fail():
    """Sad sound for level fail - descending minor tones."""
    duration = 1.0
    n = int(SAMPLE_RATE * duration)
    samples = []
    # Descending minor: E4 -> C4 -> A3 (Am chord descending)
    sad_notes = [
        (0.0, 329.63, 0.35),   # E4
        (0.25, 261.63, 0.35),  # C4
        (0.50, 220.00, 0.5),   # A3 (sustained)
    ]
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        for note_start, freq, note_len in sad_notes:
            if t >= note_start:
                nt = t - note_start
                env = envelope_adsr(nt, note_len, 0.02, 0.08, 0.6, 0.2)
                if nt > note_len:
                    env = envelope_exp_decay(nt - note_len + 0.2, 2.5) * 0.2
                # Slightly detuned for sadness
                s += sine(freq, t) * env * 0.35
                s += sine(freq * 0.998, t) * env * 0.15  # slight detune
                s += sine(freq * 2, t) * env * 0.05  # soft harmonic
        # Add subtle vibrato on the last note
        if t > 0.5:
            vib = 1.0 + 0.008 * sine(5.0, t)
            # Recalculate last note with vibrato
            nt = t - 0.5
            env = envelope_adsr(nt, 0.5, 0.02, 0.08, 0.5, 0.2)
            s += sine(220.0 * vib, t) * env * 0.1
        # Fade out
        if t > duration - 0.2:
            s *= (duration - t) / 0.2
        samples.append(max(-1.0, min(1.0, s * 0.7)))
    write_wav("sfx_level_fail.wav", samples)


def generate_button_click():
    """Simple click for button - very short, clean."""
    duration = 0.08
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = envelope_exp_decay(t, 40.0)
        # Sharp click with quick decay
        s = sine(800, t) * 0.5 + sine(1600, t) * 0.3
        # Tiny noise click at very start
        if t < 0.003:
            s += noise() * 0.4
        samples.append(s * env * 0.7)
    write_wav("sfx_button_click.wav", samples)


if __name__ == "__main__":
    print("Generating match-3 puzzle game sound effects...")
    print()
    generate_swap()
    generate_match3()
    generate_match4()
    generate_match5()
    generate_combo()
    generate_special_create()
    generate_special_explode()
    generate_level_complete()
    generate_level_fail()
    generate_button_click()
    print()
    print("All sound effects generated successfully!")
