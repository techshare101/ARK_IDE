import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Sparkles, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { arkAPI } from '../../api/ark';

const ExecutionSummary = ({ sessionId, status }) => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (sessionId && ['completed', 'failed', 'cancelled'].includes(status)) {
      loadSummary();
    }
  }, [sessionId, status]);

  const loadSummary = async () => {
    setLoading(true);
    try {
      const data = await arkAPI.getExecutionSummary(sessionId);
      setSummary(data.summary);
    } catch (error) {
      console.error('Error loading summary:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!sessionId || !['completed', 'failed', 'cancelled'].includes(status)) {
    return null;
  }

  return (
    <Card 
      className="border-2 border-blue-200 bg-blue-50" 
      data-testid="execution-summary"
    >
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-blue-900">
          <Sparkles className="w-5 h-5" />
          Execution Summary
          {status === 'completed' && (
            <CheckCircle2 className="w-5 h-5 text-green-600 ml-auto" />
          )}
          {status === 'failed' && (
            <XCircle className="w-5 h-5 text-red-600 ml-auto" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center gap-2 text-blue-700">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Generating summary...</span>
          </div>
        ) : summary ? (
          <div className="space-y-2">
            <p className="text-sm text-blue-900 font-medium">{summary}</p>
            <Badge variant="outline" className="text-xs">
              AI-Generated Summary
            </Badge>
          </div>
        ) : (
          <p className="text-sm text-blue-700">Summary will appear here...</p>
        )}
      </CardContent>
    </Card>
  );
};

export default ExecutionSummary;
