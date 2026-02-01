"use client";

import { useState, useCallback } from 'react';

// Ring Debug Info keys with examples
const RING_DEBUG_INFO_KEYS = [
  { key: 'soft_reset_done', type: 'boolean', desc: 'Soft reset done status', example: 'true/false' },
  { key: 'hard_reset_done', type: 'boolean', desc: 'Hard reset done status', example: 'true/false' },
  { key: 'soft_reset_date', type: 'string', desc: 'Soft reset date', example: 'January 15, 2026 14:30' },
  { key: 'hard_reset_date', type: 'string', desc: 'Hard reset date', example: 'January 15, 2026 14:30' },
];

// Ring Battery Info keys with examples
const RING_BATTERY_INFO_KEYS = [
  { key: 'battery_life_at_current_bdr', type: 'number', desc: 'Battery life in days at current BDR', example: '4.5' },
  { key: 'last_48_hours_bdr_chill_mode', type: 'number', desc: 'Battery life with chill mode (48hrs)', example: '5.2' },
  { key: 'chill_mode_active', type: 'boolean', desc: 'Chill/passive mode active', example: 'true/false' },
  { key: 'chill_mode_last_activated_at', type: 'string', desc: 'Chill mode activated timestamp', example: '2026-01-15T14:30:00Z' },
  { key: 'cdt_events_count_last_3_days', type: 'number', desc: 'CDT events (workouts) in 3 days', example: '5' },
];

// All Kustomer Info keys with examples (from Yellow AI Test Dashboard)
const KUSTOMER_INFO_KEYS = [
  { key: 'ringSerialNumberStr', example: 'RA-CH2-DTF-WB-AG10-123456', desc: 'Ring serial number' },
  { key: 'ringDescriptionStr', example: 'Size: 8, Color: Matte Grey', desc: 'Ring details' },
  { key: 'deviceModelStr', example: 'iPhone 14 Pro', desc: 'Device model' },
  { key: 'deviceOsStr', example: 'iOS 17.0', desc: 'Device OS' },
  { key: 'ringFirmwareVersionStr', example: '1.2.3', desc: 'Ring firmware version' },
  { key: 'uhXUserStr', example: 'true', desc: 'UHX subscription status' },
  { key: 'vipUserStr', example: 'false', desc: 'VIP user status' },
  { key: 'latestAvailableAppVersionStr', example: '3.5.0', desc: 'Latest app version available' },
  { key: 'dataSharingStr', example: 'true', desc: 'Coach data sharing consent' },
  { key: 'm1First24HrsStr', example: 'False', desc: 'M1 CGM in warmup phase' },
  { key: 'ringConnectedLast24HrsStr', example: 'True', desc: 'Ring connected in last 24 hrs' },
  { key: 'noOfDaysSinceRingActivationStr', example: '45', desc: 'Days since ring activation' },
  { key: 'lastRingStatesTimestampStr', example: 'January 15, 2026 14:30', desc: 'Last ring states timestamp' },
  { key: 'softResetStr', example: 'January 15, 2026 14:30', desc: 'Last soft reset date' },
  { key: 'factoryResetStr', example: 'January 15, 2026 14:30', desc: 'Last factory reset date' },
  { key: 'last100ChargedStr', example: 'January 15, 2026 14:30', desc: 'Last time at 100%' },
  { key: 'appVersionStr', example: 'iOS 3.4.2', desc: 'Current app version' },
  { key: 'batteryTsSessionsStr', example: 'Completed at January 15, 2026', desc: 'Battery TS sessions' },
  { key: 'latestFirmwareAvailableForUserStr', example: '1.3.0', desc: 'Latest firmware available' },
  { key: 'policyStatusStr', example: 'Within Policy', desc: 'Replacement policy status' },
  { key: 'ringState10Str', example: 'false', desc: 'Ring state 10 detected' },
  { key: 'faultyHrStr', example: 'false', desc: 'Faulty HR sensor detected' },
  { key: 'uhxPlanNameStr', example: '1yr (new)', desc: 'UHX plan name' },
  { key: 'uhxExpiryStr', example: 'January 15, 2027', desc: 'UHX expiry date' },
  { key: 'uhxCountryStr', example: 'IN', desc: 'UHX subscription country' },
  { key: 'bdrTriggeredStr', example: 'true', desc: 'BDR triggered/in progress' },
  { key: 'bdrCompletedStr', example: 'false', desc: 'BDR completed' },
  { key: 'bdrValueStr', example: 'improving', desc: 'BDR trend' },
  { key: 'daysSinceBdrStr', example: '5', desc: 'Days since BDR started' },
  { key: 'bdrTimeLeftStr', example: '2d 5h 30m', desc: 'BDR time remaining' },
  { key: 'currentBatteryLevelStr', example: '85%', desc: 'Current battery level' },
  { key: 'avgWearTimeStr', example: '18 hrs/day', desc: 'Average wear time' },
  { key: 'batteryHealthScoreStr', example: 'Good', desc: 'Battery health score' },
  { key: 'replacementEligibleStr', example: 'true', desc: 'Replacement eligible' },
  { key: 'replacementCountStr', example: '1', desc: 'Number of replacements' },
  { key: 'maxReplacementsStr', example: '3', desc: 'Max replacements allowed' },
  { key: 'warrantyExpiryDateStr', example: 'January 15, 2027', desc: 'Warranty expiry date' },
  { key: 'daysUntilWarrantyExpiryStr', example: '180', desc: 'Days until warranty expires' },
  { key: 'wabiSabiReplacementCountStr', example: '1 / 3', desc: 'Wabi Sabi replacements' },
  { key: 'latestOrderIdStr', example: 'ORD-123456', desc: 'Latest order ID' },
  { key: 'latestOrderStatusStr', example: 'Shipped', desc: 'Order status' },
  { key: 'trackingUrlStr', example: 'https://track.example.com/...', desc: 'Tracking URL' },
  { key: 'orderSourceStr', example: 'shopify', desc: 'Order source' },
  { key: 'orderDateStr', example: 'January 15, 2026', desc: 'Order date' },
  { key: 'shippingAddressStr', example: '123 Main St, City', desc: 'Shipping address' },
  { key: 'shippingCountryStr', example: 'India', desc: 'Shipping country' },
  { key: 'emailIdStr', example: 'user@email.com', desc: 'User email' },
  { key: 'nameStr', example: 'John Doe', desc: 'User name' },
];

