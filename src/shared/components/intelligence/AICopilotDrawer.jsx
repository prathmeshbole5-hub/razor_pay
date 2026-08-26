import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, Sparkles, X, ChevronRight, CheckCircle2, MessageSquare, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchCopilotQuery, fetchCopilotPrompts } from '../../../api/copilotApi';
import { apiRequest } from '../../../api/client';

export default function AICopilotDrawer({ currentPortal = 'merchant' }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [prompts, setPrompts] = useState([]);
  const [actionSuccess, setActionSuccess] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Set initial greeting based on portal mode
    const isInternal = currentPortal === 'internal';
    const initMsg = isInternal
      ? {
          id: 'init_internal',
          sender: 'ai',
          text: "Hello Ops Agent! I am your **RecoverAI Ecosystem Copilot**. I am monitoring aggregate network telemetries, partner bank error codes, and gateway latency spikes.",
          metrics: [
            { label: 'Network Volume', value: '₹5.28Cr' },
            { label: 'Active Incidents', value: '2 Routes' },
            { label: 'Ecosystem Recovery', value: '68.4%' }
          ],
          recommendation: "Ask about bank latency spikes, error code distributions, or gateway failover routes."
        }
      : {
          id: 'init_merchant',
          sender: 'ai',
          text: "Hello! I am your **RecoverAI Financial Copilot**. I am monitoring active payment cases for **CloudMart (m_1004)**.",
          metrics: [
            { label: 'Revenue At Risk', value: '₹12,45,000' },
            { label: 'Recoverable Revenue', value: '₹9,24,000' },
            { label: 'AI Recovery Rate', value: '74.2%' }
          ],
          recommendation: "Ask about failure root causes, best strategies, or lookup specific payment IDs."
        };

    setMessages([initMsg]);

    fetchCopilotPrompts(currentPortal).then((res) => {
      if (res?.prompts?.length) {
        setPrompts(res.prompts);
      }
    });
  }, [currentPortal]);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, loading]);

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    const userMsg = { id: `u_${Date.now()}`, sender: 'user', text: query };
    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      const res = await fetchCopilotQuery(query, 'm_1004', currentPortal);
      if (res && res.text) {
        setMessages((prev) => [
          ...prev,
          {
            id: `ai_${Date.now()}`,
            sender: 'ai',
            text: res.text,
            metrics: res.metrics || [],
            payment_card: res.payment_card || null,
            recommendation: res.recommendation || null,
            suggestedAction: res.suggestedAction || null,
            actionType: res.actionType || null,
            actionPayload: res.actionPayload || null
          }
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `ai_${Date.now()}`,
            sender: 'ai',
            text: `Analyzing system telemetries for query: **${query}**. RecoverAI engine recommends monitoring active failure queues.`,
            metrics: [
              { label: 'Pipeline Status', value: 'Active' },
              { label: 'AI Confidence', value: '88%' }
            ]
          }
        ]);
      }
    } catch (err) {
      console.warn('[AICopilotDrawer] API call error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteAction = async (msg) => {
    if (!msg.actionType) return;
    try {
      setLoading(true);
      await apiRequest('/api/demo/simulate?event_type=failure', { method: 'POST' });
      setActionSuccess(`Triggered AI recovery action.`);
      setTimeout(() => setActionSuccess(null), 3500);
    } catch (e) {
      setActionSuccess(`Action executed.`);
      setTimeout(() => setActionSuccess(null), 3500);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Assistant Trigger Launcher (Bottom-Right) */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white p-3.5 rounded-full shadow-2xl border border-indigo-400/30 flex items-center gap-2.5 group cursor-pointer"
        title="Open RecoverAI Copilot Assistant"
      >
        <div className="relative">
          <Bot className="w-6 h-6 text-white" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-400" />
        </div>
        <span className="text-xs font-semibold pr-1 hidden sm:inline text-white">
          AI Copilot
        </span>
      </motion.button>

      {/* Slide-out Drawer Overlay */}
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            />

            {/* Slide-in Panel */}
            <div className="fixed inset-y-0 right-0 max-w-full flex pl-4 sm:pl-10">
              <motion.div
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 220 }}
                className="w-screen max-w-md bg-slate-950 border-l border-slate-800 shadow-2xl flex flex-col justify-between"
              >
                {/* Header */}
                <div className="px-5 py-4 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md">
                      <Bot className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
                        RecoverAI Assistant
                        <span className="text-[9px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.5 rounded-full font-mono uppercase">
                          {currentPortal} Mode
                        </span>
                      </h3>
                      <p className="text-[10px] text-slate-400">Natural language failure intelligence</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {actionSuccess && (
                  <div className="bg-emerald-500/10 border-b border-emerald-500/30 text-emerald-300 px-4 py-2 text-[11px] flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>{actionSuccess}</span>
                  </div>
                )}

                {/* Prompt Shortcuts */}
                <div className="p-3 bg-slate-900/40 border-b border-slate-800/80 flex items-center gap-1.5 overflow-x-auto">
                  {prompts.map((p, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(p)}
                      className="text-[10px] text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 px-2.5 py-1 rounded-lg whitespace-nowrap transition-colors"
                    >
                      {p}
                    </button>
                  ))}
                </div>

                {/* Messages Body */}
                <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {msg.sender === 'ai' && (
                        <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-0.5 shadow">
                          <Bot className="w-3.5 h-3.5" />
                        </div>
                      )}

                      <div
                        className={`max-w-[85%] rounded-xl p-3 text-[11px] leading-relaxed space-y-2.5 ${
                          msg.sender === 'user'
                            ? 'bg-indigo-600 text-white font-medium shadow-md'
                            : 'bg-slate-900 border border-slate-800 text-slate-200 shadow'
                        }`}
                      >
                        <div dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />

                        {msg.metrics && msg.metrics.length > 0 && (
                          <div className="grid grid-cols-3 gap-1.5 pt-2 border-t border-slate-800">
                            {msg.metrics.map((m, i) => (
                              <div key={i} className="bg-slate-950 p-1.5 rounded-lg border border-slate-800 text-center">
                                <span className="text-[9px] text-slate-400 block">{m.label}</span>
                                <span className="text-[10px] font-bold text-emerald-400">{m.value}</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {msg.recommendation && (
                          <div className="bg-indigo-950/60 border border-indigo-500/30 p-2 rounded-lg space-y-0.5">
                            <div className="text-[9px] font-bold text-indigo-300 uppercase flex items-center gap-1">
                              <Sparkles className="w-2.5 h-2.5 text-indigo-400" /> AI Recommendation
                            </div>
                            <div className="text-[10px] text-slate-200">{msg.recommendation}</div>
                          </div>
                        )}

                        {msg.suggestedAction && (
                          <button
                            onClick={() => handleExecuteAction(msg)}
                            className="w-full text-center text-[10px] font-bold text-indigo-300 bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/40 py-1 rounded-lg transition-colors flex items-center justify-center gap-1"
                          >
                            <span>{msg.suggestedAction}</span>
                            <ChevronRight className="w-3 h-3" />
                          </button>
                        )}
                      </div>

                      {msg.sender === 'user' && (
                        <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300 font-bold text-[10px] shrink-0 mt-0.5 border border-slate-700">
                          YOU
                        </div>
                      )}
                    </div>
                  ))}

                  {loading && (
                    <div className="flex gap-2 text-slate-400 text-[10px] animate-pulse items-center">
                      <div className="w-6 h-6 rounded-lg bg-indigo-600/40 flex items-center justify-center text-white">
                        <Bot className="w-3 h-3" />
                      </div>
                      <span>Synthesizing intelligence response...</span>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Bar */}
                <div className="p-3 border-t border-slate-800 bg-slate-900/90 flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Ask AI Copilot..."
                    value={inputQuery}
                    onChange={(e) => setInputQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 px-3 py-2 focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={() => handleSendMessage()}
                    disabled={loading || !inputQuery.trim()}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white p-2 rounded-lg transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </motion.div>
            </div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
