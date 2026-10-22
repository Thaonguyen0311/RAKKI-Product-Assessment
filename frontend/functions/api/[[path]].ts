interface Env {
  BACKEND_URL: string;
}

/**
 * Same-origin API proxy for the Cloudflare Pages staging frontend.
 *
 * Configure BACKEND_URL in Cloudflare Pages as the HTTPS origin of the
 * Azure Container App, for example https://<app-name>.<region>.azurecontainerapps.io
 * Do not include /api in BACKEND_URL; the incoming /api path is preserved.
 */
export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  const configuredBase = env.BACKEND_URL?.trim();

  if (!configuredBase) {
    return Response.json(
      { detail: "Staging API is not configured yet. Set BACKEND_URL in Cloudflare Pages." },
      { status: 503 },
    );
  }

  let base: URL;
  try {
    base = new URL(configuredBase);
  } catch {
    return Response.json({ detail: "Invalid BACKEND_URL configuration." }, { status: 500 });
  }

  if (base.protocol !== "https:" || base.username || base.password) {
    return Response.json(
      { detail: "BACKEND_URL must be an HTTPS origin without embedded credentials." },
      { status: 500 },
    );
  }

  const incoming = new URL(request.url);
  const target = new URL(incoming.pathname + incoming.search, base.origin);
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");

  try {
    const upstream = await fetch(target.toString(), {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
      redirect: "manual",
    });

    // Preserve Set-Cookie so the API's secure session cookie is stored by the
    // Pages hostname. The browser then calls /api on the same origin.
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: upstream.headers,
    });
  } catch {
    return Response.json(
      { detail: "Could not reach the staging API. Check the Azure backend deployment." },
      { status: 502 },
    );
  }
};
