import React from 'react';
import { AlertTriangle, RefreshCw, LayoutDashboard, Zap } from 'lucide-react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }


  componentDidCatch(error, errorInfo) {
    console.error('[RecoverAI Error Boundary Caught Error]:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  handleGoHome = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 select-none font-sans">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 space-y-6 shadow-2xl text-center">
            <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mx-auto shadow-lg">
              <AlertTriangle className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-extrabold tracking-tight text-white flex items-center justify-center gap-1.5">
                RECOVER<span className="text-indigo-400">AI</span>
              </h2>
              <h3 className="text-base font-bold text-slate-200">
                Unexpected Interface Exception
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                An unexpected component rendering error occurred. The application state has been safely isolated.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                onClick={this.handleRetry}
                className="flex-1 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
              >
                <RefreshCw className="w-4 h-4" />
                Retry Component
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex-1 py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <LayoutDashboard className="w-4 h-4" />
                Return to Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export function PageLoadingFallback() {
  return (
    <div className="flex flex-col items-center justify-center py-20 space-y-4 animate-fadeIn">
      <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 animate-pulse shadow-lg shadow-indigo-500/10">
        <Zap className="w-6 h-6 fill-current" />
      </div>
      <div className="text-xs font-mono font-semibold text-slate-400">
        Loading RecoverAI Module...
      </div>
    </div>
  );
}
