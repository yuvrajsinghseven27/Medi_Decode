import React from 'react';
import {
  LayoutDashboard,
  FileText,
  CalendarClock,
  ShieldAlert,
  History,
  Pill,
  ClipboardList,
} from 'lucide-react';

export type NavTab = 'overview' | 'prescriptions' | 'schedule' | 'safety' | 'reports' | 'history';

interface NavigationProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  safetyAlertCount?: number;
}

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  onTabChange,
  safetyAlertCount = 1,
}) => {
  const navItems = [
    { id: 'overview' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'schedule' as NavTab, label: 'Dose Schedule', icon: CalendarClock },
    { id: 'prescriptions' as NavTab, label: 'Prescriptions', icon: FileText },
    {
      id: 'safety' as NavTab,
      label: 'Safety & DDIs',
      icon: ShieldAlert,
      badge: safetyAlertCount,
    },
    { id: 'reports' as NavTab, label: 'Lab Reports', icon: ClipboardList },
    { id: 'history' as NavTab, label: 'Intake Log', icon: History },
  ];

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-64 flex-col justify-between border-r border-slate-800 bg-slate-900/60 p-4 min-h-[calc(100vh-4rem)]">
        <div className="space-y-6">
          {/* Patient Quick Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-800/40 p-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-500/10 text-teal-400">
                <Pill className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-200">Active Regimen</p>
                <p className="text-xs text-slate-400">4 Active Medications</p>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Menu
            </p>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={`group flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-teal-500/15 text-teal-300 font-semibold shadow-sm shadow-teal-500/10'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      className={`h-4 w-4 transition-colors ${
                        isActive ? 'text-teal-400' : 'text-slate-400 group-hover:text-slate-300'
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>
                  {item.badge ? (
                    <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-xs font-semibold text-rose-400 ring-1 ring-rose-500/30">
                      {item.badge}
                    </span>
                  ) : null}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="border-t border-slate-800 pt-4 space-y-2">
          <div className="rounded-lg bg-teal-950/40 border border-teal-800/40 p-3 text-xs text-teal-300">
            <p className="font-semibold flex items-center gap-1.5">
              <span>🛡️</span> AI Safety Guard
            </p>
            <p className="mt-1 text-[11px] text-slate-400 leading-relaxed">
              Powered by Google Gemini 2.5 multimodal clinical OCR.
            </p>
          </div>
        </div>
      </aside>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 flex h-16 items-center justify-around border-t border-slate-800 bg-slate-900/95 px-2 backdrop-blur-lg">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`relative flex flex-col items-center justify-center gap-1 py-1 px-3 text-[10px] font-medium transition-colors ${
                isActive ? 'text-teal-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className={`h-5 w-5 ${isActive ? 'text-teal-400' : 'text-slate-400'}`} />
              <span>{item.label.split(' ')[0]}</span>
              {item.badge ? (
                <span className="absolute top-1 right-2 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-rose-500 text-[9px] font-bold text-white">
                  {item.badge}
                </span>
              ) : null}
            </button>
          );
        })}
      </nav>
    </>
  );
};
