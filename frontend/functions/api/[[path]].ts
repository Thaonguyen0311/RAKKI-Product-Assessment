interface PagesEnv {
  BACKEND_ORIGIN: string;
}

interface PagesContext {
  request: Request;
  env: PagesEnv;
}

export async function onRequest({ request, env }: PagesContext): Promise<Response> {
  if (!env.BACKEND_ORIGIN) {
    return new Response('API proxy is not configured', { status: 503 });
  }

  let backend: URL;
  try {
    backend = new URL(env.BACKEND_ORIGIN);
  } catch {
    return new Response('API proxy configuration is invalid', { status: 503 });
  }
<<<<<<< HEAD
=======

>>>>>>> bd03f4e8648db440a25786389c895c13b409d242
  if (backend.protocol !== 'https:') {
    return new Response('API proxy must use HTTPS', { status: 503 });
  }

  const incoming = new URL(request.url);
  const upstream = new URL(incoming.pathname + incoming.search, backend.origin);
  return fetch(new Request(upstream, request));
}
