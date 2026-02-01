'use client';

import { useCallback, useEffect, useState, useMemo } from 'react';
import SettingsModal, { useSettings } from '@/components/SettingsModal';
import SupportHistory from '@/components/SupportHistory';
import OverridesPanel, { Overrides } from '@/components/OverridesPanel';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatMessages } from '@/components/chat/ChatMessages';
import { ErrorBanner } from '@/components/chat/ErrorBanner';
import { useAutoScroll } from '@/components/chat/useAutoScroll';
import type { ChatBubble } from '@/components/chat/types';

const POLL_INTERVAL_MS = 2000;
const RING_STATUS_POLL_MS = 10000;

// All available Kustomer Info keys
const KUSTOMER_INFO_KEYS = [
  'ringSerialNumberStr', 'ringDescriptionStr', 'deviceModelStr', 'deviceOsStr',
  'ringFirmwareVersionStr', 'uhXUserStr', 'vipUserStr', 'latestAvailableAppVersionStr',
  'dataSharingStr', 'm1First24HrsStr', 'ringConnectedLast24HrsStr', 'noOfDaysSinceRingActivationStr',
  'lastRingStatesTimestampStr', 'softResetStr', 'factoryResetStr', 'last100ChargedStr',
  'appVersionStr', 'batteryTsSessionsStr', 'latestFirmwareAvailableForUserStr', 'policyStatusStr',
  'ringState10Str', 'faultyHrStr', 'uhxPlanNameStr', 'uhxExpiryStr', 'uhxCountryStr',
  'bdrTriggeredStr', 'bdrCompletedStr', 'bdrValueStr', 'daysSinceBdrStr', 'bdrTimeLeftStr',
  'currentBatteryLevelStr', 'avgWearTimeStr', 'batteryHealthScoreStr', 'replacementEligibleStr',
  'replacementCountStr', 'maxReplacementsStr', 'warrantyExpiryDateStr', 'daysUntilWarrantyExpiryStr',
  'wabiSabiReplacementCountStr', 'latestOrderIdStr', 'latestOrderStatusStr', 'trackingUrlStr',
  'orderSourceStr', 'orderDateStr', 'shippingAddressStr', 'shippingCountryStr', 'emailIdStr', 'nameStr'
];

interface YellowPayload {
  data?: {
    payload?: Record<string, any>;
  };
  session?: {
    payload?: Record<string, any>;
  };
}

interface RingStatus {
  batteryTsSessions: string;
  ringSerialNumber: string;
  batteryHealthScore: string;
  softReset: string;
  factoryReset: string;
  latestFirmwareAvailable: string;
  ringFirmwareVersion: string;
  currentBatteryLevel: string;
  connected: boolean;
  lastUpdated: string;
}

type TabType = 'ring-status' | 'ai-support' | 'orders';
type SidebarTab = 'live' | 'payload' | 'overrides';

const formatEscapeCharacters = (text: string): string => {
  return text
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t')
    .replace(/\\r/g, '\r')
    .replace(/\\\\/g, '\\');
};

const isRenderableMessage = (entry: any) =>
  typeof entry?.role === 'string' &&
  typeof entry?.content === 'string' &&
  entry.content.trim().length > 0;

const toBubbles = (payload: any): ChatBubble[] => {
  if (!Array.isArray(payload?.messages)) return [];

  const seen = new Set<string>();
  const result: ChatBubble[] = [];

  for (const message of payload.messages) {
    if (!isRenderableMessage(message)) continue;

    const text = formatEscapeCharacters(message.content);
    const key = `${message.role}:${text}`;

    if (seen.has(key) && result.length > 0 && result[result.length - 1].text === text) {
      continue;
    }

    seen.add(key);
    result.push({
      id: `history-${result.length}-${Date.now()}`,
      role: message.role,
      text,
    });
  }

  return result;
};

// Generate or retrieve user ID
const getUserId = (): string => {
  if (typeof window === 'undefined') return 'default';
  try {
    const existing = localStorage.getItem('support_user_id');
    if (existing) return existing;
    const cryptoObj = (globalThis as { crypto?: Crypto }).crypto;
    const randomPart =
      cryptoObj && typeof cryptoObj.randomUUID === 'function'
        ? cryptoObj.randomUUID().replace(/-/g, '')
        : Math.random().toString(36).slice(2);
    const generated = `user-${randomPart}`;
    localStorage.setItem('support_user_id', generated);
    return generated;
  } catch {
    return 'default';
  }
};

