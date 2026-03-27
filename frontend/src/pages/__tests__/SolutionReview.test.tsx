import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import SolutionReview from '@/pages/SolutionReview';
import { createTestQueryClient } from '@/test/renderApp';
import type { SolutionStep } from '@/types/api';

const mockGetSolution = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api', () => ({
  getSolution: mockGetSolution,
}));

function renderReviewRoute(path = '/review/7') {
  const queryClient = createTestQueryClient();

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

    await user.click(screen.getByRole('button', { name: /next/i }));

    expect(screen.getByText('Step 2 / 3')).toBeInTheDocument();
  });

  it('shows missing-session fallback when solution query fails', async () => {
    mockGetSolution.mockRejectedValueOnce(new Error('not found'));

    renderReviewRoute('/review/99');

    expect(await screen.findByText('Session not found.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Back to Results' })).toBeInTheDocument();
  });
});
