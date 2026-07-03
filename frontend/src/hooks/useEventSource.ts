import { useEffect, useRef, useCallback, useState } from "react";

type EventHandler = (data: any) => void;

interface UseEventSourceOptions {
  onMessage?: EventHandler;
  onEvent?: (type: string, data: any) => void;
  onReconnect?: () => void;
}

export function useEventSource(
  url: string,
  options: UseEventSourceOptions = {},
) {
  const { onMessage, onEvent, onReconnect } = options;
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [connected, setConnected] = useState(false);
  const reconnectAttemptRef = useRef(0);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource(url, { withCredentials: true });
    eventSourceRef.current = es;

    es.onopen = () => {
      setConnected(true);
      reconnectAttemptRef.current = 0;
    };

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
        if (data.type && onEvent) {
          onEvent(data.type, data.payload);
        }
      } catch {
        onMessage?.(event.data);
      }
    };

    es.addEventListener("ping", () => {});

    es.onerror = () => {
      setConnected(false);
      if (es.readyState === EventSource.CLOSED) {
        const delay = Math.min(1000 * 2 ** reconnectAttemptRef.current, 30000);
        reconnectAttemptRef.current++;
        reconnectTimeoutRef.current = setTimeout(() => {
          onReconnect?.();
          connect();
        }, delay);
      }
    };
  }, [url, onMessage, onEvent, onReconnect]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      eventSourceRef.current?.close();
    };
  }, [connect]);

  const close = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    eventSourceRef.current?.close();
    setConnected(false);
  }, []);

  return { connected, close };
}
