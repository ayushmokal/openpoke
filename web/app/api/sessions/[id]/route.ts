import { NextRequest, NextResponse } from 'next/server';

const PYTHON_SERVER = process.env.PYTHON_SERVER_URL || 'http://localhost:8000';

// GET - Get a specific session by ID
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const userId = request.headers.get('x-user-id') || 'default';

    const res = await fetch(`${PYTHON_SERVER}/api/v1/sessions/${id}?user_id=${userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      return NextResponse.json({ ok: false, error: 'Session not found' }, { status: 404 });
    }

    const data = await res.json();
    return NextResponse.json({ ok: true, session: data });
  } catch (error) {
    console.error('[Session GET] Error:', error);
    return NextResponse.json({ ok: false, error: 'Failed to fetch session' }, { status: 500 });
  }
}

// DELETE - Delete a specific session
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const userId = request.headers.get('x-user-id') || 'default';

    const res = await fetch(`${PYTHON_SERVER}/api/v1/sessions/${id}?user_id=${userId}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      return NextResponse.json({ ok: false, error: 'Failed to delete session' }, { status: res.status });
    }

    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error('[Session DELETE] Error:', error);
    return NextResponse.json({ ok: false, error: 'Failed to delete session' }, { status: 500 });
  }
}
