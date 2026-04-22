export const fetchWithAbort = async (url: string, options: RequestInit = {}) => {
  const controller = new AbortController();
  const signal = controller.signal;

  const response = await fetch(url, { ...options, signal });

  return { response, controller };
};

export const api = {
  get: (url: string) => fetchWithAbort(url, { method: 'GET' }),
  post: (url: string, body: any) => fetchWithAbort(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  }),
};
