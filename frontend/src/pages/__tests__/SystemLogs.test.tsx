import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SystemLogs from '@/pages/SystemLogs';
import { renderWithAppProviders } from '@/test/renderApp';
import type { SystemLog } from '@/types/api';

const mockGetLogs = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api', () => ({
  getLogs: mockGetLogs,
}));

describe('SystemLogs', () => {
  it('renders activity console header and fatal/error scan counts', async () => {
    const logs: SystemLog[] = [
      {
        id: 1,
        session_id: 101,
        node_id: 'solver',
        severity: 'fatal',
        event_type: 'process_panic',
        message: 'Solver thread panic detected',
        metadata: '{"thread_id": 42}',
        created_at: '2026-03-27T12:00:00Z',
      },
      {
        id: 2,
        session_id: 101,
        node_id: 'scanner',
        severity: 'error',
        event_type: 'queue_overflow',
        message: 'Scanner queue overflow',
        metadata: null,
        created_at: '2026-03-27T12:00:05Z',
      },
    ];

    mockGetLogs.mockResolvedValueOnce(logs);

    renderWithAppProviders(<SystemLogs />, { route: '/logs' });

    expect(await screen.findByRole('heading', { name: 'System Activity Console' })).toBeInTheDocument();
    expect(await screen.findByText('Solver thread panic detected')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('1 / 1')).toBeInTheDocument();
    expect(screen.getByText('fatal')).toBeInTheDocument();
  });

  it('keeps empty state mounted inside the stream container', async () => {
    mockGetLogs.mockResolvedValueOnce([]);

    renderWithAppProviders(<SystemLogs />, { route: '/logs' });

    expect(await screen.findByText('No log entries')).toBeInTheDocument();
    expect(screen.getByText('Awaiting activity from execution services.')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'System Log Stream' })).toBeInTheDocument();
  });

  it('refetches logs when severity filter changes', async () => {
    const user = userEvent.setup();
    mockGetLogs.mockResolvedValue([]);

    renderWithAppProviders(<SystemLogs />, { route: '/logs' });

    await screen.findByText('No log entries');

    await user.click(screen.getByRole('radio', { name: 'Error' }));

    expect(mockGetLogs).toHaveBeenLastCalledWith('error', undefined);
  });
});
