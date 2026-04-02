import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { ScrollArea } from '../ui/scroll-area';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { FileEdit, Eye } from 'lucide-react';
import { arkAPI } from '../../api/ark';
import DiffViewer from './DiffViewer';

const FileChangesPanel = ({ sessionId }) => {
  const [fileChanges, setFileChanges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showDiff, setShowDiff] = useState(false);

  useEffect(() => {
    if (sessionId) {
      loadFileChanges();
      
      // Poll for updates every 5 seconds
      const interval = setInterval(loadFileChanges, 5000);
      return () => clearInterval(interval);
    }
  }, [sessionId]);

  const loadFileChanges = async () => {
    if (!sessionId) return;
    
    try {
      const data = await arkAPI.getFileChanges(sessionId);
      setFileChanges(data.file_changes);
    } catch (error) {
      console.error('Error loading file changes:', error);
    }
  };

  const handleViewDiff = async (file) => {
    setSelectedFile(file);
    setShowDiff(true);
  };

  if (!sessionId) {
    return null;
  }

  return (
    <div className="space-y-4" data-testid="file-changes-panel">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileEdit className="w-5 h-5" />
            File Changes ({fileChanges.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {fileChanges.length === 0 ? (
            <p className="text-sm text-gray-400 italic">No files changed yet...</p>
          ) : (
            <ScrollArea className="h-[300px]">
              <div className="space-y-2">
                {fileChanges.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="font-mono text-sm font-semibold text-gray-800">
                        {file.path}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">
                          Step {file.step_number}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {file.bytes_written} bytes
                        </span>
                      </div>
                    </div>
                    {file.original_content && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewDiff(file)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        View Diff
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {showDiff && selectedFile && selectedFile.original_content && (
        <DiffViewer
          diffs={[]} // Would need to generate from original_content
          filename={selectedFile.path}
        />
      )}
    </div>
  );
};

export default FileChangesPanel;
