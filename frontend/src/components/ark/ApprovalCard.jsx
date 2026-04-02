import React from 'react';
import { AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

const ApprovalCard = ({ event, onApprove, onReject, isProcessing }) => {
  if (!event || event.type !== 'approval_required') return null;

  const { data } = event;

  return (
    <Card className="border-yellow-400 border-2 shadow-lg" data-testid="approval-card">
      <CardHeader className="bg-yellow-50">
        <CardTitle className="flex items-center gap-2 text-yellow-800">
          <AlertCircle className="w-5 h-5" />
          Approval Required
        </CardTitle>
      </CardHeader>
      
      <CardContent className="pt-6">
        <div className="space-y-3">
          <div>
            <label className="text-sm font-semibold text-gray-700">Tool:</label>
            <div className="mt-1">
              <Badge variant="outline" className="font-mono">{data.tool_name}</Badge>
            </div>
          </div>

          <div>
            <label className="text-sm font-semibold text-gray-700">Arguments:</label>
            <pre className="mt-1 p-3 bg-gray-50 rounded border text-xs overflow-auto">
              {JSON.stringify(data.tool_args, null, 2)}
            </pre>
          </div>

          {data.reason && (
            <div>
              <label className="text-sm font-semibold text-gray-700">Reason:</label>
              <p className="mt-1 text-sm text-gray-600">{data.reason}</p>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="flex gap-3 justify-end">
        <Button
          variant="outline"
          onClick={onReject}
          disabled={isProcessing}
          className="flex items-center gap-2"
          data-testid="reject-button"
        >
          <XCircle className="w-4 h-4" />
          Reject
        </Button>
        <Button
          onClick={onApprove}
          disabled={isProcessing}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
          data-testid="approve-button"
        >
          <CheckCircle className="w-4 h-4" />
          {isProcessing ? 'Processing...' : 'Approve & Execute'}
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ApprovalCard;
