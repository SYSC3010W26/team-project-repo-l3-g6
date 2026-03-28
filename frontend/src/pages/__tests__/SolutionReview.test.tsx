import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, Link } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import SolutionReview from '../SolutionReview';
import { createTestQueryClient } from '@/test/renderApp';
import type { SolutionStep } from '@/types/api';

const mockGetSolution = vi.hoisted(() => vi.fn());
const mockGetSessions = vi.hoisted(() => vi.fn());
const mockGetScanState = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api', () => ({
  getSolution: mockGetSolution,
  getSessions: mockGetSessions,
  getScanState: mockGetScanState,
}));

vi.mock('@/components/dashboard/CubeViewer3D', () => ({
  default: vi.fn(({ stateString }) => <div data-testid="cube-viewer-3d">{stateString}</div>),
}));

function renderReviewRoute(path = '/review/7') {
  const queryClient = createTestQueryClient();
  mockGetSessions.mockResolvedValue([]);
  mockGetScanState.mockResolvedValue({ state: 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB' });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/review/:sessionId" element={<SolutionReview />} />
          <Route path="/results" element={<div>Results page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('SolutionReview', () => {
  it('renders session metadata and step navigation affordances', async () => {
    const user = userEvent.setup();
    const steps: SolutionStep[] = [
      { step_index: 0, move_notation: 'R' },
      { step_index: 1, move_notation: 'U' },
      { step_index: 2, move_notation: 'F2' },
    ];

    mockGetSolution.mockResolvedValueOnce({
      algorithm_used: 'Kociemba',
      steps,
    });

    renderReviewRoute('/review/7');

    expect(await screen.findByText('Solution Review')).toBeInTheDocument();
    expect(screen.getByText('Session #7')).toBeInTheDocument();
    expect(screen.getByText('Kociemba')).toBeInTheDocument();
    expect(screen.getByText('3 moves')).toBeInTheDocument();
    expect(screen.getByTestId('cube-viewer-3d')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Next step' }));

    expect(screen.getByText('Step 1 / 3')).toBeInTheDocument();
    // After 'R' move (move 0), the state should change.
    // Initial state is solved state in my mock.
    // 'R' move on solved state:
    // U stays U except right edge... actually applyMove will handle it.
    // I don't need to know the EXACT string, just that it's NOT the solved state anymore.
    expect(screen.getByTestId('cube-viewer-3d').textContent).not.toBe('UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB');

    await user.click(screen.getByRole('button', { name: 'Next step' }));
    await user.click(screen.getByRole('button', { name: 'Next step' }));
    expect(screen.getByText('Step 3 / 3')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Next step' })).toBeDisabled();
  });

  it('resets currentStep when navigating between sessions', async () => {
    const user = userEvent.setup();
    const queryClient = createTestQueryClient();

    mockGetSolution.mockImplementation(async (id: string) => {
      if (id === '7') {
        return {
          algorithm_used: 'Kociemba',
          steps: [{ step_index: 0, move_notation: 'R' }, { step_index: 1, move_notation: 'U' }],
        };
      }
      return {
        algorithm_used: 'Kociemba',
        steps: [{ step_index: 0, move_notation: 'L' }, { step_index: 1, move_notation: 'D' }],
      };
    });

    const { findByText } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/review/7']}>
          <Routes>
            <Route path="/review/:sessionId" element={<SolutionReview />} />
          </Routes>
          <Link to="/review/8">Go to Session 8</Link>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(await findByText('Session #7')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Next step' }));
    expect(screen.getByText('Step 1 / 2')).toBeInTheDocument();

    await user.click(screen.getByText('Go to Session 8'));
    expect(await findByText('Session #8')).toBeInTheDocument();
    
    expect(screen.getByText('Step 0 / 2')).toBeInTheDocument();
  });

  it('stops autoplay when navigating between sessions', async () => {
    const user = userEvent.setup();
    const queryClient = createTestQueryClient();

    mockGetSolution.mockImplementation(async () => ({
      algorithm_used: 'Kociemba',
      steps: [{ step_index: 0, move_notation: 'R' }, { step_index: 1, move_notation: 'U' }],
    }));

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/review/7']}>
          <Routes>
            <Route path="/review/:sessionId" element={<SolutionReview />} />
          </Routes>
          <Link to="/review/8">Go to Session 8</Link>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(await screen.findByText('Session #7')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Play autoplay' }));
    expect(screen.getByLabelText('Pause autoplay')).toBeInTheDocument();

    await user.click(screen.getByText('Go to Session 8'));
    expect(await screen.findByText('Session #8')).toBeInTheDocument();
    
    // Autoplay should probably stop on navigation
    expect(screen.getByLabelText('Play autoplay')).toBeInTheDocument();
  });

  it('handles sessions with no solution steps gracefully', async () => {
    mockGetSolution.mockResolvedValueOnce({
      algorithm_used: 'Kociemba',
      steps: [],
    });

    renderReviewRoute('/review/empty');

    expect(await screen.findByText('No moves recorded for this session.')).toBeInTheDocument();
    expect(screen.getByText('Step 0 / 0')).toBeInTheDocument();
  });

  it('shows missing-session fallback when solution query fails', async () => {
    mockGetSolution.mockRejectedValueOnce(new Error('not found'));

    renderReviewRoute('/review/99');

    expect(await screen.findByText('Session not found.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Back to Results' })).toBeInTheDocument();
  });
});
