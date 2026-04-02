import React from 'react';
import { FileText, Edit, Plus } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';

const PlanPanel = ({ events }) => {
  // Extract file changes from events
  const fileChanges = events
    .filter(e => e.type === 'tool_call' && e.data.tool_name === 'write_file')
    .map(e => ({
      file: e.data.arguments.path,
      timestamp: e.timestamp,
      type: 'modified'
    }));

  // Extract plan/thoughts
  const thoughts = events
    .filter(e => e.type === 'thought')
    .map(e => ({
      step: e.data.step,
      thought: e.data.thought,
      timestamp: e.timestamp
    }));

  return (
    <div className="h-full flex flex-col border-l" data-testid="plan-panel">
      <div className="p-4 border-b">
        <h2 className="text-lg font-bold">Plan & Changes</h2>
      </div>

      <ScrollArea className="flex-1 p-4">
        {/* Plan Section */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Thinking Process
          </h3>
          {thoughts.length === 0 ? (
            <p className="text-sm text-gray-400 italic">No thoughts yet...</p>
          ) : (
            <div className="space-y-2">
              {thoughts.map((thought, index) => (
                <Card key={index} className="bg-purple-50 border-purple-200">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-xs">
                        Step {thought.step}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(thought.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{thought.thought}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* File Changes Section */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Edit className="w-4 h-4" />
            File Changes ({fileChanges.length})
          </h3>
          {fileChanges.length === 0 ? (
            <p className="text-sm text-gray-400 italic">No files changed yet...</p>
          ) : (
            <div className="space-y-2">
              {fileChanges.map((change, index) => (
                <Card key={index} className="bg-green-50 border-green-200">
                  <CardContent className="p-3">
                    <div className="flex items-start gap-2">
                      <Plus className="w-4 h-4 text-green-600 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-mono text-gray-800">{change.file}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(change.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

export default PlanPanel;
