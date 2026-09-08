import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Command, Zap, GitBranch, Clock, CheckCircle,
  XCircle, Loader, Play, Pause, Square, RotateCw,
  ChevronDown, ChevronRight, Terminal, Globe,
  FolderOpen, Code, Cpu, AlertOctagon
} from 'lucide-react';

interface ActiveTask {
  id: string;
  name: string;
  type: 'browser' | 'filesystem' | 'terminal' | 'system' | 'ai';
  status: 'queued' | 'running' | 'paused' | 'completed' | 'failed';
  progress: number;
  steps: TaskStep[];
  currentStep: number;
  startTime: number;
  priority: 'critical' | 'high' | 'normal' | 'low';
  canPause: boolean;
  canCancel: boolean;
  output?: string[];
  eta?: number;
}

interface TaskStep {
  id: string;
  name: string;
  status: 'pending' | 'active' | 'done' | 'failed' | 'skipped';
  duration?: number;
  tool: string;
}

interface MissionControlProps {
  tasks: ActiveTask[];
  onPauseTask: (id: string) => void;
  onResumeTask: (id: string) => void;
  onCancelTask: (id: string) => void;
  onRetryTask: (id: string) => void;
  onPrioritize: (id: string, priority: string) => void;
  maxParallelTasks: number;
}

