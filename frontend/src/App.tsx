import { useState, useEffect, useCallback } from 'react';
import { TopBar } from './components/TopBar';
import { Navigation } from './components/Navigation';
import type { NavTab } from './components/Navigation';
import { PrescriptionCard } from './components/PrescriptionCard';
import type { Prescription } from './components/PrescriptionCard';
import { UploadVerificationScreen } from './components/UploadVerificationScreen';
import { SafetyAlertPanel } from './components/SafetyAlertPanel';
import { DailyScheduleDashboard } from './components/DailyScheduleDashboard';
import { api } from './services/api';
import type {
  SafetyAlertRead,
  CumulativeToxicityAlert,
  FastingAdjustment,
  ReconciliationResponse,
  DailyScheduleView,
  UserProfile,
  PrescriptionRecord,
} from './services/api';
import {
  UploadCloud,
  Pill,
  Sparkles,
  ShieldAlert,
  Clock,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';

const mockPrescriptions: Prescription[] = [
  {
    id: 'rx_01',
    brandName: 'Dolo 650',
    genericName: 'Paracetamol',
    dosage: '650mg',
    form: 'Tablet',
    doctorName: 'Dr. Evelyn Reed, MD',
    clinic: 'Metro Health Cardiology',
    prescribedDate: '2026-09-01',
    frequency: 'TID (Three times daily)',
    timingInstructions: 'Take after meals with plain water.',
    refillsRemaining: 2,
    status: 'active',
    confidenceScore: 0.98,
    warnings: [
      'Cumulative Paracetamol daily intake must not exceed 4,000mg.',
      'Report fever persisting beyond 3 days.',
    ],
    foodInteractions: ['Avoid alcohol intake during therapy'],
  },
  {
    id: 'rx_02',
    brandName: 'Thyronorm',
    genericName: 'Levothyroxine Sodium',
    dosage: '50mcg',
    form: 'Tablet',
    doctorName: 'Dr. Marcus Vance, MD',
    clinic: 'Metropolitan Endocrinology Group',
    prescribedDate: '2026-08-25',
    frequency: 'OD (Once daily morning AC)',
    timingInstructions: 'Take 30-60 minutes before breakfast on an empty stomach.',
    refillsRemaining: 4,
    status: 'active',
    confidenceScore: 0.99,
    warnings: ['Separate milk tea (chai) and calcium/dairy intake by at least 2 hours.'],
    foodInteractions: ['High-tannin milk tea blunts absorption'],
  },
  {
    id: 'rx_03',
    brandName: 'Glycomet GP 1',
    genericName: 'Metformin HCl + Glimepiride',
    dosage: '500mg/1mg',
    form: 'Tablet',
    doctorName: 'Dr. Marcus Vance, MD',
    clinic: 'Metropolitan Endocrinology Group',
    prescribedDate: '2026-08-20',
    frequency: 'BD (Twice daily with meals)',
    timingInstructions: 'Take strictly with breakfast and dinner to avoid hypoglycemia.',
    refillsRemaining: 1,
    status: 'refill_needed',
    confidenceScore: 0.94,
    warnings: ['Monitor blood glucose levels regularly during Ramadan fasting.'],
  },
];

const INITIAL_SCHEDULE: DailyScheduleView = {
  date: new Date().toISOString().split('T')[0],
  morning: [
    {
      id: 'dose_01',
      medication_id: 'med_01',
      brand_name: 'Thyronorm',
      generic_molecule: 'Levothyroxine',
      form: 'Tablet',
      strength: '50mcg',
      frequency: 'OD',
      timing_relation: 'AC',
      scheduled_timestamp: new Date().toISOString(),
      time_str: '06:30 AM',
      status: 'PENDING',
      remaining_pills: 28,
      is_low_stock: false,
      instructions: 'Take 30 mins before food on an empty stomach (Avoid morning chai)',
    },
    {
      id: 'dose_02',
      medication_id: 'med_02',
      brand_name: 'Glycomet GP 1',
      generic_molecule: 'Metformin + Glimepiride',
      form: 'Tablet',
      strength: '500mg',
      frequency: 'BD',
      timing_relation: 'PC',
      scheduled_timestamp: new Date().toISOString(),
      time_str: '08:30 AM',
      status: 'PENDING',
      remaining_pills: 3, // Low stock -> <= 3 days!
      is_low_stock: true,
      instructions: 'Take 30 mins after breakfast',
    },
  ],
  afternoon: [
    {
      id: 'dose_03',
      medication_id: 'med_03',
      brand_name: 'Dolo 650',
      generic_molecule: 'Paracetamol',
      form: 'Tablet',
      strength: '650mg',
      frequency: 'TID',
      timing_relation: 'PC',
      scheduled_timestamp: new Date().toISOString(),
      time_str: '01:30 PM',
      status: 'PENDING',
      remaining_pills: 6,
      is_low_stock: false,
      instructions: 'Take 30 mins after lunch',
    },
  ],
  evening: [
    {
      id: 'dose_04',
      medication_id: 'med_02',
      brand_name: 'Glycomet GP 1',
      generic_molecule: 'Metformin + Glimepiride',
      form: 'Tablet',
      strength: '500mg',
      frequency: 'BD',
      timing_relation: 'PC',
      scheduled_timestamp: new Date().toISOString(),
      time_str: '08:30 PM',
      status: 'PENDING',
      remaining_pills: 3,
      is_low_stock: true,
      instructions: 'Take 30 mins after dinner',
    },
  ],
  bedtime: [],
  total_doses: 4,
  taken_doses: 0,
  adherence_percentage: 0,
};

function mapBackendPrescriptions(records: PrescriptionRecord[]): Prescription[] {
  const list: Prescription[] = [];
  for (const rx of records) {
    for (const item of rx.medication_items || []) {
      list.push({
        id: item.id || rx.id,
        brandName: item.brand_name || item.generic_molecule || 'Prescribed Med',
        genericName: item.generic_molecule || item.brand_name || 'Generic Molecule',
        dosage: item.strength || 'Standard Dose',
        form: item.form === 'Capsule' ? 'Capsule' : item.form === 'Liquid' ? 'Liquid' : item.form === 'Inhaler' ? 'Inhaler' : 'Tablet',
        doctorName: rx.doctor_name || 'Attending Physician',
        clinic: rx.doctor_specialty ? `${rx.doctor_specialty} Care` : 'Metro Health Cardiology',
        prescribedDate: rx.date_prescribed || rx.created_at?.slice(0, 10) || 'Recent',
        frequency: item.frequency || 'OD',
        timingInstructions:
          item.timing_relation === 'AC'
            ? 'Take 30 mins before food on an empty stomach'
            : item.timing_relation === 'PC'
            ? 'Take 30 mins after food'
            : 'Take with food',
        refillsRemaining: item.remaining_pills !== undefined ? Math.floor(item.remaining_pills / 2) : 5,
        status: item.remaining_pills !== undefined && item.remaining_pills <= 3 ? 'refill_needed' : 'active',
        confidenceScore: 0.95,
        warnings: item.remaining_pills !== undefined && item.remaining_pills <= 3 ? ['Refill Due: Low pill stock remaining'] : [],
      });
    }
  }
  return list;
}

export function App() {
  const [activeTab, setActiveTab] = useState<NavTab>(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab') as NavTab;
      if (['overview', 'prescriptions', 'schedule', 'safety', 'history'].includes(tabParam)) {
        return tabParam;
      }
    } catch {
      // Fallback
    }
    return 'overview';
  });
  const [backendStatus, setBackendStatus] = useState<'connected' | 'checking' | 'offline'>('checking');
  const [backendVersion, setBackendVersion] = useState<string>('0.1.0');
  const [preferredLanguage, setPreferredLanguage] = useState<string>(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const lang = params.get('lang');
      if (['en', 'hi', 'ta', 'te', 'bn'].includes(lang || '')) return lang!;
    } catch {
      // Fallback
    }
    return 'en';
  });

  // Clinical & Patient State
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>(mockPrescriptions);
  const [alerts, setAlerts] = useState<SafetyAlertRead[]>([
    {
      id: 'init_alert_01',
      user_id: 'default_user',
      alert_type: 'FOOD_INTERACTION',
      severity: 'MODERATE',
      advisory_text:
        'Cultural Dietary Conflict: Tannins and casein in daily morning milk tea (chai) blunt Levothyroxine absorption. Maintain a strict 2-hour separation window.',
      localized_advisory: {
        hi: 'चाय में मौजूद टैनिन इस दवा के अवशोषण को रोकते हैं। दवा लेने के 2 घंटे पहले और बाद तक दूध वाली चाय न पिएं।',
        ta: 'தேநீரில் உள்ள டானின் சத்து இந்த மருந்தின் சத்து உறிஞ்சுதலைத் தடுக்கிறது. மருந்து உட்கொள்வதற்கு 2 மணி நேரத்திற்குள் தேநீர் அருந்த வேண்டாம்.',
        te: 'టీలోని టానిన్లు ఈ ఔషధ శోషణను అడ్డుకుంటాయి. మందు తీసుకునే 2 గంటల ముందు మరియు తరువాత టీ తాగవద్దు.',
        bn: 'দুধ চায়ে থাকা ট্যানিন এই ওষুধের শোষণ ব্যাহত করে। ওষুধ খাওয়ার ২ ঘণ্টার মধ্যে চা খাবেন না।',
      },
      created_at: new Date().toISOString(),
    },
    {
      id: 'init_alert_02',
      user_id: 'default_user',
      alert_type: 'DUPLICATE_MOLECULE',
      severity: 'CRITICAL',
      advisory_text:
        "Duplicate Molecule Alert: Paracetamol is prescribed under both 'Dolo 650' and 'Crocin'. Concomitant intake risks exceeding the 4,000mg daily ceiling.",
      localized_advisory: {
        hi: 'चेतावनी: पेरासिटामोल डोलो और क्रोसिन दोनों में मौजूद है। दोनों को एक साथ लेने से बचें।',
        ta: 'எச்சரிக்கை: பாராசிட்டமால் இரண்டு வெவ்வேறு பெயர்களில் பரிந்துரைக்கப்பட்டுள்ளது.',
        te: 'హెచ్చరిక: పారాసిటమాల్ రెండు వేర్వేరు బ్రాండ్ పేర్లతో ఇవ్వబడింది.',
        bn: 'সতর্কতা: প্যারাসিটামল দুটি ভিন্ন নামে প্রেসক্রিপশনে রয়েছে।',
      },
      created_at: new Date().toISOString(),
    },
  ]);
  const [cumulativeToxicities, setCumulativeToxicities] = useState<CumulativeToxicityAlert[]>([]);
  const [fastingAdjustments, setFastingAdjustments] = useState<FastingAdjustment[]>([]);
  const [doctorQuerySummary, setDoctorQuerySummary] = useState<string | undefined>(
    '# MediDecode Clinical Safety & Multi-Script Reconciliation Report\n\n**Patient Name**: Primary Patient  \n**Date Generated**: 2026-09-03 11:45 UTC  \n\n---\n\n## ⚠️ Clinical Attention Required Prior to Dispensation\n\n### 1. Duplicate Molecule Overlap:\n- **Paracetamol (Acetaminophen)**: Actively prescribed as **Dolo 650mg** (TID = 1950mg) and **Crocin 500mg** (BD = 1000mg).\n- Cumulative Daily Dose: **2,950 mg/day** (Safe Ceiling: 4,000 mg/day).\n\n### 2. Clinician Consultation Query:\n> *"Doctor, the patient has active prescriptions containing Paracetamol from multiple clinicians. Please confirm if one should be discontinued to prevent accidental acute hepatotoxicity."*'
  );

  // Schedule State
  const [scheduleData, setScheduleData] = useState<DailyScheduleView>(INITIAL_SCHEDULE);

  const loadLiveBackendData = useCallback(async (userId: string) => {
    try {
      const [schedRes, alertsRes, rxRes] = await Promise.allSettled([
        api.getTodaySchedule(userId),
        api.getSafetyAdvisories(userId),
        api.getPrescriptions(userId),
      ]);

      if (schedRes.status === 'fulfilled' && schedRes.value && schedRes.value.total_doses > 0) {
        setScheduleData(schedRes.value);
      }
      if (alertsRes.status === 'fulfilled' && alertsRes.value && alertsRes.value.length > 0) {
        setAlerts(alertsRes.value);
      }
      if (rxRes.status === 'fulfilled' && rxRes.value && rxRes.value.length > 0) {
        const mapped = mapBackendPrescriptions(rxRes.value);
        if (mapped.length > 0) {
          setPrescriptions(mapped);
        }
      }
    } catch (err) {
      console.warn('Non-fatal error loading live backend data:', err);
    }
  }, []);

  // Sync with live backend on mount & periodically
  useEffect(() => {
    let isMounted = true;

    const syncWithBackend = async () => {
      try {
        const data = await api.checkHealth();
        if (!isMounted) return;
        setBackendStatus('connected');
        if (data.version) setBackendVersion(data.version);

        try {
          const user = await api.getDefaultUser();
          if (!isMounted) return;
          setCurrentUser(user);
          if (user.preferred_language && !window.location.search.includes('lang=')) {
            setPreferredLanguage(user.preferred_language);
          }
          await loadLiveBackendData(user.id);
        } catch (uErr) {
          console.warn('Unable to sync patient profile:', uErr);
        }
      } catch {
        if (!isMounted) return;
        setBackendStatus('offline');
      }
    };

    syncWithBackend();
    const interval = setInterval(syncWithBackend, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [loadLiveBackendData]);

  const handleReconciliationComplete = (response: ReconciliationResponse) => {
    if (response.alerts && response.alerts.length > 0) {
      setAlerts(response.alerts);
    }
    if (response.cumulative_toxicities) {
      setCumulativeToxicities(response.cumulative_toxicities);
    }
    if (response.fasting_adjustments) {
      setFastingAdjustments(response.fasting_adjustments);
    }
    if (response.doctor_query_summary) {
      setDoctorQuerySummary(response.doctor_query_summary);
    }

    if (currentUser?.id) {
      loadLiveBackendData(currentUser.id);
    }

    // Route to safety panel to review results
    setActiveTab('safety');
  };

  const handleDoseUpdated = useCallback(() => {
    if (currentUser?.id) {
      api.getTodaySchedule(currentUser.id)
        .then((fresh) => {
          if (fresh && fresh.total_doses > 0) {
            setScheduleData(fresh);
          }
        })
        .catch(() => {
          // Fallback local update
          setScheduleData((prev) => {
            let taken = 0;
            let total = 0;
            const updateSlot = (items: typeof prev.morning) =>
              items.map((item) => {
                total += 1;
                if (item.status === 'TAKEN') taken += 1;
                return item;
              });
            return {
              ...prev,
              morning: updateSlot(prev.morning),
              afternoon: updateSlot(prev.afternoon),
              evening: updateSlot(prev.evening),
              bedtime: updateSlot(prev.bedtime),
              total_doses: total,
              taken_doses: taken,
              adherence_percentage: total > 0 ? Math.round((taken / total) * 100) : 0,
            };
          });
        });
    }
  }, [currentUser]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header Bar */}
      <TopBar
        backendStatus={backendStatus}
        backendVersion={backendVersion}
        patientName={currentUser?.full_name || 'Ramesh Patel'}
        patientId={currentUser ? `#MED-${currentUser.id.slice(0, 4).toUpperCase()}` : '#MED-4092'}
        onUploadClick={() => setActiveTab('prescriptions')}
      />

      <div className="flex flex-1">
        {/* Navigation (Desktop Sidebar / Mobile Bottom Bar) */}
        <Navigation
          activeTab={activeTab}
          onTabChange={setActiveTab}
          safetyAlertCount={alerts.filter((a) => a.severity === 'CRITICAL').length || 1}
        />

        {/* Main Workspace Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full pb-20 md:pb-8">
          {/* TAB 1: OVERVIEW DASHBOARD */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Critical Safety Conflict Banner */}
              {alerts.some((a) => a.severity === 'CRITICAL') && (
                <div
                  onClick={() => setActiveTab('safety')}
                  className="rounded-2xl border border-rose-500/40 bg-gradient-to-r from-rose-500/15 via-rose-500/5 to-transparent p-4 sm:p-5 flex items-start gap-4 shadow-lg shadow-rose-950/20 cursor-pointer hover:border-rose-400 transition-colors"
                >
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-rose-500/20 text-rose-400">
                    <ShieldAlert className="h-6 w-6 animate-pulse" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h2 className="text-sm sm:text-base font-bold text-rose-200">
                        Cross-Doctor Duplicate Molecule Overlap Detected
                      </h2>
                      <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-300 border border-rose-500/30">
                        CRITICAL SAFETY ALERT
                      </span>
                    </div>
                    <p className="mt-1 text-xs sm:text-sm text-slate-300 leading-relaxed">
                      Paracetamol is currently prescribed under multiple brands (Dolo 650 + Crocin). Click to review cumulative toxicity and generate the Doctor Consultation Note.
                    </p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-rose-400 self-center" />
                </div>
              )}

              {/* Quick Metrics Bar */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">Active Regimen</span>
                    <Pill className="h-4 w-4 text-teal-400" />
                  </div>
                  <p className="text-2xl font-bold text-white mt-1">3 Meds</p>
                  <p className="text-[11px] text-teal-400 mt-1">Multimodal OCR Verified</p>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">Today's Doses</span>
                    <Clock className="h-4 w-4 text-emerald-400" />
                  </div>
                  <p className="text-2xl font-bold text-white mt-1">
                    {scheduleData.taken_doses} / {scheduleData.total_doses} Logged
                  </p>
                  <p className="text-[11px] text-emerald-400 mt-1">
                    {scheduleData.adherence_percentage}% adherence score
                  </p>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">Cross-Doctor Audit</span>
                    <Sparkles className="h-4 w-4 text-amber-400" />
                  </div>
                  <p className="text-2xl font-bold text-white mt-1">{alerts.length} Warnings</p>
                  <p className="text-[11px] text-amber-400 mt-1">Chai & Duplicate alerts</p>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">Refill Alert</span>
                    <AlertTriangle className="h-4 w-4 text-rose-400" />
                  </div>
                  <p className="text-2xl font-bold text-rose-400 mt-1">1 Med Due</p>
                  <p className="text-[11px] text-slate-400 mt-1">Glycomet (3 pills left)</p>
                </div>
              </div>

              {/* Upload Prescription CTA Banner */}
              <div
                onClick={() => setActiveTab('prescriptions')}
                className="rounded-2xl border-2 border-dashed border-slate-800 hover:border-teal-500/50 bg-slate-900/40 p-6 text-center transition-all cursor-pointer group"
              >
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-500/10 text-teal-400 group-hover:scale-110 transition-transform shadow-inner">
                  <UploadCloud className="h-6 w-6" />
                </div>
                <h3 className="mt-3 text-base font-bold text-white">
                  Ingest & Verify New Prescription
                </h3>
                <p className="mt-1 text-xs text-slate-400 max-w-md mx-auto">
                  Scan doctor handwriting or pharmacy PDFs. Side-by-side split screen highlights low-confidence items in yellow.
                </p>
              </div>

              {/* Daily Schedule Preview on Dashboard */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Clock className="h-4 w-4 text-teal-400" />
                    Today's Medication Doses
                  </h3>
                  <button
                    onClick={() => setActiveTab('schedule')}
                    className="text-xs font-semibold text-teal-400 hover:text-teal-300 flex items-center gap-1 cursor-pointer"
                  >
                    Open Full Chrono-Schedule <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>

                <DailyScheduleDashboard
                  scheduleData={scheduleData}
                  onDoseUpdated={handleDoseUpdated}
                  preferredLanguage={preferredLanguage}
                  onLanguageChange={setPreferredLanguage}
                />
              </div>

              {/* Active Prescriptions List */}
              <div className="space-y-4 pt-4 border-t border-slate-800">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-white">Active Reconciled Prescriptions</h3>
                  <span className="text-xs font-semibold text-teal-400">
                    {prescriptions.length} Records
                  </span>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  {prescriptions.map((rx) => (
                    <PrescriptionCard key={rx.id} prescription={rx} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: DOSE SCHEDULE */}
          {activeTab === 'schedule' && (
            <DailyScheduleDashboard
              scheduleData={scheduleData}
              onDoseUpdated={handleDoseUpdated}
              preferredLanguage={preferredLanguage}
              onLanguageChange={setPreferredLanguage}
            />
          )}

          {/* TAB 3: PRESCRIPTION INGESTION & SPLIT SCREEN VERIFICATION */}
          {activeTab === 'prescriptions' && (
            <UploadVerificationScreen
              userId={currentUser?.id}
              onReconciliationComplete={handleReconciliationComplete}
            />
          )}

          {/* TAB 4: CROSS-DOCTOR SAFETY & DIETARY DDIS */}
          {activeTab === 'safety' && (
            <SafetyAlertPanel
              alerts={alerts}
              cumulativeToxicities={cumulativeToxicities}
              fastingAdjustments={fastingAdjustments}
              doctorQuerySummary={doctorQuerySummary}
              preferredLanguage={preferredLanguage}
            />
          )}

          {/* TAB 5: INTAKE LOG */}
          {activeTab === 'history' && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
              <Pill className="h-10 w-10 text-teal-400 mx-auto mb-3 opacity-60" />
              <h3 className="text-base font-bold text-white">Adherence & Intake History</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Logged timestamps, snoozed intervals, and reasons for skipped doses are permanently archived for review at your next clinical consultation.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
