import React from 'react';
import { Brain, Code2, FlaskConical, Rocket, Activity, CheckCircle2, XCircle, Loader2, StopCircle } from 'lucide-react';

const STAGES = [
  { id: 'planner',  label: 'Planner',  icon: Brain,         desc: 'Analyzing requirements & creating execution plan', textClass: 'text-purple-400', bgClass: 'bg-purple-500/10', borderClass: 'border-purple-500/40', ringClass: 'ring-purple-500/30', lineClass: 'bg-purple-500/40', badgeBg: 'bg-purple-500/10', progress: 20 },
  { id: 'builder',  label: 'Builder',  icon: Code2,         desc: 'Writing production-ready code',                   textClass: 'text-blue-400',   bgClass: 'bg-blue-500/10',   borderClass: 'border-blue-500/40',   ringClass: 'ring-blue-500/30',   lineClass: 'bg-blue-500/40',   badgeBg: 'bg-blue-500/10',   progress: 40 },
  { id: 'tester',   label: 'Tester',   icon: FlaskConical,  desc: 'Running tests & validating functionality',         textClass: 'text-yellow-400', bgClass: 'bg-yellow-500/10', borderClass: 'border-yellow-500/40', ringClass: 'ring-yellow-500/30', lineClass: 'bg-yellow-500/40', badgeBg: 'bg-yellow-500/10', progress: 60 },
  { id: 'deployer', label: 'Deployer', icon: Rocket,        desc: 'Packaging & deploying the application',            textClass: 'text-green-400',  bgClass: 'bg-green-500/10',  borderClass: 'border-green-500/40',  ringClass: 'ring-green-500/30',  lineClass: 'bg-green-500/40',  badgeBg: 'bg-green-500/10',  progress: 80 },
  { id: 'monitor',  label: 'Monitor',  icon: Activity,      desc: 'Monitoring health & performance',                  textClass: 'text-slate-400',  bgClass: 'bg-slate-500/10',  borderClass: 'border-slate-500/40',  ringClass: 'ring-slate-500/30',  lineClass: 'bg-slate-500/40',  badgeBg: 'bg-slate-500/10',  progress: 100 },
];

function StageIcon({ stage, status }) {
  const Icon = stage.icon;
  if (status === 'running')   return <Loader2 className={`w-5 h-5 ${stage.textClass} animate-spin`} />;
  if (status === 'completed') return <CheckCircle2 className="w-5 h-5 text-green-400" />;
  if (status === 'failed')    return <XCircle className="w-5 h-5 text-red-400" />;
  return <Icon className={`w-5 h-5 ${status === 'pending' ? 'text-slate-600' : stage.textClass}`} />;
}

