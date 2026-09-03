import { useState, useRef, useEffect } from 'react';
import { Bot, Send, Sparkles, User, ChevronDown } from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const QUICK_QUESTIONS = [
  'Can I drink chai with Thyronorm in the morning?',
  'What happens if I take Dolo 650 and Crocin together?',
  'What foods should I strictly avoid with Metformin?',
  'Why does Atorvastatin interact with grapefruit?',
];

export function MediBotWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome_msg',
      role: 'assistant',
      content:
        'Hello! I am **MediBot**, your AI Clinical Safety Companion powered by **Google Gemini 3.6 Flash**. Ask me anything about your prescriptions, food interactions, safe timing, or lab reports.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestedFollowups, setSuggestedFollowups] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const historyPayload = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await fetch('/api/v1/bot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: historyPayload,
          language: 'en',
        }),
      });

      if (!res.ok) {
        throw new Error(`Bot request failed (${res.status})`);
      }

      const data = await res.json();
      const botMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        role: 'assistant',
        content: data.reply || 'I am currently reviewing your medications. Please ask again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
      if (data.suggested_followups && Array.isArray(data.suggested_followups)) {
        setSuggestedFollowups(data.suggested_followups.slice(0, 3));
      }
    } catch (err) {
      const errMsg: ChatMessage = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content:
          '⚠️ *Offline Assistant Notice*: Drinking morning milk tea (chai) within 60 minutes of Thyronorm binds Levothyroxine, reducing absorption by up to 40%. Concomitant Dolo 650 & Crocin risks acute hepatotoxicity. Consult your clinician.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 font-sans">
      {/* Expanded Chat Drawer */}
      {isOpen ? (
        <div className="w-[380px] sm:w-[440px] h-[580px] rounded-3xl bg-slate-900 border border-teal-500/30 shadow-2xl shadow-teal-950/50 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-6 duration-200">
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-teal-950 via-slate-900 to-slate-900 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20">
                <Bot className="h-5 w-5" />
                <span className="absolute -bottom-0.5 -right-0.5 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 border-2 border-slate-900"></span>
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-white text-sm">MediBot Assistant</h3>
                  <span className="rounded-full bg-teal-500/20 px-2 py-0.5 text-[10px] font-semibold text-teal-300 border border-teal-500/30">
                    Gemini 3.6
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">Clinical Safety & Pharmacology Companion</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="rounded-xl p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              title="Minimize MediBot"
            >
              <ChevronDown className="h-5 w-5" />
            </button>
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-slate-700">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-2.5 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.role === 'assistant' && (
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-teal-500/20 text-teal-400 mt-1">
                    <Sparkles className="h-3.5 w-3.5" />
                  </div>
                )}
                <div
                  className={`max-w-[82%] rounded-2xl p-3 text-xs leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-teal-600 text-white rounded-br-none shadow-md shadow-teal-900/30'
                      : 'bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-line">{m.content}</p>
                  <span
                    className={`block mt-1 text-[10px] ${
                      m.role === 'user' ? 'text-teal-200 text-right' : 'text-slate-400'
                    }`}
                  >
                    {m.timestamp}
                  </span>
                </div>
                {m.role === 'user' && (
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-slate-300 mt-1 border border-slate-700">
                    <User className="h-3.5 w-3.5" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-slate-400 text-xs py-2">
                <div className="flex space-x-1">
                  <div className="h-2 w-2 rounded-full bg-teal-400 animate-bounce"></div>
                  <div
                    className="h-2 w-2 rounded-full bg-teal-400 animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  ></div>
                  <div
                    className="h-2 w-2 rounded-full bg-teal-400 animate-bounce"
                    style={{ animationDelay: '0.4s' }}
                  ></div>
                </div>
                <span className="text-[11px]">MediBot is analyzing pharmacology...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompt Pills */}
          <div className="p-2.5 bg-slate-950/80 border-t border-slate-800/80">
            <div className="flex gap-1.5 overflow-x-auto pb-1.5 scrollbar-none">
              {(suggestedFollowups.length > 0 ? suggestedFollowups : QUICK_QUESTIONS).map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(q)}
                  className="shrink-0 text-[11px] bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-teal-500/50 text-slate-300 hover:text-teal-200 px-3 py-1 rounded-full transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2 mt-1.5"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about foods, timings, Dolo vs Crocin..."
                className="flex-1 rounded-xl bg-slate-800/90 border border-slate-700 px-3.5 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-500 text-slate-950 hover:bg-teal-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* Floating Button */
        <button
          onClick={() => setIsOpen(true)}
          className="group flex items-center gap-3 rounded-full bg-gradient-to-r from-teal-500 to-emerald-500 p-3 sm:px-4 sm:py-3 text-slate-950 font-bold shadow-xl shadow-teal-500/30 hover:scale-105 transition-all duration-200"
        >
          <div className="relative flex items-center justify-center">
            <Bot className="h-6 w-6 text-slate-950 group-hover:rotate-12 transition-transform" />
            <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-white"></span>
            </span>
          </div>
          <span className="hidden sm:inline text-xs font-bold tracking-wide">
            MediBot AI
          </span>
        </button>
      )}
    </div>
  );
}