export type Overrides = {
  ringDebugOverrides: Record<string, any>;
  ringBatteryOverrides: Record<string, any>;
  kustomerOverrides: Record<string, any>;
  overridesEnabled: boolean;
};

interface OverridesPanelProps {
  overrides: Overrides;
  onOverridesChange: (overrides: Overrides) => void;
  onSave: () => Promise<void>;
  saving?: boolean;
}

type Section = 'debug' | 'battery' | 'kustomer';

export default function OverridesPanel({ overrides, onOverridesChange, onSave, saving }: OverridesPanelProps) {
  const [expandedSection, setExpandedSection] = useState<Section | null>('kustomer');
  const [searchQuery, setSearchQuery] = useState('');

  const handleSetOverride = useCallback((type: Section, key: string, value: any) => {
    const newOverrides = { ...overrides };
    if (type === 'debug') {
      newOverrides.ringDebugOverrides = { ...overrides.ringDebugOverrides, [key]: value };
    } else if (type === 'battery') {
      newOverrides.ringBatteryOverrides = { ...overrides.ringBatteryOverrides, [key]: value };
    } else {
      newOverrides.kustomerOverrides = { ...overrides.kustomerOverrides, [key]: value };
    }
    onOverridesChange(newOverrides);
  }, [overrides, onOverridesChange]);

  const handleClearOverride = useCallback((type: Section, key: string) => {
    const newOverrides = { ...overrides };
    if (type === 'debug') {
      const next = { ...overrides.ringDebugOverrides };
      delete next[key];
      newOverrides.ringDebugOverrides = next;
    } else if (type === 'battery') {
      const next = { ...overrides.ringBatteryOverrides };
      delete next[key];
      newOverrides.ringBatteryOverrides = next;
    } else {
      const next = { ...overrides.kustomerOverrides };
      delete next[key];
      newOverrides.kustomerOverrides = next;
    }
    onOverridesChange(newOverrides);
  }, [overrides, onOverridesChange]);

  const handleClearAll = useCallback((type: Section) => {
    const newOverrides = { ...overrides };
    if (type === 'debug') newOverrides.ringDebugOverrides = {};
    else if (type === 'battery') newOverrides.ringBatteryOverrides = {};
    else newOverrides.kustomerOverrides = {};
    onOverridesChange(newOverrides);
  }, [overrides, onOverridesChange]);

  const filteredKustomerKeys = KUSTOMER_INFO_KEYS.filter(item =>
    searchQuery === '' ||
    item.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.desc.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const overrideCount =
    Object.keys(overrides.ringDebugOverrides).length +
    Object.keys(overrides.ringBatteryOverrides).length +
    Object.keys(overrides.kustomerOverrides).length;

  const renderBooleanField = (type: Section, key: string, currentValue: any) => (
    <select
      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 focus:border-white/30 focus:outline-none"
      value={currentValue ?? ''}
      onChange={(e) => handleSetOverride(type, key, e.target.value === '' ? undefined : e.target.value === 'true')}
    >
      <option value="">Not Set</option>
      <option value="true">true</option>
      <option value="false">false</option>
    </select>
  );

  const renderStringField = (type: Section, key: string, currentValue: any, placeholder: string) => (
    <input
      type="text"
      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 placeholder:text-white/30 focus:border-white/30 focus:outline-none"
      placeholder={placeholder}
      value={currentValue ?? ''}
      onChange={(e) => handleSetOverride(type, key, e.target.value || undefined)}
    />
  );

  const renderNumberField = (type: Section, key: string, currentValue: any, placeholder: string) => (
    <input
      type="number"
      step="0.1"
      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 placeholder:text-white/30 focus:border-white/30 focus:outline-none"
      placeholder={placeholder}
      value={currentValue ?? ''}
      onChange={(e) => handleSetOverride(type, key, e.target.value ? Number(e.target.value) : undefined)}
    />
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-white/5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-medium text-white uppercase tracking-wider">Overrides</h3>
            {overrideCount > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-uh-warning/20 text-uh-warning">
                {overrideCount} active
              </span>
            )}
          </div>
          <button
            onClick={() => onOverridesChange({ ...overrides, overridesEnabled: !overrides.overridesEnabled })}
            className={`w-9 h-5 rounded-full transition-colors ${
              overrides.overridesEnabled ? 'bg-uh-success' : 'bg-white/20'
            }`}
          >
            <div className={`w-4 h-4 rounded-full bg-white transition-transform ${
              overrides.overridesEnabled ? 'translate-x-4' : 'translate-x-0.5'
            }`} />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            className="w-full bg-black/40 border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-white/80 placeholder:text-white/30 focus:border-white/30 focus:outline-none"
            placeholder="Search overrides..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Sections */}
      <div className="flex-1 overflow-y-auto">
        {/* Ring Debug Info */}
        <div className="border-b border-white/5">
          <button
            onClick={() => setExpandedSection(expandedSection === 'debug' ? null : 'debug')}
            className="w-full p-3 flex items-center justify-between hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-white/60">Ring Debug Info</span>
              {Object.keys(overrides.ringDebugOverrides).length > 0 && (
                <span className="text-[9px] px-1 py-0.5 rounded bg-white/10 text-white/50">
                  {Object.keys(overrides.ringDebugOverrides).length}
                </span>
              )}
            </div>
            <svg className={`w-3.5 h-3.5 text-white/40 transition-transform ${expandedSection === 'debug' ? 'rotate-180' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>

          {expandedSection === 'debug' && (
            <div className="px-3 pb-3 space-y-2">
              {Object.keys(overrides.ringDebugOverrides).length > 0 && (
                <button
                  onClick={() => handleClearAll('debug')}
                  className="text-[10px] text-uh-error hover:text-uh-error/80"
                >
                  Clear All
                </button>
              )}
              {RING_DEBUG_INFO_KEYS.map(({ key, type, desc, example }) => {
                const isSet = overrides.ringDebugOverrides[key] !== undefined;
                return (
                  <div key={key} className={`p-2.5 rounded-lg ${isSet ? 'bg-uh-warning/10 border border-uh-warning/20' : 'bg-black/20'}`}>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-mono text-white/70">{key}</span>
                      {isSet && (
                        <button onClick={() => handleClearOverride('debug', key)} className="text-[9px] text-uh-error">
                          Clear
                        </button>
                      )}
                    </div>
                    <p className="text-[9px] text-white/40 mb-1.5">{desc}</p>
                    {type === 'boolean' ? (
                      renderBooleanField('debug', key, overrides.ringDebugOverrides[key])
                    ) : (
                      renderStringField('debug', key, overrides.ringDebugOverrides[key], `e.g., ${example}`)
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Ring Battery Info */}
        <div className="border-b border-white/5">
          <button
            onClick={() => setExpandedSection(expandedSection === 'battery' ? null : 'battery')}
            className="w-full p-3 flex items-center justify-between hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-white/60">Ring Battery Info</span>
              {Object.keys(overrides.ringBatteryOverrides).length > 0 && (
                <span className="text-[9px] px-1 py-0.5 rounded bg-white/10 text-white/50">
                  {Object.keys(overrides.ringBatteryOverrides).length}
                </span>
              )}
            </div>
            <svg className={`w-3.5 h-3.5 text-white/40 transition-transform ${expandedSection === 'battery' ? 'rotate-180' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>

          {expandedSection === 'battery' && (
            <div className="px-3 pb-3 space-y-2">
              {Object.keys(overrides.ringBatteryOverrides).length > 0 && (
                <button
                  onClick={() => handleClearAll('battery')}
                  className="text-[10px] text-uh-error hover:text-uh-error/80"
                >
                  Clear All
                </button>
              )}
              {RING_BATTERY_INFO_KEYS.map(({ key, type, desc, example }) => {
                const isSet = overrides.ringBatteryOverrides[key] !== undefined;
                return (
                  <div key={key} className={`p-2.5 rounded-lg ${isSet ? 'bg-uh-warning/10 border border-uh-warning/20' : 'bg-black/20'}`}>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-mono text-white/70">{key}</span>
                      {isSet && (
                        <button onClick={() => handleClearOverride('battery', key)} className="text-[9px] text-uh-error">
                          Clear
                        </button>
                      )}
                    </div>
                    <p className="text-[9px] text-white/40 mb-1.5">{desc}</p>
                    {type === 'boolean' ? (
                      renderBooleanField('battery', key, overrides.ringBatteryOverrides[key])
                    ) : type === 'number' ? (
                      renderNumberField('battery', key, overrides.ringBatteryOverrides[key], `e.g., ${example}`)
                    ) : (
                      renderStringField('battery', key, overrides.ringBatteryOverrides[key], `e.g., ${example}`)
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Kustomer Info */}
        <div>
          <button
            onClick={() => setExpandedSection(expandedSection === 'kustomer' ? null : 'kustomer')}
            className="w-full p-3 flex items-center justify-between hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-white/60">Kustomer Info</span>
              {Object.keys(overrides.kustomerOverrides).length > 0 && (
                <span className="text-[9px] px-1 py-0.5 rounded bg-white/10 text-white/50">
                  {Object.keys(overrides.kustomerOverrides).length}
                </span>
              )}
            </div>
            <svg className={`w-3.5 h-3.5 text-white/40 transition-transform ${expandedSection === 'kustomer' ? 'rotate-180' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>

          {expandedSection === 'kustomer' && (
            <div className="px-3 pb-3 space-y-2">
              {/* Active Overrides Summary */}
              {Object.keys(overrides.kustomerOverrides).length > 0 && (
                <div className="p-2 bg-uh-warning/10 border border-uh-warning/20 rounded-lg mb-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] text-uh-warning font-medium">Active Overrides</span>
                    <button
                      onClick={() => handleClearAll('kustomer')}
                      className="text-[9px] text-uh-error hover:text-uh-error/80"
                    >
                      Clear All
                    </button>
                  </div>
                  <div className="space-y-1">
                    {Object.entries(overrides.kustomerOverrides).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between text-[10px]">
                        <span className="font-mono text-white/60">{key}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-white/80 truncate max-w-[100px]">{String(value)}</span>
                          <button onClick={() => handleClearOverride('kustomer', key)} className="text-uh-error">×</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* All Keys */}
              {filteredKustomerKeys.map(({ key, desc, example }) => {
                const isSet = overrides.kustomerOverrides[key] !== undefined;
                if (isSet) return null; // Already shown in active overrides
                return (
                  <div key={key} className="p-2.5 rounded-lg bg-black/20 hover:bg-black/30 transition-colors">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-mono text-white/70">{key}</span>
                    </div>
                    <p className="text-[9px] text-white/40 mb-1.5">{desc}</p>
                    <input
                      type="text"
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 placeholder:text-white/30 focus:border-white/30 focus:outline-none"
                      placeholder={`e.g., ${example}`}
                      onBlur={(e) => {
                        if (e.target.value) {
                          handleSetOverride('kustomer', key, e.target.value);
                          e.target.value = '';
                        }
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && (e.target as HTMLInputElement).value) {
                          handleSetOverride('kustomer', key, (e.target as HTMLInputElement).value);
                          (e.target as HTMLInputElement).value = '';
                        }
                      }}
                    />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Save Button */}
      <div className="p-3 border-t border-white/5">
        <button
          onClick={onSave}
          disabled={saving}
          className="w-full btn text-xs"
        >
          {saving ? 'Saving...' : 'Save Overrides'}
        </button>
      </div>
    </div>
  );
}