function StageCard({ stage, status, message, isLast }) {
  const isActive  = status === 'running';
  const isDone    = status === 'completed';
  const isFailed  = status === 'failed';
  const isPending = !status || status === 'pending';

  let iconWrap = `${stage.bgClass} ${stage.borderClass}`;
  if (isDone)   iconWrap = 'bg-green-500/10 border-green-500/40';
  if (isFailed) iconWrap = 'bg-red-500/10 border-red-500/40';
  if (isPending) iconWrap = 'bg-slate-800 border-slate-700';

  let labelColor = stage.textClass;
  if (isDone)    labelColor = 'text-green-400';
  if (isFailed)  labelColor = 'text-red-400';
  if (isPending) labelColor = 'text-slate-500';

  return (
    <div className="flex items-start gap-3">
      <div className="flex flex-col items-center">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center border-2 transition-all duration-300 ${iconWrap} ${ isActive ? `ring-2 ${stage.ringClass} pipeline-stage-active` : '' }`}>
          <StageIcon stage={stage} status={status} />
        </div>
        {!isLast && (
          <div className={`w-0.5 h-8 mt-1 transition-all duration-500 ${isDone ? stage.lineClass : 'bg-slate-800'}`} />
        )}
      </div>
      <div className="flex-1 pb-5">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`font-semibold text-sm ${labelColor}`}>{stage.label}</span>
          {isActive  && <span className={`text-xs px-2 py-0.5 rounded-full ${stage.badgeBg} ${stage.textClass} font-medium`}>Running</span>}
          {isDone    && <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 font-medium">Done</span>}
          {isFailed  && <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 font-medium">Failed</span>}
        </div>
        <p className={`text-xs leading-relaxed ${isPending ? 'text-slate-600' : 'text-slate-400'}`}>
          {message || stage.desc}
        </p>
      </div>
    </div>
  );
}

export function PipelineView({ project, events, onStop }) {
  const { statuses, messages, currentStage } = React.useMemo(() => {
    const statuses = {};
    const messages = {};
    let currentStage = null;
    
    // If no events, infer stage status from project.stage
    if (!events || events.length === 0) {
      const projectStage = project?.stage || 'idle';
      if (projectStage === 'complete') {
        // Mark all stages as completed
        STAGES.forEach(s => { statuses[s.id] = 'completed'; });
      } else if (projectStage === 'failed') {
        // Find which stage failed (assume last one)
        const failedIdx = STAGES.findIndex(s => s.id === 'monitor');
        STAGES.forEach((s, idx) => {
          statuses[s.id] = idx < failedIdx ? 'completed' : (idx === failedIdx ? 'failed' : 'pending');
        });
      } else if (projectStage !== 'idle') {
        // Find current running stage
        const stageMap = { planning: 'planner', building: 'builder', testing: 'tester', deploying: 'deployer', monitoring: 'monitor' };
        const currentId = stageMap[projectStage];
        const currentIdx = STAGES.findIndex(s => s.id === currentId);
        STAGES.forEach((s, idx) => {
          statuses[s.id] = idx < currentIdx ? 'completed' : (idx === currentIdx ? 'running' : 'pending');
        });
        currentStage = STAGES[currentIdx];
      }
      return { statuses, messages, currentStage };
    }
    
    events.forEach(event => {
      const agent = (event.agent || '').toLowerCase();
      const type  = event.event_type;
      const stage = STAGES.find(s => agent.includes(s.id));
      if (!stage) return;
      
      if (type === 'stage_start')    { statuses[stage.id] = 'running';   messages[stage.id] = event.message || null; currentStage = stage; }
      if (type === 'stage_complete') { statuses[stage.id] = 'completed'; messages[stage.id] = event.message || null; }
      if (type === 'error')          { statuses[stage.id] = 'failed';    messages[stage.id] = event.message || null; }
    });
    
    return { statuses, messages, currentStage };
  }, [events, project]);

  const completedCount = STAGES.filter(s => statuses[s.id] === 'completed').length;
  const runningStage = STAGES.find(s => statuses[s.id] === 'running');
  const progressPercent = runningStage ? runningStage.progress : (completedCount === 5 ? 100 : completedCount * 20);
  
  const overallStatus  = project?.stage || project?.status || 'idle';
  const isRunning = overallStatus === 'planning' || overallStatus === 'building' || overallStatus === 'testing' || overallStatus === 'deploying' || overallStatus === 'monitoring';

  const statusColors = {
    idle:       'bg-slate-700 text-slate-300',
    planning:   'bg-purple-500/20 text-purple-300',
    building:   'bg-blue-500/20 text-blue-300',
    testing:    'bg-yellow-500/20 text-yellow-300',
    deploying:  'bg-green-500/20 text-green-300',
    monitoring: 'bg-slate-500/20 text-slate-300',
    complete:   'bg-green-500/20 text-green-300',
    failed:     'bg-red-500/20 text-red-300',
  };

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
      {/* Header with Stop Button */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pipeline</h3>
          {isRunning && (
            <button
              onClick={onStop}
              className="flex items-center gap-1.5 px-3 py-1 text-xs font-medium text-red-400 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-lg transition-colors"
            >
              <StopCircle className="w-3.5 h-3.5" />
              Stop
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{completedCount}/{STAGES.length}</span>
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium capitalize ${statusColors[overallStatus] || statusColors.idle}`}>
            {overallStatus}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      {isRunning && (
        <div className="mb-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400 font-medium">
              {currentStage ? `${currentStage.label} Agent` : 'Processing...'}
            </span>
            <span className="text-xs font-semibold text-green-400">{progressPercent}%</span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-700 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Stages */}
      <div className="space-y-0">
        {STAGES.map((stage, idx) => (
          <StageCard
            key={stage.id}
            stage={stage}
            status={statuses[stage.id]}
            message={messages[stage.id]}
            isLast={idx === STAGES.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

export default PipelineView;
