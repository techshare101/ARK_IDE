import React, { useState } from 'react';
import { FileCode2, Folder, FolderOpen, ChevronRight, ChevronDown, File } from 'lucide-react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import css from 'react-syntax-highlighter/dist/esm/languages/hljs/css';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';

SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('css', css);
SyntaxHighlighter.registerLanguage('json', json);

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 10) / 10 + ' ' + sizes[i];
}

function getLanguage(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const map = {
    'js': 'javascript', 'jsx': 'javascript', 'ts': 'javascript', 'tsx': 'javascript',
    'py': 'python',
    'css': 'css', 'scss': 'css',
    'json': 'json',
    'html': 'xml',
  };
  return map[ext] || 'text';
}

function FileTree({ files, onFileClick, selectedFile }) {
  const [expanded, setExpanded] = useState({});

  const tree = React.useMemo(() => {
    const root = {};
    files.forEach(file => {
      const parts = file.file_path.split('/');
      let current = root;
      parts.forEach((part, idx) => {
        if (!current[part]) {
          current[part] = idx === parts.length - 1 ? file : {};
        }
        current = current[part];
      });
    });
    return root;
  }, [files]);

  const renderNode = (node, path = '', level = 0) => {
    return Object.keys(node).map(key => {
      const fullPath = path ? `${path}/${key}` : key;
      const isFile = node[key].file_path !== undefined;
      const isExpanded = expanded[fullPath];

      if (isFile) {
        const file = node[key];
        const isSelected = selectedFile?.file_path === file.file_path;
        return (
          <div
            key={fullPath}
            onClick={() => onFileClick(file)}
            className={`flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-slate-800/50 transition-colors ${
              isSelected ? 'bg-blue-500/10 border-l-2 border-blue-500' : ''
            }`}
            style={{ paddingLeft: `${level * 16 + 12}px` }}
          >
            <File className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            <span className={`text-xs flex-1 truncate ${
              isSelected ? 'text-blue-400 font-medium' : 'text-slate-300'
            }`}>
              {key}
            </span>
            {file.output && (
              <span className="text-xs text-slate-600 flex-shrink-0">
                {formatBytes(file.output.match(/\((\d+) chars\)/)?.[1] || 0)}
              </span>
            )}
          </div>
        );
      }

      return (
        <div key={fullPath}>
          <div
            onClick={() => setExpanded(prev => ({ ...prev, [fullPath]: !prev[fullPath] }))}
            className="flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-slate-800/50 transition-colors"
            style={{ paddingLeft: `${level * 16 + 12}px` }}
          >
            {isExpanded ? (
              <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
            )}
            {isExpanded ? (
              <FolderOpen className="w-3.5 h-3.5 text-blue-400" />
            ) : (
              <Folder className="w-3.5 h-3.5 text-slate-500" />
            )}
            <span className="text-xs text-slate-300 font-medium">{key}</span>
          </div>
          {isExpanded && renderNode(node[key], fullPath, level + 1)}
        </div>
      );
    });
  };

  return (
    <div className="border-r border-slate-800 bg-slate-900/50 overflow-y-auto">
      {renderNode(tree)}
    </div>
  );
}

export function FileExplorer({ files, loading }) {
  const [selectedFile, setSelectedFile] = useState(null);

  // Auto-select first file
  React.useEffect(() => {
    if (files && files.length > 0 && !selectedFile) {
      setSelectedFile(files[0]);
    }
  }, [files, selectedFile]);

  if (loading) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400">Loading files...</p>
        </div>
      </div>
    );
  }

  if (!files || files.length === 0) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 flex items-center justify-center">
        <div className="text-center">
          <FileCode2 className="w-10 h-10 text-slate-700 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No files generated yet</p>
          <p className="text-xs text-slate-600 mt-1">Files will appear here after the Builder stage completes</p>
        </div>
      </div>
    );
  }

  // Extract content from file output
  const getFileContent = (file) => {
    // If it's a created file from task_tree
    if (file.output && file.output.includes('Written:')) {
      return '// File content not available in preview\n// File was written to sandbox';
    }
    return file.content || '// No content available';
  };

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
      <div className="grid grid-cols-3 h-[600px]">
        {/* File Tree */}
        <div className="col-span-1">
          <div className="px-3 py-2 border-b border-slate-800 bg-slate-800/50">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Files ({files.length})</h4>
          </div>
          <FileTree files={files} onFileClick={setSelectedFile} selectedFile={selectedFile} />
        </div>

        {/* File Content */}
        <div className="col-span-2 flex flex-col">
          {selectedFile ? (
            <>
              <div className="px-4 py-2 border-b border-slate-800 bg-slate-800/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileCode2 className="w-3.5 h-3.5 text-blue-400" />
                  <span className="text-xs font-medium text-slate-300">{selectedFile.file_path}</span>
                </div>
                {selectedFile.output && (
                  <span className="text-xs text-slate-500">
                    {formatBytes(selectedFile.output.match(/\((\d+) chars\)/)?.[1] || 0)}
                  </span>
                )}
              </div>
              <div className="flex-1 overflow-auto">
                <SyntaxHighlighter
                  language={getLanguage(selectedFile.file_path)}
                  style={atomOneDark}
                  customStyle={{
                    margin: 0,
                    padding: '1rem',
                    fontSize: '0.75rem',
                    lineHeight: '1.5',
                    background: 'transparent',
                  }}
                  showLineNumbers
                >
                  {getFileContent(selectedFile)}
                </SyntaxHighlighter>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-sm text-slate-500">Select a file to view its contents</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default FileExplorer;
