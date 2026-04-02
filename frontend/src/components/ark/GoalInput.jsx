import React, { useState } from 'react';
import { Rocket, Loader2, Sparkles } from 'lucide-react';

const EXAMPLE_GOALS = [
  'Build a REST API for a todo app with authentication and PostgreSQL',
  'Create a real-time chat application using WebSockets',
  'Develop a CLI tool for bulk image resizing with progress tracking',
  'Build a URL shortener service with analytics dashboard',
  'Create a markdown blog engine with RSS feed support',
];

export function GoalInput({ onSubmit, loading }) {
  const [goal, setGoal] = useState('');
  const [focused, setFocused] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = goal.trim();
    if (!trimmed || loading) return;
    onSubmit(trimmed);
  };

  const charCount = goal.length;
  const isValid = charCount >= 10 && charCount <= 2000;

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">ARK IDE <span className="text-indigo-400">v3.0</span></h1>
            <p className="text-slate-400 text-sm">Autonomous Software Development Platform</p>
          </div>
        </div>
        <p className="text-slate-300 text-lg">
          Describe what you want to build. ARK will plan, code, test, and deploy it.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div
          className={`relative rounded-xl border-2 transition-all duration-200 ${
            focused
              ? 'border-indigo-500 shadow-lg shadow-indigo-500/20'
              : 'border-slate-700 hover:border-slate-600'
          } bg-slate-900`}
        >
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Describe your project goal in detail..."
            className="w-full bg-transparent text-slate-100 placeholder-slate-500 p-4 pb-14 resize-none outline-none text-sm leading-relaxed min-h-[140px]"
            disabled={loading}
            maxLength={2000}
          />
          <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between">
            <span className={`text-xs ${
              charCount > 1800 ? 'text-red-400' : charCount > 1500 ? 'text-yellow-400' : 'text-slate-500'
            }`}>
              {charCount}/2000
            </span>
            <button
              type="submit"
              disabled={!isValid || loading}
              className="flex items-center gap-2 px-5 py-2 rounded-lg font-medium text-sm transition-all duration-200 bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 disabled:cursor-not-allowed active:scale-95"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating Project...
                </>
              ) : (
                <>
                  <Rocket className="w-4 h-4" />
                  Launch ARK Pipeline
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      <div className="mt-6">
        <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider">Example goals</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_GOALS.map((example, i) => (
            <button
              key={i}
              onClick={() => setGoal(example)}
              disabled={loading}
              className="text-xs px-3 py-1.5 rounded-full border border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-300 hover:bg-indigo-500/10 transition-all duration-150 disabled:opacity-40"
            >
              {example.length > 55 ? example.slice(0, 55) + '...' : example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default GoalInput;
