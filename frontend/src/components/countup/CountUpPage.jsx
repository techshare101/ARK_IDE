import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Pause, Play, RotateCcw, Timer, Minus, Plus } from 'lucide-react';

import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';

const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

const CountUpPage = () => {
  const [count, setCount] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [step, setStep] = useState(1);
  const [intervalMs, setIntervalMs] = useState(1000);

  const intervalRef = useRef(null);

  const safeStep = useMemo(() => {
    const n = Number(step);
    if (!Number.isFinite(n)) return 1;
    return clamp(Math.trunc(n), 1, 1_000_000);
  }, [step]);

  const safeIntervalMs = useMemo(() => {
    const n = Number(intervalMs);
    if (!Number.isFinite(n)) return 1000;
    return clamp(Math.trunc(n), 50, 60_000);
  }, [intervalMs]);

  useEffect(() => {
    if (!isRunning) return;

    intervalRef.current = window.setInterval(() => {
      setCount((c) => c + safeStep);
    }, safeIntervalMs);

    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    };
  }, [isRunning, safeStep, safeIntervalMs]);

  const onReset = () => setCount(0);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Count Up</h1>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <Badge variant={isRunning ? 'secondary' : 'outline'}>
                {isRunning ? 'Running' : 'Paused'}
              </Badge>
              <Separator orientation="vertical" className="h-4" />
              <Link to="/" className="text-sm text-gray-600 hover:text-gray-900 underline underline-offset-4">
                Back to Ark IDE
              </Link>
              <span className="text-gray-300">•</span>
              <Link to="/todos" className="text-sm text-gray-600 hover:text-gray-900 underline underline-offset-4">
                Todos
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant={isRunning ? 'outline' : 'default'}
              size="sm"
              onClick={() => setIsRunning((v) => !v)}
              data-testid="countup-toggle"
            >
              {isRunning ? (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Start
                </>
              )}
            </Button>
            <Button variant="outline" size="sm" onClick={onReset} data-testid="countup-reset">
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6">
        <Card>
          <CardContent className="p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row sm:items-end gap-4 sm:gap-6">
              <div className="flex-1">
                <div className="text-sm text-gray-600">Current count</div>
                <div className="mt-1 text-4xl sm:text-5xl font-bold text-gray-900 tabular-nums" data-testid="countup-value">
                  {count.toLocaleString()}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCount((c) => c - safeStep)}
                  aria-label="Decrement"
                  data-testid="countup-dec"
                >
                  <Minus className="w-4 h-4" />
                </Button>
                <Button
                  type="button"
                  onClick={() => setCount((c) => c + safeStep)}
                  aria-label="Increment"
                  data-testid="countup-inc"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add
                </Button>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-1">Step</label>
                <Input
                  type="number"
                  min={1}
                  step={1}
                  value={step}
                  onChange={(e) => setStep(e.target.value)}
                  data-testid="countup-step"
                />
                <div className="mt-1 text-xs text-gray-500">Applied to manual and auto increments.</div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-900 mb-1">Interval (ms)</label>
                <div className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                    <Timer className="w-4 h-4" />
                  </div>
                  <Input
                    className="pl-9"
                    type="number"
                    min={50}
                    step={50}
                    value={intervalMs}
                    onChange={(e) => setIntervalMs(e.target.value)}
                    data-testid="countup-interval"
                  />
                </div>
                <div className="mt-1 text-xs text-gray-500">When running, increments every {safeIntervalMs}ms.</div>
              </div>
            </div>

            <div className="mt-6 text-xs text-gray-500">
              Tip: You can use <span className="font-mono">Start</span> for automatic counting, or the buttons for manual changes.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CountUpPage;
