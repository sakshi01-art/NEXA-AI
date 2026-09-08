import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Cpu, MemoryStick, HardDrive, Wifi, Battery,
  Thermometer, Activity, AlertTriangle
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
  BarChart, Bar
} from 'recharts';

interface SystemStats {
  cpu: number;
  memory: number;
  disk: number;
  network: { sent: number; received: number };
  battery?: number;
  temperature?: number;
  processes: Array<{ name: string; cpu: number; memory: number }>;
}

interface SystemDashboardProps {
  stats: SystemStats;
  history: SystemStats[];
}

export const SystemDashboard: React.FC<SystemDashboardProps> = ({
  stats,
  history,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'processes' | 'network'>('overview');
  const [alerts, setAlerts] = useState<string[]>([]);

  useEffect(() => {
    const newAlerts: string[] = [];

    if (stats.cpu > 90) newAlerts.push('⚠️ CPU usage critical!');
    if (stats.memory > 85) newAlerts.push('⚠️ Memory almost full!');
    if (stats.disk > 90) newAlerts.push('⚠️ Low disk space!');
    if (stats.battery && stats.battery < 15) newAlerts.push('🔋 Battery critical!');

    setAlerts(newAlerts);
  }, [stats]);

  return (
    <div className="h-full flex flex-col gap-4 overflow-y-auto custom-scrollbar p-4">
      {/* Alert Banner */}
      <AnimatePresence>
        {alerts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-red-500/20 border border-red-500/50 rounded-xl p-4"
          >
            {alerts.map((alert, i) => (
              <p key={i} className="text-red-300 text-sm">{alert}</p>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          icon={<Cpu className="w-5 h-5" />}
          label="CPU"
          value={stats.cpu}
          unit="%"
          color={stats.cpu > 80 ? '#EF4444' : stats.cpu > 60 ? '#F59E0B' : '#10B981'}
          history={history.map(h => h.cpu)}
        />

        <StatCard
          icon={<MemoryStick className="w-5 h-5" />}
          label="RAM"
          value={stats.memory}
          unit="%"
          color={stats.memory > 80 ? '#EF4444' : stats.memory > 60 ? '#F59E0B' : '#6366F1'}
          history={history.map(h => h.memory)}
        />

        <StatCard
          icon={<HardDrive className="w-5 h-5" />}
          label="Disk"
          value={stats.disk}
          unit="%"
          color={stats.disk > 85 ? '#EF4444' : '#8B5CF6'}
          history={history.map(h => h.disk)}
        />

        {stats.battery !== undefined && (
          <StatCard
            icon={<Battery className="w-5 h-5" />}
            label="Battery"
            value={stats.battery}
            unit="%"
            color={stats.battery < 20 ? '#EF4444' : '#10B981'}
            history={[]}
          />
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 p-1 bg-gray-800/50 rounded-xl">
        {(['overview', 'processes', 'network'] as const).map((tab) => (
          <motion.button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium capitalize transition-all ${
              activeTab === tab
                ? 'bg-indigo-500 text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {tab}
          </motion.button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            {/* CPU History Chart */}
            <div className="glass-panel rounded-xl p-4 mb-3">
              <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                CPU History
              </h3>
              <ResponsiveContainer width="100%" height={120}>
                <AreaChart data={history.map((h, i) => ({ time: i, value: h.cpu }))}>
                  <defs>
                    <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6366F1" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#6366F1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" hide />
                  <YAxis domain={[0, 100]} hide />
                  <Tooltip
                    contentStyle={{
                      background: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F9FAFB'
                    }}
                    formatter={(value: number) => [`${value}%`, 'CPU']}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#6366F1"
                    fill="url(#cpuGrad)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Memory + Disk Pie Charts */}
            <div className="grid grid-cols-2 gap-3">
              <ResourcePieChart
                label="Memory"
                used={stats.memory}
                color="#6366F1"
              />
              <ResourcePieChart
                label="Disk"
                used={stats.disk}
                color="#8B5CF6"
              />
            </div>
          </motion.div>
        )}

        {activeTab === 'processes' && (
          <motion.div
            key="processes"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="glass-panel rounded-xl p-4"
          >
            <h3 className="text-sm font-semibold text-gray-400 mb-3">
              Top Processes
            </h3>
            <div className="space-y-2">
              {stats.processes?.slice(0, 10).map((proc, i) => (
                <motion.div
                  key={proc.name}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-800/50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{proc.name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <MiniBar value={proc.cpu} max={100} color="#6366F1" label="CPU" />
                      <MiniBar value={proc.memory} max={100} color="#8B5CF6" label="RAM" />
                    </div>
                  </div>
                  <div className="ml-4 text-right">
                    <p className="text-xs text-gray-400">{proc.cpu.toFixed(1)}% CPU</p>
                    <p className="text-xs text-gray-500">{proc.memory.toFixed(1)}% RAM</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {activeTab === 'network' && (
          <motion.div
            key="network"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            <div className="glass-panel rounded-xl p-4 mb-3">
              <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
                <Wifi className="w-4 h-4" />
                Network Activity
              </h3>
              <ResponsiveContainer width="100%" height={150}>
                <BarChart
                  data={history.slice(-20).map((h, i) => ({
                    time: i,
                    sent: h.network.sent / 1024,
                    received: h.network.received / 1024,
                  }))}
                >
                  <XAxis dataKey="time" hide />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{
                      background: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F9FAFB'
                    }}
                    formatter={(value: number, name: string) => [
                      `${value.toFixed(1)} KB`,
                      name === 'sent' ? '↑ Sent' : '↓ Received'
                    ]}
                  />
                  <Bar dataKey="sent" fill="#6366F1" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="received" fill="#10B981" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>

              <div className="flex justify-center gap-6 mt-2">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-indigo-500" />
                  <span className="text-xs text-gray-400">
                    ↑ {(stats.network.sent / 1024).toFixed(1)} KB/s
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-xs text-gray-400">
                    ↓ {(stats.network.received / 1024).toFixed(1)} KB/s
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Sub-components
const StatCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: number;
  unit: string;
  color: string;
  history: number[];
}> = ({ icon, label, value, unit, color, history }) => (
  <motion.div
    className="glass-panel rounded-xl p-4 relative overflow-hidden"
    whileHover={{ scale: 1.02 }}
  >
    {/* Background mini chart */}
    {history.length > 0 && (
      <div className="absolute inset-0 opacity-20">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history.map((v, i) => ({ v, i }))}>
            <Area type="monotone" dataKey="v" stroke={color} fill={color} strokeWidth={1} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    )}

    <div className="relative z-10">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2" style={{ color }}>
          {icon}
          <span className="text-xs font-medium text-gray-400">{label}</span>
        </div>
        <motion.div
          key={value}
          initial={{ scale: 1.2 }}
          animate={{ scale: 1 }}
          className="text-right"
        >
          <span className="text-2xl font-bold text-white">{value.toFixed(0)}</span>
          <span className="text-sm text-gray-400">{unit}</span>
        </motion.div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    </div>
  </motion.div>
);

const ResourcePieChart: React.FC<{
  label: string;
  used: number;
  color: string;
}> = ({ label, used, color }) => {
  const free = 100 - used;

  return (
    <div className="glass-panel rounded-xl p-4 text-center">
      <PieChart width={120} height={120} style={{ margin: '0 auto' }}>
        <Pie
          data={[
            { value: used, name: 'Used' },
            { value: free, name: 'Free' }
          ]}
          cx={55}
          cy={55}
          innerRadius={35}
          outerRadius={50}
          startAngle={90}
          endAngle={-270}
          dataKey="value"
        >
          <Cell fill={color} />
          <Cell fill="#1F2937" />
        </Pie>
      </PieChart>
      <p className="text-sm font-semibold text-white -mt-2">{used.toFixed(0)}%</p>
      <p className="text-xs text-gray-400">{label}</p>
    </div>
  );
};

const MiniBar: React.FC<{
  value: number;
  max: number;
  color: string;
  label: string;
}> = ({ value, max, color, label }) => (
  <div className="flex items-center gap-1 flex-1">
    <div className="flex-1 h-1 bg-gray-700 rounded-full overflow-hidden">
      <motion.div
        className="h-full rounded-full"
        style={{ backgroundColor: color }}
        animate={{ width: `${(value / max) * 100}%` }}
        transition={{ duration: 0.3 }}
      />
    </div>
  </div>
);
