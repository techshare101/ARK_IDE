import React, { useState } from 'react';
import { Sparkles, Code2, Database, Layout } from 'lucide-react';

const QUICK_STARTS = [
  { 
    icon: Layout, 
    title: 'Todo App', 
    desc: 'React + TailwindCSS',
    prompt: 'Build a todo app in React with TailwindCSS. Include add, delete, and mark complete features.'
  },
  { 
    icon: Database, 
    title: 'REST API', 
    desc: 'FastAPI + MongoDB',
    prompt: 'Create a REST API with FastAPI and MongoDB for a blog. Include CRUD endpoints for posts.'
  },
  { 
    icon: Code2, 
    title: 'Dashboard', 
    desc: 'Analytics UI',
    prompt: 'Build an analytics dashboard in React with charts, metrics cards, and a data table.'
  },
];

export function HeroSection({ onStartBuild }) {
  const [goal, setGoal] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (goal.trim()) {
      onStartBuild(goal);
      setGoal('');
      setIsExpanded(false);
    }
  };

  const handleQuickStart = (prompt) => {
    setGoal(prompt);
    setIsExpanded(true);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-16 fade-in">
      {/* Hero text */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6" style={{
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border)'
        }}>
          <Sparkles className="w-4 h-4" style={{ color: 'var(--accent-purple)' }} />
          <span className="text-sm font-medium gradient-text">Autonomous Software Development</span>
        </div>
        
        <h1 className="text-5xl md:text-6xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
          What will you{' '}
          <span className="gradient-text">build</span>{' '}
          today?
        </h1>
        
        <p className="text-lg" style={{ color: 'var(--text-muted)' }}>
          Describe your app. Watch 5 AI agents plan, build, test & deploy it.
        </p>
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="relative">
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onFocus={() => setIsExpanded(true)}
            placeholder="e.g., Build a real-time chat app with React and Socket.io..."
            rows={isExpanded ? 4 : 2}
            className="w-full px-6 py-4 rounded-xl text-base resize-none transition-all"
            style={{
              background: 'var(--bg-card)',
              border: '2px solid var(--border)',
              color: 'var(--text-primary)',
              outline: 'none'
            }}
            onFocus={(e) => e.target.style.borderColor = 'var(--accent-purple)'}
            onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
          />
          
          {goal.trim() && (
            <button
              type="submit"
              className="absolute bottom-4 right-4 btn-primary flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Start Building
            </button>
          )}
        </div>
      </form>

      {/* Quick starts */}
      <div>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-muted)' }}>
          OR START WITH A TEMPLATE
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {QUICK_STARTS.map((qs, idx) => {
            const Icon = qs.icon;
            return (
              <button
                key={idx}
                onClick={() => handleQuickStart(qs.prompt)}
                className="p-6 rounded-xl text-left transition-all hover:scale-105"
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  boxShadow: '0 4px 12px var(--shadow)'
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-purple)'}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border)'}
              >
                <div className="w-10 h-10 rounded-lg mb-3 flex items-center justify-center" style={{
                  background: 'var(--accent-purple)',
                  opacity: 0.1
                }}>
                  <Icon className="w-5 h-5" style={{ color: 'var(--accent-purple)' }} />
                </div>
                <h4 className="font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
                  {qs.title}
                </h4>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {qs.desc}
                </p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default HeroSection;
