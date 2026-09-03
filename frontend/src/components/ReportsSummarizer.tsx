import { useState } from 'react';
import { FileText, Sparkles, HelpCircle, Activity, RefreshCw, UploadCloud } from 'lucide-react';

interface Biomarker {
  name: string;
  value: string;
  normal_range: string;
  status: 'HIGH' | 'LOW' | 'NORMAL';
  explanation: string;
}

interface ReportSummary {
  report_title: string;
  patient_name: string;
  test_date: string;
  lab_name: string;
  overall_status: string;
  plain_language_summary: string;
  biomarkers: Biomarker[];
  questions_for_doctor: string[];
  model_used?: string;
}

const SAMPLE_REPORT_TEXT = `PATIENT: Ramesh Patel | AGE: 62 | GENDER: Male | REF DR: Dr. S. K. Gupta
DIAGNOSTIC LAB: Metropolis Pathology & Healthcare
TEST: Comprehensive Metabolic, Lipid & Glycemic Panel
DATE: 28-Aug-2026

INVESTIGATION                          RESULT        REFERENCE INTERVAL   UNIT
HbA1c (Glycated Hemoglobin)            7.8           4.0 - 5.6           %     [HIGH]
Estimated Average Glucose (eAG)        177           70 - 126            mg/dL [HIGH]
Fasting Blood Sugar (FBS)              142           70 - 99             mg/dL [HIGH]
Serum Creatinine                       0.9           0.7 - 1.2           mg/dL [NORMAL]
Total Cholesterol                      228           < 200               mg/dL [HIGH]
LDL Cholesterol (Direct)               162           < 100               mg/dL [HIGH]
HDL Cholesterol                        42            > 40                mg/dL [NORMAL]
Triglycerides                          180           < 150               mg/dL [HIGH]
TSH (Thyroid Stimulating Hormone)      2.4           0.4 - 4.2           uIU/mL [NORMAL]
SGPT (ALT)                             28            < 45                U/L   [NORMAL]`;

export function ReportsSummarizer() {
  const [inputText, setInputText] = useState(SAMPLE_REPORT_TEXT);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSummarize = async () => {
    if (!inputText.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/v1/reports/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: inputText }),
      });

      if (!res.ok) {
        throw new Error(`Report analysis failed with status: ${res.status}`);
      }

      const data = await res.json();
      setSummary(data);
    } catch (err: any) {
      setError(err.message || 'Unable to connect to diagnostic analysis service.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-3xl border border-teal-500/30 bg-gradient-to-r from-teal-950/40 via-slate-900 to-slate-950 p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-500/20 text-teal-400 border border-teal-500/30">
                <FileText className="h-5 w-5" />
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                Diagnostic Lab Reports Summarizer
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 max-w-2xl">
              Paste or upload any medical lab report (Lipid Profile, HbA1c, CBC, Kidney function).
              Gemini 3.6 Flash translates medical jargon into plain-language guidance, highlights out-of-range biomarkers, and generates doctor questions.
            </p>
          </div>
          <button
            onClick={() => {
              setInputText(SAMPLE_REPORT_TEXT);
              handleSummarize();
            }}
            className="flex items-center gap-2 rounded-2xl bg-teal-500/20 border border-teal-500/40 hover:bg-teal-500/30 px-4 py-2.5 text-xs font-bold text-teal-300 transition-colors shrink-0"
          >
            <RefreshCw className="h-4 w-4" />
            Load Ramesh's Report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Input text area */}
        <div className="lg:col-span-5 space-y-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Raw Diagnostic Report Text
              </label>
              <span className="text-[11px] text-teal-400 font-medium">Text / OCR Input</span>
            </div>
            <textarea
              rows={12}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste lab results, blood tests, pathology text here..."
              className="w-full rounded-xl bg-slate-950 border border-slate-800 p-3.5 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
            />
            <button
              onClick={handleSummarize}
              disabled={loading || !inputText.trim()}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold py-3 text-xs tracking-wide shadow-lg shadow-teal-500/20 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Analyzing Diagnostic Biomarkers...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Analyze with Gemini AI
                </>
              )}
            </button>
            {error && (
              <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl p-3">
                {error}
              </p>
            )}
          </div>
        </div>

        {/* Right Column: Summarized Analysis Result */}
        <div className="lg:col-span-7 space-y-4">
          {summary ? (
            <div className="space-y-4 animate-in fade-in duration-300">
              {/* Overview Card */}
              <div className="rounded-2xl border border-teal-500/30 bg-slate-900/90 p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="text-base font-bold text-white">{summary.report_title}</h3>
                    <p className="text-xs text-slate-400">
                      Patient: <span className="text-slate-200 font-semibold">{summary.patient_name}</span> | Date: {summary.test_date}
                    </p>
                  </div>
                  <span className="rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-300 text-[11px] font-bold px-3 py-1">
                    {summary.overall_status}
                  </span>
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-teal-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5" /> Plain-Language Patient Summary
                  </h4>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 rounded-xl p-4 border border-slate-800/80">
                    {summary.plain_language_summary}
                  </p>
                </div>
              </div>

              {/* Biomarkers Table / Cards */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 space-y-3">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5 text-teal-400" /> Extracted Clinical Biomarkers ({summary.biomarkers?.length || 0})
                </h4>
                <div className="space-y-2.5">
                  {summary.biomarkers?.map((bio, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl bg-slate-950 border border-slate-800/80 p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-white">{bio.name}</span>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                              bio.status === 'HIGH'
                                ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                                : bio.status === 'LOW'
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                            }`}
                          >
                            {bio.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400">{bio.explanation}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-xs font-mono font-bold text-slate-200">{bio.value}</span>
                        <p className="text-[10px] text-slate-500">Ref: {bio.normal_range}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Doctor Questions Card */}
              {summary.questions_for_doctor && summary.questions_for_doctor.length > 0 && (
                <div className="rounded-2xl border border-amber-500/30 bg-amber-950/15 p-5 space-y-3">
                  <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                    <HelpCircle className="h-3.5 w-3.5" /> Questions to Ask Your Doctor
                  </h4>
                  <ul className="space-y-1.5 text-xs text-amber-100">
                    {summary.questions_for_doctor.map((q, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-amber-400 font-bold">•</span>
                        <span>{q}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full min-h-[380px] rounded-2xl border border-dashed border-slate-800 flex flex-col items-center justify-center p-8 text-center space-y-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-800/80 text-slate-400">
                <UploadCloud className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-bold text-slate-300">No Report Analyzed Yet</h3>
              <p className="text-xs text-slate-500 max-w-sm">
                Paste your laboratory report text on the left or click <strong>"Load Ramesh's Report"</strong> to preview comprehensive AI biomarker analysis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
