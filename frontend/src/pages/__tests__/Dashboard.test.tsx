import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from '../Dashboard';
import { createTestQueryClient } from '@/test/renderApp';
import * as useSocket from '@/hooks/useSocket';
import * as api from '@/lib/api';

vi.mock('@/lib/api', () => ({
  getAllNodes: vi.fn(),
  getSessions: vi.fn(),
  startSolve: vi.fn(),
  postControlFlag: vi.fn(),
  getScanState: vi.fn(),
}));

vi.mock('@/hooks/useSocket', () => ({
  useSocketEvent: vi.fn(),
  useSocketStatus: vi.fn(() => true),
}));

vi.mock('@/components/dashboard/CubeViewer3D', () => ({
  default: vi.fn(({ stateString, animatingMove }) => (
    <div data-testid="cube-viewer-3d">
      <span data-testid="cube-state">{stateString}</span>
      <span data-testid="animating-move">{animatingMove}</span>
    </div>
  )),
}));

vi.mock('@/components/dashboard/PipelineStepper', () => ({ default: () => <div data-testid="pipeline-stepper" /> }));
vi.mock('@/components/dashboard/NodeHealthCard', () => ({ default: () => <div data-testid="node-health-card" /> }));
vi.mock('@/components/dashboard/ControlButtons', () => ({ default: () => <div data-testid="control-buttons" /> }));
vi.mock('@/components/dashboard/DashboardLogPanel', () => ({ default: () => <div data-testid="log-panel" /> }));

const SOLVED_STATE = 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB';

describe('Dashboard Live Updates', () => {
  let queryClient: QueryClient;
  let executionProgressHandler: (data: unknown) => void;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();

    vi.mocked(api.getAllNodes).mockResolvedValue([]);
    vi.mocked(api.getSessions).mockResolvedValue([
      {
        session_id: 1,
        status: 'executing',
        selected_algorithm: 'CFOP',
        session_name: 'Test Session',
        started_at: '2026-03-30T12:00:00Z',
        completed_at: null,
      },
    ]);
    vi.mocked(api.getScanState).mockResolvedValue({
      session_id: 1,
      state_string: SOLVED_STATE,
      is_valid: true,
      confidence: 0.99,
      created_at: '2026-03-30T12:00:05Z',
    });

    vi.mocked(useSocket.useSocketEvent).mockImplementation((event, handler) => {
      if (event === 'execution_progress') {
        executionProgressHandler = handler;
      }
    });
  });

  it('updates cube state when execution_progress event is received', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    );

    // Wait for initial data to load
    await waitFor(() => {
      expect(screen.getByTestId('cube-state').textContent).toBe(SOLVED_STATE);
    });

    expect(executionProgressHandler).toBeDefined();

    // Simulate execution_progress event for session 1
    // Let's do a 'U' move.
    // We don't need to know the exact state, just that it changed and it's not the solved state anymore.
    // And that animating-move is set.
    await waitFor(() => {
        executionProgressHandler({ session_id: 1, move: 'U' });
    });

    await waitFor(() => {
      expect(screen.getByTestId('animating-move').textContent).toBe('U');
      expect(screen.getByTestId('cube-state').textContent).not.toBe(SOLVED_STATE);
    });

    const stateAfterU = screen.getByTestId('cube-state').textContent;

    // Simulate another move 'R'
    await waitFor(() => {
        executionProgressHandler({ session_id: 1, move: 'R' });
    });

    await waitFor(() => {
      expect(screen.getByTestId('animating-move').textContent).toBe('R');
      expect(screen.getByTestId('cube-state').textContent).not.toBe(stateAfterU);
      expect(screen.getByTestId('cube-state').textContent).not.toBe(SOLVED_STATE);
    });
  });

  it('ignores execution_progress event for different session', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('cube-state').textContent).toBe(SOLVED_STATE);
    });

    // Simulate execution_progress event for session 2 (current is 1)
    await waitFor(() => {
        executionProgressHandler({ session_id: 2, move: 'U' });
    });

    // Should still be solved state
    expect(screen.getByTestId('cube-state').textContent).toBe(SOLVED_STATE);
    expect(screen.getByTestId('animating-move').textContent).toBe('');
  });

  it('resets cube state when sessionId changes', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('cube-state').textContent).toBe(SOLVED_STATE);
    });

    // Update session mock
    vi.mocked(api.getSessions).mockResolvedValue([
      {
        session_id: 2,
        status: 'executing',
        selected_algorithm: 'CFOP',
        session_name: 'Test Session 2',
        started_at: '2026-03-30T13:00:00Z',
        completed_at: null,
      },
    ]);
    
    // Mock getScanState for session 2 to return a different state
    const NEW_STATE = 'RRRRRRRRRUUUUUUUUUFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB';
    vi.mocked(api.getScanState).mockImplementation(async (id: string | number) => {
        if (String(id) === '2') {
          return {
            session_id: 2,
            state_string: NEW_STATE,
            is_valid: true,
            confidence: 0.99,
            created_at: '2026-03-30T13:00:05Z',
          };
        }
        return {
          session_id: 1,
          state_string: SOLVED_STATE,
          is_valid: true,
          confidence: 0.99,
          created_at: '2026-03-30T12:00:05Z',
        };
    });

    // Invalidate queries to trigger update
    queryClient.invalidateQueries({ queryKey: ['sessions'] });

    // Wait for session change to propagate to cube state
    await waitFor(() => {
      expect(screen.getByTestId('cube-state').textContent).toBe(NEW_STATE);
    });
  });
});
