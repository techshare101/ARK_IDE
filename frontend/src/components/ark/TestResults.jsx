import React, { useState } from 'react';
import { FlaskConical, CheckCircle2, XCircle, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react';

function TestRow({ test }) {
  const [expanded, setExpanded] = useState(false);
  const passed  = test.status === 'passed'  || test.passed === true;
  const failed  = test.status === 'failed'  || test.passed === false;
  const skipped = test.status === 'skipped';
  const hasDetail = test.error || test.output || test.duration;

  return (
    <div className={`rounded-lg border transition-colors ${
      passed  ? 'border-green-500/20 bg-green-500/5'  :
      failed  ? 'border-red-500/20 bg-red-500/5'      :
      skipped ? 'border-slate-700 bg-slate-800/50'    :
                'border-slate-700 bg-slate-800/50'
    }`}>
      <button
        onClick={() => hasDetail && setExpanded(!expanded)}
        className={`w-full flex items-center gap-3 px-3 py-2.5 text-left ${
          hasDetail ? 'cursor-pointer' : 'cursor-default'
        }`}
      >
        <div className="flex-shrink-0">
          {passed  && <CheckCircle2 className="w-4 h-4 text-green-400" />}
          {failed  && <XCircle      className="w-4 h-4 text-red-400"   />}
          {skipped && <AlertCircle  className="w-4 h-4 text-slate-500" />}
          {!passed && !failed && !skipped && <AlertCircle className="w-4 h-4 text-slate-500" />}
        </div>
        <span className={`flex-1 text-xs font-mono truncate ${
          passed ? 'text-slate-200' : failed ? 'text-red-200' : 'text-slate-500'
        }`}>
          {test.name || test.test_name || 'Unnamed test'}
        </span>
        {test.duration && (
          <span className="text-[10px] text-slate-600 flex-shrink-0">
            {test.duration < 1 ? `${Math.round(test.duration * 1000)}ms` : `${test.duration.toFixed(2)}s`}
          </span>
        )}
        {hasDetail && (
          expanded
            ? <ChevronDown  className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
            : <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
        )}
      </button>
      {expanded && hasDetail && (
        <div className="px-3 pb-3 border-t border-slate-700/50 pt-2">
          {test.error && (
            <pre className="text-xs text-red-300 font-mono whitespace-pre-wrap break-words bg-red-500/10 rounded p-2">
              {test.error}
            </pre>
          )}
          {test.output && (
            <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap break-words bg-slate-800 rounded p-2 mt-1">
              {test.output}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

export function TestResults({ tests, loading }) {
  const [filter, setFilter] = useState('all');

  if (loading) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400">Running tests...</p>
        </div>
      </div>
    );
  }

  if (!tests || tests.length === 0) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 flex items-center justify-center">
        <div className="text-center">
          <FlaskConical className="w-10 h-10 text-slate-700 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No test results yet</p>
          <p className="text-xs text-slate-600 mt-1">Tests will appear after the Tester stage completes</p>
        </div>
      </div>
    );
  }

  const passed  = tests.filter(t => t.status === 'passed'  || t.passed === true);
  const failed  = tests.filter(t => t.status === 'failed'  || t.passed === false);
  const skipped = tests.filter(t => t.status === 'skipped');
  const passRate = tests.length > 0 ? Math.round((passed.length / tests.length) * 100) : 0;

  const filtered = filter === 'all'    ? tests
                 : filter === 'passed' ? passed
                 : filter === 'failed' ? failed
                 : skipped;

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 flex flex-col" style={{ minHeight: '400px' }}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex-shrink-0">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-yellow-400" />
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Test Results</h3>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-sm font-bold ${
              passRate === 100 ? 'text-green-400' :
              passRate >= 70   ? 'text-yellow-400' :
                                 'text-red-400'
            }`}>{passRate}%</span>
            <span className="text-xs text-slate-500">{passed.length}/{tests.length} passed</span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden mb-3">
          <div
            className={`h-full rounded-full transition-all duration-700 ${
              passRate === 100 ? 'bg-green-500' :
              passRate >= 70   ? 'bg-yellow-500' :
                                 'bg-red-500'
            }`}
            style={{ width: `${passRate}%` }}
          />
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
            <span className="text-xs text-slate-400">{passed.length} passed</span>
          </div>
          <div className="flex items-center gap-1.5">
            <XCircle className="w-3.5 h-3.5 text-red-400" />
            <span className="text-xs text-slate-400">{failed.length} failed</span>
          </div>
          {skipped.length > 0 && (
            <div className="flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-xs text-slate-400">{skipped.length} skipped</span>
            </div>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 px-4 py-2 border-b border-slate-800 flex-shrink-0">
        {[
          { key: 'all',     label: 'All',     count: tests.length   },
          { key: 'failed',  label: 'Failed',  count: failed.length  },
          { key: 'passed',  label: 'Passed',  count: passed.length  },
          { key: 'skipped', label: 'Skipped', count: skipped.length },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              filter === tab.key
                ? 'bg-slate-700 text-slate-200'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {tab.label}
            {tab.count > 0 && (
              <span className="ml-1.5 text-[10px] text-slate-600">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Test list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-sm text-slate-600">No {filter} tests</p>
          </div>
        ) : (
          filtered.map((test, i) => (
            <TestRow key={test.id || test.name || i} test={test} />
          ))
        )}
      </div>
    </div>
  );
}

export default TestResults;
