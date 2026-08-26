import React, { useState, useEffect } from 'react';
import { Sparkles, ChevronLeft, ChevronRight, Play, Square, X, ShieldCheck, Zap, RefreshCw, AlertTriangle } from 'lucide-react';
import { DEMO_STEPS } from '../../../config/demoConfig';
import { triggerSimulateEvent, resetDemoSimulation, seedDemoScenario, resetAllDemoData } from '../../../api/intelligenceApi';

export default function GuidedDemoBanner({ currentPortal, onPortalChange, activeTab, onTabChange }) {
  const [demoActive, setDemoActive] = useState(false);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [isAutoPlay, setIsAutoPlay] = useState(false);
  const [simMessage, setSimMessage] = useState(null);
  const [loadingSeed, setLoadingSeed] = useState(false);

  const currentStep = DEMO_STEPS[currentStepIdx];

  const handleLoadSeed = async () => {
    setLoadingSeed(true);
    try {
      await seedDemoScenario();
      setSimMessage('✓ Demo Scenario Ready: Seeded ₹12,499 HDFC 3DS failure payment in DB');
      onPortalChange('merchant');
      onTabChange('live-payments');
      setDemoActive(true);
      setCurrentStepIdx(2); // Jump to Step 3: Live Failed Payment
    } catch (err) {
      console.error('Failed to seed demo scenario:', err);
      setSimMessage(`Demo Seed Error: ${err.message}`);
    } finally {
      setLoadingSeed(false);
      setTimeout(() => setSimMessage(null), 5000);
    }
  };

  const handleResetAll = async () => {
    try {
      await resetAllDemoData();
      setSimMessage('✓ All demo payments and database records reset to clean state');
      if (activeTab === 'live-payments') {
        window.location.reload();
      }
    } catch (err) {
      console.error('Failed to reset demo data:', err);
      setSimMessage(`Reset Error: ${err.message}`);
    } finally {
      setTimeout(() => setSimMessage(null), 4000);
    }
  };

  const handleSimulate = async (type) => {
    try {
      const res = await triggerSimulateEvent(type);
      const evt = res.event || {};
      setSimMessage(`Simulated Event Triggered: ${evt.event_type} (${evt.gateway || evt.payment_id || 'OK'})`);
      setTimeout(() => setSimMessage(null), 4000);
    } catch (err) {
      console.error('Failed to trigger simulation event:', err);
    }
  };

  const handleResetSim = async () => {
    try {
      await resetDemoSimulation();
      setSimMessage('Simulation State Reset to Baseline Clean State');
      setTimeout(() => setSimMessage(null), 4000);
    } catch (err) {
      console.error('Failed to reset simulation:', err);
    }
  };

  if (!demoActive) {
    return (
      <div className="bg-gradient-to-r from-indigo-950/90 via-slate-950 to-indigo-950/90 border-b border-indigo-500/30 px-4 py-2 text-xs font-mono flex flex-wrap items-center justify-between text-indigo-300 gap-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400 animate-pulse" />
          <span className="font-bold text-white">RecoverAI Hackathon Presentation Mode</span>
          <span className="hidden md:inline text-slate-400">— Real ML Model & Persistent SQLite Backend</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleLoadSeed}
            disabled={loadingSeed}
            className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold rounded-lg transition-all shadow-md shadow-emerald-500/20 cursor-pointer disabled:opacity-50"
          >
            <Zap className="w-3.5 h-3.5 fill-current" />
            <span>{loadingSeed ? 'Seeding...' : 'Load Demo Scenario'}</span>
          </button>

          <button
            onClick={startDemo}
            className="flex items-center gap-1.5 px-3 py-1 bg-indigo-500 hover:bg-indigo-400 text-slate-950 font-bold rounded-lg transition-all shadow-md shadow-indigo-500/20 cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Guided Tour</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-950 border-b border-indigo-500/40 px-4 py-3 text-xs font-mono shadow-2xl space-y-2.5 z-40 relative">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="px-2.5 py-1 bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 font-extrabold rounded-lg shrink-0">
            STEP {currentStep.step} OF {DEMO_STEPS.length}
          </span>
          <h3 className="font-bold text-white text-sm truncate">{currentStep.title}</h3>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Hackathon Demo Controls */}
          <button
            onClick={handleLoadSeed}
            disabled={loadingSeed}
            title="Seed deterministic payment scenario in SQLite DB"
            className="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-emerald-300 font-bold rounded-lg flex items-center gap-1 transition-all cursor-pointer"
          >
            <Zap className="w-3 h-3 text-emerald-400 fill-current" />
            <span>Load Scenario</span>
          </button>

          <button
            onClick={handleResetAll}
            title="Reset All Live Demo Data"
            className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 font-semibold rounded-lg flex items-center gap-1 transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reset Demo</span>
          </button>

          <div className="h-4 w-[1px] bg-slate-800 mx-1 hidden sm:block" />

          {/* Real-time Simulation Triggers */}
          <button
            onClick={() => handleSimulate('failure')}
            title="Simulate Payment Failure Event"
            className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-rose-500/30 text-rose-300 font-semibold rounded-lg flex items-center gap-1 transition-colors"
          >
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            <span>Simulate Failure</span>
          </button>

          <button
            onClick={handleResetSim}
            title="Reset Simulation State"
            className="p-1.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 hover:text-white"
          >

            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          <div className="h-4 w-[1px] bg-slate-800 mx-1 hidden sm:block" />

          <button
            onClick={() => setIsAutoPlay(!isAutoPlay)}
            className={`px-2.5 py-1 rounded-lg border font-semibold flex items-center gap-1 transition-all ${
              isAutoPlay ? 'bg-amber-500/20 border-amber-500/40 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            {isAutoPlay ? <Square className="w-3 h-3 fill-current" /> : <Play className="w-3 h-3 fill-current" />}
            <span>{isAutoPlay ? 'Pause' : 'Auto Play'}</span>
          </button>

          <button
            onClick={handlePrev}
            disabled={currentStepIdx === 0}
            className="p-1.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <button
            onClick={handleNext}
            disabled={currentStepIdx === DEMO_STEPS.length - 1}
            className="p-1.5 bg-indigo-500 hover:bg-indigo-400 text-slate-950 rounded-lg font-bold disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <button
            onClick={stopDemo}
            className="p-1.5 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 hover:text-rose-400 transition-colors ml-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="bg-indigo-950/40 border border-indigo-500/20 p-2.5 rounded-xl text-slate-200 text-xs leading-normal flex items-start gap-2">
        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <strong className="text-white font-semibold">Demo Insight: </strong>
          {currentStep.narration}
          {simMessage && (
            <div className="text-amber-300 font-bold mt-1 animate-fadeIn">
              ⚡ {simMessage}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
