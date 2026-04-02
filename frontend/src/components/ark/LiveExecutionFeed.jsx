import React from 'react';
import { Loader2, CheckCircle2, XCircle, Brain, Wrench, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';

const LiveExecutionFeed = ({ events, isConnected }) => {
  const getEventIcon = (type) => {
    switch (type) {
      case 'started':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'thinking':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'thought':
        return <Brain className="w-5 h-5 text-purple-500" />;
      case 'tool_call':
        return <Wrench className="w-5 h-5 text-orange-500" />;
      case 'tool_result':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'approval_required':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'done':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <div className="w-5 h-5 rounded-full bg-gray-400" />;
    }
  };

  const renderEventContent = (event) => {
    const { type, data } = event;

    switch (type) {
      case 'started':
        return (
          <div>
            <div className="font-semibold text-green-600">Session Started</div>
            <div className="text-sm text-gray-600 mt-1">{data.prompt}</div>
          </div>
        );

      case 'thinking':
        return (
          <div>
            <div className="font-semibold text-blue-600">Thinking...</div>
            <div className="text-sm text-gray-500">{data.message}</div>
          </div>
        );

      case 'thought':
        return (
          <div>
            <div className="font-semibold text-purple-600">Step {data.step} - Planning</div>
            <div className="text-sm text-gray-700 mt-1 italic">{data.thought}</div>
          </div>
        );

      case 'tool_call':
        return (
          <div>
            <div className="font-semibold text-orange-600">Executing Tool</div>
            <Badge variant="outline" className="mt-1">{data.tool_name}</Badge>
            <pre className="text-xs bg-gray-50 p-2 rounded mt-2 overflow-auto">
              {JSON.stringify(data.arguments, null, 2)}
            </pre>
          </div>
        );

      case 'tool_result':
        return (
          <div>
            <div className="font-semibold text-green-600">Tool Result</div>
            <Badge variant={data.success ? "default" : "destructive"} className="mt-1">
              {data.success ? '✓ Success' : '✗ Failed'}
            </Badge>
            {data.result && (
              <pre className="text-xs bg-gray-50 p-2 rounded mt-2 overflow-auto max-h-32">
                {JSON.stringify(data.result, null, 2)}
              </pre>
            )}
          </div>
        );

      case 'approval_required':
        return (
          <div>
            <div className="font-semibold text-yellow-600">⚠️ Approval Required</div>
            <div className="text-sm mt-1">Tool: <Badge>{data.tool_name}</Badge></div>
            <div className="text-xs text-gray-600 mt-1">Reason: {data.reason}</div>
          </div>
        );

      case 'done':
        return (
          <div>
            <div className="font-semibold text-green-700">✅ Task Completed</div>
            <div className="text-sm text-gray-700 mt-1">{data.summary}</div>
          </div>
        );

      case 'error':
        return (
          <div>
            <div className="font-semibold text-red-600">❌ Error</div>
            <div className="text-sm text-red-700 mt-1">{data.error}</div>
          </div>
        );

      default:
        return <div className="text-sm text-gray-600">{JSON.stringify(data)}</div>;
    }
  };

  return (
    <div className="h-full flex flex-col" data-testid="live-execution-feed">
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-lg font-bold">Execution Feed</h2>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        {events.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <Loader2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Waiting for execution...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((event, index) => (
              <Card key={index} className="border-l-4" style={{
                borderLeftColor: event.type === 'error' ? '#ef4444' :
                                event.type === 'done' ? '#10b981' :
                                event.type === 'approval_required' ? '#f59e0b' :
                                '#3b82f6'
              }} data-testid={`event-${event.type}`}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="mt-1">{getEventIcon(event.type)}</div>
                    <div className="flex-1">
                      {renderEventContent(event)}
                      <div className="text-xs text-gray-400 mt-2">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
};

export default LiveExecutionFeed;
