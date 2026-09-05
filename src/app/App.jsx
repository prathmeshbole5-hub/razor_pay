import React, { useState, lazy, Suspense } from 'react';
import { ErrorBoundary, PageLoadingFallback } from '../shared/components/ErrorBoundary';

import MerchantLayout from '../merchant/layout/MerchantLayout';
import InternalLayout from '../internal/layout/InternalLayout';
import GuidedDemoBanner from '../shared/components/demo/GuidedDemoBanner';
import AICopilotDrawer from '../shared/components/intelligence/AICopilotDrawer';

// Lazy loading for Merchant Portal pages
const MerchantDashboard = lazy(() => import('../merchant/pages/MerchantDashboard'));
const LivePayments = lazy(() => import('../merchant/pages/LivePayments'));
const PaymentDenials = lazy(() => import('../merchant/pages/PaymentDenials'));
const RecoveryCases = lazy(() => import('../merchant/pages/RecoveryCases'));
const AICopilot = lazy(() => import('../merchant/pages/AICopilot'));
const Analytics = lazy(() => import('../merchant/pages/Analytics'));
const MerchantProfile = lazy(() => import('../merchant/pages/MerchantProfile'));

// Lazy loading for Internal Portal pages
const InternalOverview = lazy(() => import('../internal/pages/InternalOverview'));
const GatewayHealth = lazy(() => import('../internal/pages/GatewayHealth'));
const FailureIntelligence = lazy(() => import('../internal/pages/FailureIntelligence'));
const MerchantNetwork = lazy(() => import('../internal/pages/MerchantNetwork'));
const SystemFlow = lazy(() => import('../internal/pages/SystemFlow'));
const InternalAnalytics = lazy(() => import('../internal/pages/InternalAnalytics'));

export default function App() {
  const [currentPortal, setCurrentPortal] = useState('merchant'); // 'merchant' | 'internal'
  const [merchantTab, setMerchantTab] = useState('dashboard');
  const [internalTab, setInternalTab] = useState('overview');

  const handlePortalChange = (portal) => {
    setCurrentPortal(portal);
  };

  const handleActiveTabChange = (tab) => {
    if (currentPortal === 'merchant') {
      setMerchantTab(tab);
    } else {
      setInternalTab(tab);
    }
  };

  const renderMerchantPage = () => {
    switch (merchantTab) {
      case 'dashboard':
        return <MerchantDashboard onNavigate={(tab) => setMerchantTab(tab)} />;
      case 'live-payments':
        return <LivePayments />;
      case 'denials':
        return <PaymentDenials />;
      case 'cases':
        return <RecoveryCases />;
      case 'copilot':
        return <AICopilot />;
      case 'analytics':
        return <Analytics />;
      case 'profile':
        return <MerchantProfile />;
      default:
        return <MerchantDashboard onNavigate={(tab) => setMerchantTab(tab)} />;
    }
  };

  const renderInternalPage = () => {
    switch (internalTab) {
      case 'overview':
        return <InternalOverview onNavigate={(tab) => setInternalTab(tab)} />;
      case 'gateway':
        return <GatewayHealth />;
      case 'intelligence':
        return <FailureIntelligence onNavigate={(tab) => setInternalTab(tab)} />;
      case 'network':
        return <MerchantNetwork />;
      case 'flow':
        return <SystemFlow />;
      case 'analytics':
        return <InternalAnalytics />;
      default:
        return <InternalOverview onNavigate={(tab) => setInternalTab(tab)} />;
    }
  };

  const activeTab = currentPortal === 'merchant' ? merchantTab : internalTab;

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans relative">
        {/* Presentation Guided Demo Bar */}
        <GuidedDemoBanner
          currentPortal={currentPortal}
          onPortalChange={handlePortalChange}
          activeTab={activeTab}
          onTabChange={handleActiveTabChange}
        />

        <div className="flex-1 flex flex-col">
          <Suspense fallback={<PageLoadingFallback />}>
            {currentPortal === 'merchant' ? (
              <MerchantLayout
                currentPortal={currentPortal}
                onPortalChange={handlePortalChange}
                activeTab={merchantTab}
                setActiveTab={setMerchantTab}
              >
                {renderMerchantPage()}
              </MerchantLayout>
            ) : (
              <InternalLayout
                currentPortal={currentPortal}
                onPortalChange={handlePortalChange}
                activeTab={internalTab}
                setActiveTab={setInternalTab}
              >
                {renderInternalPage()}
              </InternalLayout>
            )}
          </Suspense>
        </div>

        {/* Floating AI Copilot Assistant Drawer */}
        <AICopilotDrawer currentPortal={currentPortal} />
      </div>
    </ErrorBoundary>
  );
}
