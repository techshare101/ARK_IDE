import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { FileCode, Plus, Minus } from 'lucide-react';

const DiffViewer = ({ diffs, filename = 'file' }) => {
  if (!diffs || diffs.length === 0) {
    return (
      <Card className="w-full">
        <CardContent className="p-6 text-center text-gray-400">
          <FileCode className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No file changes yet...</p>
        </CardContent>
      </Card>
    );
  }

  // Calculate stats
  const additions = diffs.filter(d => d.type === 'added').length;
  const deletions = diffs.filter(d => d.type === 'removed').length;

  return (
    <Card className="w-full" data-testid="diff-viewer">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FileCode className="w-5 h-5" />
            {filename}
          </CardTitle>
          <div className="flex gap-2">
            <Badge variant="outline" className="text-green-600">
              <Plus className="w-3 h-3 mr-1" />
              +{additions}
            </Badge>
            <Badge variant="outline" className="text-red-600">
              <Minus className="w-3 h-3 mr-1" />
              -{deletions}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]">
          <div className="font-mono text-sm">
            {diffs.map((diff, index) => (
              <div
                key={index}
                className={`flex items-start gap-2 px-2 py-1 ${
                  diff.type === 'added'
                    ? 'bg-green-50 border-l-2 border-green-500'
                    : diff.type === 'removed'
                    ? 'bg-red-50 border-l-2 border-red-500'
                    : 'bg-gray-50'
                }`}
                data-testid={`diff-line-${diff.type}`}
              >
                <span className="text-gray-400 select-none w-8 text-right">
                  {index + 1}
                </span>
                <span
                  className={`flex-1 ${
                    diff.type === 'added'
                      ? 'text-green-700'
                      : diff.type === 'removed'
                      ? 'text-red-700'
                      : 'text-gray-700'
                  }`}
                >
                  {diff.type === 'added' && '+ '}
                  {diff.type === 'removed' && '- '}
                  {diff.type === 'unchanged' && '  '}
                  {diff.content}
                </span>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default DiffViewer;
