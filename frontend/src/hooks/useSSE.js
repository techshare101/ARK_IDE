import { useState, useEffect, useCallback, useRef } from 'react';

export const useSSE = (url, enabled = false) => {
  const [events, setEvents] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);

  const connect = useCallback(() => {
    if (!url || !enabled) return;

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('SSE connected');
        setIsConnected(true);
        setError(null);
      };

      // Handle all event types
      const eventTypes = [
        'started',
        'thinking',
        'thought',
        'tool_call',
        'tool_result',
        'approval_required',
        'done',
        'error'
      ];

      eventTypes.forEach(eventType => {
        eventSource.addEventListener(eventType, (e) => {
          try {
            const data = JSON.parse(e.data);
            const event = {
              type: eventType,
              data,
              timestamp: new Date().toISOString()
            };
            setEvents(prev => [...prev, event]);
          } catch (err) {
            console.error('Error parsing SSE event:', err);
          }
        });
      });

      eventSource.onerror = (err) => {
        console.error('SSE error:', err);
        setError('Connection error');
        setIsConnected(false);
        eventSource.close();
      };

    } catch (err) {
      console.error('Failed to create EventSource:', err);
      setError(err.message);
    }
  }, [url, enabled]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [url, enabled, connect, disconnect]);

  return { events, isConnected, error, clearEvents, reconnect: connect };
};
