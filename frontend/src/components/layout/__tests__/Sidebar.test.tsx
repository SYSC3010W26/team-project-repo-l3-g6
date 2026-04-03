/**
 * @file Sidebar.test.tsx
 * @description Test for Layout component: Sidebar
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Sidebar from '../Sidebar';
import { startSolve } from '@/lib/api';
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('@/lib/api', () => ({
  startSolve: vi.fn(),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders navigation links', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Live Session')).toBeInTheDocument();
    expect(screen.getByText('Solve Results')).toBeInTheDocument();
    expect(screen.getByText('Execution Monitor')).toBeInTheDocument();
    expect(screen.getByText('Solution Review')).toBeInTheDocument();
    expect(screen.getByText('Lab Logs')).toBeInTheDocument();
  });

  it('calls startSolve when NEW SOLVE is clicked', async () => {
    vi.mocked(startSolve).mockResolvedValue({ session_id: 123 });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const newSolveButton = screen.getByText('NEW SOLVE');
    fireEvent.click(newSolveButton);

    await waitFor(() => {
      expect(startSolve).toHaveBeenCalled();
    });
  });
});
