import { describe, expect, it, vi } from 'vitest';
import { screen } from '@testing-library/react';
import ExecutionMonitor from '@/pages/ExecutionMonitor';
import { renderWithAppProviders } from '@/test/renderApp';
import type { ExecutionProgressUpdate, SolutionStep, SolveSession } from '@/types/api';

const mockGetSessions = vi.hoisted(() => vi.fn<() => Promise<SolveSession[]>>());
const mockGetSolution = vi.hoisted(() => vi.fn<(sessionId: string) => Promise<{ steps: SolutionStep[] }>>());
const mockUseSocketEvent = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api', () => ({
  getSessions: mockGetSessions,
  getSolution: mockGetSolution,
}));

vi.mock('@/hooks/useSocket', () => ({
  useSocketEvent: mockUseSocketEvent,
}));

describe('ExecutionMonitor', () => {
  it('shows empty-state affordances when no active solve exists', async () => {
    mockGetSessions.mockResolvedValueOnce([]);

    renderWithAppProviders(<ExecutionMonitor />, { route: '/execution' });

    expect(await screen.findByText('No active solve')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go to Dashboard' })).toBeInTheDocument();
  });

  it('renders execution progress and move sequence for active session', async () => {
    mockGetSessions.mockResolvedValueOnce([
      {
        session_id: 42,
        status: 'executing',
        selected_algorithm: 'kociemba',
        session_name: null,
        started_at: '2026-03-27T12:00:00Z',
        completed_at: null,
      },
    ]);

    mockGetSolution.mockResolvedValueOnce({
      steps: [
        { step_index: 0, move_notation: 'R' },
        { step_index: 1, move_notation: "U'" },
      ],
    });

    const progress: ExecutionProgressUpdate = {
      session_id: '42',
      current_step: 1,
      total_steps: 2,
      move: "U'",
      pct_complete: 0.5,
    };

    mockUseSocketEvent.mockImplementation((_event: string, handler: (data: any) => void) => {
      handler(progress);
    });

    renderWithAppProviders(<ExecutionMonitor />, { route: '/execution' });

    expect(await screen.findByText('Session #42')).toBeInTheDocument();
    expect(await screen.findByText("U'")).toBeInTheDocument();
    expect(screen.getByText('50% complete')).toBeInTheDocument();
    expect(screen.getByText('Move Sequence')).toBeInTheDocument();
  });
});
