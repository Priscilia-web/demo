import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {F, scaleOf} from '../lib/time';
import {EPISODE} from './data';
import {SUBS, type Sub} from './subs';

const Title: React.FC = () => {
  const t = EPISODE.title;
  const frame = useCurrentFrame();
  const {width} = useVideoConfig();
  const s = scaleOf(width);
  const len = F(t.endSec - t.startSec);
  const fade = F(t.fadeSec);
  const opacity = interpolate(frame, [0, fade, len - fade, len], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        position: 'absolute',
        top: t.y * s,
        width: '100%',
        textAlign: 'center',
        opacity,
        color: t.color,
        fontFamily: t.fontFamily,
        fontWeight: t.fontWeight,
        fontSize: t.fontSize * s,
      }}
    >
      {t.text}
    </div>
  );
};

const SubChunk: React.FC<{sub: Sub}> = ({sub}) => {
  const st = EPISODE.subs;
  const frame = useCurrentFrame();
  const {width} = useVideoConfig();
  const s = scaleOf(width);
  const enter = interpolate(frame, [0, st.enterFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scale = interpolate(enter, [0, 1], [st.enterFromScale, 1]);
  return (
    <div
      style={{
        position: 'absolute',
        top: st.y * s,
        left: (width - st.maxWidth * s) / 2,
        width: st.maxWidth * s,
        textAlign: 'center',
        opacity: enter,
        transform: `scale(${scale})`,
        color: st.color,
        fontFamily: st.fontFamily,
        textShadow: st.shadow,
        lineHeight: 1.1,
      }}
    >
      {sub.text.split(' ').map((w, i) => {
        const strong = w.length > 1 && w === w.toUpperCase() && /\p{L}/u.test(w);
        return (
          <span
            key={i}
            style={{
              fontWeight: strong ? st.emphasisWeight : st.fontWeight,
              fontSize: st.fontSize * s * (strong ? st.emphasisScale : 1),
            }}
          >
            {i > 0 ? ' ' : ''}
            {w}
          </span>
        );
      })}
    </div>
  );
};

export const Episode: React.FC = () => {
  const m = EPISODE.media;
  return (
    <AbsoluteFill style={{backgroundColor: EPISODE.background}}>
      {m && (
        <OffthreadVideo
          src={staticFile(m.src)}
          startFrom={m.audio === 'aac' ? 1 : 0}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      )}
      <Sequence from={F(EPISODE.title.startSec)} durationInFrames={F(EPISODE.title.endSec - EPISODE.title.startSec)}>
        <Title />
      </Sequence>
      {SUBS.map((sub, i) => {
        const from = Math.max(0, F(sub.start - EPISODE.subs.leadSec));
        const to = F(sub.end - EPISODE.subs.leadSec);
        return (
          <Sequence key={i} from={from} durationInFrames={Math.max(1, to - from)} layout="none">
            <SubChunk sub={sub} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
