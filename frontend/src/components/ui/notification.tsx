'use client';

import { cn } from '@/lib/utils';
import { CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';

interface NotificationProps {
  type: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Notification({ type, title, children, className }: NotificationProps) {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const Icon = icons[type];

  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg p-4 border-l-4',
        {
          'notification-success': type === 'success',
          'notification-error': type === 'error',
          'notification-warning': type === 'warning',
          'notification-info': type === 'info',
        },
        className
      )}
    >
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        {title && (
          <h3 className="text-sm font-semibold mb-1">
            {title}
          </h3>
        )}
        <div className="text-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
