import React, { useState, useEffect, useCallback, useRef } from 'react';
import { GoalInput }    from './components/ark/GoalInput';
import { PipelineView } from './components/ark/PipelineView';
import { EventLog }     from './components/ark/EventLog';
import { FileExplorer } from './components/ark/FileExplorer';
import { TestResults }  from './components/ark/TestResults';
import { DeployPanel }  from './components/ark/DeployPanel';
import { ProjectList }  from './components/ark/ProjectList';
import { useSSE }       from './hooks/useSSE';
import { arkAPI }       from './api/ark';
import { LayoutDashboard, Terminal, FileCode2, FlaskConical, Rocket, X, Menu } from 'lucide-react';

const TABS = [
  { id: 'pipeline', label: 'Pipeline', icon: LayoutDashboard },
  { id: 'events',   label: 'Events',   icon: Terminal        },
  { id: 'files',    label: 'Files',    icon: FileCode2       },
  { id: 'tests',    label: 'Tests',    icon: FlaskConical    },
  { id: 'deploy',   label: 'Deploy',   icon: Rocket          },
];

const POLL_INTERVAL = 4000;

function Toast({ message, type = 'info', onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 4500);
    return () => clearTimeout(t);
  }, [onClose]);
  const styles = {
    info:    'bg-slate-800 border-slate-700 text-slate-200',
    success: 'bg-green-900/80 border-green-700 text-green-200',
    error:   'bg-red-900/80 border-red-700 text-red-200',
    warning: 'bg-yellow-900/80 border-yellow-700 text-yellow-200',
  };
  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border shadow-xl text-sm ${styles[type]}`}>
      <span className="flex-1">{message}</span>
      <button onClick={onClose} className="opacity-60 hover:opacity-100 transition-opacity">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

function useToast() {
  const [toasts, setToasts] = useState([]);
  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
  }, []);
  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);
  return { toasts, addToast, removeToast };
}
export default function App() {
  const [projects,        setProjects]        = useState([]);
  const [activeProject,   setActiveProject]   = useState(null);
  const [activeTab,       setActiveTab]       = useState('pipeline');
  const [view,            setView]            = useState('list');
  const [creating,        setCreating]        = useState(false);
  const [files,           setFiles]           = useState([]);
  const [tests,           setTests]           = useState([]);
  const [deploy,          setDeploy]          = useState(null);
  const [loadingFiles,    setLoadingFiles]    = useState(false);
  const [loadingTests,    setLoadingTests]    = useState(false);
  const [loadingDeploy,   setLoadingDeploy]   = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [sidebarOpen,     setSidebarOpen]     = useState(true);
  const [backendOk,       setBackendOk]       = useState(null);
  const pollRef = useRef(null);
  const { toasts, addToast, removeToast } = useToast();

  const streamUrl = activeProject?.id && activeProject?.status === 'running'
    ? arkAPI.getStreamUrl(activeProject.id) : null;
  const { events, connected, error: sseError, clearEvents } = useSSE(streamUrl, !!streamUrl);

  useEffect(() => {
    arkAPI.health().then(() => setBackendOk(true)).catch(() => setBackendOk(false));
  }, []);

  useEffect(() => { loadProjects(); }, []);

  const loadProjects = async () => {
    setLoadingProjects(true);
    try {
      const data = await arkAPI.listProjects();
      setProjects(Array.isArray(data) ? data : (data.projects || []));
    } catch (err) {
      addToast('Failed to load projects: ' + err.message, 'error');
    } finally {
      setLoadingProjects(false);
    }
  };

  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    if (!activeProject?.id || activeProject?.status !== 'running') return;
    pollRef.current = setInterval(async () => {
      try {
        const updated = await arkAPI.getProject(activeProject.id);
        setActiveProject(updated);
        setProjects(prev => prev.map(p => p.id === updated.id ? updated : p));
        if (updated.status !== 'running') {
          clearInterval(pollRef.current);
          if (updated.status === 'completed') {
            addToast('Pipeline completed successfully!', 'success');
          } else if (updated.status === 'failed') {
            addToast('Pipeline failed. Check the event log.', 'error');
          }
        }
      } catch (e) { console.warn('Poll error:', e); }
    }, POLL_INTERVAL);
    return () => clearInterval(pollRef.current);
  }, [activeProject?.id, activeProject?.status]);

  const loadTabData = async (tab, projectId) => {
    const id = projectId || activeProject?.id;
    if (!id) return;
    try {
      if (tab === 'files') {
        setLoadingFiles(true);
        const data = await arkAPI.getFiles(id);
        setFiles(Array.isArray(data) ? data : (data.files || []));
        setLoadingFiles(false);
      } else if (tab === 'tests') {
        setLoadingTests(true);
        const data = await arkAPI.getTests(id);
        setTests(Array.isArray(data) ? data : (data.tests || []));
        setLoadingTests(false);
      } else if (tab === 'deploy') {
        setLoadingDeploy(true);
        const data = await arkAPI.getDeploy(id);
        setDeploy(data);
        setLoadingDeploy(false);
      }
    } catch (err) {
      if (tab === 'files')  setLoadingFiles(false);
      if (tab === 'tests')  setLoadingTests(false);
      if (tab === 'deploy') setLoadingDeploy(false);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (activeProject?.id) loadTabData(tab);
  };
  const handleCreateProject = async (goal) => {
    setCreating(true);
    try {
      const project = await arkAPI.createProject(goal);
      setProjects(prev => [project, ...prev]);
      setActiveProject(project);
      setView('project');
      setActiveTab('pipeline');
      clearEvents();
      setFiles([]); setTests([]); setDeploy(null);
      addToast('Project created! Starting pipeline...', 'success');
      try {
        await arkAPI.runPipeline(project.id);
        const running = { ...project, status: 'running' };
        setActiveProject(running);
        setProjects(prev => prev.map(p => p.id === running.id ? running : p));
      } catch (runErr) {
        addToast('Pipeline start failed: ' + runErr.message, 'warning');
      }
    } catch (err) {
      addToast('Failed to create project: ' + err.message, 'error');
    } finally {
      setCreating(false);
    }
  };

  const handleSelectProject = async (project) => {
    setActiveProject(project);
    setView('project');
    setActiveTab('pipeline');
    clearEvents();
    setFiles([]); setTests([]); setDeploy(null);
    try {
      const detail = await arkAPI.getProject(project.id);
      setActiveProject(detail);
    } catch {}
  };

  const handleRunPipeline = async (projectId) => {
    try {
      await arkAPI.runPipeline(projectId);
      const running = projects.find(p => p.id === projectId);
      if (running) {
        const updated = { ...running, status: 'running' };
        setProjects(prev => prev.map(p => p.id === projectId ? updated : p));
        if (activeProject?.id === projectId) {
          setActiveProject(updated);
          clearEvents();
        }
      }
      addToast('Pipeline started!', 'info');
    } catch (err) {
      addToast('Failed to run pipeline: ' + err.message, 'error');
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Delete this project? This cannot be undone.')) return;
    try {
      await arkAPI.deleteProject(projectId);
      setProjects(prev => prev.filter(p => p.id !== projectId));
      if (activeProject?.id === projectId) {
        setActiveProject(null);
        setView('list');
      }
      addToast('Project deleted.', 'info');
    } catch (err) {
      addToast('Failed to delete project: ' + err.message, 'error');
    }
  };

  const handleNewProject = () => {
    setView('new');
    setActiveProject(null);
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">

      {/* ── Sidebar ── */}
      <div className={`flex-shrink-0 flex flex-col border-r border-slate-800 bg-slate-900 transition-all duration-300 ${sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'}`}>
        {/* Logo */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-500/20 flex items-center justify-center">
              <span className="text-indigo-400 text-xs font-bold">A</span>
            </div>
            <span className="text-sm font-semibold text-slate-200">ARK IDE</span>
            <span className="text-xs text-indigo-400 font-mono">v3.0</span>
          </div>
          <div className="flex items-center gap-2">
            {backendOk === true  && <div className="w-2 h-2 rounded-full bg-green-400" title="Backend connected" />}
            {backendOk === false && <div className="w-2 h-2 rounded-full bg-red-400"   title="Backend offline"  />}
            {backendOk === null  && <div className="w-2 h-2 rounded-full bg-slate-600" title="Checking..."      />}
          </div>
        </div>

        {/* New project CTA */}
        <div className="px-3 py-3 border-b border-slate-800 flex-shrink-0">
          <button onClick={handleNewProject}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors active:scale-95">
            + New Project
          </button>
        </div>

        {/* Project list */}
        <div className="flex-1 overflow-hidden p-3">
          <ProjectList
            projects={projects}
            activeProjectId={activeProject?.id}
            onSelect={handleSelectProject}
            onRun={handleRunPipeline}
            onDelete={handleDeleteProject}
            onNew={handleNewProject}
            loading={loadingProjects}
          />
        </div>
      </div>

      {/* ── Main content ── */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Top bar */}
        <div className="flex items-center gap-3 px-4 py-2.5 border-b border-slate-800 bg-slate-900 flex-shrink-0">
          <button onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors">
            <Menu className="w-4 h-4" />
          </button>
          <div className="flex-1 min-w-0">
            {activeProject ? (
              <p className="text-sm text-slate-300 truncate">{activeProject.goal}</p>
            ) : (
              <p className="text-sm text-slate-500">Select or create a project</p>
            )}
          </div>
          {activeProject && (
            <div className="flex items-center gap-2">
              {connected && <span className="flex items-center gap-1.5 text-xs text-green-400"><span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />Live</span>}
              {sseError  && <span className="text-xs text-yellow-400">{sseError}</span>}
            </div>
          )}
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {(view === 'list' || view === 'new') && (
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="w-full max-w-2xl">
                <div className="text-center mb-8">
                  <h1 className="text-3xl font-bold text-slate-100 mb-2">ARK IDE <span className="text-indigo-400">v3.0</span></h1>
                  <p className="text-slate-400">Autonomous software development — describe what you want to build</p>
                </div>
                <GoalInput onSubmit={handleCreateProject} loading={creating} />
              </div>
            </div>
          )}

          {view === 'project' && activeProject && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Tabs */}
              <div className="flex items-center gap-1 px-4 py-2 border-b border-slate-800 bg-slate-900 flex-shrink-0">
                {TABS.map(tab => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button key={tab.id} onClick={() => handleTabChange(tab.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        isActive ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
                      }`}>
                      <Icon className="w-3.5 h-3.5" />
                      {tab.label}
                      {tab.id === 'events' && events.length > 0 && (
                        <span className="ml-1 px-1.5 py-0.5 rounded-full bg-indigo-500/30 text-indigo-300 text-[10px]">{events.length}</span>
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Tab content */}
              <div className="flex-1 overflow-auto p-4">
                {activeTab === 'pipeline' && (
                  <PipelineView project={activeProject} events={events} />
                )}
                {activeTab === 'events' && (
                  <EventLog events={events} connected={connected} onClear={clearEvents} />
                )}
                {activeTab === 'files' && (
                  <FileExplorer files={files} loading={loadingFiles} />
                )}
                {activeTab === 'tests' && (
                  <TestResults tests={tests} loading={loadingTests} />
                )}
                {activeTab === 'deploy' && (
                  <DeployPanel deploy={deploy} loading={loadingDeploy} />
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Toast notifications ── */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80">
        {toasts.map(toast => (
          <Toast key={toast.id} message={toast.message} type={toast.type} onClose={() => removeToast(toast.id)} />
        ))}
      </div>
    </div>
  );
}
