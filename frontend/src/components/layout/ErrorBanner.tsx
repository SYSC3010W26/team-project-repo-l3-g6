/**
 * @file ErrorBanner.tsx
 * @description Layout component: ErrorBanner
 */

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getLogs } from '@/lib/api';
import type { SystemLog } from '@/types/api';

const RECOVERY_GUIDANCE: Record<string, string> = {
  scanner: 'Check Scanner Pi camera connection and restart scanner service.',
  solver: 'Check Solver Pi connection and restart solver service.',
  motor: 'Check Motor Pi connection and ensure motors are homed.',
  database: 'Check Database Pi and restart the backend service.',
};

const FALLBACK_GUIDANCE = 'Check system connections and restart affected Pi services.';

export default function ErrorBanner() {
  const { data: fatalLogs = [] } = useQuery<SystemLog[]>({
    queryKey: ['fatal-logs'],
    queryFn: () => getLogs('fatal'),
    refetchInterval: 10_000,
  });

  const latestFatal: SystemLog | null = fatalLogs[0] ?? null;
  const [dismissed, setDismissed] = useState<number | null>(null);
  const notifiedId = useRef<number | null>(null);

  // Browser Notification effect — fires once per unique fatal log id
  useEffect(() => {
    if (!latestFatal) return;
    if (typeof Notification === 'undefined') return;
    if (notifiedId.current === latestFatal.id) return;

    const fire = () => {
      notifiedId.current = latestFatal.id;
      new Notification('Pi³ Fatal Error', {
        body: latestFatal.message,
        icon: '/vite.svg',
      });
    };

    if (Notification.permission === 'granted') {
      fire();
    } else if (Notification.permission === 'default') {
      Notification.requestPermission().then((perm) => {
        if (perm === 'granted') fire();
      });
    }
    // 'denied' → skip silently
  }, [latestFatal?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const showBanner = latestFatal && latestFatal.id !== dismissed;

  if (!showBanner) return null;

  const guidance =
    latestFatal.node_id ? (RECOVERY_GUIDANCE[latestFatal.node_id] ?? FALLBACK_GUIDANCE) : FALLBACK_GUIDANCE;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-red-900/95 border-b border-red-600 px-4 py-3 flex items-start justify-between gap-4">
      <div className="flex items-start gap-3 min-w-0">
        {/* Warning icon */}
        <span className="text-red-300 text-xl font-bold shrink-0 leading-tight" aria-hidden="true">
          ⚠
        </span>
        <div className="min-w-0">
          <p className="text-red-100 font-semibold text-sm leading-snug break-words">
            <span className="uppercase tracking-wide text-red-400 text-xs mr-2">
              [{latestFatal.node_id?.toUpperCase() ?? 'SYSTEM'}]
            </span>
            {latestFatal.message}
          </p>
          <p className="text-red-300 text-xs mt-1 leading-snug">{guidance}</p>
        </div>
      </div>

      {/* Dismiss button */}
      <button
        onClick={() => setDismissed(latestFatal.id)}
        className="shrink-0 text-red-300 hover:text-red-100 text-lg font-bold leading-none focus:outline-none"
        aria-label="Dismiss error banner"
      >
        ×
      </button>
    </div>
  );
}
