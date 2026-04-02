import React from 'react';
import { Terminal as TerminalIcon } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { ScrollArea } from '../ui/scroll-area';
import { Badge } from '../ui/badge';

const TerminalPanel = ({ events }) => {
  // Extract command executions
  const commandResults = events
    .filter(e => 
      (e.type === 'tool_call' && e.data.tool_name === 'run_command') ||
      (e.type === 'tool_result' && e.data.tool_name === 'run_command')
    )
    .reduce((acc, event) => {
      if (event.type === 'tool_call') {
        acc.push({
          command: event.data.arguments.command,
          timestamp: event.timestamp,
          result: null
        });
      } else if (event.type === 'tool_result' && acc.length > 0) {
        const lastCmd = acc[acc.length - 1];
        if (!lastCmd.result) {
          lastCmd.result = event.data.result.result;
        }
      }
      return acc;
    }, []);

  return (
    <div className="h-full flex flex-col border-t bg-gray-900 text-gray-100" data-testid="terminal-panel">
      <div className="p-3 border-b border-gray-700 flex items-center gap-2">
        <TerminalIcon className="w-4 h-4" />
        <h3 className="text-sm font-semibold">Terminal Output</h3>
        <Badge variant="outline" className="ml-auto text-xs border-gray-600 text-gray-300">
          {commandResults.length} commands
        </Badge>
      </div>

      <ScrollArea className="flex-1 p-4">
        {commandResults.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p className="text-sm">No commands executed yet...</p>
          </div>
        ) : (
          <div className="space-y-4 font-mono text-sm">
            {commandResults.map((cmd, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-green-400">$</span>
                  <span className="text-gray-200">{cmd.command}</span>
                  <span className="text-xs text-gray-500 ml-auto">
                    {new Date(cmd.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                
                {cmd.result && (
                  <Card className="bg-gray-800 border-gray-700">
                    <CardContent className="p-3">
                      {cmd.result.stdout && (
                        <div className="mb-2">
                          <div className="text-xs text-gray-400 mb-1">stdout:</div>
                          <pre className="text-xs text-green-300 whitespace-pre-wrap">
                            {cmd.result.stdout}
                          </pre>
                        </div>
                      )}
                      
                      {cmd.result.stderr && (
                        <div className="mb-2">
                          <div className="text-xs text-gray-400 mb-1">stderr:</div>
                          <pre className="text-xs text-red-300 whitespace-pre-wrap">
                            {cmd.result.stderr}
                          </pre>
                        </div>
                      )}
                      
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-gray-400">exit code:</span>
                        <Badge variant={cmd.result.exit_code === 0 ? "default" : "destructive"} className="text-xs">
                          {cmd.result.exit_code}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
};

export default TerminalPanel;
