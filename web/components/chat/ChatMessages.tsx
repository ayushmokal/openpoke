import clsx from 'clsx';
import { RefObject } from 'react';
import ReactMarkdown from 'react-markdown';

import type { ChatBubble } from './types';

interface ChatMessagesProps {
  messages: ReadonlyArray<ChatBubble>;
  isWaitingForResponse: boolean;
  scrollContainerRef: RefObject<HTMLDivElement | null>;
  onScroll: () => void;
  onQuickAction?: (action: string) => void;
}

export function ChatMessages({ messages, isWaitingForResponse, scrollContainerRef, onScroll, onQuickAction }: ChatMessagesProps) {
  return (
    <div
      ref={scrollContainerRef}
      onScroll={onScroll}
      className="flex flex-1 flex-col gap-4 overflow-y-auto p-6 scroll-smooth"
    >
      {messages.length === 0 && <EmptyState onQuickAction={onQuickAction} />}

      {messages.map((message, index) => {
        const isUser = message.role === 'user';
        const isDraft = message.role === 'draft';
        const next = messages[index + 1];
        const isLast = index === messages.length - 1;
        const tail = !next || next.role !== message.role;

        return (
          <div
            key={message.id}
            className={clsx(
              'flex gap-3',
              isUser ? 'flex-row-reverse' : 'flex-row'
            )}
          >
            {/* Avatar for assistant messages */}
            {!isUser && (
              <div className={clsx(
                'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
                'bg-gradient-to-br from-white/10 to-white/5 border border-white/10',
                !tail && 'invisible'
              )}>
                <svg className="w-4 h-4 text-white/60" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="9" />
                  <circle cx="12" cy="12" r="5" />
                </svg>
              </div>
            )}

            <div className={clsx('flex flex-col max-w-[75%]', isUser && 'items-end')}>
              <div
                className={clsx(
                  isUser ? 'bubble-user' : 'bubble-assistant',
                  tail ? (isUser ? 'rounded-br-md' : 'rounded-bl-md') : '',
                  isDraft && 'opacity-70',
                  'shadow-lg'
                )}
              >
                {isUser ? (
                  <span className="whitespace-pre-wrap break-words leading-relaxed">
                    {message.text}
                  </span>
                ) : (
                  <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
                        li: ({ children }) => <li className="text-white/90">{children}</li>,
                        strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                        em: ({ children }) => <em className="italic">{children}</em>,
                        code: ({ children }) => (
                          <code className="bg-black/30 px-1.5 py-0.5 rounded text-xs font-mono text-white/90">
                            {children}
                          </code>
                        ),
                        pre: ({ children }) => (
                          <pre className="bg-black/30 p-3 rounded-lg overflow-x-auto my-2 text-xs">
                            {children}
                          </pre>
                        ),
                        h1: ({ children }) => <h1 className="text-lg font-bold mb-2 text-white">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-base font-bold mb-2 text-white">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-sm font-bold mb-1 text-white">{children}</h3>,
                        a: ({ href, children }) => (
                          <a href={href} className="text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">
                            {children}
                          </a>
                        ),
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-2 border-white/30 pl-3 italic text-white/70 my-2">
                            {children}
                          </blockquote>
                        ),
                      }}
                    >
                      {message.text}
                    </ReactMarkdown>
                  </div>
                )}
              </div>

              {/* Timestamp for last message */}
              {isLast && tail && (
                <span className={clsx(
                  'text-[10px] text-white/30 mt-1.5 px-1',
                  isUser ? 'text-right' : 'text-left'
                )}>
                  Just now
                </span>
              )}
            </div>
          </div>
        );
      })}

      {isWaitingForResponse && <TypingIndicator />}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-white/10 to-white/5 border border-white/10">
        <svg className="w-4 h-4 text-white/60" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="9" />
          <circle cx="12" cy="12" r="5" />
        </svg>
      </div>
      <div className="bubble-assistant rounded-bl-md">
        <div className="flex items-center gap-1.5 py-1 px-1">
          <div className="typing-dot" style={{ animationDelay: '0ms' }} />
          <div className="typing-dot" style={{ animationDelay: '150ms' }} />
          <div className="typing-dot" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

interface EmptyStateProps {
  onQuickAction?: (action: string) => void;
}

function EmptyState({ onQuickAction }: EmptyStateProps) {
  const quickActions = [
    { label: 'Sleep', icon: '😴', action: 'How did I sleep last night?' },
    { label: 'Heart rate', icon: '❤️', action: "What's my heart rate?" },
    { label: 'Battery', icon: '🔋', action: 'My battery is draining fast' },
    { label: 'Orders', icon: '📦', action: "What's my order status?" },
  ];

  return (
    <div className="flex flex-col items-center justify-center flex-1 py-8">
      {/* Logo/Icon */}
      <div className="relative mb-6">
        <div className="h-20 w-20 rounded-full bg-gradient-to-br from-white/10 to-white/5 flex items-center justify-center border border-white/10 shadow-2xl">
          <svg className="h-10 w-10 text-white/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        {/* Glow effect */}
        <div className="absolute inset-0 rounded-full bg-white/5 blur-xl animate-pulse" />
      </div>

      {/* Text */}
      <h2 className="text-xl font-semibold text-white mb-2">How can I help?</h2>
      <p className="text-sm text-white/40 mb-8 text-center max-w-xs">
        Ask about your ring, health data, or get support
      </p>

      {/* Quick Actions Grid */}
      <div className="grid grid-cols-2 gap-3 w-full max-w-sm">
        {quickActions.map((item) => (
          <button
            key={item.label}
            onClick={() => onQuickAction?.(item.action)}
            className="quick-chip group"
          >
            <span className="text-base mr-2">{item.icon}</span>
            <span className="text-sm text-white/70 group-hover:text-white transition-colors">{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
