import React, { useState } from 'react';
import confetti from 'canvas-confetti';
import {
  Sun,
  SunMedium,
  Sunset,
  Moon,
  CheckCircle2,
  Clock,
  RotateCcw,
  SkipForward,
  Pill,
  AlertCircle,
  Languages,
  Check,
} from 'lucide-react';
import { api } from '../services/api';
import type { DailyScheduleView, DoseItemDetail } from '../services/api';

interface DailyScheduleDashboardProps {
  scheduleData: DailyScheduleView;
  onDoseUpdated: () => void;
  preferredLanguage: string;
  onLanguageChange: (lang: string) => void;
}

// Translations for dose instructions in regional languages
const DOSE_TRANSLATIONS: Record<string, Record<string, string>> = {
  hi: {
    AC: 'भोजन से 30 मिनट पहले खाली पेट लें',
    PC: 'भोजन के 30 मिनट बाद लें',
    WITH_FOOD: 'भोजन के साथ लें',
    Morning: 'सुबह',
    Afternoon: 'दोपहर',
    Evening: 'शाम',
    Bedtime: 'रात (सोते समय)',
    Taken: 'ली गई',
    Snooze: '30 मिनट टालें',
    Skip: 'छोड़ें',
    RefillAlert: 'दवा समाप्त होने वाली है!',
  },
  ta: {
    AC: 'உணவுக்கு 30 நிமிடங்களுக்கு முன் வெறும் வயிற்றில் உட்கொள்ளவும்',
    PC: 'உணவுக்கு 30 நிமிடங்களுக்குப் பிறகு உட்கொள்ளவும்',
    WITH_FOOD: 'உணவுடன் உட்கொள்ளவும்',
    Morning: 'காலை',
    Afternoon: 'மதியம்',
    Evening: 'மாலை',
    Bedtime: 'இரவு (படுக்கைக்கு முன்)',
    Taken: 'எடுத்துக்கொள்ளப்பட்டது',
    Snooze: '30 நிமிடம் ஒத்திவைக்க',
    Skip: 'தவிர்க்க',
    RefillAlert: 'மருந்து தீரப்போகிறது!',
  },
  te: {
    AC: 'భోజనానికి 30 నిమిషాల ముందు ఖాళీ కడుపుతో తీసుకోండి',
    PC: 'భోజనం చేసిన 30 నిమిషాల తర్వాత తీసుకోండి',
    WITH_FOOD: 'భోజనంతో పాటు తీసుకోండి',
    Morning: 'ఉదయం',
    Afternoon: 'మధ్యాహ్నం',
    Evening: 'సాయంత్రం',
    Bedtime: 'రాత్రి (పడుకునే ముందు)',
    Taken: 'తీసుకున్నారు',
    Snooze: '30 నిమి వాయిదా',
    Skip: 'వదిలేయండి',
    RefillAlert: 'మందులు అయిపోతున్నాయి!',
  },
  bn: {
    AC: 'খাওয়ার ৩০ মিনিট আগে খালি পেটে খান',
    PC: 'খাওয়ার ৩০ মিনিট পরে খান',
    WITH_FOOD: 'খাবারের সাথে খান',
    Morning: 'সকাল',
    Afternoon: 'দুপুর',
    Evening: 'সন্ধ্যা',
    Bedtime: 'রাত (ঘুমানোর আগে)',
    Taken: 'গ্রহণ করা হয়েছে',
    Snooze: '৩০ মিনিট স্থগিত',
    Skip: 'বাদ দিন',
    RefillAlert: 'ওষুধ শেষ হয়ে আসছে!',
  },
};

