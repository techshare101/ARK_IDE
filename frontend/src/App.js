import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { Header }       from './components/ark/Header';
import { Footer }       from './components/ark/Footer';
import { HeroSection }  from './components/ark/HeroSection';
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

  // Health check with retry logic to prevent false "Cannot connect" errors on startup
  useEffect(() => {
    const checkHealthWithRetry = async (attempt = 1, maxAttempts = 3) => {
      try {
        await arkAPI.health();
        setBackendOk(true);
      } catch (err) {
        if (attempt < maxAttempts) {
          const delay = attempt * 1000; // Exponential backoff: 1s, 2s
          console.log(`Health check failed (attempt ${attempt}/${maxAttempts}), retrying in ${delay}ms...`);
          setTimeout(() => checkHealthWithRetry(attempt + 1, maxAttempts), delay);
        } else {
          console.error('Health check failed after', maxAttempts, 'attempts');
          setBackendOk(false);
        }
      }
    };
    checkHealthWithRetry();
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
      const projectId = project.project_id || project.id;
      const projectObj = { ...project, id: projectId };
      setProjects(prev => [projectObj, ...prev]);
      setActiveProject(projectObj);
      setView('project');
      setActiveTab('pipeline');
      clearEvents();
      setFiles([]); setTests([]); setDeploy(null);
      addToast('Project created! Pipeline starting...', 'success');
      // Pipeline auto-starts in background, no need to call /run
      const running = { ...projectObj, status: 'running' };
      setActiveProject(running);
      setProjects(prev => prev.map(p => p.id === running.id ? running : p));
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

  const handleStopPipeline = async () => {
    if (!activeProject?.id) return;
    if (!window.confirm('Stop the running pipeline? This will terminate all agents.')) return;
    
    try {
      // Call DELETE /projects/{id}/run
      await fetch(`${arkAPI.baseUrl}/projects/${activeProject.id}/run`, {
        method: 'DELETE',
      });
      
      const stopped = { ...activeProject, status: 'failed', error: 'Stopped by user' };
      setActiveProject(stopped);
      setProjects(prev => prev.map(p => p.id === stopped.id ? stopped : p));
      addToast('Pipeline stopped', 'warning');
    } catch (err) {
      addToast('Failed to stop pipeline: ' + err.message, 'error');
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
    <ThemeProvider>
      <div className="flex flex-col h-screen overflow-hidden" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
        
        {/* Premium Header */}
        <Header connected={backendOk === true} />

        <div className="flex flex-1 overflow-hidden">
          {/* ── Sidebar ── */}
          <div className={`flex-shrink-0 flex flex-col transition-all duration-300 ${sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'}`} style={{
            borderRight: '1px solid var(--border)',
            background: 'var(--bg-secondary)'
          }}>
            {/* Logo */}
            <div className="flex items-center justify-between px-4 py-3 flex-shrink-0" style={{ borderBottom: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'rgba(124, 58, 237, 0.2)' }}>
                  <span className="text-xs font-bold" style={{ color: 'var(--accent-purple)' }}>A</span>
                </div>
                <span className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>ARK IDE</span>
                <span className="text-xs font-mono" style={{ color: 'var(--accent-purple)' }}>v3.0</span>
              </div>
            </div>

            {/* New project CTA */}
            <div className="px-3 py-3 flex-shrink-0" style={{ borderBottom: '1px solid var(--border)' }}>
              <button onClick={handleNewProject}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-white text-sm font-medium transition-all active:scale-95 hover:opacity-90"
                style={{ background: 'linear-gradient(135deg, var(--accent-purple), var(--accent-blue))' }}>
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
            <div className="flex items-center gap-3 px-4 py-2.5 flex-shrink-0" style={{
              borderBottom: '1px solid var(--border)',
              background: 'var(--bg-secondary)'
            }}>
              <button onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-1.5 rounded-lg transition-colors"
                style={{
                  color: 'var(--text-muted)',
                  background: 'transparent'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = 'var(--text-secondary)';
                  e.currentTarget.style.background = 'var(--bg-tertiary)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'var(--text-muted)';
                  e.currentTarget.style.background = 'transparent';
                }}>
                <Menu className="w-4 h-4" />
              </button>
              <div className="flex-1 min-w-0">
                {activeProject ? (
                  <p className="text-sm truncate" style={{ color: 'var(--text-secondary)' }}>{activeProject.goal}</p>
                ) : (
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Select or create a project</p>
                )}
              </div>
              {activeProject && (
                <div className="flex items-center gap-2">
                  {connected && <span className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--accent-green)' }}><span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--accent-green)' }} />Live</span>}
                  {sseError  && <span className="text-xs" style={{ color: 'var(--accent-red)' }}>{sseError}</span>}
                </div>
              )}
            </div>

            {/* Content area */}
            <div className="flex-1 overflow-hidden flex flex-col">
              {(view === 'list' || view === 'new') && (
                <div className="flex-1 overflow-auto">
                  <HeroSection onStartBuild={handleCreateProject} />
                </div>
              )}

              {view === 'project' && activeProject && (
                <div className="flex-1 flex flex-col overflow-hidden">
                  {/* Tabs */}
                  <div className="flex items-center gap-1 px-4 py-2 flex-shrink-0" style={{
                    borderBottom: '1px solid var(--border)',
                    background: 'var(--bg-secondary)'
                  }}>
                    {TABS.map(tab => {
                      const Icon = tab.icon;
                      const isActive = activeTab === tab.id;
                      return (
                        <button key={tab.id} onClick={() => handleTabChange(tab.id)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                            isActive ? '' : ''
                          }`}
                          style={{
                            background: isActive ? 'rgba(124, 58, 237, 0.2)' : 'transparent',
                            color: isActive ? 'var(--accent-purple)' : 'var(--text-muted)',
                            border: isActive ? '1px solid rgba(124, 58, 237, 0.3)' : '1px solid transparent'
                          }}
                          onMouseEnter={(e) => {
                            if (!isActive) {
                              e.currentTarget.style.color = 'var(--text-secondary)';
                              e.currentTarget.style.background = 'var(--bg-tertiary)';
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (!isActive) {
                              e.currentTarget.style.color = 'var(--text-muted)';
                              e.currentTarget.style.background = 'transparent';
                            }
                          }}>
                          <Icon className="w-3.5 h-3.5" />
                          {tab.label}
                          {tab.id === 'events' && events.length > 0 && (
                            <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px]" style={{
                              background: 'rgba(124, 58, 237, 0.3)',
                              color: 'var(--accent-purple)'
                            }}>{events.length}</span>
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Tab content */}
                  <div className="flex-1 overflow-auto p-4">
                    {activeTab === 'pipeline' && (
                      <PipelineView 
                        project={activeProject} 
                        events={events} 
                        onStop={handleStopPipeline}
                      />
                    )}
                    {activeTab === 'events' && (
                      <EventLog events={events} connected={connected} onClear={clearEvents} />
                    )}
                    {activeTab === 'files' && (
                      <FileExplorer files={files} loading={loadingFiles} />
                    )}
                    {activeTab === 'tests' && (
                      <TestResults tests={tests} loading={loadingFiles} />
                    )}
                    {activeTab === 'deploy' && (
                      <DeployPanel deploy={deploy} loading={loadingDeploy} />
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Premium Footer */}
        <Footer />

        {/* ── Toast notifications ── */}
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80">
          {toasts.map(toast => (
            <Toast key={toast.id} message={toast.message} type={toast.type} onClose={() => removeToast(toast.id)} />
          ))}
        </div>
      </div>
    </ThemeProvider>
  );
}
