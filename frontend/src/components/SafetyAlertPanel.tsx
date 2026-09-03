import React, { useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  Check,
  Copy,
  Printer,
  Coffee,
  Sparkles,
  X,
  FileText,
  UserCheck,
} from 'lucide-react';
import type { SafetyAlertRead, CumulativeToxicityAlert, FastingAdjustment } from '../services/api';

interface SafetyAlertPanelProps {
  alerts: SafetyAlertRead[];
  cumulativeToxicities?: CumulativeToxicityAlert[];
  fastingAdjustments?: FastingAdjustment[];
  doctorQuerySummary?: string;
  preferredLanguage?: string;
}

export const SafetyAlertPanel: React.FC<SafetyAlertPanelProps> = ({
  alerts,
  cumulativeToxicities = [],
  fastingAdjustments = [],
  doctorQuerySummary,
  preferredLanguage = 'en',
}) => {
  const [isModalOpen, setIsModalOpen] = useState(
    () => typeof window !== 'undefined' && window.location.search.includes('modal=doctor')
  );
  const [copied, setCopied] = useState(false);

  const criticalAlerts = alerts.filter((a) => a.severity === 'CRITICAL');
  const moderateAlerts = alerts.filter((a) => a.severity === 'MODERATE');
  const infoAlerts = alerts.filter((a) => a.severity === 'INFO');

  const handleCopy = async () => {
    if (!doctorQuerySummary) return;
    try {
      await navigator.clipboard.writeText(doctorQuerySummary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const getLocalizedText = (alert: SafetyAlertRead): string => {
    if (preferredLanguage !== 'en' && alert.localized_advisory && alert.localized_advisory[preferredLanguage]) {
      return alert.localized_advisory[preferredLanguage];
    }
    return alert.advisory_text;
  };

  return (
    <div className="space-y-6">
      {/* Overview & Doctor Query Trigger Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="h-6 w-6 text-rose-400" />
            Cross-Doctor Reconciliation & Cultural Safety Guard
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Audits concurrent medications across clinicians for duplicate molecules, cumulative toxicities, and traditional Indian dietary conflicts.
          </p>
        </div>

        {doctorQuerySummary && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-rose-500 to-amber-500 px-4 py-2 text-xs sm:text-sm font-bold text-white shadow-lg shadow-rose-500/20 hover:brightness-110 active:scale-95 transition-all cursor-pointer"
          >
            <FileText className="h-4 w-4" />
            View Doctor Query Note
          </button>
        )}
      </div>

      {/* Summary Badges Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Critical Badge */}
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-rose-400">
              Critical Overlaps
            </span>
            <p className="text-2xl font-bold text-white mt-0.5">
              {criticalAlerts.length + cumulativeToxicities.filter((c) => c.is_toxic).length}
            </p>
            <p className="text-[11px] text-rose-300">Duplicate molecules & toxicity</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/20 text-rose-400">
            <ShieldAlert className="h-6 w-6 animate-pulse" />
          </div>
        </div>

        {/* Moderate Badge */}
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
              Dietary & Fasting Rules
            </span>
            <p className="text-2xl font-bold text-white mt-0.5">{moderateAlerts.length}</p>
            <p className="text-[11px] text-amber-300">Chai / Dairy / Fasting sync</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400">
            <Coffee className="h-6 w-6" />
          </div>
        </div>

        {/* Info Badge */}
        <div className="rounded-xl border border-teal-500/30 bg-teal-500/10 p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-teal-400">
              Inventory & Clinical Notes
            </span>
            <p className="text-2xl font-bold text-white mt-0.5">{infoAlerts.length}</p>
            <p className="text-[11px] text-teal-300">Refill status & diet tips</p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/20 text-teal-400">
            <Info className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Cumulative Toxicity Highlights (if any) */}
      {cumulativeToxicities.length > 0 && (
        <div className="rounded-2xl border border-rose-500/30 bg-gradient-to-r from-rose-950/40 to-slate-900 p-5 shadow-xl">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-5 w-5 text-rose-400" />
            <h3 className="text-sm sm:text-base font-bold text-white">
              Cumulative Toxicity Ceiling Audits
            </h3>
          </div>

          <div className="space-y-3">
            {cumulativeToxicities.map((tox, i) => (
              <div
                key={i}
                className="rounded-xl border border-rose-500/20 bg-slate-950/60 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-white">{tox.generic_molecule}</h4>
                    <span className="rounded bg-rose-500/20 text-rose-300 text-[10px] font-bold px-2 py-0.5 border border-rose-500/30">
                      Calculated: {tox.cumulative_daily_dose_mg} mg/day (Max Safe: {tox.max_safe_daily_dose_mg} mg)
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1">{tox.clinical_risk}</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Prescribed as: <span className="text-rose-300 font-semibold">{tox.contributing_brands.join(', ')}</span>
                  </p>
                </div>

                <div className="shrink-0 text-right">
                  <span className="rounded-full bg-rose-500/20 border border-rose-500/30 px-3 py-1 text-xs font-bold text-rose-400">
                    {tox.is_toxic ? 'TOXIC OVERAGE' : 'ELEVATED DOSE'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Safety Advisories List */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
          Detected Interaction & Advisory Cards ({alerts.length})
        </h3>

        {alerts.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
            <UserCheck className="h-8 w-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-200">No Safety Conflicts Detected</p>
            <p className="text-xs text-slate-500 mt-0.5">
              Active medications do not share identical molecules or immediate dietary counteractions.
            </p>
          </div>
        ) : (
          alerts.map((alert) => {
            const isCritical = alert.severity === 'CRITICAL';
            const isModerate = alert.severity === 'MODERATE';

            return (
              <div
                key={alert.id}
                className={`rounded-2xl p-4 border transition-all ${
                  isCritical
                    ? 'border-rose-500/40 bg-rose-950/15 shadow-md shadow-rose-950/20'
                    : isModerate
                    ? 'border-amber-500/40 bg-amber-950/15 shadow-md shadow-amber-950/20'
                    : 'border-slate-800 bg-slate-900/80'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div
                      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl mt-0.5 ${
                        isCritical
                          ? 'bg-rose-500/20 text-rose-400'
                          : isModerate
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-teal-500/20 text-teal-400'
                      }`}
                    >
                      {isCritical ? (
                        <ShieldAlert className="h-5 w-5" />
                      ) : isModerate ? (
                        <AlertTriangle className="h-5 w-5" />
                      ) : (
                        <Info className="h-5 w-5" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                            isCritical
                              ? 'bg-rose-500/20 text-rose-300'
                              : isModerate
                              ? 'bg-amber-500/20 text-amber-300'
                              : 'bg-teal-500/20 text-teal-300'
                          }`}
                        >
                          {alert.alert_type.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-slate-400">
                          {new Date(alert.created_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <p className="mt-1 text-xs sm:text-sm font-medium text-slate-200 leading-relaxed">
                        {getLocalizedText(alert)}
                      </p>
                    </div>
                  </div>

                  <span
                    className={`shrink-0 text-[11px] font-bold px-2.5 py-1 rounded-lg ${
                      isCritical
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        : isModerate
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {alert.severity}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Fasting Adaptations (if present) */}
      {fastingAdjustments.length > 0 && (
        <div className="rounded-2xl border border-teal-500/30 bg-teal-950/15 p-5">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-5 w-5 text-teal-400" />
            <h3 className="text-sm sm:text-base font-bold text-white">
              Ramadan & Religious Fasting Timing Adaptations
            </h3>
          </div>
          <div className="space-y-2">
            {fastingAdjustments.map((adj, i) => (
              <div
                key={i}
                className="rounded-xl border border-teal-500/20 bg-slate-950/60 p-3.5 text-xs text-slate-300"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">{adj.original_timing}</span>
                  <span className="rounded bg-teal-500/20 text-teal-300 font-semibold px-2 py-0.5 text-[11px]">
                    {adj.adapted_timing}
                  </span>
                </div>
                <p className="mt-1 text-slate-400">{adj.rationale}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* DOCTOR QUERY NOTE MODAL */}
      {isModalOpen && doctorQuerySummary && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="relative w-full max-w-2xl rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl max-h-[85vh] flex flex-col justify-between">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-teal-400" />
                <h3 className="text-base font-bold text-white">
                  Clinician Consultation Summary Sheet
                </h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Markdown Body */}
            <div className="flex-1 my-4 overflow-y-auto pr-2 bg-slate-950/50 p-4 rounded-xl border border-slate-800/80 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
              {doctorQuerySummary}
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              <p className="text-[11px] text-slate-400">
                Share with your doctor or pharmacist prior to taking overlapping medications.
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={handlePrint}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition-colors cursor-pointer"
                >
                  <Printer className="h-3.5 w-3.5" />
                  Print
                </button>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 rounded-lg bg-teal-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-teal-400 shadow-md shadow-teal-500/20 transition-all cursor-pointer"
                >
                  {copied ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-slate-950" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      1-Tap Copy
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
