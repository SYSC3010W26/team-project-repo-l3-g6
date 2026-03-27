import { NavLink } from 'react-router-dom';
import { LayoutDashboard, History, Activity, BookOpen, ScrollText } from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/results', icon: History, label: 'Solve Results', end: false },
  { to: '/execution', icon: Activity, label: 'Execution Monitor', end: false },
  { to: '/review', icon: BookOpen, label: 'Solution Review', end: false },
  { to: '/logs', icon: ScrollText, label: 'System Logs', end: false },
];

export default function Sidebar() {
  return (
    <aside className="hidden md:flex flex-col w-60 min-h-screen bg-slate-900 border-r border-slate-800 py-6">
      <div className="px-4 mb-8">
        <h1 className="text-lg font-bold text-white tracking-tight">Pi³ Solver</h1>
        <p className="text-xs text-slate-500 mt-0.5">Dashboard</p>
      </div>
      <nav className="flex flex-col gap-1 px-2">
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-blue-600/20 text-blue-400 font-medium'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
