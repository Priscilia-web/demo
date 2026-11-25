// ─────────────────────────────────────────────────────────────
// TÉLÉCOMMANDE de l'épisode « exemple ».
// Tous les réglages sont ici : timings (en secondes), textes,
// couleurs, positions, tailles (en px pensés pour 1080 de large).
// Episode.tsx ne contient aucune valeur en dur.
// ─────────────────────────────────────────────────────────────

export const EPISODE = {
  id: 'exemple',
  durationSec: 11,

  // Vidéo source (dans public/). null = épisode sans média.
  // audio : 'aac' pour un mp4/mov (startFrom={1}), 'wav' pour un WAV (startFrom={0}).
  media: null as null | {src: string; audio: 'aac' | 'wav'},

  background: '#111111',

  title: {
    text: 'Mon studio vidéo',
    startSec: 0.3,
    endSec: 2.6,
    fadeSec: 0.15,
    y: 760, // px depuis le haut
    fontSize: 110,
    fontWeight: 800,
    color: '#FFFFFF',
    fontFamily: 'Inter, Helvetica, Arial, sans-serif',
  },

  // Style des sous-titres (contraste typographique uniquement, jamais de couleur).
  subs: {
    leadSec: 0.1, // apparition un peu AVANT l'attaque du mot
    enterFrames: 4, // durée d'entrée : 5-6 frames max
    y: 1380,
    fontSize: 92,
    fontWeight: 800,
    emphasisWeight: 900, // mots en MAJUSCULES : plus gras + plus grands
    emphasisScale: 1.15,
    color: '#FFFFFF',
    fontFamily: 'Inter, Helvetica, Arial, sans-serif',
    shadow: '0 4px 18px rgba(0,0,0,0.55)',
    enterFromScale: 0.92,
    maxWidth: 900,
  },
};
