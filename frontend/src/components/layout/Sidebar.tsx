import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/',          icon: 'precision_manufacturing', label: 'Live Session',      end: true },
  { to: '/results',   icon: 'bolt',                    label: 'Solve Results',     end: false },
  { to: '/execution', icon: 'settings_input_component', label: 'Execution Monitor', end: false },
  { to: '/review',    icon: 'list_alt',                label: 'Solution Review',   end: false },
  { to: '/logs',      icon: 'terminal',                label: 'Lab Logs',          end: false },
];

export default function Sidebar() {
  return (
    <aside className="h-screen w-64 fixed left-0 top-0 pt-20 bg-kl-surface-low hidden lg:flex flex-col z-40 shadow-2xl shadow-black/40">
      {/* Branding */}
      <div className="px-6 py-4 mb-4">
        <div className="text-lg font-headline font-bold text-white uppercase tracking-wider">
          KINETIC LAB
        </div>
        <div className="text-xs text-kl-secondary opacity-70">Precision v2.4</div>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-0.5 flex-1">
        {navItems.map(({ to, icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'px-6 py-3 flex items-center gap-3 transition-all duration-200 hover:translate-x-1',
                isActive
                  ? 'bg-kl-surface-high text-kl-secondary border-r-4 border-kl-secondary'
                  : 'text-kl-on-surface-variant hover:bg-kl-surface-high hover:text-white'
              )
            }
          >
            <span className="material-symbols-outlined text-[20px]">{icon}</span>
            <span className="text-sm font-medium">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom Section */}
      <div className="px-6 pb-6 space-y-4">
        <NavLink to="/">
          <button className="w-full bg-kl-primary text-[#3C0089] font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-all active:scale-95 glow-primary font-headline">
            <span className="material-symbols-outlined">add</span>
            <span>NEW SOLVE</span>
          </button>
        </NavLink>

        <div className="pt-4 border-t border-kl-outline-variant/10 space-y-1">
          <a href="#" className="text-kl-outline hover:text-white text-[10px] tracking-widest uppercase flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">help</span>
            <span>Support</span>
          </a>
          <a href="#" className="text-kl-outline hover:text-white text-[10px] tracking-widest uppercase flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">code</span>
            <span>API</span>
          </a>
        </div>
      </div>
    </aside>
  );
}
