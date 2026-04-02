import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, RefreshCw, Trash2, CheckCircle2, Circle } from 'lucide-react';

import { todosAPI } from '../../api/todos';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent } from '../ui/card';
import { Checkbox } from '../ui/checkbox';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { toast } from 'sonner';

const TodoPage = () => {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [title, setTitle] = useState('');
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [togglingId, setTogglingId] = useState(null);

  const remainingCount = useMemo(
    () => todos.filter((t) => !t.completed).length,
    [todos]
  );

  const completedCount = useMemo(
    () => todos.filter((t) => t.completed).length,
    [todos]
  );

  const loadTodos = async (opts = { silent: false }) => {
    try {
      if (!opts.silent) setLoading(true);
      const data = await todosAPI.list();
      setTodos(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
      toast.error('Failed to load todos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTodos();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await loadTodos({ silent: true });
      toast.success('Refreshed');
    } catch {
      // handled in loadTodos
    } finally {
      setRefreshing(false);
    }
  };

  const onCreate = async (e) => {
    e?.preventDefault?.();
    const trimmed = title.trim();
    if (!trimmed) return;

    setCreating(true);
    try {
      const created = await todosAPI.create({ title: trimmed });
      setTodos((prev) => [created, ...prev]);
      setTitle('');
      toast.success('Todo added');
    } catch (err) {
      console.error(err);
      toast.error('Failed to add todo');
    } finally {
      setCreating(false);
    }
  };

  const onToggle = async (todo) => {
    setTogglingId(todo.id);
    const nextCompleted = !todo.completed;

    // optimistic
    setTodos((prev) => prev.map((t) => (t.id === todo.id ? { ...t, completed: nextCompleted } : t)));

    try {
      const updated = await todosAPI.update(todo.id, { completed: nextCompleted });
      setTodos((prev) => prev.map((t) => (t.id === todo.id ? updated : t)));
    } catch (err) {
      console.error(err);
      // rollback
      setTodos((prev) => prev.map((t) => (t.id === todo.id ? { ...t, completed: todo.completed } : t)));
      toast.error('Failed to update todo');
    } finally {
      setTogglingId(null);
    }
  };

  const onDelete = async (id) => {
    setDeletingId(id);
    const prev = todos;
    setTodos((cur) => cur.filter((t) => t.id !== id));

    try {
      await todosAPI.remove(id);
      toast.success('Todo deleted');
    } catch (err) {
      console.error(err);
      setTodos(prev);
      toast.error('Failed to delete todo');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Todos</h1>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <Badge variant="secondary">Remaining: {remainingCount}</Badge>
              <Badge variant="outline">Completed: {completedCount}</Badge>
              <Separator orientation="vertical" className="h-4" />
              <Link to="/" className="text-sm text-gray-600 hover:text-gray-900 underline underline-offset-4">
                Back to Ark IDE
              </Link>
            </div>
          </div>

          <Button variant="outline" size="sm" onClick={onRefresh} disabled={refreshing || loading} className="shrink-0">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6">
        <Card>
          <CardContent className="p-4 sm:p-6">
            <form onSubmit={onCreate} className="flex items-center gap-2">
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Add a new todo..."
                disabled={creating}
                data-testid="todo-input"
              />
              <Button type="submit" disabled={creating || !title.trim()} data-testid="todo-add">
                <Plus className="w-4 h-4 mr-2" />
                Add
              </Button>
            </form>

            <div className="mt-5">
              {loading ? (
                <div className="text-sm text-gray-600">Loading todos…</div>
              ) : todos.length === 0 ? (
                <div className="text-sm text-gray-600">No todos yet. Add your first one above.</div>
              ) : (
                <ul className="space-y-2" data-testid="todo-list">
                  {todos.map((todo) => {
                    const busy = deletingId === todo.id || togglingId === todo.id;
                    return (
                      <li key={todo.id}>
                        <div className="flex items-center justify-between gap-3 rounded-lg border bg-white px-3 py-2">
                          <div className="flex items-center gap-3 min-w-0">
                            <button
                              type="button"
                              className="shrink-0"
                              onClick={() => onToggle(todo)}
                              disabled={busy}
                              aria-label={todo.completed ? 'Mark as incomplete' : 'Mark as completed'}
                            >
                              <Checkbox checked={!!todo.completed} />
                            </button>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                {todo.completed ? (
                                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                                ) : (
                                  <Circle className="w-4 h-4 text-gray-400" />
                                )}
                                <span className={`text-sm break-words ${todo.completed ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                                  {todo.title}
                                </span>
                              </div>
                              {todo.created_at && (
                                <div className="text-xs text-gray-500 mt-0.5">
                                  Created: {new Date(todo.created_at).toLocaleString()}
                                </div>
                              )}
                            </div>
                          </div>

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onDelete(todo.id)}
                            disabled={busy}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            aria-label="Delete todo"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TodoPage;
