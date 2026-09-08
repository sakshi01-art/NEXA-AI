import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell, BellOff, CheckCircle, AlertTriangle,
  Info, XCircle, X, Volume2, VolumeX
} from 'lucide-react';

type NotificationType = 'success' | 'warning' | 'error' | 'info' | 'suggestion';

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: number;
  action?: {
    label: string;
    handler: () => void;
  };
  read: boolean;
  persistent?: boolean;
}

interface NotificationCenterProps {
  notifications: Notification[];
  onDismiss: (id: string) => void;
  onDismissAll: () => void;
  onMarkRead: (id: string) => void;
  onAction: (id: string) => void;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  notifications,
  onDismiss,
  onDismissAll,
  onMarkRead,
  onAction,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [muted, setMuted] = useState(false);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const getIcon = (type: NotificationType) => {
    const icons = {
      success: <CheckCircle className="w-4 h-4 text-green-400" />,
      warning: <AlertTriangle className="w-4 h-4 text-yellow-400" />,
      error: <XCircle className="w-4 h-4 text-red-400" />,
      info: <Info className="w-4 h-4 text-blue-400" />,
      suggestion: <Info className="w-4 h-4 text-purple-400" />,
    };
    return icons[type];
  };

  const getBorderColor = (type: NotificationType) => {
    const colors = {
      success: 'border-l-green-500',
      warning: 'border-l-yellow-500',
      error: 'border-l-red-500',
      info: 'border-l-blue-500',
      suggestion: 'border-l-purple-500',
    };
    return colors[type];
  };

  return (
    <div className="relative">
      {/* Bell Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl hover:bg-gray-800 transition-colors"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {unreadCount > 0 ? (
          <Bell className="w-5 h-5 text-indigo-400" />
        ) : (
          <Bell className="w-5 h-5 text-gray-400" />
        )}

        {unreadCount > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center"
          >
            <span className="text-xs text-white font-bold">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          </motion.div>
        )}
      </motion.button>

      {/* Notification Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute right-0 top-12 w-96 glass-panel rounded-2xl border border-gray-700/50 shadow-xl z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 border-b border-gray-700/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-indigo-400" />
                <h3 className="font-semibold text-white">Notifications</h3>
                {unreadCount > 0 && (
                  <span className="px-2 py-0.5 bg-indigo-500/20 text-indigo-400 rounded-full text-xs">
                    {unreadCount} new
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <motion.button
                  onClick={() => setMuted(!muted)}
                  className="p-1.5 rounded-lg hover:bg-gray-700 transition-colors"
                  whileHover={{ scale: 1.05 }}
                  title={muted ? 'Unmute' : 'Mute'}
                >
                  {muted ? (
                    <VolumeX className="w-4 h-4 text-gray-400" />
                  ) : (
                    <Volume2 className="w-4 h-4 text-gray-400" />
                  )}
                </motion.button>

                {notifications.length > 0 && (
                  <motion.button
                    onClick={onDismissAll}
                    className="text-xs text-gray-400 hover:text-white transition-colors px-2 py-1 rounded-lg hover:bg-gray-700"
                    whileHover={{ scale: 1.05 }}
                  >
                    Clear all
                  </motion.button>
                )}
              </div>
            </div>

            {/* Notifications List */}
            <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
              {notifications.length === 0 ? (
                <div className="p-8 text-center">
                  <BellOff className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-500 text-sm">No notifications</p>
                </div>
              ) : (
                <AnimatePresence>
                  {notifications.map((notif) => (
                    <motion.div
                      key={notif.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20, height: 0 }}
                      onClick={() => onMarkRead(notif.id)}
                      className={`
                        p-4 border-l-2 ${getBorderColor(notif.type)}
                        ${!notif.read ? 'bg-gray-800/50' : 'opacity-60'}
                        hover:bg-gray-800/70 cursor-pointer transition-colors
                        border-b border-gray-700/30
                      `}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-0.5">
                          {getIcon(notif.type)}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-sm font-medium text-white">
                              {notif.title}
                            </p>
                            <div className="flex items-center gap-1 flex-shrink-0">
                              <span className="text-xs text-gray-500">
                                {formatRelativeTime(notif.timestamp)}
                              </span>
                              <motion.button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDismiss(notif.id);
                                }}
                                className="p-0.5 rounded hover:bg-gray-700 transition-colors"
                                whileHover={{ scale: 1.1 }}
                              >
                                <X className="w-3 h-3 text-gray-500" />
                              </motion.button>
                            </div>
                          </div>

                          <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">
                            {notif.message}
                          </p>

                          {notif.action && (
                            <motion.button
                              onClick={(e) => {
                                e.stopPropagation();
                                onAction(notif.id);
                                notif.action!.handler();
                              }}
                              className="mt-2 px-3 py-1 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400 rounded-lg text-xs transition-colors"
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                            >
                              {notif.action.label}
                            </motion.button>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

function formatRelativeTime(timestamp: number): string {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

// Toast Notification Component
export const ToastContainer: React.FC<{
  toasts: Notification[];
  onDismiss: (id: string) => void;
}> = ({ toasts, onDismiss }) => (
  <div className="fixed bottom-24 right-6 z-50 space-y-2 max-w-sm">
    <AnimatePresence>
      {toasts.slice(0, 3).map((toast) => (
        <motion.div
          key={toast.id}
          initial={{ opacity: 0, x: 100, scale: 0.9 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: 100, scale: 0.9 }}
          className={`glass-panel rounded-xl p-4 shadow-xl border border-gray-700/50 flex items-start gap-3`}
        >
          <div className="flex-shrink-0 mt-0.5">
            {toast.type === 'success' && <CheckCircle className="w-5 h-5 text-green-400" />}
            {toast.type === 'warning' && <AlertTriangle className="w-5 h-5 text-yellow-400" />}
            {toast.type === 'error' && <XCircle className="w-5 h-5 text-red-400" />}
            {toast.type === 'info' && <Info className="w-5 h-5 text-blue-400" />}
          </div>

          <div className="flex-1">
            <p className="text-sm font-medium text-white">{toast.title}</p>
            <p className="text-xs text-gray-400 mt-0.5">{toast.message}</p>
          </div>

          <button
            onClick={() => onDismiss(toast.id)}
            className="flex-shrink-0 p-1 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        </motion.div>
      ))}
    </AnimatePresence>
  </div>
);
