import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, Play, Pause } from 'lucide-react';
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
          if (prev >= total - 1) {
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
    <div className="flex items-center gap-3">
      <Button
        variant="outline"
        size="icon"
        onClick={() => onStep(Math.max(0, current - 1))}
        disabled={current === 0}
        className="border-slate-700 text-slate-300 hover:bg-slate-800"
      >
        <ChevronLeft size={16} />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => setPlaying((p) => !p)}
        disabled={total === 0}
        className="border-slate-700 text-slate-300 hover:bg-slate-800"
      >
        {playing ? <Pause size={16} /> : <Play size={16} />}
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => onStep(Math.min(total - 1, current + 1))}
        disabled={current >= total - 1}
        className="border-slate-700 text-slate-300 hover:bg-slate-800"
      >
        <ChevronRight size={16} />
      </Button>
      <span className="text-slate-400 text-sm">
        Step {current + 1} / {total || 1}
      </span>
    </div>
  );
}
