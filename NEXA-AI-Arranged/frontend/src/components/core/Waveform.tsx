import React from 'react';
import { motion } from 'framer-motion';

interface WaveformProps {
  audioLevel?: number;
  isActive?: boolean;
  className?: string;
}

export const Waveform: React.FC<WaveformProps> = ({
  audioLevel = 0,
  isActive = false,
  className = ''
}) => {
  const bars = [0.4, 0.7, 1.0, 0.8, 0.5, 0.9, 0.6, 0.3, 0.8, 0.5, 1.0, 0.7, 0.4];

  return (
    <div className={`flex items-center justify-center gap-1.5 h-16 w-full ${className}`}>
      {bars.map((heightRatio, i) => {
        const height = isActive
          ? Math.max(12, Math.min(60, heightRatio * 40 + audioLevel * 30))
          : 6;

        return (
          <motion.div
            key={i}
            className="w-1.5 rounded-full bg-gradient-to-t from-blue-500 via-indigo-400 to-purple-400"
            animate={{
              height: `${height}px`,
              opacity: isActive ? 0.9 : 0.3
            }}
            transition={{
              type: 'spring',
              stiffness: 300,
              damping: 20
            }}
          />
        );
      })}
    </div>
  );
};
