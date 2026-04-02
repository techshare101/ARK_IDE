import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  Wrench, Bug, FileSearch, FolderSearch, 
  Play, Loader2, CheckCircle2 
} from 'lucide-react';
import { arkAPI } from '../../api/ark';
import { toast } from 'sonner';

const QuickActionsPanel = ({ onWorkflowStart }) => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [executingWorkflow, setExecutingWorkflow] = useState(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const data = await arkAPI.listWorkflows();
      setWorkflows(data.workflows);
    } catch (error) {
      console.error('Error loading workflows:', error);
    }
  };

  const getWorkflowIcon = (type) => {
    switch (type) {
      case 'fix_build':
        return <Wrench className="w-5 h-5" />;
      case 'debug_error':
        return <Bug className="w-5 h-5" />;
      case 'explain_code':
        return <FileSearch className="w-5 h-5" />;
      case 'scan_project':
        return <FolderSearch className="w-5 h-5" />;
      default:
        return <Play className="w-5 h-5" />;
    }
  };

  const handleWorkflowClick = async (workflow) => {
    setLoading(true);
    setExecutingWorkflow(workflow.type);
    
    try {
      const response = await arkAPI.executeWorkflow(workflow.type);
      toast.success(`${workflow.name} workflow started!`);
      
      if (onWorkflowStart) {
        onWorkflowStart(response.session_id, workflow);
      }
    } catch (error) {
      console.error('Error starting workflow:', error);
      toast.error(`Failed to start ${workflow.name}`);
    } finally {
      setLoading(false);
      setExecutingWorkflow(null);
    }
  };

  return (
    <Card className="w-full" data-testid="quick-actions-panel">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Play className="w-5 h-5" />
          Quick Actions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {workflows.map((workflow) => (
            <Button
              key={workflow.type}
              variant="outline"
              className="w-full justify-start gap-3 h-auto py-3"
              onClick={() => handleWorkflowClick(workflow)}
              disabled={loading}
              data-testid={`workflow-btn-${workflow.type}`}
            >
              <div className="flex items-center gap-3 flex-1">
                <div className="p-2 rounded-lg bg-blue-50">
                  {getWorkflowIcon(workflow.type)}
                </div>
                <div className="flex-1 text-left">
                  <div className="font-semibold">{workflow.name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {workflow.description}
                  </div>
                  <Badge variant="secondary" className="mt-1 text-xs">
                    {workflow.estimated_duration}
                  </Badge>
                </div>
                {executingWorkflow === workflow.type && (
                  <Loader2 className="w-4 h-4 animate-spin" />
                )}
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default QuickActionsPanel;
