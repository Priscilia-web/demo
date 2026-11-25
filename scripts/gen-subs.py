#!/usr/bin/env python3
"""
Transforme src/<episode>/words.json en src/<episode>/subs.ts.

Usage :
    python3 scripts/gen-subs.py public/<episode>/voix.mp4 <episode>

RÈGLE CRITIQUE : on n'utilise JAMAIS les timestamps whisper bruts (jitter ±150 ms
par mot, qu'aucun offset global ne corrige). On lit la waveform et on recale le
début de chaque mot sur l'attaque physique la plus proche (« onset-snapping »).
Les mots sans frontière nette reçoivent le biais médian mesuré sur les autres.
"""
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# ─── Corrections manuelles (à remplir au besoin) ─────────────────────────────
# Texte : mot tel que whisper l'écrit (sans ponctuation, minuscule) -> texte affiché
CORRECTIONS: dict[str, str] = {}
# Timing : index du mot (dans words.json) -> décalage en secondes ajouté après snapping
TIMING_FIXES: dict[int, float] = {}
# Forcer une coupure de chunk AVANT ces index de mots
FORCE_BREAKS: set[int] = set()
# Empêcher la coupure avant ces index de mots
NO_BREAKS: set[int] = set()

# ─── Réglages ────────────────────────────────────────────────────────────────
SR = 16000
HOP = 0.005            # enveloppe par pas de 5 ms
WIN = 0.010            # fenêtre RMS de 10 ms
REL_THRESHOLD = 0.08   # seuil = 8 % du 98e centile de l'enveloppe (~ -22 dB)
RISE_DB = 6.0          # attaque interne : +6 dB en 20 ms
SEARCH = 0.20          # on cherche une attaque à ±200 ms du timestamp whisper
GAP_BREAK = 0.35       # coupe si silence > 0.35 s
MAX_CHARS = 14         # coupe si le chunk dépasse 14 caractères
MAX_WORDS = 2          # chunks de 1-2 mots
HOLD = 0.40            # durée max d'affichage après la fin du dernier mot
PUNCT = ".,!?;:…"


def read_audio(media: Path) -> np.ndarray:
    tmp = Path(tempfile.mkdtemp()) / "a.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(media),
                    "-vn", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(tmp)], check=True)
    with wave.open(str(tmp)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x


def onsets(x: np.ndarray) -> np.ndarray:
    hop, win = int(SR * HOP), int(SR * WIN)
    n = max(0, (len(x) - win) // hop)
    env = np.array([np.sqrt(np.mean(x[i * hop:i * hop + win] ** 2)) for i in range(n)])
    if n < 3:
        return np.array([])
    thr = np.percentile(env, 98) * REL_THRESHOLD
    above = env >= thr
    # 1) sorties de silence : l'enveloppe franchit le seuil vers le haut
    cross = np.where(above[1:] & ~above[:-1])[0] + 1
    # 2) attaques internes (mots enchaînés) : remontée brutale de l'énergie
    db = 20 * np.log10(env + 1e-9)
    k = int(0.020 / HOP)
    rise = np.zeros_like(db)
    rise[k:] = db[k:] - db[:-k]
    cand = np.where((rise > RISE_DB) & above)[0]
    peaks = [i - k for i in cand
             if rise[i] == rise[max(0, i - k):i + k + 1].max()]
    all_on = np.unique(np.concatenate([cross, np.array(peaks, dtype=int)]))
    return all_on * HOP


def snap(words: list[dict], ons: np.ndarray) -> list[float]:
    raw = [w["start"] for w in words]
    snapped: list[float | None] = []
    biases = []
    for t in raw:
        if len(ons):
            j = int(np.argmin(np.abs(ons - t)))
            if abs(ons[j] - t) <= SEARCH:
                snapped.append(float(ons[j]))
                biases.append(ons[j] - t)
                continue
        snapped.append(None)
    med = float(np.median(biases)) if biases else 0.0
    out = []
    prev = -1.0
    for i, (t, s) in enumerate(zip(raw, snapped)):
        v = (s if s is not None else t + med) + TIMING_FIXES.get(i, 0.0)
        v = max(v, prev + 0.03)  # ordre strict
        out.append(round(v, 3))
        prev = v
    n_ok = sum(s is not None for s in snapped)
    print(f"Onset-snapping : {n_ok}/{len(raw)} mots recalés, biais médian {med*1000:+.0f} ms")
    return out


def clean(word: str) -> str:
    w = word.strip()
    key = w.strip(PUNCT).lower()
    return CORRECTIONS.get(key, w)


def chunk(words: list[dict], starts: list[float], med_end_shift: float) -> list[dict]:
    chunks: list[dict] = []
    cur: list[int] = []

    def flush():
        if cur:
            chunks.append({"idx": list(cur)})
            cur.clear()

    for i, w in enumerate(words):
        if cur and i not in NO_BREAKS:
            p = cur[-1]
            text = " ".join(clean(words[j]["word"]) for j in cur + [i])
            if (i in FORCE_BREAKS
                    or starts[i] - (words[p]["end"] + med_end_shift) > GAP_BREAK
                    or words[p]["word"].strip()[-1:] in PUNCT
                    or len(text) > MAX_CHARS
                    or len(cur) >= MAX_WORDS):
                flush()
        cur.append(i)
    flush()

    out = []
    for k, c in enumerate(chunks):
        first, last = c["idx"][0], c["idx"][-1]
        start = starts[first]
        end_word = max(words[last]["end"] + med_end_shift, start + 0.12)
        nxt = starts[chunks[k + 1]["idx"][0]] if k + 1 < len(chunks) else None
        end = min(nxt, end_word + HOLD) if nxt is not None else end_word + HOLD
        text = " ".join(clean(words[j]["word"]) for j in c["idx"]).strip()
        out.append({"text": text, "start": round(start, 3), "end": round(end, 3)})
    return out


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    media, episode = Path(sys.argv[1]), sys.argv[2]
    src = ROOT / "src" / episode / "words.json"
    words = json.loads(src.read_text())["words"]
    if not words:
        sys.exit("Aucun mot dans words.json")
    starts = snap(words, onsets(read_audio(media)))
    shift = float(np.median([s - w["start"] for s, w in zip(starts, words)]))
    subs = chunk(words, starts, shift)

    lines = [
        "// GÉNÉRÉ par scripts/gen-subs.py — NE PAS ÉDITER À LA MAIN.",
        "// Pour corriger : remplir les dicts de corrections du script, puis relancer.",
        "export type Sub = {text: string; start: number; end: number};",
        "",
        "export const SUBS: Sub[] = [",
    ]
    for s in subs:
        lines.append(f"  {{text: {json.dumps(s['text'], ensure_ascii=False)}, start: {s['start']}, end: {s['end']}}},")
    lines.append("];\n")
    out = ROOT / "src" / episode / "subs.ts"
    out.write_text("\n".join(lines))
    print(f"OK : {len(subs)} sous-titres -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
