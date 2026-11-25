# Studio de montage vidéo (Remotion)

Studio piloté par Claude. L'utilisatrice/l'utilisateur n'est pas développeur : parler simplement,
une étape à la fois, et écrire tout le code soi-même.

Format : réels 9:16, 1080×1920, 30 fps (voir `src/lib/time.ts`). Ordinateur : Windows/Linux
(pas de détourage Vision/Swift).

## Structure d'un épisode

Chaque vidéo vit dans `src/<episode>/` avec TROIS fichiers :
- `data.ts` — la télécommande : tous les réglages (timings en secondes via `F(sec)`, textes,
  couleurs, positions). C'est ici qu'on itère.
- `subs.ts` — GÉNÉRÉ par `scripts/gen-subs.py`, jamais édité à la main.
- `Episode.tsx` — le rendu, qui lit tout dans les deux autres. Aucune valeur magique en dur.

(`words.json` = sortie brute de `scripts/transcribe.py`.) Chaque épisode est déclaré dans `src/Root.tsx`.

## Workflow

1. Dérush manuel (CapCut…) → vidéo propre dans `public/<episode>/`.
2. `python3 scripts/transcribe.py public/<episode>/voix.mp4 <episode>` → `src/<episode>/words.json`
3. `python3 scripts/gen-subs.py public/<episode>/voix.mp4 <episode>` → `src/<episode>/subs.ts`
4. Montage en itérant sur `data.ts`.
5. Render depuis l'interface du Studio (`npm run dev`).

## Règles permanentes (durement apprises)

- Le dérush est MANUEL : je coupe moi-même mes ratés dans mon éditeur (CapCut…) et je t'amène
  une vidéo déjà propre. Ne propose jamais de l'automatiser.
- `startFrom={1}` UNIQUEMENT sur les sources AAC/mp4 (compensation du priming). Sur un WAV c'est
  un bug : la voix joue ~33 ms en avance.
- Jamais de timestamps whisper bruts → onset-snapping (cf. `scripts/gen-subs.py`).
- Entrée de sous-titre ≤ 5-6 frames, déclenchée sur l'attaque (lead ~0.1 s) : une apparition plus
  longue est PERÇUE désync même si le timing est juste. Si un cas résiste : forced alignment (WhisperX).
- `startFrom`, pas `trimBefore`. Mezzanine 30 fps CFR avant montage (le VFR des téléphones fait
  dériver le son). Toujours scaler par `width/1080`.
- Médias pré-accélérés par ffmpeg (`setpts`/`atempo`), jamais `playbackRate`.
- Vidéos alpha : webm VP9 `yuva420p` `-g 1`, monté via `<OffthreadVideo transparent />`.
- Juger la fluidité au RENDER, jamais au preview (le Studio saccade par nature). C'est moi qui
  rends, depuis l'interface du Studio.
- Sous-titres : toujours me demander quel style utiliser. JAMAIS de couleur dans les subs — le
  contraste est typographique (poids, taille, italique), pas chromatique.
- Sound design : piocher dans une banque de SFX locale (pas de synthèse), volume 0.2–0.4 sous la
  voix, calé sur les beats de la voix.
- Motion library : le jour où je valide un motion réutilisable, propose de le documenter dans une
  fiche (`docs/library/` : nom, description, fichier source, props, contexte). Un motion validé
  jamais documenté = travail perdu.

## Secrets

La clé OpenAI vit dans `.env` (ignoré par git). Ne jamais la commiter, ni l'afficher.

## Commande mezzanine (référence)

    ffmpeg -i brut.mov -vf fps=30 -vsync cfr -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -b:a 192k public/<episode>/voix.mp4
