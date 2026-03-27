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
  it('renders fetched logs with count and severity badges', async () => {
    const logs: SystemLog[] = [
      {
        id: 1,
        node_id: 'solver',
        severity: 'warning',
        message: 'Queue depth increased',
        created_at: '2026-03-27T12:00:00Z',
      },
    ];

    mockGetLogs.mockResolvedValueOnce(logs);

    renderWithAppProviders(<SystemLogs />, { route: '/logs' });

    expect(await screen.findByText('1 entries')).toBeInTheDocument();
    expect(screen.getByText('Queue depth increased')).toBeInTheDocument();
    expect(screen.getByText('warning')).toBeInTheDocument();
  });

  it('shows empty-state presentation when no logs are returned', async () => {
    mockGetLogs.mockResolvedValueOnce([]);

    renderWithAppProviders(<SystemLogs />, { route: '/logs' });

    expect(await screen.findByText('No log entries')).toBeInTheDocument();
    expect(screen.getByText('Events will appear here once a solve runs.')).toBeInTheDocument();
  });

  it('refetches logs when severity filter changes', async () => {
    const user = userEvent.setup();
    mockGetLogs.mockResolvedValue([]);

    renderWithAppProviders(<SystemLogs />, { route: '/logs' });

    await screen.findByText('No log entries');

    await user.click(screen.getByRole('button', { name: 'Error' }));

    expect(mockGetLogs).toHaveBeenCalledWith('error', undefined);
  });
});
