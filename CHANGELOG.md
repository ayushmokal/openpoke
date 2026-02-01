# OpenPoke Support Automation - Change Log

---

## 2026-02-01: Battery Agent Training from 30-Day Historical Data

### Data Source
- **27,170 battery tickets** analyzed from Yellow AI database
- **Date range**: December 17, 2025 - January 15, 2026
- **Source files**: `yellow_bot_analysis.db`, `YELLOW_BOT_30DAY_ANALYSIS.md`

### Key Findings Incorporated

| Metric | Value | Implication |
|--------|-------|-------------|
| Battery repeat rate | **166%** | Users create 1.66 additional tickets after first |
| Same-day returns | **55%** | Troubleshooting often doesn't fix issue first time |
| Factory reset mentioned | **63%** | Most common resolution step |
| Replacement needed | **17%** | After troubleshooting exhausted |
| Battery + Connection combined | **24%** | Often co-occurring issues |

### Issue Type Distribution (from 27K tickets)
```
draining fast    █████████████████████████████████████ 86%
charging issues  ██ 1.1%
battery health   █ 0.9%
low battery      ▏ 0.2%
other           ████████████ 12%
```

### User Language Patterns Added
| What users say | Frequency |
|----------------|-----------|
| "draining" / "draining fast" | Most common |
| "dying" / "dies quickly" | Second most common |
| "not charging" / "won't charge" | Charging-specific |
| "stuck on charger" | Connection issue masquerading as battery |

### Changes Made

**Execution Agent (`system_prompt.md`):**
- Added Battery Support Knowledge section with real data
- Resolution step success rates from actual tickets
- Multi-issue handling guidance (battery + connection)
- User sentiment patterns (repeat users, warranty concerns)
- Clear criteria for when to recommend replacement

