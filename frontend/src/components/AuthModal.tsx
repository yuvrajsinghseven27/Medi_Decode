import { useState } from 'react';
import { User, Key, X, Shield, ExternalLink, Activity, Sparkles } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPatientName: string;
  onSelectPatient: (name: string, id: string) => void;
}

export function AuthModal({ isOpen, onClose, currentPatientName, onSelectPatient }: AuthModalProps) {
  const [email, setEmail] = useState('ramesh.patel@example.com');
  const [password, setPassword] = useState('••••••••');
  const [activeTab, setActiveTab] = useState<'signin' | 'portal_links'>('signin');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-teal-500/30 p-6 shadow-2xl shadow-teal-950/60 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-500/20 text-teal-400 border border-teal-500/30">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Patient Account & System Hub</h3>
              <p className="text-[11px] text-slate-400">Manage patient sessions & platform links</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex rounded-xl bg-slate-950 p-1 border border-slate-800">
          <button
            onClick={() => setActiveTab('signin')}
            className={`flex-1 rounded-lg py-1.5 text-xs font-bold transition-all ${
              activeTab === 'signin'
                ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Patient Sign In
          </button>
          <button
            onClick={() => setActiveTab('portal_links')}
            className={`flex-1 rounded-lg py-1.5 text-xs font-bold transition-all ${
              activeTab === 'portal_links'
                ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All System Links
          </button>
        </div>

        {activeTab === 'signin' ? (
          <div className="space-y-4">
            {/* Active Seeded Patient Card */}
            <div className="rounded-2xl border border-teal-500/40 bg-teal-950/20 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold tracking-wider text-teal-400 uppercase">
                  Active Clinical Patient
                </span>
                <span className="rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-semibold px-2 py-0.5">
                  Live in DB
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-white">{currentPatientName}</h4>
                  <p className="text-[11px] text-slate-400">Age: 62 | Hindi | Hypertension & T2D</p>
                </div>
                <button
                  onClick={() => {
                    onSelectPatient('Ramesh Patel', '68fda962-765d-42c5-b199-6e355d9b80a4');
                    onClose();
                  }}
                  className="rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold px-3 py-1.5 transition-colors"
                >
                  Active
                </button>
              </div>
            </div>

            {/* Form */}
            <div className="space-y-3">
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                />
              </div>
              <div>
                <label className="text-[11px] font-medium text-slate-300 block mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                />
              </div>
            </div>

            <button
              onClick={() => {
                onSelectPatient(email.split('@')[0], 'user_' + Date.now());
                onClose();
              }}
              className="w-full rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold py-2.5 transition-colors shadow-lg shadow-teal-500/20"
            >
              Sign In to Patient Portal
            </button>
          </div>
        ) : (
          /* All System Links View */
          <div className="space-y-3">
            <p className="text-xs text-slate-400">
              Access any sub-portal or developer utility directly from this unified interface:
            </p>

            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-xl bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-slate-200 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-500/20 text-teal-400">
                  <Key className="h-4 w-4" />
                </div>
                <div>
                  <h5 className="text-xs font-bold text-white group-hover:text-teal-300">
                    Interactive API Documentation (Swagger)
                  </h5>
                  <p className="text-[10px] text-slate-400">Test all REST endpoints & schema contracts</p>
                </div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-teal-400" />
            </a>

            <a
              href="/healthz"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-xl bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-slate-200 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
                  <Activity className="h-4 w-4" />
                </div>
                <div>
                  <h5 className="text-xs font-bold text-white group-hover:text-emerald-300">
                    System Health Probe
                  </h5>
                  <p className="text-[10px] text-slate-400">Uptime & version JSON monitor</p>
                </div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-emerald-400" />
            </a>

            <a
              href="/login"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-xl bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-slate-200 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-400">
                  <User className="h-4 w-4" />
                </div>
                <div>
                  <h5 className="text-xs font-bold text-white group-hover:text-indigo-300">
                    Dedicated Standalone Login Page
                  </h5>
                  <p className="text-[10px] text-slate-400">Direct full-screen login portal</p>
                </div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-indigo-400" />
            </a>

            <a
              href="/signup"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-3 rounded-xl bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-slate-200 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/20 text-purple-400">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <h5 className="text-xs font-bold text-white group-hover:text-purple-300">
                    Dedicated Registration Portal
                  </h5>
                  <p className="text-[10px] text-slate-400">New patient intake & onboarding</p>
                </div>
              </div>
              <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-purple-400" />
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