export const DailyScheduleDashboard: React.FC<DailyScheduleDashboardProps> = ({
  scheduleData,
  onDoseUpdated,
  preferredLanguage,
  onLanguageChange,
}) => {
  const [loadingItemId, setLoadingItemId] = useState<string | null>(null);

  const t = (key: string, defaultText: string): string => {
    if (
      preferredLanguage !== 'en' &&
      DOSE_TRANSLATIONS[preferredLanguage] &&
      DOSE_TRANSLATIONS[preferredLanguage][key]
    ) {
      return DOSE_TRANSLATIONS[preferredLanguage][key];
    }
    return defaultText;
  };

  const fireConfetti = () => {
    try {
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.7 },
        colors: ['#2dd4bf', '#34d399', '#38bdf8', '#fbbf24'],
      });
    } catch {
      // Fallback
    }
  };

  const handleAction = async (
    item: DoseItemDetail,
    action: 'TAKEN' | 'SNOOZED' | 'SKIPPED',
    snoozeMin = 30
  ) => {
    setLoadingItemId(item.id);
    try {
      await api.applyScheduleAction(item.id, action, snoozeMin);
      if (action === 'TAKEN') {
        fireConfetti();
      }
      onDoseUpdated();
    } catch (err) {
      console.error('Failed to update dose action:', err);
    } finally {
      setLoadingItemId(null);
    }
  };

  const renderSlotSection = (
    titleKey: string,
    titleEn: string,
    icon: React.ReactNode,
    items: DoseItemDetail[]
  ) => {
    if (items.length === 0) return null;

    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 pb-1 border-b border-slate-800">
          {icon}
          <h4 className="text-sm font-bold text-white tracking-wide">
            {t(titleKey, titleEn)} ({items.length})
          </h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {items.map((item) => {
            const isTaken = item.status === 'TAKEN';
            const isSnoozed = item.status === 'SNOOZED';
            const isSkipped = item.status === 'SKIPPED';
            const isLoading = loadingItemId === item.id;

            return (
              <div
                key={item.id}
                className={`relative rounded-2xl p-4 border transition-all ${
                  isTaken
                    ? 'border-emerald-500/30 bg-emerald-950/10 opacity-90'
                    : isSnoozed
                    ? 'border-amber-500/30 bg-amber-950/10'
                    : isSkipped
                    ? 'border-slate-800 bg-slate-950/40 opacity-60'
                    : 'border-slate-800 bg-slate-900/80 hover:border-slate-700 shadow-md'
                }`}
              >
                {/* Header info */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
                        isTaken
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-teal-500/10 text-teal-400'
                      }`}
                    >
                      <Pill className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h5
                          className={`text-sm font-bold ${
                            isTaken ? 'line-through text-slate-400' : 'text-white'
                          }`}
                        >
                          {item.brand_name}
                        </h5>
                        <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[11px] font-mono text-slate-300">
                          {item.strength}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        {item.generic_molecule || item.form}
                      </p>
                    </div>
                  </div>

                  <span className="flex items-center gap-1 rounded-md bg-slate-800 px-2 py-0.5 text-xs font-mono font-bold text-teal-300">
                    <Clock className="h-3 w-3" />
                    {item.time_str}
                  </span>
                </div>

                {/* Timing instructions (Localized) */}
                <div className="mt-3 rounded-xl bg-slate-950/40 border border-slate-800/80 p-2.5 text-xs text-slate-300">
                  <span className="font-semibold text-teal-300">
                    {t(item.timing_relation, item.timing_relation)}:
                  </span>{' '}
                  <span>{t(item.timing_relation, item.instructions)}</span>
                </div>

                {/* Low Stock Warning */}
                {item.is_low_stock && (
                  <div className="mt-2 flex items-center gap-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 text-[11px] font-semibold text-amber-300">
                    <AlertCircle className="h-3.5 w-3.5 text-amber-400" />
                    <span>
                      {t('RefillAlert', 'Refill Due')}: Only {item.remaining_pills} pills remaining!
                    </span>
                  </div>
                )}

                {/* Interactive Action Controls */}
                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between gap-2">
                  <div className="text-[11px] text-slate-400">
                    Pills left: <strong className="text-slate-200">{item.remaining_pills}</strong>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {isTaken ? (
                      <span className="flex items-center gap-1 rounded-lg bg-emerald-500/20 text-emerald-300 px-3 py-1.5 text-xs font-bold border border-emerald-500/30">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        {t('Taken', 'Taken')}
                      </span>
                    ) : (
                      <>
                        <button
                          onClick={() => handleAction(item, 'TAKEN')}
                          disabled={isLoading}
                          className="flex items-center gap-1 rounded-lg bg-teal-500 px-3 py-1.5 text-xs font-bold text-slate-950 hover:bg-teal-400 shadow-sm shadow-teal-500/20 active:scale-95 transition-all cursor-pointer disabled:opacity-50"
                        >
                          <Check className="h-3.5 w-3.5" />
                          {t('Taken', 'Mark Taken')}
                        </button>
                        <button
                          onClick={() => handleAction(item, 'SNOOZED', 30)}
                          disabled={isLoading}
                          className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1.5 text-[11px] font-semibold text-slate-300 hover:bg-slate-700 active:scale-95 transition-all cursor-pointer"
                          title="Snooze 30 minutes"
                        >
                          <RotateCcw className="h-3 w-3 text-amber-400" />
                          30m
                        </button>
                        <button
                          onClick={() => handleAction(item, 'SKIPPED')}
                          disabled={isLoading}
                          className="rounded-lg border border-slate-800 p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 cursor-pointer"
                          title="Skip Dose"
                        >
                          <SkipForward className="h-3.5 w-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Header with Language Selector & Adherence Progress */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Clock className="h-6 w-6 text-teal-400" />
            Daily Chrono-Medication Schedule
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Synchronized with your personal meal times. Log doses to update real-time adherence and smart inventory depletion.
          </p>
        </div>

        {/* Language Dialect Toggle Selector */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl p-1 shadow-md">
          <Languages className="h-4 w-4 text-teal-400 ml-2" />
          <div className="flex items-center gap-1">
            {[
              { id: 'en', label: 'English' },
              { id: 'hi', label: 'हिन्दी' },
              { id: 'ta', label: 'தமிழ்' },
              { id: 'te', label: 'తెలుగు' },
              { id: 'bn', label: 'বাংলা' },
            ].map((lang) => (
              <button
                key={lang.id}
                onClick={() => onLanguageChange(lang.id)}
                className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-all cursor-pointer ${
                  preferredLanguage === lang.id
                    ? 'bg-teal-500 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Adherence Progress Bar Card */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 to-slate-950 p-5 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
          <div>
            <span className="text-xs font-semibold text-teal-400 uppercase tracking-wider">
              Today's Adherence Score
            </span>
            <h3 className="text-2xl font-bold text-white mt-0.5">
              {scheduleData.adherence_percentage}% Complete
            </h3>
          </div>
          <span className="text-xs font-mono font-bold text-slate-300 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
            {scheduleData.taken_doses} of {scheduleData.total_doses} Doses Logged
          </span>
        </div>

        <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-teal-500 via-emerald-400 to-teal-300 h-3 rounded-full transition-all duration-500"
            style={{ width: `${scheduleData.adherence_percentage}%` }}
          />
        </div>
      </div>

      {/* Time-Grouped Slots */}
      <div className="space-y-6">
        {renderSlotSection(
          'Morning',
          'Morning Slot (05:00 AM - 11:59 AM)',
          <Sun className="h-5 w-5 text-amber-400" />,
          scheduleData.morning
        )}

        {renderSlotSection(
          'Afternoon',
          'Afternoon Slot (12:00 PM - 04:59 PM)',
          <SunMedium className="h-5 w-5 text-orange-400" />,
          scheduleData.afternoon
        )}

        {renderSlotSection(
          'Evening',
          'Evening Slot (05:00 PM - 08:59 PM)',
          <Sunset className="h-5 w-5 text-rose-400" />,
          scheduleData.evening
        )}

        {renderSlotSection(
          'Bedtime',
          'Bedtime Slot (09:00 PM - 04:59 AM)',
          <Moon className="h-5 w-5 text-indigo-400" />,
          scheduleData.bedtime
        )}
      </div>
    </div>
  );
};
