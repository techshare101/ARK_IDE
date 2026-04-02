import React from 'react';
import { FolderOpen, Play, Trash2, Clock, CheckCircle2, XCircle, Loader2, ChevronRight, Plus } from 'lucide-react';

const STATUS_CONFIG = {
  idle:      { icon: Clock,         color: 'text-slate-400',  bg: 'bg-slate-700/50',     border: 'border-slate-700',   label: 'Idle'      },
  running:   { icon: Loader2,       color: 'text-indigo-400', bg: 'bg-indigo-500/10',    border: 'border-indigo-500/30', label: 'Running'  },
  completed: { icon: CheckCircle2,  color: 'text-green-400',  bg: 'bg-green-500/10',     border: 'border-green-500/30',  label: 'Complete' },
  failed:    { icon: XCircle,       color: 'text-red-400',    bg: 'bg-red-500/10',       border: 'border-red-500/30',    label: 'Failed'   },
};

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins  < 1)  return 'just now';
  if (mins  < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

function ProjectCard({ project, onSelect, onRun, onDelete, isActive }) {
  const cfg = STATUS_CONFIG[project.status] || STATUS_CONFIG.idle;
  const StatusIcon = cfg.icon;
  const isRunning = project.status === 'running';

  return (
    <div
      className={`group relative rounded-xl border transition-all duration-200 cursor-pointer ${
        isActive
          ? 'border-indigo-500/50 bg-indigo-500/5 shadow-lg shadow-indigo-500/10'
          : `${cfg.border} bg-slate-900 hover:border-slate-600 hover:bg-slate-800/50`
      }`}
      onClick={() => onSelect(project)}
    >
      <div className="p-4">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2 min-w-0">
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${cfg.bg}`}>
              <StatusIcon className={`w-3.5 h-3.5 ${cfg.color} ${isRunning ? 'animate-spin' : ''}`} />
            </div>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color}`}>
              {cfg.label}
            </span>
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
            {!isRunning && (
              <button
                onClick={(e) => { e.stopPropagation(); onRun(project.id); }}
                className="p-1.5 rounded-lg text-slate-500 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                title="Run pipeline"
              >
                <Play className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(project.id); }}
              className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Delete project"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Goal text */}
        <p className="text-sm text-slate-200 leading-relaxed line-clamp-2 mb-3">
          {project.goal}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-mono text-slate-600">
              {project.id?.slice(0, 8)}...
            </span>
          </div>
          <div className="flex items-center gap-1 text-[10px] text-slate-600">
            <Clock className="w-3 h-3" />
            <span>{timeAgo(project.created_at || project.updated_at)}</span>
          </div>
        </div>

        {/* Active indicator */}
        {isActive && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <ChevronRight className="w-4 h-4 text-indigo-400" />
          </div>
        )}
      </div>

      {/* Running progress bar */}
      {isRunning && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-800 rounded-b-xl overflow-hidden">
          <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 animate-pulse" style={{ width: '60%' }} />
        </div>
      )}
    </div>
  );
}

export function ProjectList({ projects, activeProjectId, onSelect, onRun, onDelete, onNew, loading }) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-28 rounded-xl bg-slate-800/50 border border-slate-800 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FolderOpen className="w-4 h-4 text-slate-400" />
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Projects</h3>
          {projects.length > 0 && (
            <span className="text-xs text-slate-600">({projects.length})</span>
          )}
        </div>
        <button
          onClick={onNew}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 border border-indigo-500/20 hover:border-indigo-500/40 transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          New
        </button>
      </div>

      {/* Project list */}
      {projects.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center py-12 text-center">
          <FolderOpen className="w-10 h-10 text-slate-700 mb-3" />
          <p className="text-sm text-slate-500">No projects yet</p>
          <p className="text-xs text-slate-600 mt-1">Create your first project above</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {projects.map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              isActive={project.id === activeProjectId}
              onSelect={onSelect}
              onRun={onRun}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default ProjectList;
