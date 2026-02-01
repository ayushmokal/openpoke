import { NextRequest, NextResponse } from 'next/server';

const PYTHON_SERVER = process.env.PYTHON_SERVER_URL || 'http://localhost:8000';

// GET - Load overrides for a user
export async function GET(request: NextRequest) {
  try {
    const userId = request.headers.get('x-user-id') || 'default';

    const res = await fetch(`${PYTHON_SERVER}/api/v1/overrides?user_id=${userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      // Return empty overrides if not found
      return NextResponse.json({
        ok: true,
        data: {
          ringDebugOverrides: {},
          ringBatteryOverrides: {},
          kustomerOverrides: {},
          overridesEnabled: true,
        }
      });
    }

    const data = await res.json();
    return NextResponse.json({ ok: true, data });
  } catch (error) {
    console.error('[Overrides GET] Error:', error);
    return NextResponse.json({
      ok: true,
      data: {
        ringDebugOverrides: {},
        ringBatteryOverrides: {},
        kustomerOverrides: {},
        overridesEnabled: true,
      }
    });
  }
}

// POST - Save overrides for a user
export async function POST(request: NextRequest) {
  try {
    const userId = request.headers.get('x-user-id') || 'default';
    const body = await request.json();

    const res = await fetch(`${PYTHON_SERVER}/api/v1/overrides`, {
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
      console.error('[Overrides POST] Backend error:', errorText);
      // Still return success - we'll fall back to localStorage
      return NextResponse.json({ ok: true, persisted: false });
    }

    return NextResponse.json({ ok: true, persisted: true });
  } catch (error) {
    console.error('[Overrides POST] Error:', error);
    return NextResponse.json({ ok: true, persisted: false });
  }
}
