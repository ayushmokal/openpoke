"use client";
import { useCallback, useEffect, useState } from 'react';

export type Settings = {
  timezone: string;
};

export function useSettings() {
  const [settings, setSettings] = useState<Settings>({ timezone: '' });

  useEffect(() => {
    try {
      const timezone = localStorage.getItem('user_timezone') || '';
      setSettings({ timezone });
    } catch {}
  }, []);

  const persist = useCallback((s: Settings) => {
    setSettings(s);
    try {
      localStorage.setItem('user_timezone', s.timezone);
    } catch {}
  }, []);

  return { settings, setSettings: persist } as const;
}

export default function SettingsModal({
  open,
  onClose,
  settings,
  onSave,
  userId,
}: {
  open: boolean;
  onClose: () => void;
  settings: Settings;
  onSave: (s: Settings) => void;
  userId?: string;
}) {
  const [timezone, setTimezone] = useState(settings.timezone);

  useEffect(() => {
    setTimezone(settings.timezone);
  }, [settings]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="glass-card w-full max-w-md p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-base font-medium text-white">Settings</h2>
          <button onClick={onClose} className="btn-icon" aria-label="Close">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" strokeLinecap="round" strokeLinejoin="round" />
              <line x1="6" y1="6" x2="18" y2="18" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>

        <div className="space-y-6">
          {/* Timezone */}
          <div>
            <label className="mb-2 block text-xs font-medium text-white/40 uppercase tracking-wider">
              Timezone
            </label>
            <input
              className="input"
              type="text"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              placeholder="e.g. America/New_York"
            />
            <p className="mt-2 text-xs text-white/30">
              {timezone ? 'Auto-detected. Edit to override.' : 'Will be auto-detected.'}
            </p>
          </div>

          {/* User ID */}
          {userId && (
            <div>
              <label className="mb-2 block text-xs font-medium text-white/40 uppercase tracking-wider">
                Session ID
              </label>
              <div className="glass-card p-3">
                <code className="text-xs text-white/60 font-mono break-all">{userId}</code>
                <p className="mt-2 text-[10px] text-white/30">
                  Your settings and overrides are tied to this session.
                </p>
              </div>
            </div>
          )}

          {/* Info */}
          <div className="p-3 bg-white/5 rounded-lg border border-white/10">
            <p className="text-xs text-white/50">
              <strong className="text-white/70">Tip:</strong> Use the <span className="font-medium text-white/70">Overrides</span> tab in the sidebar to configure test data for the AI agent.
            </p>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button onClick={onClose} className="btn-ghost text-sm">Cancel</button>
          <button
            className="btn text-sm"
            onClick={() => {
              onSave({ timezone });
              onClose();
            }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
