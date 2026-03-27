import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import ErrorBanner from './ErrorBanner';

export default function AppShell() {
  return (
    <div className="min-h-screen bg-kl-background">
      <ErrorBanner />
      <TopBar />
      <Sidebar />
      <main className="lg:ml-64 pt-24 pb-12 px-8 min-h-screen">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
