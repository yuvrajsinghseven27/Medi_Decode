import { useState, useEffect } from 'react';
import { TopBar } from './components/TopBar';
import { Navigation } from './components/Navigation';
import type { NavTab } from './components/Navigation';
import { PrescriptionCard } from './components/PrescriptionCard';
import type { Prescription } from './components/PrescriptionCard';
import { ScheduleTimeline } from './components/ScheduleTimeline';
import {
  UploadCloud,
  AlertTriangle,
  Pill,
  Sparkles,
  ShieldAlert,
  Clock,
} from 'lucide-react';

const mockPrescriptions: Prescription[] = [
  {
    id: 'rx_01',
    brandName: 'Lipitor',
    genericName: 'Atorvastatin Calcium',
    dosage: '20mg',
    form: 'Tablet',
    doctorName: 'Dr. Evelyn Reed, MD',
    clinic: 'St. Jude Heart & Vascular Center',
    prescribedDate: '2026-08-20',
    frequency: 'Once daily at bedtime',
    timingInstructions: 'Take with a full glass of water before sleep. Avoid grapefruit juice.',
    refillsRemaining: 3,
    status: 'active',
    confidenceScore: 0.98,
    warnings: [
      'Avoid consumption of grapefruit or grapefruit juice due to elevated bioavailability risk.',
      'Report any unexplained muscle pain or weakness promptly.',
    ],
    foodInteractions: ['Grapefruit / Citrus paradisi (CYP3A4 inhibition)'],
  },
  {
    id: 'rx_02',
    brandName: 'Glucophage',
    genericName: 'Metformin HCl',
    dosage: '500mg',
    form: 'Tablet',
    doctorName: 'Dr. Marcus Vance, MD',
    clinic: 'Metropolitan Endocrinology Group',
    prescribedDate: '2026-08-15',
    frequency: 'Twice daily with meals (Breakfast & Dinner)',
    timingInstructions: 'Take strictly with or immediately after food to minimize GI discomfort.',
    refillsRemaining: 1,
    status: 'refill_needed',
    confidenceScore: 0.95,
    warnings: ['Stay well hydrated. Avoid excessive alcohol consumption.'],
  },
  {
    id: 'rx_03',
    brandName: 'Synthroid',
    genericName: 'Levothyroxine Sodium',
    dosage: '50mcg',
    form: 'Tablet',
    doctorName: 'Dr. Marcus Vance, MD',
    clinic: 'Metropolitan Endocrinology Group',
    prescribedDate: '2026-07-28',
    frequency: 'Once daily in the morning',
    timingInstructions: 'Take 30-60 minutes before breakfast with plain water only.',
    refillsRemaining: 4,
    status: 'active',
    confidenceScore: 0.99,
    warnings: ['Do not take within 4 hours of calcium or iron supplements.'],
  },
];

