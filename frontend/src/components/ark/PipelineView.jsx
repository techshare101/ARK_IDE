import React from 'react';
import { Brain, Code2, FlaskConical, Rocket, Activity, CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';

const STAGES = [
  { id: 'planner',  label: 'Planner',  icon: Brain,         desc: 'Analyzing requirements & creating execution plan', textClass: 'text-purple-400', bgClass: 'bg-purple-500/10', borderClass: 'border-purple-500/40', ringClass: 'ring-purple-500/30', lineClass: 'bg-purple-500/40', badgeBg: 'bg-purple-500/10' },
  { id: 'builder',  label: 'Builder',  icon: Code2,         desc: 'Writing production-ready code',                   textClass: 'text-blue-400',   bgClass: 'bg-blue-500/10',   borderClass: 'border-blue-500/40',   ringClass: 'ring-blue-500/30',   lineClass: 'bg-blue-500/40',   badgeBg: 'bg-blue-500/10'   },
  { id: 'tester',   label: 'Tester',   icon: FlaskConical,  desc: 'Running tests & validating functionality',         textClass: 'text-yellow-400', bgClass: 'bg-yellow-500/10', borderClass: 'border-yellow-500/40', ringClass: 'ring-yellow-500/30', lineClass: 'bg-yellow-500/40', badgeBg: 'bg-yellow-500/10' },
  { id: 'deployer', label: 'Deployer', icon: Rocket,        desc: 'Packaging & deploying the application',            textClass: 'text-green-400',  bgClass: 'bg-green-500/10',  borderClass: 'border-green-500/40',  ringClass: 'ring-green-500/30',  lineClass: 'bg-green-500/40',  badgeBg: 'bg-green-500/10'  },
  { id: 'monitor',  label: 'Monitor',  icon: Activity,      desc: 'Monitoring health & performance',                  textClass: 'text-slate-400',  bgClass: 'bg-slate-500/10',  borderClass: 'border-slate-500/40',  ringClass: 'ring-slate-500/30',  lineClass: 'bg-slate-500/40',  badgeBg: 'bg-slate-500/10'  },
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

export function PipelineView({ project, events }) {
  const { statuses, messages } = React.useMemo(() => {
    const statuses = {};
    const messages = {};
    if (!events || events.length === 0) return { statuses, messages };
    events.forEach(event => {
      const agent = (event.agent || '').toLowerCase();
      const type  = event.event_type;
      const stage = STAGES.find(s => agent.includes(s.id));
      if (!stage) return;
      if (type === 'agent_start')    { statuses[stage.id] = 'running';   messages[stage.id] = event.message || null; }
      if (type === 'agent_complete') { statuses[stage.id] = 'completed'; messages[stage.id] = event.message || null; }
      if (type === 'agent_error')    { statuses[stage.id] = 'failed';    messages[stage.id] = event.message || null; }
      if (type === 'agent_message' && statuses[stage.id] === 'running') { messages[stage.id] = event.message || null; }
    });
    return { statuses, messages };
  }, [events]);

  const completedCount = STAGES.filter(s => statuses[s.id] === 'completed').length;
  const overallStatus  = project?.status || 'idle';

  const statusColors = {
    idle:      'bg-slate-700 text-slate-300',
    running:   'bg-indigo-500/20 text-indigo-300',
    completed: 'bg-green-500/20 text-green-300',
    failed:    'bg-red-500/20 text-red-300',
  };

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pipeline</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{completedCount}/{STAGES.length}</span>
          <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium capitalize ${statusColors[overallStatus] || statusColors.idle}`}>
            {overallStatus}
          </span>
        </div>
      </div>

      {overallStatus !== 'idle' && (
        <div className="mb-5">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Progress</span>
            <span>{Math.round((completedCount / STAGES.length) * 100)}%</span>
          </div>
          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-700"
              style={{ width: `${(completedCount / STAGES.length) * 100}%` }}
            />
          </div>
        </div>
      )}

      <div>
        {STAGES.map((stage, i) => (
          <StageCard
            key={stage.id}
            stage={stage}
            status={statuses[stage.id]}
            message={messages[stage.id]}
            isLast={i === STAGES.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

export default PipelineView;
