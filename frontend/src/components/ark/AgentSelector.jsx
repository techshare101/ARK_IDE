import React, { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Users, Brain } from 'lucide-react';
import { arkAPI } from '../../api/ark';
import { toast } from 'sonner';

const AgentSelector = ({ sessionId, onAgentAssigned }) => {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await arkAPI.listAgents();
      setAgents(data.agents);
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  const handleAgentSelect = async (role) => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      await arkAPI.assignAgent(sessionId, role);
      setSelectedAgent(role);
      toast.success(`Assigned ${role} agent to session`);
      
      if (onAgentAssigned) {
        onAgentAssigned(role);
      }
    } catch (error) {
      console.error('Error assigning agent:', error);
      toast.error('Failed to assign agent');
    } finally {
      setLoading(false);
    }
  };

  const getAgentColor = (role) => {
    const colors = {
      architect: 'bg-purple-100 text-purple-700',
      coder: 'bg-blue-100 text-blue-700',
      reviewer: 'bg-green-100 text-green-700',
      qa: 'bg-yellow-100 text-yellow-700',
      debugger: 'bg-red-100 text-red-700'
    };
    return colors[role] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="flex items-center gap-2" data-testid="agent-selector">
      <Users className="w-4 h-4 text-gray-500" />
      <Select onValueChange={handleAgentSelect} disabled={!sessionId || loading}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select agent..." />
        </SelectTrigger>
        <SelectContent>
          {agents.map((agent) => (
            <SelectItem key={agent.role} value={agent.role}>
              <div className="flex items-center gap-2">
                <Brain className="w-3 h-3" />
                <span className="capitalize">{agent.role}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {selectedAgent && (
        <Badge className={getAgentColor(selectedAgent)}>
          {selectedAgent}
        </Badge>
      )}
    </div>
  );
};

export default AgentSelector;
