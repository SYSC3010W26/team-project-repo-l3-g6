/**
 * @file App.tsx
 * @description Root application component that defines routes and provides the main application shell.
 */

import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import Dashboard from '@/pages/Dashboard';
import SolveResults from '@/pages/SolveResults';
import ExecutionMonitor from '@/pages/ExecutionMonitor';
import SolutionReview from '@/pages/SolutionReview';
import SystemLogs from '@/pages/SystemLogs';

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'results', element: <SolveResults /> },
      { path: 'execution', element: <ExecutionMonitor /> },
      { path: 'review/:sessionId?', element: <SolutionReview /> },
      { path: 'logs', element: <SystemLogs /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
