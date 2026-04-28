export const useShadowEmit = () => {
  const emit = async (eventType: string, payload: any, traceId: string) => {
    // Call backend SHADOW API
    const response = await fetch('/api/shadow/commit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: eventType,
        payload: payload,
        trace_id: traceId
      })
    });
    return response.json();
  };

  return { emit };
};
