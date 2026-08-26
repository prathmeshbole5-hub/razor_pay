import React from 'react';
import InternalSidebar from './InternalSidebar';
import InternalTopbar from './InternalTopbar';

export default function InternalLayout({ currentPortal, onPortalChange, activeTab, setActiveTab, children }) {
  const pageTitles = {
    overview: 'Razorpay Infrastructure Command Center',
    gateway: 'Gateway & Banking Health Monitor',
    intelligence: 'AI Failure Anomaly & Root Cause Intelligence',
    network: 'Ecosystem Merchant Network Analytics',
    flow: 'System Architecture & Recovery Flow Diagram',
    analytics: 'Network Performance & Failure Metrics'
  };

  return (
    <div className="theme-internal min-h-screen bg-slate-950 text-slate-100 flex telemetry-grid">
      {/* Sidebar */}
      <InternalSidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <InternalTopbar
          currentPortal={currentPortal}
          onPortalChange={onPortalChange}
          activePageTitle={pageTitles[activeTab] || 'Overview'}
        />

        <main className="flex-1 p-4 sm:p-8 max-w-7xl w-full mx-auto space-y-8">
          {children}
        </main>
      </div>
    </div>
  );
}
