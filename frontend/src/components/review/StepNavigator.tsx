import { Button } from '@/components/ui/button';
import { useEffect, useRef, useState } from 'react';

interface Props {
  total: number;
  current: number;
  onStep: (step: number | ((prev: number) => number)) => void;
}

export default function StepNavigator({ total, current, onStep }: Props) {
  const [playing, setPlaying] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        onStep((prev: number) => {
          if (prev >= total) {
            setPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 400);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [playing, total, onStep]);

  return (
    <div className="rounded-xl border border-kl-outline-variant/70 bg-kl-surface-low/45 p-3">
      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          onClick={() => onStep(Math.max(0, current - 1))}
          disabled={current === 0}
          className="border-kl-outline-variant text-kl-on-surface-variant hover:bg-kl-surface-high"
          aria-label="Previous step"
        >
          <span className="material-symbols-outlined text-base" aria-hidden="true">chevron_left</span>
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => setPlaying((p) => !p)}
          disabled={total === 0}
          className="border-kl-outline-variant text-kl-on-surface-variant hover:bg-kl-surface-high"
          aria-label={playing ? 'Pause autoplay' : 'Play autoplay'}
        >
          <span className="material-symbols-outlined text-base" aria-hidden="true">{playing ? 'pause' : 'play_arrow'}</span>
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => onStep(Math.min(total, current + 1))}
          disabled={current >= total}
          className="border-kl-outline-variant text-kl-on-surface-variant hover:bg-kl-surface-high"
          aria-label="Next step"
        >
          <span className="material-symbols-outlined text-base" aria-hidden="true">chevron_right</span>
        </Button>
        <span className="font-mono text-sm text-kl-on-surface-variant">
          Step {current} / {total}
        </span>
      </div>
    </div>
  );
}
