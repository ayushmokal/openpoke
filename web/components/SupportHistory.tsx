"use client";

import { useCallback, useEffect, useState } from 'react';

interface Session {
  id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  summary?: string;
  preview?: string;
}

interface Message {
  role: string;
  content: string;
  timestamp?: string;
}

interface SupportHistoryProps {
  open: boolean;
  onClose: () => void;
  userId: string;
  onRestoreSession?: (sessionId: string) => void;
}

export default function SupportHistory({ open, onClose, userId, onRestoreSession }: SupportHistoryProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [sessionMessages, setSessionMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  const loadSessions = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/sessions', {
        headers: { 'x-user-id': userId },
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const loadSessionMessages = useCallback(async (sessionId: string) => {
    try {
      setLoadingMessages(true);
      const res = await fetch(`/api/sessions/${sessionId}`, {
        headers: { 'x-user-id': userId },
      });
      if (res.ok) {
        const data = await res.json();
        setSessionMessages(data.session?.messages || []);
      }
    } catch (err) {
      console.error('Failed to load session messages:', err);
    } finally {
      setLoadingMessages(false);
    }
  }, [userId]);

  const handleDeleteSession = useCallback(async (sessionId: string) => {
    if (!confirm('Delete this conversation? This cannot be undone.')) return;

    try {
      const res = await fetch(`/api/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { 'x-user-id': userId },
      });
      if (res.ok) {
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        if (selectedSession?.id === sessionId) {
          setSelectedSession(null);
          setSessionMessages([]);
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  }, [userId, selectedSession]);

  useEffect(() => {
    if (open) {
      loadSessions();
    }
  }, [open, loadSessions]);

  useEffect(() => {
    if (selectedSession) {
      loadSessionMessages(selectedSession.id);
    }
  }, [selectedSession, loadSessionMessages]);

  if (!open) return null;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return `Today at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else if (diffDays === 1) {
      return `Yesterday at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="glass-card w-full max-w-4xl h-[80vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <div>
            <h2 className="text-base font-medium text-white">Support History</h2>
            <p className="text-xs text-white/40 mt-0.5">View and manage past conversations</p>
          </div>
          <button onClick={onClose} className="btn-icon" aria-label="Close">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" strokeLinecap="round" strokeLinejoin="round" />
              <line x1="6" y1="6" x2="18" y2="18" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Sessions List */}
          <div className="w-72 border-r border-white/5 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="h-5 w-5 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
              </div>
            ) : sessions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                <svg className="h-12 w-12 text-white/20 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <p className="text-sm text-white/40">No past conversations</p>
                <p className="text-xs text-white/30 mt-1">Your support history will appear here</p>
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {sessions.map(session => (
                  <button
                    key={session.id}
                    onClick={() => setSelectedSession(session)}
                    className={`w-full p-3 text-left transition-colors ${
                      selectedSession?.id === session.id
                        ? 'bg-white/10'
                        : 'hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-white/60 truncate">
                          {session.preview || session.summary || `Conversation ${session.id.slice(0, 8)}`}
                        </p>
                        <p className="text-[10px] text-white/30 mt-1">
                          {formatDate(session.created_at)}
                        </p>
                      </div>
                      <span className="flex-shrink-0 text-[10px] px-1.5 py-0.5 bg-white/10 rounded text-white/50">
                        {session.message_count} msg{session.message_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Session Detail */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {selectedSession ? (
              <>
                {/* Session Header */}
                <div className="p-3 border-b border-white/5 flex items-center justify-between bg-black/20">
                  <div>
                    <p className="text-xs text-white/60">{formatDate(selectedSession.created_at)}</p>
                    <p className="text-[10px] text-white/30 mt-0.5">
                      {selectedSession.message_count} messages
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {onRestoreSession && (
                      <button
                        onClick={() => {
                          onRestoreSession(selectedSession.id);
                          onClose();
                        }}
                        className="btn-ghost text-[11px] py-1.5"
                      >
                        Restore
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteSession(selectedSession.id)}
                      className="btn-icon text-uh-error hover:bg-uh-error/10"
                      title="Delete conversation"
                    >
                      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4">
                  {loadingMessages ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="h-5 w-5 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
                    </div>
                  ) : sessionMessages.length === 0 ? (
                    <p className="text-sm text-white/40 text-center py-12">No messages in this conversation</p>
                  ) : (
                    <div className="space-y-3">
                      {sessionMessages.map((msg, idx) => (
                        <div
                          key={idx}
                          className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                        >
                          <div className={`flex flex-col max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                            <div
                              className={`px-3 py-2 rounded-xl text-sm ${
                                msg.role === 'user'
                                  ? 'bg-white text-black'
                                  : 'bg-white/10 text-white/80 border border-white/10'
                              }`}
                            >
                              <span className="whitespace-pre-wrap break-words">{msg.content}</span>
                            </div>
                            {msg.timestamp && (
                              <span className="text-[10px] text-white/30 mt-1 px-1">
                                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <svg className="h-16 w-16 text-white/10 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <p className="text-sm text-white/30">Select a conversation to view</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
