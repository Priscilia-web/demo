// Réglages globaux du studio.
export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

// F(sec) : convertit des secondes en frames. Toujours écrire les timings en secondes.
export const F = (sec: number): number => Math.round(sec * FPS);

// Facteur d'échelle : toutes les tailles sont pensées pour 1080 px de large.
export const scaleOf = (width: number): number => width / 1080;
