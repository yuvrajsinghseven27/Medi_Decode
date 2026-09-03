import React from 'react';
import {
  Pill,
  AlertTriangle,
  Sparkles,
  User,
  Clock,
  RotateCcw,
  CheckCircle2,
  Info,
} from 'lucide-react';

export interface Prescription {
  id: string;
  brandName: string;
  genericName: string;
  dosage: string;
  form: 'Tablet' | 'Capsule' | 'Liquid' | 'Inhaler';
  doctorName: string;
  clinic: string;
  prescribedDate: string;
  frequency: string;
  timingInstructions: string;
  refillsRemaining: number;
  status: 'active' | 'refill_needed' | 'completed';
  confidenceScore: number;
  warnings: string[];
  foodInteractions?: string[];
}

interface PrescriptionCardProps {
  prescription: Prescription;
  onLogDose?: (id: string) => void;
}

export const PrescriptionCard: React.FC<PrescriptionCardProps> = ({
  prescription,
  onLogDose,
}) => {
  const getStatusBadge = () => {
    switch (prescription.status) {
      case 'active':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 ring-1 ring-inset ring-emerald-500/20">
            <CheckCircle2 className="h-3 w-3" />
            Active Regimen
          </span>
        );
      case 'refill_needed':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-400 ring-1 ring-inset ring-amber-500/20">
            <RotateCcw className="h-3 w-3" />
            Refill Due
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-500/10 px-2.5 py-0.5 text-xs font-semibold text-slate-400 ring-1 ring-inset ring-slate-500/20">
            Completed
          </span>
        );
    }
  };

  return (
    <div className="group relative flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg transition-all hover:border-slate-700 hover:shadow-teal-950/20">
      {/* Header Info */}
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400 group-hover:scale-105 transition-transform">
              <Pill className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white sm:text-lg">
                  {prescription.brandName}
                </h3>
                <span className="rounded bg-slate-800 px-1.5 py-0.5 text-xs font-mono font-medium text-slate-300">
                  {prescription.dosage}
                </span>
              </div>
              <p className="text-xs text-slate-400 italic">
                {prescription.genericName} • {prescription.form}
              </p>
            </div>
          </div>
          {getStatusBadge()}
        </div>

        {/* Clinical Instructions */}
        <div className="mt-4 rounded-xl border border-slate-800/80 bg-slate-800/30 p-3.5 space-y-2">
          <div className="flex items-start gap-2 text-xs text-slate-200">
            <Clock className="h-4 w-4 shrink-0 text-teal-400 mt-0.5" />
            <div>
              <span className="font-semibold text-teal-300">{prescription.frequency}</span>
              <p className="text-slate-400 mt-0.5">{prescription.timingInstructions}</p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400 pt-1 border-t border-slate-800/60">
            <User className="h-3.5 w-3.5 text-slate-400" />
            <span>
              Prescribed by <strong className="text-slate-300">{prescription.doctorName}</strong> ({prescription.clinic})
            </span>
          </div>
        </div>

        {/* Warnings & AI Confidence */}
        <div className="mt-3.5 space-y-2">
          {prescription.warnings.length > 0 && (
            <div className="flex items-start gap-2 rounded-lg bg-rose-500/10 border border-rose-500/20 px-3 py-2 text-xs text-rose-300">
              <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
              <span>{prescription.warnings[0]}</span>
            </div>
          )}

          {prescription.foodInteractions && prescription.foodInteractions.length > 0 && (
            <div className="flex items-start gap-2 rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2 text-xs text-amber-300">
              <Info className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
              <span>{prescription.foodInteractions[0]}</span>
            </div>
          )}
        </div>
      </div>

      {/* Footer / Actions */}
      <div className="mt-5 pt-3.5 border-t border-slate-800 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-slate-400">
          <Sparkles className="h-3.5 w-3.5 text-teal-400" />
          <span>AI OCR Confidence: </span>
          <span className="font-semibold text-teal-300">
            {Math.round(prescription.confidenceScore * 100)}%
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400">
            Refills: <strong className="text-slate-200">{prescription.refillsRemaining}</strong>
          </span>
          <button
            onClick={() => onLogDose?.(prescription.id)}
            className="rounded-lg bg-slate-800 px-2.5 py-1 font-semibold text-teal-300 hover:bg-slate-700 hover:text-teal-200 transition-colors"
          >
            Log Dose
          </button>
        </div>
      </div>
    </div>
  );
};
