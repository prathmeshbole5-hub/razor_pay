import React from 'react';
import MerchantSidebar from './MerchantSidebar';
import MerchantTopbar from './MerchantTopbar';

export default function MerchantLayout({ currentPortal, onPortalChange, activeTab, setActiveTab, children }) {
  const pageTitles = {
    dashboard: 'Merchant Dashboard',
    denials: 'Payment Denials & Failed Transactions',
    cases: 'Active Recovery Cases Lifecycle',
    copilot: 'RecoverAI Financial Assistant',
    analytics: 'Merchant Failure & Recovery Analytics',
    profile: 'Merchant Profile & Webhook Settings'
  };

  return (
    <div className="theme-merchant min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Sidebar */}
      <MerchantSidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <MerchantTopbar
          currentPortal={currentPortal}
          onPortalChange={onPortalChange}
          activePageTitle={pageTitles[activeTab] || 'Dashboard'}
        />

        <main className="flex-1 p-4 sm:p-8 max-w-7xl w-full mx-auto space-y-8">
          {children}
        </main>
      </div>
    </div>
  );
}