**Interaction Agent (`system_prompt.md`):**
- Added Battery Conversation Patterns section
- How users actually describe battery issues (with response styles)
- Repeat user handling (don't repeat steps already tried)
- Multi-issue handling flow
- Warranty anxiety reassurance patterns
- Follow-up vs new issue detection

### Expected Impact
Based on 30-day data analysis:
- Should reduce battery repeat rate from 166% toward target of <100%
- Better first-contact resolution by not skipping steps
- Proper handling of repeat users (acknowledge, don't repeat)
- Correct routing for follow-up questions vs new issues

---

## 2026-02-01: Fix Post-Reset Loop Bug

### Problem
After user completed factory reset and reported battery still bad, agent got stuck in a loop:
1. User: "done" (factory reset)
2. Agent: "How's battery now?"
3. User: "bad"
4. Agent: Re-runs battery troubleshoot → recommends factory reset again (payload not updated)
5. Loop continues...

### Root Cause
The Yellow AI payload doesn't update immediately after user performs reset. So `factoryReset: "N/A"` even though user just did it.

### Fix
Added to interaction agent system prompt:
- **Post-Reset Conversation Flow** section
- When user confirms reset done AND reports battery still bad → skip re-running troubleshoot
- Move directly to replacement recommendation
- Don't loop on "Hang on, checking..."

### Correct Flow Now
```
Agent: "Do a factory reset"
User: "done"
Agent: "How's the battery now?"
User: "bad" / "still draining" / "same"
Agent: "Since you've done the factory reset and battery is still not right, let's get you a replacement. You're within warranty."
```

---

## 2026-02-01: Conversational & Sentiment-Aware Interaction Agent

### Problem
Agent responses were too robotic and corporate. Didn't acknowledge user frustration or match their conversational style.

### Fix
Complete rewrite of `server/agents/interaction_agent/system_prompt.md` with:

**Sentiment Detection:**
| User Mood | Agent Response |
|-----------|----------------|
| Frustrated ("ugh", "again") | Acknowledge first: "That's frustrating. Let me check..." |
| Confused ("what is", "how do I") | Be patient, explain simply |
| Casual ("hey", "thanks") | Match their vibe, keep it brief |
| Worried ("is this covered??") | Be reassuring but honest |

**Conversation Flow:**
- DON'T: "I will now proceed to check your battery status"
- DO: "Let me check that" / "One sec, pulling up your info"

**Presenting Results:**
- DON'T: "I have completed my analysis and found that..."
- DO: "So your battery health is Moderate, and..."

**Natural Translations:**
| Technical Result | Human Response |
|-----------------|----------------|
| BDR normal | "Good news - your battery's actually looking fine" |
| App outdated | "Looks like your app's a version behind - updating usually helps" |
| Recommend Chill Mode | "Have you tried Chill Mode? It can stretch battery by like 35%" |
| Recommend soft reset | "Let's try a soft reset - it's like rebooting your phone" |
| Recommend replacement | "I think it's time for a replacement. You're within warranty" |

**Personality:**
- Warm but not fake
- Casual but competent
- Empathetic but efficient
- "You're a friend who happens to be really good at Ultrahuman support"

---

## 2026-02-01: Rewrite Battery Troubleshooting Flow

### Problem
Battery troubleshooting was not following the exact decision tree flowchart. Agent was showing "issue retrieving battery information" instead of using payload data.

### Fix
Complete rewrite of `server/agents/execution_agent/tools/ultrahuman/battery.py` to follow exact flowchart:

```
User: "Battery is draining really fast"
         │
         ▼
1. Check App Version
   - Outdated? → "Update to latest app" → EXIT
   - Latest? → Continue
         │
         ▼
2. Check BDR Status
   - ≤1.4 (normal)? → "Battery within expected range" + tips → EXIT
   - >1.4 (high)? → Continue troubleshooting
   - Calibrating/N/A? → Continue with fallback
         │
         ▼
3. Check Firmware Version
   - Outdated? → "Update firmware" → EXIT
   - Latest? → Continue
         │
         ▼
4. Check CDT Usage (Workout/Breathwork)
   - High usage? → Note it affects battery
         │
         ▼
5. Check Chill Mode
   - Inactive + high BDR? → "Enable Chill Mode" → EXIT
   - Active? → Continue
         │
         ▼
6. Check Soft Reset
   - Not done? → "Initiate soft reset" → EXIT
   - Done <24hrs ago? → "Monitor for 24hrs" → EXIT
   - Done >24hrs ago? → Continue
         │
         ▼
7. Check Factory Reset
   - Not done? → "Initiate factory reset" → EXIT
   - Done <24hrs ago? → "Monitor for 24hrs" → EXIT
   - Done >24hrs ago? → Continue
         │
         ▼
8. All Exhausted → Recommend Replacement
   - Within policy? → "Request replacement"
   - Outside policy? → "Wabi-Sabi replacement"
```

### Key Improvements
- Added `_get_ctx_value()` helper to read payload keys with/without "Str" suffix
- Proper date parsing for soft/factory reset dates
- 24-hour monitoring period check after resets
- Conversational messages matching flowchart exactly
- Returns structured JSON with `message`, `recommendation`, `next_action`

---

## 2026-02-01: Block Internal Error Messages to User

### Problem
Agent was telling user about internal issues like "authorization issues and Gmail connection" which exposes backend problems.

### Fix
Added explicit "NEVER SAY THESE TO THE USER" blocklist to both system prompts:
- "authorization issues"
- "API issues"
- "Gmail connection"
- "having trouble accessing"
- Any technical/backend problem mentions

---

## 2026-02-01: Fix React Hydration Error

### Problem
Next.js hydration error: "Text content does not match server-rendered HTML" caused by timestamp mismatch between server and client render.

### Fix
Added `suppressHydrationWarning` to the "Last updated" timestamp display in `web/app/page.tsx:708`. This is the standard fix for dynamic timestamps that inherently can't match between server and client renders.

---

## 2026-02-01: Fix FAQ Asking for Email

### Problem
Agent was asking for email after successfully answering FAQ questions like "can I wear ring air to swimming". FAQ search is local - no email needed.

### Fix
- Added "CRITICAL - FAQ DOES NOT NEED EMAIL" to execution agent
- Added "NEVER ask for email for FAQ questions" to interaction agent
- FAQ questions should return answer and stop, not call API tools

---

## 2026-02-01: Fix Premature Replacement Routing

### Problem
Agent was jumping straight to "I'll create a replacement request" for sizing issues like "my ring is too loose" instead of:
1. First searching FAQ for sizing guidance
2. Asking user what they want (tips vs exchange)

### Fix
Updated routing guidelines in both system prompts:

**Interaction Agent:**
- Added "CRITICAL FOR SIZING ISSUES" section
- Added "CRITICAL - DO NOT JUMP TO REPLACEMENTS" section
- Sizing issues now route to FAQ first, then ask user intent

**Execution Agent:**
- Added "CRITICAL - DO NOT CREATE REPLACEMENTS FOR" section
- Sizing, fit issues must search FAQ first
- Only create replacement when explicitly told by Poke

### Correct Flow Now
```
User: "my ring is too loose"
         │
         ▼
1. Search FAQ for sizing guidance
         │
         ▼
2. Ask user: "Would you like sizing tips, or are you looking to exchange for a different size?"
         │
         ▼
3. Only proceed with exchange if user confirms
```

---

## 2026-02-01: Smart FAQ Agent & Knowledge Base Search

### Summary
Added intelligent FAQ search agent with advanced NLP features that queries the UH-CXbible knowledge base. Uses TF-IDF ranking, synonym expansion, and section-aware search for accurate answers.

### New Files

| File | Purpose |
|------|---------|
| `server/agents/execution_agent/tools/faq_search.py` | Smart FAQ search with TF-IDF, synonyms, indexing |
| `server/agents/execution_agent/tools/faq_tools.py` | FAQ tool wrapper with logging |

### Modified Files

| File | Changes |
|------|---------|
| `server/agents/execution_agent/tools/registry.py` | Added faq_tools to schemas and registry |
| `server/agents/execution_agent/system_prompt.md` | Added FAQ tools documentation |
| `server/agents/interaction_agent/system_prompt.md` | Added FAQ routing guidelines |

### Smart Search Features

| Feature | Description |
|---------|-------------|
| **Pre-indexed Content** | `FAQIndex` class builds inverted index on startup for O(1) lookups |
| **TF-IDF Ranking** | Documents scored by term frequency × inverse document frequency |
| **Synonym Expansion** | "battery" → power, charge, drain, dying, dead |
| **Section-Aware Search** | `SmartHTMLParser` extracts h1-h6 sections from HTML |
| **Category Classification** | Auto-tags queries: battery, sizing, connectivity, warranty, etc. |
| **Context Snippets** | Extracts most relevant 300-char snippet around matches |

### Synonym Mappings

```python
SYNONYMS = {
    "battery": ["power", "charge", "charging", "drain", "draining", "dying", "dead"],
    "size": ["sizing", "fit", "fitting", "measurement", "dimensions"],
    "replace": ["replacement", "exchange", "swap", "new ring"],
    "connect": ["connection", "connectivity", "sync", "syncing", "pairing", "bluetooth"],
    "warranty": ["guarantee", "coverage", "policy", "protection"],
    "broken": ["damaged", "cracked", "defective", "faulty", "not working"],
    "sleep": ["sleeping", "rest", "bedtime", "night"],
    "heart": ["hr", "heart rate", "pulse", "bpm"],
    "hrv": ["heart rate variability", "variability"],
    "water": ["waterproof", "swimming", "shower", "wet"],
    "firmware": ["update", "software update", "version"],
    "reset": ["restart", "reboot", "factory reset", "soft reset"],
}
```

### FAQ Tool Usage

```
User: "What sizes does the ring come in?"
         │
         ▼
Interaction Agent → creates "FAQ Search" agent
         │
         ▼
Execution Agent calls faq_search(query="ring sizes")
         │
         ▼
FAQIndex.search() runs:
  1. Tokenize query → ["ring", "sizes"]
  2. Expand with synonyms → {"ring", "sizes", "sizing", "fit", "measurement", ...}
  3. Query inverted index → find matching doc_ids
  4. Score with TF-IDF → rank by relevance
  5. Extract best sections → get snippets
         │
         ▼
Returns ranked results with snippets and categories
```

### Available Tools

| Tool | Purpose |
|------|---------|
| `faq_search(query)` | Smart search with ranking and snippets |
| `faq_get_topics()` | List all indexed topics and categories |
| `faq_answer(question)` | Direct answer with confidence score |

### Available FAQ Topics
- Ring AIR (features, specs, hardware)
- Blood Vision
- M1 Sensor
- Ultrahuman Home
- Powerplug
- UltrahumanX
- Misc support docs

---

## 2026-02-01: Battery Troubleshooting & Context System

### Summary
Implemented context-based battery troubleshooting flow that uses Yellow AI payload data instead of API calls (which return 401 Unauthorized).

---

### New Files Created

| File | Purpose |
|------|---------|
| `server/agents/execution_agent/tools/ultrahuman/context.py` | Context store for Yellow AI payload data |
| `server/routes/context.py` | API endpoints for setting/getting/clearing user context |
| `web/app/api/context/set/route.ts` | Next.js proxy for context set endpoint |
| `web/app/api/context/get/route.ts` | Next.js proxy for context get endpoint |
| `web/app/api/context/clear/route.ts` | Next.js proxy for context clear endpoint |

---

### Modified Files

#### Backend

| File | Changes |
|------|---------|
| `server/agents/execution_agent/tools/ultrahuman/__init__.py` | Added exports for `ultrahuman_battery_troubleshoot` and all context functions |
| `server/agents/execution_agent/tools/ultrahuman/battery.py` | - Added `ultrahuman_battery_troubleshoot` tool with full decision tree<br>- Tools now check `has_context()` first, fallback to API<br>- Added context-first data retrieval |
| `server/routes/__init__.py` | Registered context router |
| `server/services/conversation/log.py` | - Added deduplication in `to_chat_messages()`<br>- Strengthened `record_reply()` deduplication |
| `server/agents/execution_agent/system_prompt.md` | - Added `ultrahuman_battery_troubleshoot` tool docs<br>- Emphasized: NO email needed for battery issues |
| `server/agents/interaction_agent/system_prompt.md` | - Updated routing guidelines<br>- Battery issues: don't ask for email, use troubleshoot tool |

#### Frontend

| File | Changes |
|------|---------|
| `web/app/page.tsx` | - Added `syncContextToBackend()` function<br>- Added `clearContextOnBackend()` function<br>- Added useEffect to sync context on payload/override changes<br>- Added deduplication in `toBubbles()`<br>- Added console logging for debugging |
| `web/app/globals.css` | Added `status-dot-error` CSS class |

---

### Architecture: Battery Troubleshooting Flow

```
User loads Yellow AI payload in UI
         │
         ▼
Frontend syncs to /api/v1/context/set
         │
         ▼
Context store populated (server memory)
         │
         ▼
User asks: "my battery is draining"
         │
         ▼
Interaction Agent → creates Battery Support agent
         │
         ▼
Execution Agent calls ultrahuman_battery_troubleshoot()
         │
         ▼
Tool checks has_context() → TRUE → uses cached data
         │
         ▼
Decision tree runs:
  1. Check BDR (≤1.4 normal, >1.4 high)
  2. Check app version (latest?)
  3. Check firmware version (latest?)
  4. Check CDT usage (workout/breathwork events)
  5. Check Chill Mode (active?)
  6. Check reset history (soft/hard done?)
         │
         ▼
Returns recommendations + next_action
```

---

### Context Store Keys

From Yellow AI payload:

| Key | Description |
|-----|-------------|
| `batteryHealthScoreStr` | Battery health: Good/Moderate/Bad |
| `bdrValueStr` | Battery Drain Rate value |
| `currentBatteryLevelStr` | Current battery % |
| `softResetStr` | Last soft reset date |
| `factoryResetStr` | Last factory reset date |
| `ringFirmwareVersionStr` | Current firmware |
| `latestFirmwareAvailableForUserStr` | Latest firmware available |
| `appVersionStr` | Current app version |
| `latestAvailableAppVersionStr` | Latest app version |
| `ringSerialNumberStr` | Ring serial number |
| `warrantyExpiryDateStr` | Warranty expiry |
| `replacementEligibleStr` | Replacement eligibility |

---

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/context/set` | POST | Set user context from payload |
| `/api/v1/context/get` | GET | Get current context |
| `/api/v1/context/clear` | POST | Clear context |

---

### Issues Fixed

1. **401 Unauthorized from Ultrahuman API** → Use context data instead
2. **Duplicate chat messages** → Added deduplication in frontend and backend
3. **Agent asking for email for battery issues** → Updated prompts to use context
4. **Agent mentioning authorization issues** → Updated prompts to hide internal errors

---

### Pending / Known Issues

- [ ] Server must be restarted after code changes for routes to load
- [ ] Context is stored in memory (lost on server restart)
- [ ] Battery % shows 0% when `currentBatteryLevelStr` is N/A in payload

---

### How to Test

1. Start Python server: `python3 -c "from server.server import main; main()"`
2. Load Yellow AI payload in UI (Payload tab)
3. Check browser console for `[Context Sync] Success`
4. Check server logs for `Context set successfully`
5. Ask: "my battery is draining" → should use cached data, no email asked
