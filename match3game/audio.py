"""
Audio: procedurally generated sound effects + optional background music.
Music files are downloaded on first run from soundimage.org (CC licensed).
"""
import os
import math
import array
import struct
import urllib.request
import threading
import pygame

SOUNDS_DIR = os.path.join(os.path.dirname(__file__), 'assets', 'sounds')
os.makedirs(SOUNDS_DIR, exist_ok=True)

# Royalty-free puzzle music from soundimage.org (Eric Matyas, CC BY 4.0)
MUSIC_URLS = [
    ('bgm_01.mp3', 'https://soundimage.org/wp-content/uploads/2014/06/Puzzle-Game-1.mp3'),
    ('bgm_02.mp3', 'https://soundimage.org/wp-content/uploads/2014/07/Puzzle-Game-3.mp3'),
    ('bgm_03.mp3', 'https://soundimage.org/wp-content/uploads/2016/10/Puzzle-Game-1_Looping.mp3'),
]

SAMPLE_RATE = 44100


# ── PCM helpers ──────────────────────────────────────────────────────
def _sine_wave(freq, duration, volume=0.5, sample_rate=SAMPLE_RATE):
    n_samples = int(sample_rate * duration)
    buf = array.array('h')
    for i in range(n_samples):
        v = int(volume * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
        buf.append(v)
    return buf


def _adsr(buf, attack, decay, sustain, release, sample_rate=SAMPLE_RATE):
    n = len(buf)
    a = int(attack * sample_rate)
    d = int(decay * sample_rate)
    r = int(release * sample_rate)
    s_start = a + d
    s_end = n - r
    result = array.array('h')
    for i, v in enumerate(buf):
        if i < a:
            env = i / max(1, a)
        elif i < a + d:
            env = 1.0 - (1.0 - sustain) * (i - a) / max(1, d)
        elif i < s_end:
            env = sustain
        else:
            env = sustain * max(0, (n - i) / max(1, r))
        result.append(int(v * env))
    return result


def _make_sound(buf) -> pygame.mixer.Sound:
    stereo = array.array('h')
    for v in buf:
        stereo.append(v)
        stereo.append(v)
    return pygame.mixer.Sound(buffer=stereo.tobytes())


# ── Sound library ────────────────────────────────────────────────────
class AudioManager:
    def __init__(self):
        self.enabled = True
        self.music_enabled = True
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self._music_files: list[str] = []
        self._current_music_idx = 0
        self._music_loaded = False

    def init(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            self._build_sounds()
            # Start downloading music in background
            threading.Thread(target=self._download_music, daemon=True).start()
        except Exception as e:
            print(f'[audio] init failed: {e}')
            self.enabled = False

    def _build_sounds(self):
        try:
            # Match sound — cheerful chord
            buf = _sine_wave(523.25, 0.12, 0.4)  # C5
            buf2 = _sine_wave(659.25, 0.12, 0.3)  # E5
            buf3 = _sine_wave(783.99, 0.12, 0.3)  # G5
            combined = array.array('h', [buf[i]+buf2[i]+buf3[i] for i in range(len(buf))])
            combined = _adsr(combined, 0.01, 0.03, 0.6, 0.05)
            self.sounds['match'] = _make_sound(combined)

            # Combo sound — higher, brighter
            buf = _sine_wave(783.99, 0.15, 0.45)
            buf2 = _sine_wave(1046.5, 0.15, 0.35)
            combined = array.array('h', [buf[i]+buf2[i] for i in range(len(buf))])
            combined = _adsr(combined, 0.005, 0.04, 0.5, 0.06)
            self.sounds['combo'] = _make_sound(combined)

            # Select sound — soft click
            buf = _sine_wave(1000, 0.05, 0.25)
            buf = _adsr(buf, 0.005, 0.01, 0.4, 0.03)
            self.sounds['select'] = _make_sound(buf)

            # Swap sound — swoosh (descending)
            buf = array.array('h')
            dur = 0.1
            n = int(SAMPLE_RATE * dur)
            for i in range(n):
                freq = 600 - 300 * (i / n)
                v = int(0.3 * 32767 * math.sin(2*math.pi*freq*i/SAMPLE_RATE))
                buf.append(v)
            buf = _adsr(buf, 0.01, 0.03, 0.3, 0.04)
            self.sounds['swap'] = _make_sound(buf)

            # Invalid swap — low thud
            buf = _sine_wave(150, 0.12, 0.4)
            buf2 = _sine_wave(100, 0.12, 0.3)
            combined = array.array('h', [buf[i]+buf2[i] for i in range(len(buf))])
            combined = _adsr(combined, 0.01, 0.05, 0.3, 0.05)
            self.sounds['invalid'] = _make_sound(combined)

            # Level complete — ascending fanfare
            notes = [523.25, 659.25, 783.99, 1046.5]
            durations = [0.15, 0.15, 0.15, 0.35]
            all_samples = array.array('h')
            for freq, dur in zip(notes, durations):
                buf = _sine_wave(freq, dur, 0.4)
                buf = _adsr(buf, 0.01, 0.05, 0.7, 0.04)
                all_samples.extend(buf)
            self.sounds['level_complete'] = _make_sound(all_samples)

            # Game over — descending sad
            notes = [523.25, 440, 392, 349.23]
            durations = [0.2, 0.2, 0.2, 0.4]
            all_samples = array.array('h')
            for freq, dur in zip(notes, durations):
                buf = _sine_wave(freq, dur, 0.35)
                buf = _adsr(buf, 0.01, 0.05, 0.6, 0.08)
                all_samples.extend(buf)
            self.sounds['game_over'] = _make_sound(all_samples)

            # Special gem activate — rising gliss
            buf = array.array('h')
            n = int(SAMPLE_RATE * 0.25)
            for i in range(n):
                freq = 400 + 800 * (i / n)
                v = int(0.35 * 32767 * math.sin(2*math.pi*freq*i/SAMPLE_RATE))
                buf.append(v)
            buf = _adsr(buf, 0.01, 0.05, 0.5, 0.08)
            self.sounds['special'] = _make_sound(buf)

        except Exception as e:
            print(f'[audio] sound build error: {e}')

    def _download_music(self):
        for filename, url in MUSIC_URLS:
            path = os.path.join(SOUNDS_DIR, filename)
            if not os.path.exists(path):
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = resp.read()
                    with open(path, 'wb') as f:
                        f.write(data)
                    print(f'[audio] Downloaded {filename}')
                except Exception as e:
                    print(f'[audio] Could not download {filename}: {e}')
        # Collect whatever was downloaded
        self._music_files = [
            os.path.join(SOUNDS_DIR, fn)
            for fn, _ in MUSIC_URLS
            if os.path.exists(os.path.join(SOUNDS_DIR, fn))
        ]
        self._music_loaded = True
        if self.music_enabled and self._music_files:
            self._play_next_track()

    def _play_next_track(self):
        if not self._music_files:
            return
        path = self._music_files[self._current_music_idx % len(self._music_files)]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play()
        except Exception as e:
            print(f'[audio] music play error: {e}')

    def on_music_end(self):
        """Call from game loop when MUSIC_END event fires."""
        if not self._music_files:
            return
        self._current_music_idx = (self._current_music_idx + 1) % len(self._music_files)
        self._play_next_track()

    def play(self, name: str, volume=1.0):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.set_volume(volume)
                snd.play()
            except Exception:
                pass

    def set_music_volume(self, vol: float):
        try:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
        except Exception:
            pass

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
            if not pygame.mixer.music.get_busy() and self._music_files:
                self._play_next_track()
