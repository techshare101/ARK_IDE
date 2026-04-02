import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Loader2 } from 'lucide-react';

const NewSessionModal = ({ open, onClose, onCreateSession }) => {
  const [prompt, setPrompt] = useState('');
  const [workspacePath, setWorkspacePath] = useState('/app');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = async () => {
    if (!prompt.trim()) return;

    setIsCreating(true);
    try {
      await onCreateSession(prompt, workspacePath);
      setPrompt('');
      setWorkspacePath('/app');
      onClose();
    } catch (error) {
      console.error('Error creating session:', error);
      alert('Failed to create session: ' + error.message);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]" data-testid="new-session-modal">
        <DialogHeader>
          <DialogTitle>Create New Agent Session</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="prompt">What would you like the agent to do?</Label>
            <Textarea
              id="prompt"
              placeholder="e.g., Fix the build error, Create a landing page, Debug the API issue..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={6}
              className="resize-none"
              data-testid="session-prompt-input"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="workspace">Workspace Path</Label>
            <Input
              id="workspace"
              value={workspacePath}
              onChange={(e) => setWorkspacePath(e.target.value)}
              placeholder="/app"
              data-testid="workspace-path-input"
            />
            <p className="text-xs text-gray-500">
              The agent will operate within this directory
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isCreating}>
            Cancel
          </Button>
          <Button 
            onClick={handleCreate} 
            disabled={!prompt.trim() || isCreating}
            data-testid="create-session-button"
          >
            {isCreating && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            {isCreating ? 'Creating...' : 'Create & Start'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default NewSessionModal;
