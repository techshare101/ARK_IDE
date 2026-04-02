import React, { useEffect, useRef } from 'react';
import { Terminal, Wifi, WifiOff, Trash2, AlertCircle } from 'lucide-react';

const EVENT_STYLES = {
  planner:  { text: 'text-purple-300', bg: 'bg-purple-500/10', badge: 'bg-purple-500/20 text-purple-300', dot: 'bg-purple-400' },
  builder:  { text: 'text-blue-300',   bg: 'bg-blue-500/10',   badge: 'bg-blue-500/20 text-blue-300',   dot: 'bg-blue-400'   },
  tester:   { text: 'text-yellow-300', bg: 'bg-yellow-500/10', badge: 'bg-yellow-500/20 text-yellow-300', dot: 'bg-yellow-400' },
  deployer: { text: 'text-green-300',  bg: 'bg-green-500/10',  badge: 'bg-green-500/20 text-green-300',  dot: 'bg-green-400'  },
  monitor:  { text: 'text-slate-300',  bg: 'bg-slate-500/10',  badge: 'bg-slate-500/20 text-slate-300',  dot: 'bg-slate-400'  },
  error:    { text: 'text-red-300',    bg: 'bg-red-500/10',    badge: 'bg-red-500/20 text-red-300',      dot: 'bg-red-400'    },
  system:   { text: 'text-indigo-300', bg: 'bg-indigo-500/10', badge: 'bg-indigo-500/20 text-indigo-300', dot: 'bg-indigo-400' },
  default:  { text: 'text-slate-300',  bg: '',                 badge: 'bg-slate-700 text-slate-400',      dot: 'bg-slate-500'  },
};

const EVENT_TYPE_LABELS = {
  agent_start:    'START',
  agent_complete: 'DONE',
  agent_error:    'ERROR',
  agent_message:  'MSG',
  tool_call:      'TOOL',
  tool_result:    'RESULT',
  code_generated: 'CODE',
  test_result:    'TEST',
  deploy_event:   'DEPLOY',
  pipeline_start: 'PIPELINE',
  pipeline_end:   'PIPELINE',
  stream_end:     'END',
};

function getStyle(event) {
  const agent = (event.agent || '').toLowerCase();
  const type  = (event.event_type || '').toLowerCase();
  if (type.includes('error')) return EVENT_STYLES.error;
  for (const key of Object.keys(EVENT_STYLES)) {
    if (agent.includes(key)) return EVENT_STYLES[key];
  }
  if (type.includes('pipeline') || type.includes('system')) return EVENT_STYLES.system;
  return EVENT_STYLES.default;
}

function EventRow({ event }) {
  const style = getStyle(event);
  const label = EVENT_TYPE_LABELS[event.event_type] || event.event_type?.toUpperCase() || 'EVT';
  const agentName = event.agent ? event.agent.replace(/_?agent$/i, '') : null;
  const isError = (event.event_type || '').includes('error');

  return (
    <div className={`sse-event flex items-start gap-2.5 px-3 py-2 rounded-lg text-xs ${style.bg} border border-transparent hover:border-slate-700/50 transition-colors`}>
      <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${style.dot}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          {agentName && (
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${style.badge}`}>
              {agentName}
            </span>
          )}
          <span className="text-[10px] text-slate-600 font-mono uppercase">{label}</span>
          {event.timestamp && (
            <span className="text-[10px] text-slate-700 ml-auto font-mono">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
        {event.message && (
          <p className={`leading-relaxed break-words ${isError ? 'text-red-300' : style.text}`}>
            {event.message}
          </p>
        )}
        {event.data && typeof event.data === 'object' && (
          <pre className="mt-1 text-[10px] text-slate-500 font-mono overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(event.data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

export function EventLog({ events, connected, error, onClear }) {
  const bottomRef = useRef(null);
  const containerRef = useRef(null);
  const autoScrollRef = useRef(true);

  useEffect(() => {
    if (autoScrollRef.current && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events]);

  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    autoScrollRef.current = scrollHeight - scrollTop - clientHeight < 80;
  };

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 flex flex-col h-full min-h-[400px]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-slate-400" />
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Event Stream</h3>
          <span className="text-xs text-slate-600">({events.length})</span>
        </div>
        <div className="flex items-center gap-3">
          {connected ? (
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              <span className="text-[10px] text-green-400 font-medium">LIVE</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-600" />
              <span className="text-[10px] text-slate-500">IDLE</span>
            </div>
          )}
          {onClear && events.length > 0 && (
            <button
              onClick={onClear}
              className="p-1 rounded text-slate-600 hover:text-slate-400 hover:bg-slate-800 transition-colors"
              title="Clear events"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border-b border-red-500/20 flex-shrink-0">
          <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
          <span className="text-xs text-red-300">{error}</span>
        </div>
      )}

      {/* Events list */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-3 space-y-1.5"
      >
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-12 text-center">
            <Terminal className="w-8 h-8 text-slate-700 mb-3" />
            <p className="text-sm text-slate-600">Waiting for events...</p>
            <p className="text-xs text-slate-700 mt-1">Events will appear here when the pipeline runs</p>
          </div>
        ) : (
          events.map((event) => (
            <EventRow key={event._id} event={event} />
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

export default EventLog;
