import React from 'react';
import { Zap, Github, Twitter } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t mt-auto" style={{
      background: 'var(--bg-secondary)',
      borderColor: 'var(--border)'
    }}>
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-6">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold gradient-text">ARK IDE v3.0</span>
            </div>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Autonomous Software Development Platform
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>Platform</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-sm hover:underline" style={{ color: 'var(--text-muted)' }}>Documentation</a></li>
              <li><a href="#" className="text-sm hover:underline" style={{ color: 'var(--text-muted)' }}>API Reference</a></li>
              <li><a href="#" className="text-sm hover:underline" style={{ color: 'var(--text-muted)' }}>Examples</a></li>
            </ul>
          </div>

          {/* Tech */}
          <div>
            <h4 className="font-semibold mb-3" style={{ color: 'var(--text-secondary)' }}>Powered By</h4>
            <ul className="space-y-2 text-sm" style={{ color: 'var(--text-muted)' }}>
              <li>• GPT-5.2 (Planning & Code Generation)</li>
              <li>• E2B Sandboxes (Isolated Execution)</li>
              <li>• FastAPI + React + MongoDB</li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-6 border-t flex items-center justify-between" style={{ borderColor: 'var(--border)' }}>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            © 2026 ARK Intelligence. Built with autonomous agents.
          </p>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:scale-110 transition-transform" style={{ color: 'var(--text-muted)' }}>
              <Github className="w-5 h-5" />
            </a>
            <a href="#" className="hover:scale-110 transition-transform" style={{ color: 'var(--text-muted)' }}>
              <Twitter className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
