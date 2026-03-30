import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

interface ScannerCameraFeedProps {
  scannerIp?: string;
  sessionActive?: boolean;
}

export default function ScannerCameraFeed({ scannerIp = 'localhost', sessionActive = false }: ScannerCameraFeedProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const streamUrl = `http://${scannerIp}:8001/video_feed`;
  const maxRetries = 3;

  // Test stream connectivity
  useEffect(() => {
    setIsLoading(true);
    setHasError(false);

    const testImage = new Image();
    const timeoutId = setTimeout(() => {
      setIsOnline(false);
      setHasError(true);
      setIsLoading(false);
    }, 5000);

    testImage.onload = () => {
      clearTimeout(timeoutId);
      setIsOnline(true);
      setHasError(false);
      setIsLoading(false);
      setRetryCount(0);
    };

    testImage.onerror = () => {
      clearTimeout(timeoutId);
      setIsOnline(false);
      setHasError(true);
      setIsLoading(false);

      // Auto-retry
      if (retryCount < maxRetries) {
        setTimeout(() => setRetryCount((prev) => prev + 1), 3000);
      }
    };

    testImage.src = `${streamUrl}?t=${Date.now()}`;

    return () => clearTimeout(timeoutId);
  }, [scannerIp, retryCount]);

  const statusBadgeColor = isOnline ? 'bg-green-500/20 text-green-400 border-green-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30';
  const statusDotColor = isOnline ? 'bg-green-500' : 'bg-red-500';

  return (
    <Card className="glass border-kl-outline-variant/70">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium uppercase tracking-wide text-kl-on-surface-variant">
            Live Scanner Feed
          </CardTitle>
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${statusDotColor}`} />
            <Badge variant="outline" className={`border-kl-outline-variant font-mono text-xs ${statusBadgeColor}`}>
              {isOnline ? 'ONLINE' : 'OFFLINE'}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 p-0 px-4 pb-4">
        {isLoading ? (
          <Skeleton className="h-[280px] w-full rounded-lg bg-kl-surface-high" />
        ) : hasError && !isOnline ? (
          <div className="flex h-[280px] items-center justify-center rounded-lg border border-dashed border-kl-outline-variant bg-kl-surface-high/50">
            <div className="text-center">
              <p className="text-sm font-medium text-kl-on-surface-variant">📷 Camera Offline</p>
              <p className="mt-1 text-xs text-kl-on-surface-variant/70">
                {retryCount < maxRetries ? `Retrying... (${retryCount + 1}/${maxRetries})` : 'Unable to connect'}
              </p>
              <p className="mt-3 text-xs text-kl-on-surface-variant/60">
                Ensure stream_server.py is running on Scanner Pi
              </p>
            </div>
          </div>
        ) : (
          <img
            src={streamUrl}
            alt="Live scanner camera feed"
            className="w-full rounded-lg border border-kl-outline-variant bg-black"
            onError={() => {
              setIsOnline(false);
              setHasError(true);
              setIsLoading(false);
            }}
          />
        )}

        {isOnline && (
          <p className="text-xs text-kl-on-surface-variant/70">
            {sessionActive ? '🔴 REC - Scanner is capturing' : '🟢 Stream ready'}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
