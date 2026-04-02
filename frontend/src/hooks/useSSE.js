import { useState, useEffect, useRef, useCallback } from 'react';

const MAX_EVENTS = 200;
const RECONNECT_DELAY = 3000;
const MAX_RECONNECTS = 5;

export function useSSE(url, enabled = true) {
  const [events, setEvents] = useState([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!url || !enabled || !mountedRef.current) return;
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      if (!mountedRef.current) return;
      setConnected(true);
      setError(null);
      reconnectCountRef.current = 0;
    };

    es.onmessage = (e) => {
      if (!mountedRef.current) return;
      try {
        const event = JSON.parse(e.data);
        if (event.event_type === 'heartbeat') return;
        if (event.event_type === 'stream_end') {
          setConnected(false);
          es.close();
          return;
        }
        setEvents(prev => {
          const updated = [...prev, { ...event, _id: Date.now() + Math.random() }];
          return updated.slice(-MAX_EVENTS);
        });
      } catch (err) {
        console.warn('Failed to parse SSE event:', err);
      }
    };

    es.onerror = () => {
      if (!mountedRef.current) return;
      setConnected(false);
      es.close();

      if (reconnectCountRef.current < MAX_RECONNECTS) {
        reconnectCountRef.current++;
        setError(`Connection lost. Reconnecting (${reconnectCountRef.current}/${MAX_RECONNECTS})...`);
        reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY);
      } else {
        setError('Connection failed after maximum retries.');
      }
    };
  }, [url, enabled]);

  useEffect(() => {
    mountedRef.current = true;
    if (enabled && url) connect();
    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (eventSourceRef.current) eventSourceRef.current.close();
    };
  }, [url, enabled, connect]);

  const clearEvents = useCallback(() => setEvents([]), []);

  return { events, connected, error, clearEvents };
}

export default useSSE;
