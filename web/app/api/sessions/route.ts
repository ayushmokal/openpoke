import { NextRequest, NextResponse } from 'next/server';

const PYTHON_SERVER = process.env.PYTHON_SERVER_URL || 'http://localhost:8000';

// GET - List all support sessions
export async function GET(request: NextRequest) {
  try {
    const userId = request.headers.get('x-user-id') || 'default';

    const res = await fetch(`${PYTHON_SERVER}/api/v1/sessions?user_id=${userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      return NextResponse.json({ ok: true, sessions: [] });
    }

    const data = await res.json();
    return NextResponse.json({ ok: true, sessions: data.sessions || [] });
  } catch (error) {
    console.error('[Sessions GET] Error:', error);
    return NextResponse.json({ ok: true, sessions: [] });
  }
}

// POST - Create a new session (archive current and start fresh)
export async function POST(request: NextRequest) {
  try {
    const userId = request.headers.get('x-user-id') || 'default';
    const body = await request.json();

    const res = await fetch(`${PYTHON_SERVER}/api/v1/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': userId,
      },
      body: JSON.stringify({
        user_id: userId,
        ...body,
      }),
    });

    if (!res.ok) {
      const errorText = await res.text();
      return NextResponse.json({ ok: false, error: errorText }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json({ ok: true, ...data });
  } catch (error) {
    console.error('[Sessions POST] Error:', error);
    return NextResponse.json({ ok: false, error: 'Failed to create session' }, { status: 500 });
  }
}