export const MissionControl: React.FC<MissionControlProps> = ({
  tasks,
  onPauseTask,
  onResumeTask,
  onCancelTask,
  onRetryTask,
  onPrioritize,
  maxParallelTasks,
}) => {
  const [expandedTask, setExpandedTask] = useState<string | null>(null);
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [filter, setFilter] = useState<string>('all');
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const runningTasks = tasks.filter((t) => t.status === 'running');
  const queuedTasks = tasks.filter((t) => t.status === 'queued');
  const completedTasks = tasks.filter((t) => t.status === 'completed' || t.status === 'failed');

  const filteredTasks = filter === 'all' ? tasks : tasks.filter((t) => t.status === filter);

  // Draw task dependency graph on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || tasks.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawDependencyGraph(ctx, tasks, canvas.width, canvas.height);
  }, [tasks]);

  return (
    <div className="h-full flex flex-col bg-gray-950">
      {/* Header */}
      <div className="glass-panel border-b border-gray-700/50 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
              <Command className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <h2 className="font-bold text-white">Mission Control</h2>
              <p className="text-xs text-gray-400">
                {runningTasks.length} running • {queuedTasks.length} queued • {maxParallelTasks} max parallel
              </p>
            </div>
          </div>

          {/* Parallel Task Capacity Indicator */}
          <div className="flex items-center gap-2">
            {Array.from({ length: maxParallelTasks }).map((_, i) => (
              <motion.div
                key={i}
                className={`w-3 h-3 rounded-full border-2 ${
                  i < runningTasks.length
                    ? 'bg-green-500 border-green-400'
                    : 'bg-gray-700 border-gray-600'
                }`}
                animate={i < runningTasks.length ? {
                  boxShadow: ['0 0 0 0 rgba(34,197,94,0)', '0 0 0 6px rgba(34,197,94,0)']
                } : {}}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            ))}
            <span className="text-xs text-gray-400 ml-1">
              {runningTasks.length}/{maxParallelTasks} slots
            </span>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mt-3">
          {['all', 'running', 'queued', 'completed', 'failed'].map((f) => (
            <motion.button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-lg text-xs capitalize transition-all ${
                filter === f
                  ? 'bg-indigo-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {f} {f !== 'all' && `(${tasks.filter((t) => t.status === f).length})`}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Task Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredTasks.length === 0 ? (
          <EmptyState filter={filter} />
        ) : (
          <div className={view === 'grid'
            ? 'grid grid-cols-1 xl:grid-cols-2 gap-4'
            : 'space-y-3'
          }>
            <AnimatePresence>
              {filteredTasks.map((task, index) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  index={index}
                  isExpanded={expandedTask === task.id}
                  onToggleExpand={() => setExpandedTask(
                    expandedTask === task.id ? null : task.id
                  )}
                  onPause={() => onPauseTask(task.id)}
                  onResume={() => onResumeTask(task.id)}
                  onCancel={() => onCancelTask(task.id)}
                  onRetry={() => onRetryTask(task.id)}
                  onPrioritize={(p) => onPrioritize(task.id, p)}
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Dependency Graph (hidden canvas for calculations) */}
      <canvas ref={canvasRef} className="hidden" width={800} height={200} />
    </div>
  );
};

const TaskCard: React.FC<{
  task: ActiveTask;
  index: number;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  onRetry: () => void;
  onPrioritize: (priority: string) => void;
}> = ({
  task,
  index,
  isExpanded,
  onToggleExpand,
  onPause,
  onResume,
  onCancel,
  onRetry,
  onPrioritize,
}) => {
  const elapsed = ((Date.now() - task.startTime) / 1000).toFixed(0);
  const eta = task.eta ? `~${Math.ceil(task.eta)}s` : '...';

  const getStatusColor = () => {
    const colors = {
      queued: 'text-gray-400 border-gray-600',
      running: 'text-blue-400 border-blue-500',
      paused: 'text-yellow-400 border-yellow-500',
      completed: 'text-green-400 border-green-500',
      failed: 'text-red-400 border-red-500',
    };
    return colors[task.status] || colors.queued;
  };

  const getTaskIcon = () => {
    const icons = {
      browser: <Globe className="w-4 h-4" />,
      filesystem: <FolderOpen className="w-4 h-4" />,
      terminal: <Terminal className="w-4 h-4" />,
      system: <Cpu className="w-4 h-4" />,
      ai: <Zap className="w-4 h-4" />,
    };
    return icons[task.type] || icons.ai;
  };

  const getPriorityBadge = () => {
    const styles = {
      critical: 'bg-red-500/20 text-red-400 border-red-500/30',
      high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      normal: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      low: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    };
    return styles[task.priority] || styles.normal;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ delay: index * 0.05 }}
      className={`glass-panel rounded-xl border overflow-hidden ${
        task.status === 'running'
          ? 'border-blue-500/30'
          : task.status === 'failed'
          ? 'border-red-500/30'
          : task.status === 'completed'
          ? 'border-green-500/20'
          : 'border-gray-700/50'
      }`}
    >
      {/* Progress Bar - Top */}
      {task.status === 'running' && (
        <div className="h-0.5 bg-gray-800">
          <motion.div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
            animate={{ width: `${task.progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      )}

      {/* Card Header */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            {/* Task Type Icon */}
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
              task.status === 'running' ? 'bg-blue-500/20' :
              task.status === 'completed' ? 'bg-green-500/20' :
              task.status === 'failed' ? 'bg-red-500/20' :
              'bg-gray-700/50'
            }`}>
              <span className={getStatusColor().split(' ')[0]}>
                {getTaskIcon()}
              </span>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-sm font-semibold text-white truncate">
                  {task.name}
                </h3>

                {/* Priority Badge */}
                <span className={`px-2 py-0.5 rounded-full text-xs border flex-shrink-0 ${getPriorityBadge()}`}>
                  {task.priority}
                </span>
              </div>

              {/* Status + Timing */}
              <div className="flex items-center gap-3 text-xs">
                <div className={`flex items-center gap-1 ${getStatusColor().split(' ')[0]}`}>
                  {task.status === 'running' && (
                    <Loader className="w-3 h-3 animate-spin" />
                  )}
                  {task.status === 'completed' && (
                    <CheckCircle className="w-3 h-3" />
                  )}
                  {task.status === 'failed' && (
                    <XCircle className="w-3 h-3" />
                  )}
                  <span className="capitalize">{task.status}</span>
                </div>

                <span className="text-gray-500">•</span>

                <div className="flex items-center gap-1 text-gray-400">
                  <Clock className="w-3 h-3" />
                  <span>{elapsed}s</span>
                </div>

                {task.status === 'running' && (
                  <>
                    <span className="text-gray-500">•</span>
                    <span className="text-gray-400">ETA {eta}</span>
                  </>
                )}

                <span className="text-gray-500">•</span>
                <span className="text-gray-400">
                  {task.progress.toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-1 flex-shrink-0">
            {task.status === 'running' && task.canPause && (
              <ActionButton
                icon={<Pause className="w-3 h-3" />}
                onClick={onPause}
                title="Pause"
                color="yellow"
              />
            )}

            {task.status === 'paused' && (
              <ActionButton
                icon={<Play className="w-3 h-3" />}
                onClick={onResume}
                title="Resume"
                color="green"
              />
            )}

            {task.status === 'failed' && (
              <ActionButton
                icon={<RotateCw className="w-3 h-3" />}
                onClick={onRetry}
                title="Retry"
                color="blue"
              />
            )}

            {(task.status === 'running' || task.status === 'queued') && task.canCancel && (
              <ActionButton
                icon={<Square className="w-3 h-3" />}
                onClick={onCancel}
                title="Cancel"
                color="red"
              />
            )}

            <ActionButton
              icon={isExpanded
                ? <ChevronDown className="w-3 h-3" />
                : <ChevronRight className="w-3 h-3" />
              }
              onClick={onToggleExpand}
              title="Details"
              color="gray"
            />
          </div>
        </div>

        {/* Step Progress */}
        <div className="mt-3">
          <div className="flex gap-1">
            {task.steps.map((step, i) => (
              <div
                key={step.id}
                className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                  step.status === 'done' ? 'bg-green-500' :
                  step.status === 'active' ? 'bg-blue-500 animate-pulse' :
                  step.status === 'failed' ? 'bg-red-500' :
                  step.status === 'skipped' ? 'bg-yellow-500' :
                  'bg-gray-700'
                }`}
                title={step.name}
              />
            ))}
          </div>

          {/* Current Step Label */}
          {task.status === 'running' && task.steps[task.currentStep] && (
            <p className="text-xs text-gray-400 mt-1">
              Step {task.currentStep + 1}/{task.steps.length}:
              {' '}{task.steps[task.currentStep].name}
            </p>
          )}
        </div>
      </div>

      {/* Expanded Details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-700/50 overflow-hidden"
          >
            <div className="p-4 space-y-3">
              {/* Steps Detail */}
              <div>
                <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                  Execution Steps
                </h4>
                <div className="space-y-1">
                  {task.steps.map((step, i) => (
                    <div
                      key={step.id}
                      className={`flex items-center gap-2 p-2 rounded-lg text-xs ${
                        step.status === 'active' ? 'bg-blue-500/10' : 'bg-gray-800/30'
                      }`}
                    >
                      <StepIcon status={step.status} />
                      <span className={
                        step.status === 'done' ? 'text-green-400' :
                        step.status === 'active' ? 'text-blue-400 font-medium' :
                        step.status === 'failed' ? 'text-red-400' :
                        'text-gray-400'
                      }>
                        {step.name}
                      </span>
                      {step.duration && (
                        <span className="ml-auto text-gray-500">
                          {step.duration}ms
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Output */}
              {task.output && task.output.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                    Output
                  </h4>
                  <div className="bg-black/50 rounded-lg p-3 max-h-32 overflow-y-auto">
                    {task.output.map((line, i) => (
                      <p key={i} className="text-xs font-mono text-green-400">
                        {line}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Priority Control */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">Priority:</span>
                {['critical', 'high', 'normal', 'low'].map((p) => (
                  <motion.button
                    key={p}
                    onClick={() => onPrioritize(p)}
                    className={`px-2 py-1 rounded text-xs capitalize transition-colors ${
                      task.priority === p
                        ? 'bg-indigo-500 text-white'
                        : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                    }`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {p}
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

const ActionButton: React.FC<{
  icon: React.ReactNode;
  onClick: () => void;
  title: string;
  color: string;
}> = ({ icon, onClick, title, color }) => {
  const colorMap: Record<string, string> = {
    yellow: 'hover:bg-yellow-500/20 hover:text-yellow-400',
    green: 'hover:bg-green-500/20 hover:text-green-400',
    blue: 'hover:bg-blue-500/20 hover:text-blue-400',
    red: 'hover:bg-red-500/20 hover:text-red-400',
    gray: 'hover:bg-gray-700 hover:text-white',
  };

  return (
    <motion.button
      onClick={onClick}
      title={title}
      className={`w-7 h-7 rounded-lg flex items-center justify-center text-gray-500 transition-colors ${colorMap[color]}`}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
    >
      {icon}
    </motion.button>
  );
};

const StepIcon: React.FC<{ status: string }> = ({ status }) => {
  const icons = {
    done: <CheckCircle className="w-3 h-3 text-green-400" />,
    active: <Loader className="w-3 h-3 text-blue-400 animate-spin" />,
    failed: <XCircle className="w-3 h-3 text-red-400" />,
    skipped: <AlertOctagon className="w-3 h-3 text-yellow-400" />,
    pending: <div className="w-3 h-3 rounded-full border border-gray-600" />,
  };
  return icons[status as keyof typeof icons] || icons.pending;
};

const EmptyState: React.FC<{ filter: string }> = ({ filter }) => (
  <div className="h-full flex flex-col items-center justify-center text-center p-8">
    <motion.div
      animate={{ y: [0, -10, 0] }}
      transition={{ duration: 3, repeat: Infinity }}
    >
      <Command className="w-16 h-16 text-gray-700 mx-auto mb-4" />
    </motion.div>
    <p className="text-gray-400 font-medium">No {filter} tasks</p>
    <p className="text-gray-600 text-sm mt-1">
      Voice commands se tasks start karo
    </p>
  </div>
);

function drawDependencyGraph(
  ctx: CanvasRenderingContext2D,
  tasks: ActiveTask[],
  width: number,
  height: number
) {
  // Draw simple dependency graph
  const nodeRadius = 20;
  const spacing = width / (tasks.length + 1);

  tasks.forEach((task, i) => {
    const x = spacing * (i + 1);
    const y = height / 2;

    // Draw node
    ctx.beginPath();
    ctx.arc(x, y, nodeRadius, 0, Math.PI * 2);
    ctx.fillStyle = task.status === 'running' ? '#6366F1' :
                    task.status === 'completed' ? '#10B981' :
                    task.status === 'failed' ? '#EF4444' : '#374151';
    ctx.fill();

    // Draw label
    ctx.fillStyle = '#F9FAFB';
    ctx.font = '10px Inter';
    ctx.textAlign = 'center';
    ctx.fillText(task.name.slice(0, 8), x, y + 4);

    // Draw connection to next
    if (i < tasks.length - 1) {
      const nextX = spacing * (i + 2);
      ctx.beginPath();
      ctx.moveTo(x + nodeRadius, y);
      ctx.lineTo(nextX - nodeRadius, y);
      ctx.strokeStyle = '#4B5563';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  });
}
