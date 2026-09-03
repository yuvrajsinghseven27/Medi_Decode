import React, { useState } from 'react';
import {
  CheckCircle2,
  Circle,
  Sun,
  SunMedium,
  Sunset,
  Moon,
  AlertOctagon,
} from 'lucide-react';

export interface DoseSlot {
  id: string;
  timeSlot: 'Morning' | 'Afternoon' | 'Evening' | 'Bedtime';
  time: string;
  medicationName: string;
  dosage: string;
  instructions: string;
  taken: boolean;
  hasInteractionWarning?: boolean;
  interactionWarningText?: string;
}

const initialDoseSlots: DoseSlot[] = [
  {
    id: 'dose_1',
    timeSlot: 'Morning',
    time: '08:00 AM',
    medicationName: 'Metformin HCl',
    dosage: '500mg',
    instructions: 'Take with breakfast',
    taken: true,
  },
  {
    id: 'dose_2',
    timeSlot: 'Morning',
    time: '08:30 AM',
    medicationName: 'Levothyroxine Sodium',
    dosage: '50mcg',
    instructions: 'Take 30 mins before food on an empty stomach with a full glass of water',
    taken: true,
  },
  {
    id: 'dose_3',
    timeSlot: 'Afternoon',
    time: '01:00 PM',
    medicationName: 'Multivitamin Complex',
    dosage: '1 Capsule',
    instructions: 'Take with lunch',
    taken: false,
    hasInteractionWarning: true,
    interactionWarningText: 'Spacing alert: Ensure 4-hour window between Levothyroxine and Calcium/Iron in vitamins.',
  },
  {
    id: 'dose_4',
    timeSlot: 'Evening',
    time: '07:30 PM',
    medicationName: 'Metformin HCl',
    dosage: '500mg',
    instructions: 'Take with dinner',
    taken: false,
  },
  {
    id: 'dose_5',
    timeSlot: 'Bedtime',
    time: '10:00 PM',
    medicationName: 'Atorvastatin Calcium',
    dosage: '20mg',
    instructions: 'Take at bedtime. Avoid grapefruit juice.',
    taken: false,
  },
];

export const ScheduleTimeline: React.FC = () => {
  const [slots, setSlots] = useState<DoseSlot[]>(initialDoseSlots);

  const toggleDose = (id: string) => {
    setSlots((prev) =>
      prev.map((slot) =>
        slot.id === id ? { ...slot, taken: !slot.taken } : slot
      )
    );
  };

  const takenCount = slots.filter((s) => s.taken).length;
  const adherencePercentage = Math.round((takenCount / slots.length) * 100);

  const getSlotIcon = (slot: DoseSlot['timeSlot']) => {
    switch (slot) {
      case 'Morning':
        return <Sun className="h-4 w-4 text-amber-400" />;
      case 'Afternoon':
        return <SunMedium className="h-4 w-4 text-orange-400" />;
      case 'Evening':
        return <Sunset className="h-4 w-4 text-rose-400" />;
      case 'Bedtime':
        return <Moon className="h-4 w-4 text-indigo-400" />;
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg">
      {/* Header & Adherence Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base sm:text-lg font-bold text-white">Daily Medication Timeline</h3>
            <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs font-medium text-slate-300">
              Today
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Synchronized with clinical Rx frequency rules
          </p>
        </div>

        {/* Adherence Gauge */}
        <div className="flex items-center gap-3 bg-slate-800/40 rounded-xl px-4 py-2 border border-slate-800">
          <div className="w-24 bg-slate-800 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-gradient-to-r from-teal-500 to-emerald-400 h-2.5 rounded-full transition-all duration-500"
              style={{ width: `${adherencePercentage}%` }}
            />
          </div>
          <div className="text-right">
            <p className="text-xs font-bold text-teal-300">{adherencePercentage}% Adherence</p>
            <p className="text-[10px] text-slate-400">
              {takenCount} of {slots.length} doses taken
            </p>
          </div>
        </div>
      </div>

      {/* Timeline Items */}
      <div className="relative mt-6 space-y-4 before:absolute before:left-5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
        {slots.map((slot) => (
          <div
            key={slot.id}
            className={`relative flex items-start gap-4 pl-1 transition-all ${
              slot.taken ? 'opacity-80' : 'opacity-100'
            }`}
          >
            {/* Checkbox / Bullet */}
            <button
              onClick={() => toggleDose(slot.id)}
              className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-slate-700 bg-slate-800 text-slate-300 hover:border-teal-500 transition-colors shadow-sm cursor-pointer"
              title={slot.taken ? 'Mark as pending' : 'Mark as taken'}
            >
              {slot.taken ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-400 fill-emerald-500/20" />
              ) : (
                <Circle className="h-5 w-5 text-slate-500" />
              )}
            </button>

            {/* Dose Card Content */}
            <div className="flex-1 rounded-xl border border-slate-800/80 bg-slate-800/40 p-3.5 hover:bg-slate-800/60 transition-colors">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1.5 rounded-md bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-300">
                    {getSlotIcon(slot.timeSlot)}
                    {slot.timeSlot} • {slot.time}
                  </span>
                  <h4 className={`text-sm font-bold ${slot.taken ? 'line-through text-slate-400' : 'text-white'}`}>
                    {slot.medicationName}
                  </h4>
                  <span className="rounded bg-teal-500/10 px-1.5 py-0.5 text-[11px] font-semibold text-teal-300">
                    {slot.dosage}
                  </span>
                </div>

                <span
                  className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                    slot.taken
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : 'bg-amber-500/10 text-amber-400'
                  }`}
                >
                  {slot.taken ? 'Logged' : 'Pending'}
                </span>
              </div>

              <p className="mt-1.5 text-xs text-slate-300">{slot.instructions}</p>

              {/* Interaction Warning Badge */}
              {slot.hasInteractionWarning && (
                <div className="mt-2.5 flex items-start gap-2 rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2 text-xs text-amber-300">
                  <AlertOctagon className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
                  <span>{slot.interactionWarningText}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
