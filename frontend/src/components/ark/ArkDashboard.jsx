import React, { useState, useEffect } from 'react';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { Button } from '@/components/ui/button';
import { Play, Plus, RefreshCw } from 'lucide-react';
import { useSSE } from '@/hooks/useSSE';
import { arkAPI } from '@/api/ark';
import LiveExecutionFeed from './LiveExecutionFeed';
import PlanPanel from './PlanPanel';
import TerminalPanel from './TerminalPanel';
import ApprovalCard from './ApprovalCard';
import NewSessionModal from './NewSessionModal';
import { toast } from 'sonner';

const ArkDashboard = () => {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [showNewSessionModal, setShowNewSessionModal] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [processingApproval, setProcessingApproval] = useState(false);

  // SSE connection
  const streamURL = currentSessionId ? arkAPI.getStreamURL(currentSessionId) : null;
  const { events, isConnected, clearEvents } = useSSE(streamURL, !!currentSessionId && isExecuting);

  // Find pending approval
  const pendingApproval = events.find(e => e.type === 'approval_required');

  const handleCreateSession = async (prompt, workspacePath) => {
    try {
      const response = await arkAPI.createSession(prompt, workspacePath);
      setCurrentSessionId(response.session_id);
      clearEvents();
      toast.success('Session created successfully!');
      
      // Auto-start execution
      setTimeout(() => handleExecute(response.session_id), 500);
    } catch (error) {
      console.error('Error creating session:', error);
      toast.error('Failed to create session');
      throw error;
    }
  };

  const handleExecute = async (sessionId = currentSessionId) => {
    if (!sessionId) return;

    try {
      setIsExecuting(true);
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
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ark IDE</h1>
          <p className="text-sm text-gray-500">AI Agent Workbench v1.0</p>
        </div>
        <div className="flex items-center gap-3">
          {currentSessionId && (
            <div className="text-sm text-gray-600">
              Session: <span className="font-mono text-xs">{currentSessionId.slice(0, 8)}</span>
            </div>
          )}
          <Button
            onClick={() => setShowNewSessionModal(true)}
            className="flex items-center gap-2"
            data-testid="new-session-button"
          >
            <Plus className="w-4 h-4" />
            New Session
          </Button>
        </div>
      </div>

      {/* Approval Card (if needed) */}
      {pendingApproval && (
        <div className="px-6 pt-4">
          <ApprovalCard
            event={pendingApproval}
            onApprove={() => handleApproval(true)}
            onReject={() => handleApproval(false)}
            isProcessing={processingApproval}
          />
        </div>
      )}

      {/* Main Content - 3 Panel Layout */}
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal" className="h-full">
          {/* Left: Execution Feed */}
          <ResizablePanel defaultSize={50} minSize={30}>
            <div className="h-full">
              <ResizablePanelGroup direction="vertical">
                {/* Top: Live Feed */}
                <ResizablePanel defaultSize={70} minSize={40}>
                  <LiveExecutionFeed events={events} isConnected={isConnected} />
                </ResizablePanel>

                <ResizableHandle />

                {/* Bottom: Terminal */}
                <ResizablePanel defaultSize={30} minSize={20}>
                  <TerminalPanel events={events} />
                </ResizablePanel>
              </ResizablePanelGroup>
            </div>
          </ResizablePanel>

          <ResizableHandle />

          {/* Right: Plan & Changes */}
          <ResizablePanel defaultSize={35} minSize={25}>
            <PlanPanel events={events} />
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>

      {/* Empty State */}
      {!currentSessionId && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 bg-opacity-95 pointer-events-none">
          <div className="text-center pointer-events-auto">
            <div className="text-6xl mb-4">🚀</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome to Ark IDE</h2>
            <p className="text-gray-600 mb-6">Create a new session to start building with AI</p>
            <Button
              onClick={() => setShowNewSessionModal(true)}
              size="lg"
              className="flex items-center gap-2 mx-auto"
            >
              <Plus className="w-5 h-5" />
              Create Your First Session
            </Button>
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
