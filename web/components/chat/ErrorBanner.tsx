interface ErrorBannerProps {
  message: string;
  onDismiss: () => void;
}

export function ErrorBanner({ message, onDismiss }: ErrorBannerProps) {
  return (
    <div className="mb-3 flex items-center justify-between rounded-xl bg-uh-error/10 border border-uh-error/20 px-4 py-3 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <svg className="h-4 w-4 text-uh-error flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" strokeLinecap="round" />
          <line x1="12" y1="16" x2="12.01" y2="16" strokeLinecap="round" />
        </svg>
        <span className="text-sm text-uh-error">{message}</span>
      </div>
      <button
        onClick={onDismiss}
        className="text-uh-error/60 hover:text-uh-error transition-colors flex-shrink-0"
      >
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="6" y1="6" x2="18" y2="18" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </div>
  );
}