// Icons
const RingIcon = ({ className = "h-6 w-6" }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="5" />
  </svg>
);

const BatteryIcon = ({ percent }: { percent: number }) => (
  <div className="flex items-center gap-2">
    <div className="relative h-4 w-8 rounded border border-white/30">
      <div
        className="absolute left-0.5 top-0.5 bottom-0.5 rounded-sm bg-white transition-all"
        style={{ width: `${Math.max(0, Math.min(100, percent)) * 0.85}%` }}
      />
      <div className="absolute -right-0.5 top-1/2 h-1.5 w-0.5 -translate-y-1/2 rounded-r-sm bg-white/30" />
    </div>
    <span className="text-xs font-medium text-white/70">{percent}%</span>
  </div>
);

const SettingsIcon = () => (
  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="12" cy="12" r="3" />
    <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
  </svg>
);

const HistoryIcon = () => (
  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M12 8v4l3 3" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="12" cy="12" r="9" />
  </svg>
);

export default function Page() {
  const { settings, setSettings } = useSettings();
  const [open, setOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatBubble[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('ai-support');
  const [ringStatus, setRingStatus] = useState<RingStatus | null>(null);
  const [ringStatusLoading, setRingStatusLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>('live');
  const [userId, setUserId] = useState<string>('default');

  // Yellow AI Payload state
  const [yellowPayload, setYellowPayload] = useState<YellowPayload | null>(null);
  const [payloadInput, setPayloadInput] = useState('');
  const [payloadError, setPayloadError] = useState<string | null>(null);

  // Override states
  const [overrides, setOverrides] = useState<Overrides>({
    ringDebugOverrides: {},
    ringBatteryOverrides: {},
    kustomerOverrides: {},
    overridesEnabled: true,
  });

  const { scrollContainerRef, handleScroll } = useAutoScroll({
    items: messages,
    isWaiting: isWaitingForResponse,
  });
  const closeSettings = useCallback(() => setOpen(false), [setOpen]);

  // Initialize user ID
  useEffect(() => {
    setUserId(getUserId());
  }, []);

  // Function to sync context to backend
  const syncContextToBackend = useCallback(async (payload: YellowPayload | null, debugOverrides: Record<string, any>, batteryOverrides: Record<string, any>, kustomerOvr: Record<string, any>) => {
    try {
      const payloadDataInner = payload?.data?.payload || payload?.session?.payload || {};
      const combinedContext = {
        ...payloadDataInner,
        ...kustomerOvr,
        ...debugOverrides,
        ...batteryOverrides,
      };

      const res = await fetch('/api/context/set', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(combinedContext),
      });

      if (!res.ok) {
        const errorText = await res.text();
        console.error('[Context Sync] Failed:', res.status, errorText);
      }
    } catch (err) {
      console.error('[Context Sync] Error:', err);
    }
  }, []);

  // Function to clear context on backend
  const clearContextOnBackend = useCallback(async () => {
    try {
      await fetch('/api/context/clear', { method: 'POST' });
    } catch (err) {
      console.error('Error clearing context:', err);
    }
  }, []);

  // Load overrides from server on mount
  useEffect(() => {
    const loadOverrides = async () => {
      try {
        const res = await fetch('/api/overrides', {
          headers: { 'x-user-id': userId },
        });
        if (res.ok) {
          const data = await res.json();
          if (data.ok && data.data) {
            setOverrides(data.data);
          }
        }
      } catch {
        // Fall back to localStorage
        try {
          const savedDebugOverrides = localStorage.getItem('ring_debug_overrides');
          const savedBatteryOverrides = localStorage.getItem('ring_battery_overrides');
          const savedKustomerOverrides = localStorage.getItem('kustomer_overrides');
          const savedOverridesEnabled = localStorage.getItem('overrides_enabled');

          if (savedDebugOverrides || savedBatteryOverrides || savedKustomerOverrides) {
            setOverrides({
              ringDebugOverrides: savedDebugOverrides ? JSON.parse(savedDebugOverrides) : {},
              ringBatteryOverrides: savedBatteryOverrides ? JSON.parse(savedBatteryOverrides) : {},
              kustomerOverrides: savedKustomerOverrides ? JSON.parse(savedKustomerOverrides) : {},
              overridesEnabled: savedOverridesEnabled !== 'false',
            });
          }
        } catch {}
      }
    };

    if (userId !== 'default') {
      loadOverrides();
    }
  }, [userId]);

  // Load payload from localStorage
  useEffect(() => {
    try {
      const savedPayload = localStorage.getItem('yellow_payload');
      if (savedPayload) setYellowPayload(JSON.parse(savedPayload));
    } catch {}
  }, []);

  // Save payload to localStorage
  useEffect(() => {
    try {
      if (yellowPayload) localStorage.setItem('yellow_payload', JSON.stringify(yellowPayload));
    } catch {}
  }, [yellowPayload]);

  // Sync context to backend when payload or overrides change
  useEffect(() => {
    const hasData = yellowPayload ||
      Object.keys(overrides.ringDebugOverrides).length > 0 ||
      Object.keys(overrides.ringBatteryOverrides).length > 0 ||
      Object.keys(overrides.kustomerOverrides).length > 0;
    if (hasData && overrides.overridesEnabled) {
      syncContextToBackend(yellowPayload, overrides.ringDebugOverrides, overrides.ringBatteryOverrides, overrides.kustomerOverrides);
    }
  }, [yellowPayload, overrides, syncContextToBackend]);

  // Extract payload data from Yellow AI response
  const payloadData = useMemo(() => {
    if (!yellowPayload) return null;
    return yellowPayload.data?.payload || yellowPayload.session?.payload || null;
  }, [yellowPayload]);

  // Merge payload data with overrides
  const effectiveData = useMemo(() => {
    const base = payloadData || {};
    if (!overrides.overridesEnabled) return base;
    return { ...base, ...overrides.kustomerOverrides };
  }, [payloadData, overrides]);

  const handleParsePayload = useCallback(async () => {
    try {
      const parsed = JSON.parse(payloadInput);
      let newPayload: YellowPayload;

      if (parsed.data?.payload || parsed.session?.payload) {
        newPayload = parsed;
      } else if (parsed.success !== undefined && parsed.data) {
        newPayload = parsed.data;
      } else {
        newPayload = { data: { payload: parsed } };
      }

      setYellowPayload(newPayload);
      setPayloadError(null);
      setPayloadInput('');

      await syncContextToBackend(newPayload, overrides.ringDebugOverrides, overrides.ringBatteryOverrides, overrides.kustomerOverrides);
    } catch (e: any) {
      setPayloadError('Invalid JSON: ' + (e.message || 'Parse error'));
    }
  }, [payloadInput, overrides, syncContextToBackend]);

  const handleClearPayload = useCallback(async () => {
    setYellowPayload(null);
    setPayloadInput('');
    setPayloadError(null);
    try { localStorage.removeItem('yellow_payload'); } catch {}
    await clearContextOnBackend();
  }, [clearContextOnBackend]);

  const [savingOverrides, setSavingOverrides] = useState(false);

  const handleOverridesChange = useCallback((newOverrides: Overrides) => {
    setOverrides(newOverrides);
    // Also save to localStorage as backup
    try {
      localStorage.setItem('ring_debug_overrides', JSON.stringify(newOverrides.ringDebugOverrides));
      localStorage.setItem('ring_battery_overrides', JSON.stringify(newOverrides.ringBatteryOverrides));
      localStorage.setItem('kustomer_overrides', JSON.stringify(newOverrides.kustomerOverrides));
      localStorage.setItem('overrides_enabled', String(newOverrides.overridesEnabled));
    } catch {}
  }, []);

  const handleSaveOverrides = useCallback(async () => {
    setSavingOverrides(true);
    try {
      await fetch('/api/overrides', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': userId,
        },
        body: JSON.stringify(overrides),
      });
      // Also sync to context
      await syncContextToBackend(yellowPayload, overrides.ringDebugOverrides, overrides.ringBatteryOverrides, overrides.kustomerOverrides);
    } catch (err) {
      console.error('Failed to save overrides:', err);
    } finally {
      setSavingOverrides(false);
    }
  }, [overrides, userId, yellowPayload, syncContextToBackend]);

  const loadRingStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/ring/status', { cache: 'no-store' });
      if (!res.ok) {
        setRingStatus(null);
        return;
      }
      const data = await res.json();
      if (data.ok && data.data) {
        setRingStatus(data.data);
      }
    } catch (err) {
      console.error('Failed to load ring status', err);
      setRingStatus(null);
    } finally {
      setRingStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRingStatus();
    const intervalId = window.setInterval(() => {
      void loadRingStatus();
    }, RING_STATUS_POLL_MS);
    return () => window.clearInterval(intervalId);
  }, [loadRingStatus]);

  const loadHistory = useCallback(async () => {
    try {
      const res = await fetch('/api/chat/history', { cache: 'no-store' });
      if (!res.ok) return;
      const data = await res.json();
      const newMessages = toBubbles(data);

      setMessages(prev => {
        if (prev.length !== newMessages.length) return newMessages;
        const hasChanges = newMessages.some((msg, i) =>
          msg.text !== prev[i]?.text || msg.role !== prev[i]?.role
        );
        return hasChanges ? newMessages : prev;
      });
    } catch (err: any) {
      if (err?.name === 'AbortError') return;
      console.error('Failed to load chat history', err);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    const detectAndStoreTimezone = async () => {
      if (settings.timezone) return;

      try {
        const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const response = await fetch('/api/timezone', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ timezone: browserTimezone }),
        });

        if (response.ok) {
          setSettings({ ...settings, timezone: browserTimezone });
        }
      } catch (error) {
        console.debug('Timezone detection failed:', error);
      }
    };

    void detectAndStoreTimezone();
  }, [settings, setSettings]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void loadHistory();
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, [loadHistory]);

  const canSubmit = input.trim().length > 0;
  const inputPlaceholder = 'Ask about your ring, health data, or get support...';

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      setError(null);
      setIsWaitingForResponse(true);

      const userMessage: ChatBubble = {
        id: `user-${Date.now()}`,
        role: 'user',
        text: formatEscapeCharacters(trimmed),
      };
      setMessages(prev => [...prev, userMessage]);

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [{ role: 'user', content: trimmed }],
          }),
        });

        if (!(res.ok || res.status === 202)) {
          const detail = await res.text();
          throw new Error(detail || `Request failed (${res.status})`);
        }
      } catch (err: any) {
        console.error('Failed to send message', err);
        setError(err?.message || 'Failed to send message');
        setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
        setIsWaitingForResponse(false);
        throw err instanceof Error ? err : new Error('Failed to send message');
      } finally {
        let pollAttempts = 0;
        const maxPollAttempts = 30;

        const pollForAssistantResponse = async () => {
          pollAttempts++;

          try {
            const res = await fetch('/api/chat/history', { cache: 'no-store' });
            if (res.ok) {
              const data = await res.json();
              const currentMessages = toBubbles(data);

              const lastMessage = currentMessages[currentMessages.length - 1];
              const hasUserMessage = currentMessages.some(msg => msg.text === trimmed && msg.role === 'user');
              const hasAssistantResponse = lastMessage?.role === 'assistant' && hasUserMessage;

              if (hasAssistantResponse) {
                setMessages(currentMessages);
                setIsWaitingForResponse(false);
                return;
              }
            }
          } catch (err) {
            console.error('Error polling for response:', err);
          }

          if (pollAttempts < maxPollAttempts) {
            setTimeout(pollForAssistantResponse, 1000);
          } else {
            setIsWaitingForResponse(false);
            await loadHistory();
          }
        };

        setTimeout(pollForAssistantResponse, 1000);
      }
    },
    [loadHistory],
  );

  const handleClearHistory = useCallback(async () => {
    try {
      const res = await fetch('/api/chat/history', { method: 'DELETE' });
      if (!res.ok) {
        console.error('Failed to clear chat history', res.statusText);
        return;
      }
      setMessages([]);
    } catch (err) {
      console.error('Failed to clear chat history', err);
    }
  }, [setMessages]);

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;
    const value = input;
    setInput('');
    try {
      await sendMessage(value);
    } catch {
      setInput(value);
    }
  }, [canSubmit, input, sendMessage, setInput]);

  const handleInputChange = useCallback((value: string) => {
    setInput(value);
  }, [setInput]);

  const clearError = useCallback(() => setError(null), [setError]);

  const handleQuickAction = (action: string) => {
    setInput(action);
    setActiveTab('ai-support');
  };

  // Combined status from API and payload
  const displayStatus = useMemo(() => {
    const fromPayload = effectiveData;
    const fromApi = ringStatus;

    return {
      batteryTsSessions: fromPayload?.batteryTsSessionsStr || fromApi?.batteryTsSessions || 'N/A',
      ringSerialNumber: fromPayload?.ringSerialNumberStr || fromApi?.ringSerialNumber || 'N/A',
      batteryHealthScore: fromPayload?.batteryHealthScoreStr || fromApi?.batteryHealthScore || 'N/A',
      softReset: fromPayload?.softResetStr || fromApi?.softReset || 'N/A',
      factoryReset: fromPayload?.factoryResetStr || fromApi?.factoryReset || 'N/A',
      latestFirmwareAvailable: fromPayload?.latestFirmwareAvailableForUserStr || fromApi?.latestFirmwareAvailable || 'N/A',
      ringFirmwareVersion: fromPayload?.ringFirmwareVersionStr || fromApi?.ringFirmwareVersion || 'N/A',
      currentBatteryLevel: fromPayload?.currentBatteryLevelStr || fromApi?.currentBatteryLevel || 'N/A',
      connected: fromApi?.connected ?? true,
      lastUpdated: fromApi?.lastUpdated || new Date().toISOString(),
      deviceModel: fromPayload?.deviceModelStr || 'N/A',
      deviceOs: fromPayload?.deviceOsStr || 'N/A',
      appVersion: fromPayload?.appVersionStr || 'N/A',
      avgWearTime: fromPayload?.avgWearTimeStr || 'N/A',
      warrantyExpiry: fromPayload?.warrantyExpiryDateStr || 'N/A',
      daysUntilWarrantyExpiry: fromPayload?.daysUntilWarrantyExpiryStr || 'N/A',
      policyStatus: fromPayload?.policyStatusStr || 'N/A',
      replacementEligible: fromPayload?.replacementEligibleStr || 'N/A',
      replacementCount: fromPayload?.replacementCountStr || 'N/A',
      maxReplacements: fromPayload?.maxReplacementsStr || 'N/A',
      orderStatus: fromPayload?.latestOrderStatusStr || 'N/A',
      orderId: fromPayload?.latestOrderIdStr || 'N/A',
      userName: fromPayload?.nameStr || 'N/A',
      userEmail: fromPayload?.emailIdStr || fromPayload?.userEmail || 'N/A',
    };
  }, [effectiveData, ringStatus]);

  const ringStatusJson = {
    batteryTsSessions: displayStatus.batteryTsSessions,
    ringSerialNumber: displayStatus.ringSerialNumber,
    batteryHealthScore: displayStatus.batteryHealthScore,
    softReset: displayStatus.softReset,
    factoryReset: displayStatus.factoryReset,
    latestFirmwareAvailable: displayStatus.latestFirmwareAvailable,
    ringFirmwareVersion: displayStatus.ringFirmwareVersion,
    currentBatteryLevel: displayStatus.currentBatteryLevel,
    deviceModel: displayStatus.deviceModel,
    deviceOs: displayStatus.deviceOs,
    appVersion: displayStatus.appVersion,
    avgWearTime: displayStatus.avgWearTime,
    warrantyExpiry: displayStatus.warrantyExpiry,
    policyStatus: displayStatus.policyStatus,
    userName: displayStatus.userName,
    userEmail: displayStatus.userEmail,
  };

  const overrideCount = Object.keys(overrides.ringDebugOverrides).length +
    Object.keys(overrides.ringBatteryOverrides).length +
    Object.keys(overrides.kustomerOverrides).length;

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-black/80 backdrop-blur-xl">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-white/10 flex items-center justify-center ring-glow">
                <RingIcon className="h-4 w-4 text-white" />
              </div>
              <div>
                <h1 className="text-sm font-semibold text-white">Ultrahuman</h1>
                <p className="text-[10px] text-white/40">AI Support Chat</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {overrideCount > 0 && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-uh-warning/20 text-uh-warning border border-uh-warning/30">
                  {overrideCount} override{overrideCount > 1 ? 's' : ''} active
                </span>
              )}
              <button
                onClick={() => setHistoryOpen(true)}
                className="btn-icon"
                title="Support History"
              >
                <HistoryIcon />
              </button>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="btn-icon"
                title={sidebarOpen ? 'Hide Panel' : 'Show Panel'}
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <line x1="15" y1="3" x2="15" y2="21" />
                </svg>
              </button>
              <button
                onClick={() => setOpen(true)}
                className="btn-icon"
              >
                <SettingsIcon />
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="mt-4 flex gap-2">
            {[
              { id: 'ring-status' as TabType, label: 'Ring Status' },
              { id: 'ai-support' as TabType, label: 'AI Support' },
              { id: 'orders' as TabType, label: 'Orders' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`nav-tab ${activeTab === tab.id ? 'nav-tab-active' : ''}`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 flex gap-6">
        {/* Sidebar */}
        {sidebarOpen && (
          <aside className="w-96 flex-shrink-0">
            <div className="glass-card sticky top-32 max-h-[calc(100vh-160px)] overflow-hidden flex flex-col">
              {/* Sidebar Tabs */}
              <div className="flex border-b border-white/5">
                {[
                  { id: 'live' as SidebarTab, label: 'Live Stats' },
                  { id: 'payload' as SidebarTab, label: 'Payload' },
                  { id: 'overrides' as SidebarTab, label: 'Overrides' },
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setSidebarTab(tab.id)}
                    className={`flex-1 px-3 py-2.5 text-[11px] font-medium transition-colors ${
                      sidebarTab === tab.id
                        ? 'text-white bg-white/5 border-b-2 border-white'
                        : 'text-white/40 hover:text-white/60'
                    }`}
                  >
                    {tab.label}
                    {tab.id === 'overrides' && overrideCount > 0 && (
                      <span className="ml-1 text-uh-warning">({overrideCount})</span>
                    )}
                  </button>
                ))}
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                {/* Live Stats Tab */}
                {sidebarTab === 'live' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider">Ring Data</h3>
                      <div className="flex items-center gap-2">
                        {displayStatus.connected && (
                          <div className="flex items-center gap-1.5">
                            <div className="status-dot status-dot-success" />
                            <span className="text-[10px] text-white/40">Live</span>
                          </div>
                        )}
                        <button
                          onClick={() => loadRingStatus()}
                          className="btn-icon text-white/40 hover:text-white/60"
                          title="Refresh"
                        >
                          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M23 4v6h-6M1 20v-6h6" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </button>
                      </div>
                    </div>

                    {ringStatusLoading && !payloadData ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="h-5 w-5 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
                      </div>
                    ) : (
                      <pre className="text-[11px] text-white/70 font-mono bg-black/30 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap break-all">
{JSON.stringify(ringStatusJson, null, 2)}
                      </pre>
                    )}

                    {displayStatus.lastUpdated && (
                      <p className="mt-3 text-[10px] text-white/30 text-center" suppressHydrationWarning>
                        Last updated: {displayStatus.lastUpdated}
                      </p>
                    )}

                    {payloadData && (
                      <p className="mt-2 text-[10px] text-uh-success/60 text-center">
                        Data source: Yellow AI Payload
                      </p>
                    )}
                  </div>
                )}

                {/* Payload Tab */}
                {sidebarTab === 'payload' && (
                  <div>
                    <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-3">Yellow AI Payload</h3>

                    {yellowPayload ? (
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-[10px] text-uh-success">Payload loaded</span>
                          <button
                            onClick={handleClearPayload}
                            className="text-[10px] text-uh-error hover:text-uh-error/80"
                          >
                            Clear
                          </button>
                        </div>

                        {payloadData && (
                          <div className="space-y-2">
                            <p className="text-[10px] text-white/40 mb-2">Extracted payload fields:</p>
                            <pre className="text-[10px] text-white/60 font-mono bg-black/30 rounded-lg p-3 max-h-[300px] overflow-auto whitespace-pre-wrap break-all">
{JSON.stringify(payloadData, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        <p className="text-[11px] text-white/50 mb-3">
                          Paste Yellow AI response JSON to load user context data.
                        </p>
                        <textarea
                          className="w-full h-40 bg-black/30 border border-white/10 rounded-lg p-3 text-[11px] font-mono text-white/70 placeholder:text-white/30 resize-none focus:outline-none focus:border-white/30"
                          placeholder='Paste Yellow AI JSON here...'
                          value={payloadInput}
                          onChange={(e) => setPayloadInput(e.target.value)}
                        />
                        {payloadError && (
                          <p className="mt-2 text-[10px] text-uh-error">{payloadError}</p>
                        )}
                        <button
                          onClick={handleParsePayload}
                          disabled={!payloadInput.trim()}
                          className="mt-3 w-full btn text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Load Payload
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Overrides Tab */}
                {sidebarTab === 'overrides' && (
                  <div className="-m-4">
                    <OverridesPanel
                      overrides={overrides}
                      onOverridesChange={handleOverridesChange}
                      onSave={handleSaveOverrides}
                      saving={savingOverrides}
                    />
                  </div>
                )}
              </div>
            </div>
          </aside>
        )}

        {/* Main Content */}
        <div className={`flex-1 ${sidebarOpen ? '' : 'max-w-4xl mx-auto'}`}>
        {/* Ring Status Tab */}
        {activeTab === 'ring-status' && (
          <div className="space-y-6">
            {/* Ring Visual */}
            <div className="glass-card p-8 text-center">
              <div className="mx-auto mb-6 h-32 w-32 rounded-full bg-white/5 flex items-center justify-center ring-glow animate-float">
                <RingIcon className="h-16 w-16 text-white/80" />
              </div>
              <h2 className="text-xl font-semibold text-white">Ring AIR</h2>
              <p className="mt-1 text-sm text-white/50">{displayStatus.connected ? 'Connected' : 'Disconnected'}</p>
              <div className="mt-4 flex justify-center">
                <BatteryIcon percent={parseInt(displayStatus.currentBatteryLevel?.replace('%', '') || '0') || 0} />
              </div>
            </div>

            {/* Status Grid */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Connection', value: displayStatus.connected ? 'Active' : 'Inactive', status: displayStatus.connected ? 'success' : 'error' },
                { label: 'Battery', value: displayStatus.currentBatteryLevel, status: 'success' },
                { label: 'Health Score', value: displayStatus.batteryHealthScore, status: displayStatus.batteryHealthScore === 'Good' ? 'success' : displayStatus.batteryHealthScore === 'Bad' ? 'error' : 'warning' },
                { label: 'Firmware', value: displayStatus.ringFirmwareVersion, status: 'success' },
              ].map(item => (
                <div key={item.label} className="glass-card p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/40">{item.label}</span>
                    <div className={`status-dot status-dot-${item.status}`} />
                  </div>
                  <p className="mt-2 text-lg font-medium text-white">{item.value}</p>
                </div>
              ))}
            </div>

            {/* Quick Actions */}
            <div>
              <h3 className="mb-3 text-xs font-medium text-white/40 uppercase tracking-wider">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { icon: '🔋', label: 'Battery Issues', action: "I'm having battery issues with my ring" },
                  { icon: '📶', label: 'Connection Help', action: "My ring won't connect" },
                  { icon: '🔄', label: 'Sync Issues', action: 'My data is not syncing' },
                  { icon: '📦', label: 'Replacement', action: 'I need a replacement' },
                ].map(item => (
                  <button
                    key={item.label}
                    onClick={() => handleQuickAction(item.action)}
                    className="quick-action"
                  >
                    <span className="text-2xl">{item.icon}</span>
                    <span className="text-xs text-white/60">{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* AI Support Tab */}
        {activeTab === 'ai-support' && (
          <div className="flex flex-col h-[calc(100vh-160px)]">
            {/* Mini Status Bar */}
            <div className="glass-card mb-4 p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <div className="h-10 w-10 rounded-full bg-gradient-to-br from-white/10 to-white/5 flex items-center justify-center border border-white/10">
                    <RingIcon className="h-5 w-5 text-white/70" />
                  </div>
                  <div className={`absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-black ${displayStatus.connected ? 'bg-uh-success' : 'bg-uh-error'}`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">{displayStatus.userName !== 'N/A' ? displayStatus.userName : 'Ring AIR User'}</p>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-white/40">{displayStatus.connected ? 'Connected' : 'Disconnected'}</span>
                    {displayStatus.userEmail !== 'N/A' && (
                      <>
                        <span className="text-white/20">·</span>
                        <span className="text-xs text-white/30">{displayStatus.userEmail}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <BatteryIcon percent={parseInt(displayStatus.currentBatteryLevel?.replace('%', '') || '0') || 0} />
            </div>

            {/* Chat Container */}
            <div className="glass-card flex-1 flex flex-col overflow-hidden min-h-0">
              <ChatMessages
                messages={messages}
                isWaitingForResponse={isWaitingForResponse}
                scrollContainerRef={scrollContainerRef}
                onScroll={handleScroll}
                onQuickAction={(action) => {
                  setInput(action);
                  setTimeout(() => {
                    sendMessage(action);
                  }, 100);
                }}
              />

              {/* Input Area */}
              <div className="border-t border-white/5 p-4 bg-black/20">
                {error && <ErrorBanner message={error} onDismiss={clearError} />}
                <ChatInput
                  value={input}
                  canSubmit={canSubmit}
                  placeholder={inputPlaceholder}
                  onChange={handleInputChange}
                  onSubmit={handleSubmit}
                />
              </div>
            </div>

            {/* Clear Button */}
            <button
              onClick={handleClearHistory}
              className="mt-4 text-xs text-white/30 hover:text-white/50 transition-colors self-center flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              Clear conversation
            </button>
          </div>
        )}

        {/* Orders Tab */}
        {activeTab === 'orders' && (
          <div className="space-y-6">
            <div className="glass-card p-6">
              <h2 className="text-sm font-medium text-white/40 uppercase tracking-wider mb-4">Your Orders</h2>
              <div className="glass-card p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-xl bg-white/5 flex items-center justify-center">
                    <RingIcon className="h-6 w-6 text-white/60" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">Ultrahuman Ring AIR</p>
                    <p className="text-xs text-white/40">Order #{displayStatus.orderId !== 'N/A' ? displayStatus.orderId : 'UH-2024-1234'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`chip ${displayStatus.orderStatus === 'Delivered' ? 'text-uh-success border-uh-success/20' : displayStatus.orderStatus === 'Cancelled' ? 'text-uh-error border-uh-error/20' : 'text-uh-warning border-uh-warning/20'}`}>
                    {displayStatus.orderStatus !== 'N/A' ? displayStatus.orderStatus : 'Delivered'}
                  </span>
                  <p className="text-[10px] text-white/30 mt-1">{displayStatus.warrantyExpiry !== 'N/A' ? `Warranty: ${displayStatus.warrantyExpiry}` : 'Dec 15, 2024'}</p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="mb-3 text-xs font-medium text-white/40 uppercase tracking-wider">Need Help?</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { icon: '📦', label: 'Track Order', action: "What's my order status?" },
                  { icon: '📍', label: 'Update Address', action: 'I need to update my shipping address' },
                  { icon: '🛡️', label: 'Warranty', action: "What's my warranty status?" },
                  { icon: '🔄', label: 'Replacement', action: 'I need a replacement' },
                ].map(item => (
                  <button
                    key={item.label}
                    onClick={() => handleQuickAction(item.action)}
                    className="quick-action"
                  >
                    <span className="text-xl">{item.icon}</span>
                    <span className="text-xs text-white/60">{item.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
        </div>
      </div>

      <SettingsModal
        open={open}
        onClose={closeSettings}
        settings={settings}
        onSave={setSettings}
        userId={userId}
      />

      <SupportHistory
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        userId={userId}
      />
    </main>
  );
}
