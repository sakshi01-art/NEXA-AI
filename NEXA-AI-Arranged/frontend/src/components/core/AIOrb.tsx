import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { AgentState } from '../../types';

interface AIOrbProps {
  state: AgentState;
  audioLevel?: number;
}

export const AIOrb: React.FC<AIOrbProps> = ({ state, audioLevel = 0 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrame: number;
    let time = 0;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      const centerX = width / 2;
      const centerY = height / 2;

      ctx.clearRect(0, 0, width, height);

      // Base circle
      const baseRadius = 80;
      const pulseIntensity = getPulseIntensity(state);
      const radius = baseRadius + Math.sin(time * 2) * pulseIntensity;

      // Gradient based on state
      const gradient = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, radius
      );

      const colors = getStateColors(state);
      gradient.addColorStop(0, colors.inner);
      gradient.addColorStop(0.5, colors.middle);
      gradient.addColorStop(1, colors.outer);

      // Main orb
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.fill();

      // Glow effect
      ctx.shadowBlur = 40;
      ctx.shadowColor = colors.glow;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Waveform for listening/speaking states
      if (state === AgentState.LISTENING || state === AgentState.SPEAKING) {
        drawWaveform(ctx, centerX, centerY, baseRadius, time, audioLevel);
      }

      // Particles for thinking/executing states
      if (state === AgentState.THINKING || state === AgentState.EXECUTING) {
        drawParticles(ctx, centerX, centerY, baseRadius, time);
      }

      time += 0.02;
      animationFrame = requestAnimationFrame(render);
    };

    render();

    return () => cancelAnimationFrame(animationFrame);
  }, [state, audioLevel]);

  return (
    <motion.div
      className="relative flex items-center justify-center"
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <canvas
        ref={canvasRef}
        width={400}
        height={400}
        className="orb-canvas"
      />
      
      {/* State indicator */}
      <motion.div
        className="absolute bottom-0 text-center"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <p className="text-sm font-medium text-gray-400">
          {getStateLabel(state)}
        </p>
      </motion.div>
    </motion.div>
  );
};

function getPulseIntensity(state: AgentState): number {
  switch (state) {
    case AgentState.LISTENING: return 8;
    case AgentState.THINKING: return 5;
    case AgentState.EXECUTING: return 10;
    case AgentState.SPEAKING: return 6;
    case AgentState.ERROR: return 12;
    default: return 3;
  }
}

function getStateColors(state: AgentState) {
  const colorMap = {
    [AgentState.IDLE]: {
      inner: 'rgba(99, 102, 241, 0.8)',
      middle: 'rgba(99, 102, 241, 0.4)',
      outer: 'rgba(99, 102, 241, 0)',
      glow: 'rgba(99, 102, 241, 0.6)',
    },
    [AgentState.LISTENING]: {
      inner: 'rgba(59, 130, 246, 0.8)',
      middle: 'rgba(59, 130, 246, 0.4)',
      outer: 'rgba(59, 130, 246, 0)',
      glow: 'rgba(59, 130, 246, 0.6)',
    },
    [AgentState.THINKING]: {
      inner: 'rgba(139, 92, 246, 0.8)',
      middle: 'rgba(139, 92, 246, 0.4)',
      outer: 'rgba(139, 92, 246, 0)',
      glow: 'rgba(139, 92, 246, 0.6)',
    },
    [AgentState.EXECUTING]: {
      inner: 'rgba(16, 185, 129, 0.8)',
      middle: 'rgba(16, 185, 129, 0.4)',
      outer: 'rgba(16, 185, 129, 0)',
      glow: 'rgba(16, 185, 129, 0.6)',
    },
    [AgentState.SPEAKING]: {
      inner: 'rgba(99, 102, 241, 0.8)',
      middle: 'rgba(139, 92, 246, 0.4)',
      outer: 'rgba(99, 102, 241, 0)',
      glow: 'rgba(99, 102, 241, 0.6)',
    },
    [AgentState.ERROR]: {
      inner: 'rgba(239, 68, 68, 0.8)',
      middle: 'rgba(239, 68, 68, 0.4)',
      outer: 'rgba(239, 68, 68, 0)',
      glow: 'rgba(239, 68, 68, 0.6)',
    },
  };

  return colorMap[state] || colorMap[AgentState.IDLE];
}

function drawWaveform(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  centerY: number,
  radius: number,
  time: number,
  audioLevel: number
) {
  const bars = 64;
  const angleStep = (Math.PI * 2) / bars;

  for (let i = 0; i < bars; i++) {
    const angle = i * angleStep;
    const wave = Math.sin(time * 3 + i * 0.2) * audioLevel * 30;
    const barHeight = 20 + wave;
    
    const innerRadius = radius + 10;
    const outerRadius = innerRadius + barHeight;

    const x1 = centerX + Math.cos(angle) * innerRadius;
    const y1 = centerY + Math.sin(angle) * innerRadius;
    const x2 = centerX + Math.cos(angle) * outerRadius;
    const y2 = centerY + Math.sin(angle) * outerRadius;

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = `rgba(99, 102, 241, ${0.3 + audioLevel * 0.7})`;
    ctx.lineWidth = 3;
    ctx.stroke();
  }
}

function drawParticles(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  centerY: number,
  radius: number,
  time: number
) {
  const particles = 12;
  const orbitRadius = radius + 40;

  for (let i = 0; i < particles; i++) {
    const angle = (i / particles) * Math.PI * 2 + time;
    const x = centerX + Math.cos(angle) * orbitRadius;
    const y = centerY + Math.sin(angle) * orbitRadius;
    const size = 3 + Math.sin(time * 3 + i) * 2;

    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(139, 92, 246, 0.8)';
    ctx.fill();

    // Glow
    ctx.shadowBlur = 15;
    ctx.shadowColor = 'rgba(139, 92, 246, 0.8)';
    ctx.fill();
    ctx.shadowBlur = 0;
  }
}

function getStateLabel(state: AgentState): string {
  const labels = {
    [AgentState.IDLE]: 'Ready',
    [AgentState.LISTENING]: 'Listening...',
    [AgentState.PROCESSING]: 'Processing...',
    [AgentState.THINKING]: 'Thinking...',
    [AgentState.EXECUTING]: 'Executing...',
    [AgentState.SPEAKING]: 'Speaking...',
    [AgentState.ERROR]: 'Error',
    [AgentState.WAITING_CONFIRMATION]: 'Waiting for confirmation...',
  };
  return labels[state];
}
