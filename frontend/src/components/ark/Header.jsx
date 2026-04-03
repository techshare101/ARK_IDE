import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { Sun, Moon, Zap } from 'lucide-react';

export function Header({ connected }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 border-b" style={{
      background: 'var(--bg-secondary)',
      borderColor: 'var(--border)'
    }}>
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold gradient-text">ARK IDE</h1>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>v3.0</p>
          </div>
        </div>

        {/* Right section */}
        <div className="flex items-center gap-4">
          {/* Connection status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={{
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border)'
          }}>
            <div className={`w-2 h-2 rounded-full ${
              connected ? 'bg-green-500' : 'bg-red-500'
            } ${connected ? 'animate-pulse' : ''}`} />
            <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg transition-all hover:scale-105"
            style={{
              background: 'var(--bg-tertiary)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)'
            }}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;
