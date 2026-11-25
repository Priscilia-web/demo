#!/usr/bin/env python3
"""
Transcription mot par mot via l'API OpenAI (whisper-1).

Usage :
    python3 scripts/transcribe.py public/<episode>/voix.mp4 <episode>

Sortie : src/<episode>/words.json  ->  {"text": ..., "words": [{"word", "start", "end"}, ...]}
La clé est lue dans .env (OPENAI_API_KEY=...). Aucune dépendance à installer.
"""
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://api.openai.com/v1/audio/transcriptions"
MAX_BYTES = 25 * 1024 * 1024  # limite de l'API


def load_key() -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("Clé introuvable : ajoute OPENAI_API_KEY=... dans le fichier .env")
    return key


def to_mp3(src: Path) -> Path:
    out = Path(tempfile.mkdtemp()) / (src.stem + ".mp3")
    print(f"Fichier > 25 Mo : extraction audio mp3 64k mono -> {out.name}")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-vn", "-ac", "1", "-b:a", "64k", str(out)],
        check=True,
    )
    return out


def multipart(fields: list[tuple[str, str]], file_field: str, path: Path):
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    parts.append(
        (f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
         f'filename="{path.name}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()
    )
    parts.append(path.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, episode = Path(sys.argv[1]), sys.argv[2]
    if not src.exists():
        sys.exit(f"Fichier introuvable : {src}")
    audio = to_mp3(src) if src.stat().st_size > MAX_BYTES else src

    body, ctype = multipart(
        [("model", "whisper-1"),
         ("response_format", "verbose_json"),
         ("timestamp_granularities[]", "word")],
        "file", audio,
    )
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={"Authorization": f"Bearer {load_key()}", "Content-Type": ctype},
    )
    print("Transcription en cours…")
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Erreur API {e.code} : {e.read().decode(errors='replace')}")

    words = [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in data.get("words", [])]
    out = ROOT / "src" / episode / "words.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"text": data.get("text", ""), "words": words}, ensure_ascii=False, indent=1))
    print(f"OK : {len(words)} mots -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
