import React, { useState } from 'react';
import { FileCode2, FolderOpen, File, ChevronRight, Copy, Check } from 'lucide-react';

function getFileIcon(filename) {
  const ext = filename.split('.').pop()?.toLowerCase();
  const iconMap = {
    py: '🐍', js: '📜', ts: '📘', jsx: '⚛️', tsx: '⚛️',
    json: '📋', md: '📝', txt: '📄', sh: '⚙️', yml: '⚙️',
    yaml: '⚙️', html: '🌐', css: '🎨', sql: '🗄️', env: '🔐',
    toml: '⚙️', cfg: '⚙️', ini: '⚙️', dockerfile: '🐳',
  };
  if (filename.toLowerCase() === 'dockerfile') return '🐳';
  return iconMap[ext] || '📄';
}

function getLanguage(filename) {
  const ext = filename.split('.').pop()?.toLowerCase();
  const langMap = {
    py: 'python', js: 'javascript', ts: 'typescript',
    jsx: 'jsx', tsx: 'tsx', json: 'json', md: 'markdown',
    sh: 'bash', yml: 'yaml', yaml: 'yaml', html: 'html',
    css: 'css', sql: 'sql', toml: 'toml',
  };
  return langMap[ext] || 'text';
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 px-2 py-1 rounded text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-colors"
    >
      {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

function FileTree({ files, selectedFile, onSelect }) {
  // Group files by directory
  const tree = {};
  files.forEach(f => {
    const parts = f.path.split('/');
    if (parts.length === 1) {
      if (!tree['']) tree[''] = [];
      tree[''].push(f);
    } else {
      const dir = parts.slice(0, -1).join('/');
      if (!tree[dir]) tree[dir] = [];
      tree[dir].push(f);
    }
  });

  const dirs = Object.keys(tree).sort();

  return (
    <div className="space-y-0.5">
      {dirs.map(dir => (
        <div key={dir}>
          {dir && (
            <div className="flex items-center gap-1.5 px-2 py-1 text-xs text-slate-500">
              <FolderOpen className="w-3.5 h-3.5" />
              <span className="font-medium">{dir}/</span>
            </div>
          )}
          {tree[dir].map(file => {
            const filename = file.path.split('/').pop();
            const isSelected = selectedFile?.path === file.path;
            return (
              <button
                key={file.path}
                onClick={() => onSelect(file)}
                className={`w-full flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg transition-colors text-left ${
                  isSelected
                    ? 'bg-indigo-500/20 text-indigo-300'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                } ${dir ? 'pl-6' : ''}`}
              >
                <span className="text-sm">{getFileIcon(filename)}</span>
                <span className="truncate font-mono">{filename}</span>
                {file.size && (
                  <span className="ml-auto text-slate-600 flex-shrink-0">
                    {file.size > 1024 ? `${(file.size / 1024).toFixed(1)}k` : `${file.size}b`}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}

export function FileExplorer({ files, loading }) {
  const [selectedFile, setSelectedFile] = useState(null);

  React.useEffect(() => {
    if (files && files.length > 0 && !selectedFile) {
      setSelectedFile(files[0]);
    }
  }, [files]);

  if (loading) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
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
          <p className="text-xs text-slate-600 mt-1">Files will appear after the Builder stage completes</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 flex overflow-hidden" style={{ minHeight: '400px' }}>
      {/* File tree sidebar */}
      <div className="w-56 flex-shrink-0 border-r border-slate-800 overflow-y-auto">
        <div className="px-3 py-2.5 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Files</span>
            <span className="ml-auto text-xs text-slate-600">{files.length}</span>
          </div>
        </div>
        <div className="p-2">
          <FileTree files={files} selectedFile={selectedFile} onSelect={setSelectedFile} />
        </div>
      </div>

      {/* File content viewer */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedFile ? (
          <>
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800 flex-shrink-0">
              <div className="flex items-center gap-2">
                <span className="text-sm">{getFileIcon(selectedFile.path.split('/').pop())}</span>
                <span className="text-xs font-mono text-slate-300">{selectedFile.path}</span>
                <span className="text-xs text-slate-600 bg-slate-800 px-1.5 py-0.5 rounded">
                  {getLanguage(selectedFile.path.split('/').pop())}
                </span>
              </div>
              <CopyButton text={selectedFile.content || ''} />
            </div>
            <div className="flex-1 overflow-auto">
              <pre className="p-4 text-xs font-mono text-slate-300 leading-relaxed whitespace-pre-wrap break-words">
                {selectedFile.content || '(empty file)'}
              </pre>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm text-slate-600">Select a file to view</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default FileExplorer;