export function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [backendStatus, setBackendStatus] = useState<'connected' | 'checking' | 'offline'>('checking');
  const [backendVersion, setBackendVersion] = useState<string>('0.1.0');
  const [isUploading, setIsUploading] = useState(false);
  const [prescriptions] = useState<Prescription[]>(mockPrescriptions);

  // Health check polling on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/healthz');
        if (res.ok) {
          const data = await res.json();
          setBackendStatus('connected');
          if (data.version) setBackendVersion(data.version);
        } else {
          setBackendStatus('offline');
        }
      } catch {
        setBackendStatus('offline');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulateUpload = () => {
    setIsUploading(true);
    setTimeout(() => {
      setIsUploading(false);
      alert('Prescription document received! In full mode, Gemini Flash will extract medications and dosage rules.');
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header Bar */}
      <TopBar
        backendStatus={backendStatus}
        backendVersion={backendVersion}
        onUploadClick={handleSimulateUpload}
      />

      <div className="flex flex-1">
        {/* Navigation (Sidebar on desktop / BottomNav on mobile) */}
        <Navigation
          activeTab={activeTab}
          onTabChange={setActiveTab}
          safetyAlertCount={1}
        />

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full pb-20 md:pb-8">
          {/* Active Safety Conflict Banner */}
          <div className="mb-6 rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent p-4 sm:p-5 flex items-start gap-3 sm:gap-4 shadow-lg shadow-amber-950/10">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h2 className="text-sm sm:text-base font-bold text-amber-200">
                  Potential Spacing Interaction Detected
                </h2>
                <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300">
                  Moderate Risk
                </span>
              </div>
              <p className="mt-1 text-xs sm:text-sm text-slate-300 leading-relaxed">
                Levothyroxine Sodium absorption is reduced when taken concurrently with calcium, iron, or multivitamins. Ensure a minimum <strong>4-hour separation</strong> window.
              </p>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Active Regimen</span>
                <Pill className="h-4 w-4 text-teal-400" />
              </div>
              <p className="text-2xl font-bold text-white mt-1">3 Meds</p>
              <p className="text-[11px] text-teal-400 mt-1">All scanned via Gemini AI</p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Today's Doses</span>
                <Clock className="h-4 w-4 text-emerald-400" />
              </div>
              <p className="text-2xl font-bold text-white mt-1">2 / 5 Taken</p>
              <p className="text-[11px] text-emerald-400 mt-1">40% completed today</p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Safety Checks</span>
                <Sparkles className="h-4 w-4 text-teal-400" />
              </div>
              <p className="text-2xl font-bold text-white mt-1">RxNorm Safe</p>
              <p className="text-[11px] text-slate-400 mt-1">0 Critical Contraindications</p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Refill Alert</span>
                <AlertTriangle className="h-4 w-4 text-amber-400" />
              </div>
              <p className="text-2xl font-bold text-amber-300 mt-1">1 Med Due</p>
              <p className="text-[11px] text-slate-400 mt-1">Metformin (1 refill left)</p>
            </div>
          </div>

          {/* Prescription Upload Dropzone */}
          <div className="mb-8 rounded-2xl border-2 border-dashed border-slate-800 hover:border-teal-500/50 bg-slate-900/40 p-6 sm:p-8 text-center transition-all cursor-pointer group">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-500/10 text-teal-400 group-hover:scale-110 transition-transform shadow-inner">
              <UploadCloud className="h-7 w-7" />
            </div>
            <h3 className="mt-4 text-base sm:text-lg font-bold text-white">
              Upload or Scan Medical Prescription
            </h3>
            <p className="mt-1 text-xs sm:text-sm text-slate-400 max-w-md mx-auto">
              Drag and drop prescription photos (JPEG, PNG) or pharmacy PDFs. Gemini 2.5 Flash extracts medication names, dosage instructions, and schedules automatically.
            </p>
            <div className="mt-4 flex items-center justify-center gap-3">
              <button
                onClick={handleSimulateUpload}
                disabled={isUploading}
                className="rounded-xl bg-teal-500 px-5 py-2 text-xs sm:text-sm font-semibold text-slate-950 shadow-md shadow-teal-500/20 hover:bg-teal-400 transition-colors disabled:opacity-50 cursor-pointer"
              >
                {isUploading ? 'Analyzing via Gemini AI...' : 'Choose File or Take Photo'}
              </button>
            </div>
          </div>

          {/* Section: Timeline and Prescriptions */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Schedule Timeline Column */}
            <div className="lg:col-span-6 space-y-6">
              <ScheduleTimeline />
            </div>

            {/* Prescriptions Grid Column */}
            <div className="lg:col-span-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base sm:text-lg font-bold text-white">Active Prescriptions</h3>
                  <p className="text-xs text-slate-400">Digitized and validated medications</p>
                </div>
                <span className="text-xs font-semibold text-teal-400">
                  {prescriptions.length} Records
                </span>
              </div>

              <div className="space-y-4">
                {prescriptions.map((rx) => (
                  <PrescriptionCard key={rx.id} prescription={rx} />
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
