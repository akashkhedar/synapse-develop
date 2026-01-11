import type React from "react";
import { IconExternal } from "@synapse/ui";

interface EmptyStateProps {
  icon: React.ReactNode;
  header: string;
  description: React.ReactNode;
  learnMore?: {
    href: string;
    text: string;
    testId?: string;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, header, description, learnMore }) => {
  // White-label check for docs link hiding
  // @ts-ignore
  const isWhiteLabel = typeof window !== "undefined" && window.APP_SETTINGS?.whitelabel_is_active === true;

  return (
    <div className="flex flex-col items-center justify-center gap-3 p-8 w-full" data-testid="empty-state">
      <div className="flex items-center justify-center rounded-lg p-3 mb-2" style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
        <span style={{ color: '#8b5cf6' }}>{icon}</span>
      </div>
      <div className="flex flex-col items-center w-full gap-2">
        <div
          className="font-medium text-sm leading-tight text-center"
          data-testid="empty-state-header"
          style={{ color: '#e8e4d9', textTransform: 'uppercase', letterSpacing: '0.1em', fontSize: '12px' }}
        >
          {header}
        </div>
        <div
          className="text-xs text-center w-full leading-relaxed"
          data-testid="empty-state-description"
          style={{ color: '#9ca3af', maxWidth: '280px' }}
        >
          {description}
        </div>
      </div>
      {learnMore && !isWhiteLabel && (
        <div className="flex justify-center items-center w-full pt-3 mt-1">
          <a
            href={learnMore.href}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs transition-all duration-200"
            style={{ color: '#8b5cf6', textDecoration: 'none', borderBottom: '1px solid rgba(139, 92, 246, 0.3)' }}
            {...(learnMore.testId ? { "data-testid": learnMore.testId } : {})}
          >
            {learnMore.text}
            <IconExternal width={14} height={14} className="ml-1" />
          </a>
        </div>
      )}
    </div>
  );
};

