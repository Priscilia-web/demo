import React from 'react';
import {Composition} from 'remotion';
import {F, FPS, HEIGHT, WIDTH} from './lib/time';
import {Episode as Exemple} from './exemple/Episode';
import {EPISODE as exemple} from './exemple/data';

// Un <Composition> par épisode. Pour un nouvel épisode : copier src/exemple/.
export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id={exemple.id}
      component={Exemple}
      durationInFrames={F(exemple.durationSec)}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  </>
);
