import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClientProvider } from '@tanstack/react-query';
import DashboardLogPanel from '../DashboardLogPanel';
import { createTestQueryClient } from '@/test/renderApp';
import * as api from '@/lib/api';

vi.mock('@/lib/api', () => ({
  getLogs: vi.fn(),
}));

const mockNodes = [
  { node_id: '1', node_type: 'scanner', is_online: true, last_heartbeat: '2026-03-30T12:00:00Z' },
  { node_id: '2', node_type: 'solver', is_online: true, last_heartbeat: '2026-03-30T12:00:00Z' },
];

const mockLogs = [
  {
    id: 1,
    session_id: 1,
    node_id: 'scanner',
    severity: 'info',
    event_type: 'scan_start',
    message: 'Scanner started',
    metadata: null,
    created_at: '2026-03-30T12:00:01Z',
  },
  {
    id: 2,
    session_id: 1,
    node_id: 'solver',
    severity: 'warning',
    event_type: 'slow_solve',
    message: 'Solve taking longer than expected',
    metadata: null,
    created_at: '2026-03-30T12:00:05Z',
  },
];

describe('DashboardLogPanel', () => {
  let queryClient: any;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();
    vi.mocked(api.getLogs).mockResolvedValue(mockLogs);
  });

  it('renders loading skeletons when loading prop is true', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DashboardLogPanel
          loading={true}
          status="idle"
          nodes={[]}
        />
      </QueryClientProvider>
    );

    // Should have multiple skeletons
    const skeletons = screen.getAllByRole('generic').filter(el => el.className.includes('animate-pulse'));
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders logs from the API', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DashboardLogPanel
          loading={false}
          status="solving"
          nodes={mockNodes}
          latestSession={{
            session_id: 1,
            status: 'solving',
            selected_algorithm: 'Kociemba',
            session_name: 'Test',
            started_at: '2026-03-30T12:00:00Z',
            completed_at: null,
          }}
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(api.getLogs).toHaveBeenCalled();
      expect(screen.getByText(/Scanner started/)).toBeInTheDocument();
      expect(screen.getByText(/Solve taking longer than expected/)).toBeInTheDocument();
    });

    expect(screen.getByText('live')).toBeInTheDocument();
  });

  it('shows idle status when no session is active', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DashboardLogPanel
          loading={false}
          status="idle"
          nodes={mockNodes}
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('idle')).toBeInTheDocument();
    });
  });

  it('filters logs by session if latestSession is provided', async () => {
    const sessionLogs = [
        ...mockLogs,
        {
            id: 3,
            session_id: 2,
            node_id: 'scanner',
            severity: 'info',
            event_type: 'scan_start',
            message: 'Other session log',
            metadata: null,
            created_at: '2026-03-30T12:01:00Z',
        }
    ];
    vi.mocked(api.getLogs).mockResolvedValue(sessionLogs);

    render(
      <QueryClientProvider client={queryClient}>
        <DashboardLogPanel
          loading={false}
          status="solving"
          nodes={mockNodes}
          latestSession={{
            session_id: 1,
            status: 'solving',
            selected_algorithm: 'Kociemba',
            session_name: 'Test',
            started_at: '2026-03-30T12:00:00Z',
            completed_at: null,
          }}
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Scanner started/)).toBeInTheDocument();
      expect(screen.queryByText(/Other session log/)).not.toBeInTheDocument();
    });
  });
});
