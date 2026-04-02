import React, { useState, useEffect } from 'react';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '../ui/resizable';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { Play, Plus, RefreshCw, AlertTriangle, Zap, CheckCircle, XCircle, ListChecks } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useSSE } from '../../hooks/useSSE';
import { arkAPI, BACKEND_URL } from '../../api/ark';
import LiveExecutionFeed from './LiveExecutionFeed';
import PlanPanel from './PlanPanel';
import TerminalPanel from './TerminalPanel';
import ApprovalCard from './ApprovalCard';
import NewSessionModal from './NewSessionModal';
import QuickActionsPanel from './QuickActionsPanel';
import ExecutionSummary from './ExecutionSummary';
import AgentSelector from './AgentSelector';
import { toast } from 'sonner';

const ArkDashboard = () => {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);
  const [showNewSessionModal, setShowNewSessionModal] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [processingApproval, setProcessingApproval] = useState(false);
  const [budgetError, setBudgetError] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState(null);

  // SSE connection
  const streamURL = currentSessionId ? arkAPI.getStreamURL(currentSessionId) : null;
  const { events, isConnected, clearEvents } = useSSE(streamURL, !!currentSessionId && isExecuting);

  // Find pending approval
  const pendingApproval = events.find(e => e.type === 'approval_required');

  // Check backend health on mount
  useEffect(() => {
    const checkBackendHealth = async () => {
      console.log('Checking backend health at:', BACKEND_URL);
      const health = await arkAPI.healthCheck();
      console.log('Backend health:', health);
      setBackendHealthy(health.healthy);

      if (!health.healthy) {
        toast.error('Cannot connect to backend API');
      }
    };

    checkBackendHealth();
  }, []);

  // Check for budget errors in events
  useEffect(() => {
    const errorEvent = events.find(e =>
      e.type === 'error' &&
      e.data?.error?.includes('Budget has been exceeded')
    );
    if (errorEvent) {
      setBudgetError(true);
      setIsExecuting(false);
    }
  }, [events]);

  // Fetch session details periodically
  useEffect(() => {
    if (currentSessionId) {
      const fetchSession = async () => {
        try {
          const session = await arkAPI.getSession(currentSessionId);
          setCurrentSession(session);
        } catch (error) {
          console.error('Error fetching session:', error);
        }
      };

      fetchSession();
      const interval = setInterval(fetchSession, 3000);
      return () => clearInterval(interval);
    }
  }, [currentSessionId]);

  const handleCreateSession = async (prompt, workspacePath) => {
    try {
      const response = await arkAPI.createSession(prompt, workspacePath);
      setCurrentSessionId(response.session_id);
      clearEvents();
      setBudgetError(false);
      toast.success('Session created successfully!');

      // Auto-start execution
      setTimeout(() => handleExecute(response.session_id), 500);
    } catch (error) {
      console.error('Error creating session:', error);
      toast.error('Failed to create session');
      throw error;
    }
  };

  const handleWorkflowStart = async (sessionId, workflow) => {
    setCurrentSessionId(sessionId);
    clearEvents();
    setBudgetError(false);

    // Auto-start execution
    setTimeout(() => handleExecute(sessionId), 500);
  };

  const handleExecute = async (sessionId = currentSessionId) => {
    if (!sessionId) return;

    try {
      setIsExecuting(true);
      setBudgetError(false);
      await arkAPI.executeSession(sessionId);
      toast.success('Execution started!');
    } catch (error) {
      console.error('Error executing session:', error);
      toast.error('Failed to start execution');
      setIsExecuting(false);
    }
  };

  const handleApproval = async (approved) => {
    if (!currentSessionId) return;

    setProcessingApproval(true);
    try {
      await arkAPI.approveAction(currentSessionId, approved);
      toast.success(approved ? 'Action approved' : 'Action rejected');
    } catch (error) {
      console.error('Error processing approval:', error);
      toast.error('Failed to process approval');
    } finally {
      setProcessingApproval(false);
    }
  };

  // Check if execution is done
  useEffect(() => {
    const lastEvent = events[events.length - 1];
    if (lastEvent && ['done', 'error'].includes(lastEvent.type)) {
      setIsExecuting(false);
    }
  }, [events]);

  return (
    <div className="h-screen flex flex-col bg-gray-50" data-testid="ark-dashboard">
      {/* Header */}
      <div className="bg-white border-b px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Ark IDE</h1>
              <div className="flex items-center gap-2">
                <p className="text-xs text-gray-500 hidden sm:block">AI Agent Workbench v2.0</p>
                {backendHealthy !== null && (
                  <div className="flex items-center gap-1">
                    {backendHealthy ? (
                      <CheckCircle className="w-3 h-3 text-green-500" />
                    ) : (
                      <XCircle className="w-3 h-3 text-red-500" />
                    )}
                    <span className="text-xs text-gray-500">
                      {backendHealthy ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
          {/* Navigation */}
          <Button asChild variant="outline" size="sm" className="flex items-center gap-2">
            <Link to="/todos">
              <ListChecks className="w-4 h-4" />
              <span className="hidden sm:inline">Todos</span>
            </Link>
          </Button>

          {currentSessionId && (
            <>
              <AgentSelector
                sessionId={currentSessionId}
                onAgentAssigned={() => {}}
              />
              <div className="text-xs text-gray-600 hidden sm:block">
                Session: <span className="font-mono">{currentSessionId.slice(0, 8)}</span>
              </div>
            </>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open('https://app.emergent.sh/profile', '_blank')}
            className="hidden sm:flex items-center gap-1"
          >
            <Zap className="w-3 h-3" />
            <span className="text-xs">Universal Key</span>
          </Button>
          <Button
            onClick={() => setShowNewSessionModal(true)}
            className="flex items-center gap-2"
            data-testid="new-session-button"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">New Session</span>
          </Button>
        </div>
      </div>

      {/* Backend Connection Error */}
      {backendHealthy === false && (
        <div className="px-4 sm:px-6 pt-4">
          <Alert variant="destructive" className="border-2">
            <XCircle className="h-5 w-5" />
            <AlertDescription className="ml-2">
              <strong>Connection Error:</strong> Cannot connect to backend API at <code className="text-xs">{BACKEND_URL}</code>
              <div className="mt-3 space-y-2">
                <div className="text-xs text-red-800">
                  <strong>Possible causes:</strong>
                  <ul className="list-disc ml-4 mt-1">
                    <li>Backend server is not running</li>
                    <li>Network connectivity issues</li>
                    <li>CORS configuration problem</li>
                    <li>Incorrect backend URL</li>
                  </ul>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.location.reload()}
                  className="bg-white hover:bg-gray-100"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reload Page
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Budget Error Alert */}
      {budgetError && (
        <div className="px-4 sm:px-6 pt-4">
          <Alert variant="destructive" className="border-2">
            <AlertTriangle className="h-5 w-5" />
            <AlertDescription className="ml-2">
              <strong>Universal Key Budget Limit Reached:</strong> Your Universal Key has hit its $1.00 spending limit.
              <div className="mt-3 space-y-2">
                <div className="text-sm text-red-800 bg-red-50 p-2 rounded">
                  <strong>Important:</strong> You have credits in your account, but your Universal Key needs a higher budget limit.
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open('https://app.emergent.sh/profile', '_blank')}
                    className="bg-white hover:bg-gray-100"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Increase Key Budget Limit
                  </Button>
                </div>
                <div className="text-xs text-red-800">
                  <strong>Steps:</strong>
                  <ol className="list-decimal ml-4 mt-1 space-y-1">
                    <li>Click button above to open Emergent Platform</li>
                    <li>Go to Profile → Universal Key</li>
                    <li>Find "Budget Limit" setting</li>
                    <li>Increase limit from $1.00 to $10+ (recommended)</li>
                    <li>Or set to unlimited if you prefer</li>
                  </ol>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Universal Key Info Banner */}
      {!budgetError && !currentSessionId && (
        <div className="px-4 sm:px-6 pt-4">
          <Alert className="border-blue-200 bg-blue-50">
            <AlertDescription className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-blue-600" />
                <span className="text-sm text-blue-900">
                  Ark IDE uses your <strong>Emergent Universal Key</strong> for AI features
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open('https://app.emergent.sh/profile', '_blank')}
                className="bg-white hover:bg-gray-100 text-xs"
              >
                Manage Key
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Approval Card (if needed) */}
      {pendingApproval && (
        <div className="px-4 sm:px-6 pt-4">
          <ApprovalCard
            event={pendingApproval}
            onApprove={() => handleApproval(true)}
            onReject={() => handleApproval(false)}
            isProcessing={processingApproval}
          />
        </div>
      )}

      {/* Execution Summary */}
      {currentSession && ['completed', 'failed'].includes(currentSession.status) && (
        <div className="px-4 sm:px-6 pt-4">
          <ExecutionSummary
            sessionId={currentSessionId}
            status={currentSession.status}
          />
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {/* Desktop: 3-panel layout */}
        <div className="hidden lg:block h-full">
          <ResizablePanelGroup direction="horizontal" className="h-full">
            {/* Left: Execution Feed + Terminal */}
            <ResizablePanel defaultSize={55} minSize={30}>
              <div className="h-full">
                <ResizablePanelGroup direction="vertical">
                  {/* Top: Live Feed */}
                  <ResizablePanel defaultSize={65} minSize={40}>
                    <LiveExecutionFeed events={events} isConnected={isConnected} />
                  </ResizablePanel>

                  <ResizableHandle />

                  {/* Bottom: Terminal */}
                  <ResizablePanel defaultSize={35} minSize={20}>
                    <TerminalPanel events={events} />
                  </ResizablePanel>
                </ResizablePanelGroup>
              </div>
            </ResizablePanel>

            <ResizableHandle />

            {/* Right: Quick Actions + Plan */}
            <ResizablePanel defaultSize={45} minSize={30}>
              <div className="h-full overflow-y-auto p-4 space-y-4 bg-gray-50">
                <QuickActionsPanel onWorkflowStart={handleWorkflowStart} />
                <PlanPanel events={events} />
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>

        {/* Mobile/Tablet: Tabbed layout */}
        <div className="lg:hidden h-full overflow-y-auto">
          <div className="p-4 space-y-4">
            {!currentSessionId && (
              <QuickActionsPanel onWorkflowStart={handleWorkflowStart} />
            )}

            {currentSessionId && (
              <>
                <LiveExecutionFeed events={events} isConnected={isConnected} />
                <PlanPanel events={events} />
                <TerminalPanel events={events} />
              </>
            )}
          </div>
        </div>
      </div>

      {/* Empty State */}
      {!currentSessionId && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 bg-opacity-95 pointer-events-none z-10">
          <div className="text-center pointer-events-auto max-w-md px-4">
            <div className="text-6xl mb-4">🚀</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome to Ark IDE v2.0</h2>
            <p className="text-gray-600 mb-6">
              Feature-rich AI agent workbench with workflows, multi-agent coordination, and git integration
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button
                onClick={() => setShowNewSessionModal(true)}
                size="lg"
                className="flex items-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Create Custom Session
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-4">
              Or use Quick Actions above to start a preset workflow
            </p>
          </div>
        </div>
      )}

      {/* New Session Modal */}
      <NewSessionModal
        open={showNewSessionModal}
        onClose={() => setShowNewSessionModal(false)}
        onCreateSession={handleCreateSession}
      />
    </div>
  );
};

export default ArkDashboard;
