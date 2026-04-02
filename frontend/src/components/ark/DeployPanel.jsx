import React from 'react';
import { Rocket, ExternalLink, Package, Server, Globe, Copy, Check, AlertCircle } from 'lucide-react';

function InfoRow({ label, value, mono = false, copyable = false }) {
  const [copied, setCopied] = React.useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };
  return (
    <div className="flex items-start justify-between gap-4 py-2.5 border-b border-slate-800 last:border-0">
      <span className="text-xs text-slate-500 flex-shrink-0 w-28">{label}</span>
      <div className="flex items-center gap-2 flex-1 justify-end">
        <span className={`text-xs text-slate-300 text-right break-all ${mono ? 'font-mono' : ''}`}>{value}</span>
        {copyable && (
          <button onClick={handleCopy} className="flex-shrink-0 p-1 rounded text-slate-600 hover:text-slate-300 hover:bg-slate-700 transition-colors">
            {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
          </button>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    success:    'bg-green-500/20 text-green-300 border-green-500/30',
    running:    'bg-blue-500/20 text-blue-300 border-blue-500/30',
    failed:     'bg-red-500/20 text-red-300 border-red-500/30',
    pending:    'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    deployed:   'bg-green-500/20 text-green-300 border-green-500/30',
    building:   'bg-blue-500/20 text-blue-300 border-blue-500/30',
  };
  const style = styles[status?.toLowerCase()] || 'bg-slate-700 text-slate-400 border-slate-600';
  return (
    <span className={`text-xs px-2.5 py-0.5 rounded-full border font-medium capitalize ${style}`}>
      {status || 'unknown'}
    </span>
  );
}

export function DeployPanel({ deploy, loading }) {
  if (loading) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400">Loading deployment info...</p>
        </div>
      </div>
    );
  }

  if (!deploy) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 flex items-center justify-center">
        <div className="text-center">
          <Rocket className="w-10 h-10 text-slate-700 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No deployment yet</p>
          <p className="text-xs text-slate-600 mt-1">Deployment info will appear after the Deployer stage completes</p>
        </div>
      </div>
    );
  }

  const hasUrl = deploy.url || deploy.preview_url || deploy.deployment_url;

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Rocket className="w-4 h-4 text-green-400" />
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Deployment</h3>
          </div>
          <StatusBadge status={deploy.status} />
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Live preview iframe */}
        {hasUrl && (
          <div className="rounded-xl border border-green-500/20 bg-slate-800/50 overflow-hidden">
            <div className="px-3 py-2 border-b border-slate-800 bg-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Globe className="w-3.5 h-3.5 text-green-400" />
                <span className="text-xs font-semibold text-green-400 uppercase tracking-wider">Live Preview</span>
              </div>
              <a
                href={hasUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-2 py-1 text-xs text-green-400 hover:text-green-300 hover:bg-green-500/10 rounded transition-colors"
              >
                <ExternalLink className="w-3 h-3" />
                Open
              </a>
            </div>
            <div className="relative" style={{ height: '500px' }}>
              <iframe
                src={hasUrl}
                className="w-full h-full"
                title="Live Preview"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
              />
            </div>
          </div>
        )}

        {/* Live URL card */}
        {hasUrl && (
          <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Globe className="w-4 h-4 text-green-400" />
              <span className="text-xs font-semibold text-green-400 uppercase tracking-wider">Direct URL</span>
            </div>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-sm text-green-300 font-mono bg-green-500/10 px-3 py-2 rounded truncate">
                {hasUrl}
              </code>
              <button
                onClick={async () => {
                  await navigator.clipboard.writeText(hasUrl);
                }}
                className="flex-shrink-0 p-2 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors"
                title="Copy URL"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Deployment details */}
        <div className="rounded-xl border border-slate-800 bg-slate-800/30 p-3">
          <div className="flex items-center gap-2 mb-2">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Details</span>
          </div>
          {deploy.platform    && <InfoRow label="Platform"    value={deploy.platform}    />}
          {deploy.environment && <InfoRow label="Environment" value={deploy.environment} />}
          {deploy.region      && <InfoRow label="Region"      value={deploy.region}      />}
          {deploy.runtime     && <InfoRow label="Runtime"     value={deploy.runtime}     />}
          {deploy.build_id    && <InfoRow label="Build ID"    value={deploy.build_id}    mono copyable />}
          {deploy.deployed_at && (
            <InfoRow
              label="Deployed At"
              value={new Date(deploy.deployed_at).toLocaleString()}
            />
          )}
          {deploy.duration_ms && (
            <InfoRow
              label="Build Time"
              value={`${(deploy.duration_ms / 1000).toFixed(1)}s`}
            />
          )}
        </div>

        {/* Package info */}
        {(deploy.files_count || deploy.package_size) && (
          <div className="rounded-xl border border-slate-800 bg-slate-800/30 p-3">
            <div className="flex items-center gap-2 mb-2">
              <Package className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Package</span>
            </div>
            {deploy.files_count   && <InfoRow label="Files"        value={`${deploy.files_count} files`} />}
            {deploy.package_size  && <InfoRow label="Package Size" value={deploy.package_size} />}
            {deploy.entry_point   && <InfoRow label="Entry Point"  value={deploy.entry_point} mono />}
          </div>
        )}

        {/* Error display */}
        {deploy.error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-3.5 h-3.5 text-red-400" />
              <span className="text-xs font-semibold text-red-400 uppercase tracking-wider">Error</span>
            </div>
            <pre className="text-xs text-red-300 font-mono whitespace-pre-wrap break-words">
              {deploy.error}
            </pre>
          </div>
        )}

        {/* Logs */}
        {deploy.logs && deploy.logs.length > 0 && (
          <div className="rounded-xl border border-slate-800 bg-slate-800/30 p-3">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Build Logs</p>
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {deploy.logs.map((log, i) => (
                <p key={i} className="text-xs font-mono text-slate-400 leading-relaxed">
                  <span className="text-slate-600 mr-2">{String(i + 1).padStart(3, '0')}</span>
                  {log}
                </p>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DeployPanel;
