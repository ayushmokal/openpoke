const serverBase = process.env.PY_SERVER_URL || 'http://localhost:8001';
const statusPath = `${serverBase.replace(/\/$/, '')}/api/v1/ring/status`;

export async function GET() {
  try {
    const res = await fetch(statusPath, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });

    const bodyText = await res.text();
    const headers = new Headers({ 'Content-Type': 'application/json; charset=utf-8' });
    return new Response(bodyText || '{}', { status: res.status, headers });
  } catch (error: any) {
    const message = error?.message || 'Failed to reach Python server';
    return new Response(JSON.stringify({ error: message }), {
      status: 502,
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
    });
  }
}
