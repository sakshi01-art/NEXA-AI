import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Clock, 
  Loader 
} from 'lucide-react';
import { TimelineEvent, ToolStatus } from '../../types';

interface CommandTimelineProps {
  events: TimelineEvent[];
  currentStep?: string;
}

export const CommandTimeline: React.FC<CommandTimelineProps> = ({
  events,
  currentStep,
}) => {
  if (events.length === 0) return null;

  return (
    <div className="glass-panel rounded-xl p-4 max-h-96 overflow-y-auto custom-scrollbar">
      <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
        <Clock className="w-4 h-4" />
        Execution Timeline
      </h3>

      <div className="space-y-2">
        <AnimatePresence>
          {events.map((event, index) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.05 }}
              className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${
                event.type === 'error'
                  ? 'bg-red-500/10 border border-red-500/20'
                  : event.type === 'success'
                  ? 'bg-green-500/10 border border-green-500/20'
                  : event.type === 'warning'
                  ? 'bg-yellow-500/10 border border-yellow-500/20'
                  : 'bg-gray-800/50 border border-gray-700/50'
              }`}
            >
              {/* Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {getEventIcon(event.type, event.message === currentStep)}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200">{event.message}</p>
                
                {event.details && (
                  <div className="mt-1 p-2 bg-black/20 rounded text-xs text-gray-400 font-mono">
                    {JSON.stringify(event.details, null, 2)}
                  </div>
                )}

                <p className="text-xs text-gray-500 mt-1">
                  {formatTimestamp(event.timestamp)}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

function getEventIcon(type: string, isActive: boolean) {
  if (isActive) {
    return <Loader className="w-4 h-4 text-blue-400 animate-spin" />;
  }

  switch (type) {
    case 'success':
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case 'error':
      return <XCircle className="w-4 h-4 text-red-400" />;
    case 'warning':
      return <AlertCircle className="w-4 h-4 text-yellow-400" />;
    default:
      return <CheckCircle className="w-4 h-4 text-gray-400" />;
  }
}

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });
}
