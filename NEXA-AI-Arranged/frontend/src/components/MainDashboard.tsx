import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home, MessageSquare, History, Zap, FolderOpen,
  Grid, Brain, Puzzle, Activity, Settings,
  Smartphone, Mic, MicOff, Send, Square,
  Bell, ChevronLeft, ChevronRight, Sun, Moon,
  Maximize2, Minimize2, X, Command, Search,
  Terminal, Globe, Code, FileText, Camera,
  Cpu, Wifi, Battery, HardDrive, Users,
  Calendar, Mail, Music, Shield, Database,
  Lightbulb, Clock, Star, TrendingUp, Eye
} from 'lucide-react';

import { AIOrb } from './core/AIOrb';
import { VoiceInput } from './core/VoiceInput';
import { CommandTimeline } from './features/CommandTimeline';
import { SystemDashboard } from './features/SystemDashboard';
import { PhoneHub } from './phone/PhoneHub';
import { NotificationCenter } from './features/NotificationCenter';

type NavSection =
  | 'home' | 'assistant' | 'history' | 'automations'
  | 'files' | 'apps' | 'memory' | 'integrations'
  | 'system' | 'phone' | 'smart_home' | 'meetings'
  | 'voice_keyboard' | 'code' | 'documents' | 'settings';

interface AgentMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  timeline?: any[];
  tools_used?: string[];
}

interface SystemStats {
  cpu: number;
  memory: number;
  disk: number;
  network: { sent: number; received: number };
  battery?: number;
}

type AgentState =
  'idle' | 'listening' | 'processing' |
  'thinking' | 'executing' | 'speaking' | 'error';

export const MainDashboard: React.FC = () => {
  const [activeSection, setActiveSection] = useState<NavSection>('home');
  const [agentState, setAgentState] = useState<AgentState>('idle');
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [currentTimeline, setCurrentTimeline] = useState<any[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats>({
    cpu: 0, memory: 0, disk: 0, network: { sent: 0, received: 0 }
  });
  const [statsHistory, setStatsHistory] = useState<SystemStats[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentTask, setCurrentTask] = useState<string | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [unreadNotifications, setUnreadNotifications] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // WebSocket Connection
  useEffect(() => {
    const wsUrl = window.location.port === '3000' ? 'ws://localhost:8000/ws' : `ws://${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('NEXA Connected ✓');
      ws.send(JSON.stringify({ type: 'get_status' }));
    };

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      handleWsMessage(data);
    };

    ws.onerror = () => {
      setAgentState('error');
    };

    return () => ws.close();
  }, []);

  // System stats polling
  useEffect(() => {
    const interval = setInterval(() => {
      sendWs({ type: 'get_system_stats' });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.code === 'Space') {
        e.preventDefault();
        toggleListening();
      }
      if (e.key === 'Escape') {
        sendWs({ type: 'cancel_task' });
        setIsListening(false);
      }
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(prev => !prev);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isListening]);

  const sendWs = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const handleWsMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'agent_state':
        setAgentState(data.state);
        break;

      case 'transcript':
        setTranscript(data.text);
        break;

      case 'message':
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: data.role,
          content: data.content,
          timestamp: Date.now(),
          timeline: data.timeline,
          tools_used: data.tools_used
        }]);
        if (data.role === 'assistant') {
          setTranscript('');
          setCurrentTask(null);
        }
        break;

      case 'timeline_update':
        setCurrentTimeline(prev => [...prev, data.event]);
        break;

      case 'timeline_clear':
        setCurrentTimeline([]);
        break;

      case 'system_stats':
        setSystemStats(data.stats);
        setStatsHistory(prev => [...prev.slice(-60), data.stats]);
        break;

      case 'task_start':
        setCurrentTask(data.task);
        setCurrentTimeline([]);
        break;

      case 'task_end':
        setCurrentTask(null);
        break;

      case 'notification':
        setNotifications(prev => [data.notification, ...prev].slice(0, 50));
        setUnreadNotifications(prev => prev + 1);
        break;

      case 'audio_level':
        setAudioLevel(data.level);
        break;

      case 'listening_started':
        setIsListening(true);
        setAgentState('listening');
        break;

      case 'listening_stopped':
        setIsListening(false);
        break;
    }
  }, []);

  const toggleListening = useCallback(async () => {
    if (isListening) {
      setIsListening(false);
      sendWs({ type: 'stop_listening' });

      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;
        audioChunksRef.current = [];

        recorder.ondataavailable = (e) => {
          audioChunksRef.current.push(e.data);
        };

        recorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          const arrayBuffer = await audioBlob.arrayBuffer();
          const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

          sendWs({
            type: 'process_audio',
            audio: base64,
            format: 'wav'
          });

          stream.getTracks().forEach(t => t.stop());
        };

        recorder.start();
        setIsListening(true);
        setAgentState('listening');
        sendWs({ type: 'start_listening' });

      } catch (err) {
        console.error('Microphone error:', err);
      }
    }
  }, [isListening, sendWs]);

  const sendTextMessage = useCallback((text: string) => {
    if (!text.trim()) return;

    const userMsg: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg]);
    setAgentState('processing');

    sendWs({
      type: 'text_command',
      text,
      language: 'hinglish'
    });
  }, [sendWs]);

  const cancelTask = useCallback(() => {
    sendWs({ type: 'cancel_task' });
    setAgentState('idle');
    setCurrentTask(null);
  }, [sendWs]);

  const navItems = [
    { id: 'home', icon: <Home />, label: 'Home' },
    { id: 'assistant', icon: <MessageSquare />, label: 'Assistant' },
    { id: 'history', icon: <History />, label: 'History' },
    { id: 'automations', icon: <Zap />, label: 'Automations' },
    { id: 'phone', icon: <Smartphone />, label: 'Phone', badge: true },
    { id: 'smart_home', icon: <Lightbulb />, label: 'Smart Home' },
    { id: 'meetings', icon: <Users />, label: 'Meetings' },
    { id: 'files', icon: <FolderOpen />, label: 'Files' },
    { id: 'code', icon: <Code />, label: 'Code' },
    { id: 'documents', icon: <FileText />, label: 'Documents' },
    { id: 'system', icon: <Activity />, label: 'System' },
    { id: 'memory', icon: <Brain />, label: 'Memory' },
    { id: 'integrations', icon: <Puzzle />, label: 'Integrations' },
    { id: 'settings', icon: <Settings />, label: 'Settings' },
  ];

  return (
    <div className={`h-screen flex overflow-hidden ${
      theme === 'dark' ? 'bg-gray-950 text-white' : 'bg-gray-100 text-gray-900'
    }`}>

      {/* LEFT SIDEBAR */}
      <motion.aside
        animate={{ width: isSidebarCollapsed ? 72 : 240 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="flex flex-col bg-gray-900/95 border-r border-gray-800/50 flex-shrink-0 overflow-hidden"
      >
        {/* Logo */}
        <div className="p-4 flex items-center gap-3 border-b border-gray-800/50">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Command className="w-4 h-4 text-white" />
          </div>
          <AnimatePresence>
            {!isSidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
              >
                <p className="font-bold text-white text-lg leading-none">NEXA</p>
                <p className="text-xs text-gray-400">AI Desktop Agent</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Search */}
        {!isSidebarCollapsed && (
          <div className="px-3 py-2">
            <button
              onClick={() => setSearchOpen(true)}
              className="w-full flex items-center gap-2 px-3 py-2 bg-gray-800/50 rounded-lg text-gray-400 text-sm hover:bg-gray-800 transition-colors"
            >
              <Search className="w-3 h-3" />
              <span>Search... Ctrl+K</span>
            </button>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-2 space-y-1">
          {navItems.map((item) => (
            <motion.button
              key={item.id}
              onClick={() => setActiveSection(item.id as NavSection)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all relative ${
                activeSection === item.id
                  ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
              whileHover={{ x: 2 }}
              whileTap={{ scale: 0.97 }}
            >
              <span className="w-4 h-4 flex-shrink-0">
                {item.icon}
              </span>

              <AnimatePresence>
                {!isSidebarCollapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-sm font-medium whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>

              {item.badge && (
                <div className="absolute right-2 top-2 w-2 h-2 bg-green-500 rounded-full" />
              )}
            </motion.button>
          ))}
        </nav>

        {/* System Stats Mini */}
        {!isSidebarCollapsed && (
          <div className="p-3 border-t border-gray-800/50 space-y-2">
            <MiniStat
              icon={<Cpu className="w-3 h-3" />}
              label="CPU"
              value={systemStats.cpu}
              color={systemStats.cpu > 80 ? '#EF4444' : '#6366F1'}
            />
            <MiniStat
              icon={<Database className="w-3 h-3" />}
              label="RAM"
              value={systemStats.memory}
              color={systemStats.memory > 80 ? '#EF4444' : '#8B5CF6'}
            />
            {systemStats.battery !== undefined && (
              <MiniStat
                icon={<Battery className="w-3 h-3" />}
                label="Battery"
                value={systemStats.battery}
                color={systemStats.battery < 20 ? '#EF4444' : '#10B981'}
              />
            )}
          </div>
        )}

        {/* Collapse Toggle */}
        <button
          onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          className="p-3 border-t border-gray-800/50 flex items-center justify-center text-gray-500 hover:text-white transition-colors"
        >
          {isSidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </motion.aside>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* TOP BAR */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-gray-800/50 bg-gray-900/50 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <h1 className="font-semibold text-white">
              {navItems.find(n => n.id === activeSection)?.label || 'Home'}
            </h1>

            {currentTask && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-2 px-3 py-1 bg-indigo-500/20 rounded-lg border border-indigo-500/30"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                <span className="text-xs text-indigo-300 max-w-[200px] truncate">
                  {currentTask}
                </span>
                <button
                  onClick={cancelTask}
                  className="text-indigo-400 hover:text-white ml-1"
                >
                  <X className="w-3 h-3" />
                </button>
              </motion.div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <AgentStateBadge state={agentState} />

            <NotificationCenter
              notifications={notifications}
              unreadCount={unreadNotifications}
              onDismiss={(id) => setNotifications(
                prev => prev.filter(n => n.id !== id)
              )}
              onDismissAll={() => {
                setNotifications([]);
                setUnreadNotifications(0);
              }}
              onMarkRead={() => setUnreadNotifications(0)}
              onAction={() => {}}
            />

            <motion.button
              onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {theme === 'dark'
                ? <Sun className="w-4 h-4" />
                : <Moon className="w-4 h-4" />
              }
            </motion.button>

            <motion.button
              onClick={() => setIsRightPanelOpen(p => !p)}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              whileHover={{ scale: 1.05 }}
            >
              <Eye className="w-4 h-4" />
            </motion.button>
          </div>
        </header>

        {/* CONTENT AREA */}
        <div className="flex-1 flex overflow-hidden">

          {/* CENTER PANEL */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <AnimatePresence mode="wait">

              {/* HOME / ASSISTANT */}
              {(activeSection === 'home' || activeSection === 'assistant') && (
                <motion.div
                  key="home"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 flex flex-col overflow-hidden"
                >
                  {/* AI ORB */}
                  <div className="flex-1 flex flex-col items-center justify-center p-8 overflow-y-auto">
                    <AIOrb state={agentState} audioLevel={audioLevel} />

                    {/* Messages */}
                    {messages.length > 0 && (
                      <div className="w-full max-w-3xl mt-8 space-y-4">
                        <AnimatePresence>
                          {messages.slice(-10).map((msg) => (
                            <motion.div
                              key={msg.id}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              className={`flex ${
                                msg.role === 'user' ? 'justify-end' : 'justify-start'
                              }`}
                            >
                              <div className={`max-w-lg px-4 py-3 rounded-2xl ${
                                msg.role === 'user'
                                  ? 'bg-indigo-500 text-white rounded-br-sm'
                                  : 'bg-gray-800 text-gray-100 rounded-bl-sm border border-gray-700'
                              }`}>
                                <p className="text-sm leading-relaxed">
                                  {msg.content}
                                </p>
                                {msg.tools_used && msg.tools_used.length > 0 && (
                                  <div className="flex flex-wrap gap-1 mt-2">
                                    {msg.tools_used.map((tool, i) => (
                                      <span
                                        key={i}
                                        className="px-1.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded text-xs"
                                      >
                                        {tool}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                        <div ref={messagesEndRef} />
                      </div>
                    )}

                    {/* Empty state */}
                    {messages.length === 0 && (
                      <div className="mt-8 text-center">
                        <p className="text-gray-500 text-sm mb-6">
                          Try saying something...
                        </p>
                        <div className="flex flex-wrap justify-center gap-2 max-w-lg">
                          {[
                            "Chrome kholo",
                            "System status bata",
                            "Battery kitni hai?",
                            "Downloads mein kya hai?",
                            "Screenshot le",
                            "Phone connect karo",
                          ].map((suggestion) => (
                            <motion.button
                              key={suggestion}
                              onClick={() => sendTextMessage(suggestion)}
                              className="px-4 py-2 bg-gray-800/70 hover:bg-gray-700 rounded-xl text-sm text-gray-400 hover:text-white transition-colors border border-gray-700/50"
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                            >
                              {suggestion}
                            </motion.button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* VOICE INPUT */}
                  <VoiceInput
                    isListening={isListening}
                    transcript={transcript}
                    onStartListening={toggleListening}
                    onStopListening={toggleListening}
                    onSendText={sendTextMessage}
                    onCancel={cancelTask}
                    isProcessing={['processing', 'thinking', 'executing'].includes(agentState)}
                    audioLevel={audioLevel}
                  />
                </motion.div>
              )}

              {/* PHONE */}
              {activeSection === 'phone' && (
                <motion.div
                  key="phone"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 overflow-hidden"
                >
                  <PhoneHub />
                </motion.div>
              )}

              {/* SYSTEM */}
              {activeSection === 'system' && (
                <motion.div
                  key="system"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 overflow-hidden"
                >
                  <SystemDashboard
                    stats={systemStats}
                    history={statsHistory}
                  />
                </motion.div>
              )}

              {/* SMART HOME */}
              {activeSection === 'smart_home' && (
                <motion.div
                  key="smart_home"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 overflow-y-auto p-6"
                >
                  <SmartHomePanel onCommand={sendTextMessage} />
                </motion.div>
              )}

            </AnimatePresence>
          </div>

          {/* RIGHT PANEL */}
          <AnimatePresence>
            {isRightPanelOpen && (
              <motion.aside
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 320, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="border-l border-gray-800/50 bg-gray-900/50 overflow-hidden flex flex-col"
              >
                <div className="p-4 border-b border-gray-800/50">
                  <h2 className="text-sm font-semibold text-gray-400">
                    Agent Context
                  </h2>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {/* Timeline */}
                  <CommandTimeline
                    events={currentTimeline}
                    currentStep={currentTask || undefined}
                  />

                  {/* Quick Stats */}
                  <div className="glass-panel rounded-xl p-4 space-y-3">
                    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      System
                    </h3>
                    {[
                      { label: 'CPU', value: systemStats.cpu, color: '#6366F1' },
                      { label: 'Memory', value: systemStats.memory, color: '#8B5CF6' },
                      { label: 'Disk', value: systemStats.disk, color: '#EC4899' },
                    ].map((stat) => (
                      <div key={stat.label}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-gray-400">{stat.label}</span>
                          <span className="text-gray-300">{stat.value.toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 bg-gray-700 rounded-full">
                          <motion.div
                            className="h-full rounded-full"
                            style={{ backgroundColor: stat.color }}
                            animate={{ width: `${stat.value}%` }}
                            transition={{ duration: 0.5 }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.aside>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* GLOBAL SEARCH */}
      <AnimatePresence>
        {searchOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-center pt-32"
            onClick={() => setSearchOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, y: -20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: -20 }}
              className="w-full max-w-2xl mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="glass-panel rounded-2xl border border-gray-700/50 overflow-hidden">
                <div className="flex items-center gap-3 p-4 border-b border-gray-700/50">
                  <Search className="w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        sendTextMessage(searchQuery);
                        setSearchOpen(false);
                        setSearchQuery('');
                      }
                    }}
                    placeholder="NEXA ko command do ya search karo..."
                    className="flex-1 bg-transparent text-white text-lg outline-none placeholder-gray-500"
                    autoFocus
                  />
                  <kbd className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
                    Esc
                  </kbd>
                </div>

                {/* Quick commands */}
                <div className="p-2">
                  {[
                    { icon: <Terminal />, label: 'Open Terminal', cmd: 'terminal kholo' },
                    { icon: <Globe />, label: 'Open Browser', cmd: 'chrome kholo' },
                    { icon: <Activity />, label: 'System Status', cmd: 'system status bata' },
                    { icon: <Smartphone />, label: 'Phone Control', cmd: 'phone connect karo' },
                    { icon: <Camera />, label: 'Screenshot', cmd: 'screenshot lo' },
                    { icon: <Shield />, label: 'Security Check', cmd: 'security check karo' },
                  ].map((item) => (
                    <motion.button
                      key={item.cmd}
                      onClick={() => {
                        sendTextMessage(item.cmd);
                        setSearchOpen(false);
                        setSearchQuery('');
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-800 rounded-xl transition-colors text-left"
                      whileHover={{ x: 4 }}
                    >
                      <span className="text-gray-400 w-4 h-4">{item.icon}</span>
                      <span className="text-gray-300 text-sm">{item.label}</span>
                      <span className="ml-auto text-gray-600 text-xs">{item.cmd}</span>
                    </motion.button>
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Helper Components
const AgentStateBadge: React.FC<{ state: AgentState }> = ({ state }) => {
  const config = {
    idle: { color: 'text-gray-400', bg: 'bg-gray-800', label: 'Ready', dot: 'bg-gray-500' },
    listening: { color: 'text-blue-400', bg: 'bg-blue-500/20', label: 'Listening', dot: 'bg-blue-400' },
    processing: { color: 'text-yellow-400', bg: 'bg-yellow-500/20', label: 'Processing', dot: 'bg-yellow-400' },
    thinking: { color: 'text-purple-400', bg: 'bg-purple-500/20', label: 'Thinking', dot: 'bg-purple-400' },
    executing: { color: 'text-green-400', bg: 'bg-green-500/20', label: 'Executing', dot: 'bg-green-400' },
    speaking: { color: 'text-indigo-400', bg: 'bg-indigo-500/20', label: 'Speaking', dot: 'bg-indigo-400' },
    error: { color: 'text-red-400', bg: 'bg-red-500/20', label: 'Error', dot: 'bg-red-400' },
  };

  const c = config[state] || config.idle;

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${c.bg}`}>
      <div className={`w-2 h-2 rounded-full ${c.dot} ${
        state !== 'idle' ? 'animate-pulse' : ''
      }`} />
      <span className={`text-xs font-medium ${c.color}`}>{c.label}</span>
    </div>
  );
};

const MiniStat: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}> = ({ icon, label, value, color }) => (
  <div className="flex items-center gap-2">
    <span className="text-gray-500">{icon}</span>
    <span className="text-xs text-gray-500 w-8">{label}</span>
    <div className="flex-1 h-1 bg-gray-700 rounded-full">
      <motion.div
        className="h-full rounded-full"
        style={{ backgroundColor: color }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.5 }}
      />
    </div>
    <span className="text-xs text-gray-400 w-8 text-right">
      {value.toFixed(0)}%
    </span>
  </div>
);

const SmartHomePanel: React.FC<{ onCommand: (cmd: string) => void }> = ({ onCommand }) => {
  const scenes = [
    { name: 'Movie Mode', emoji: '🎬', cmd: 'movie mode activate karo' },
    { name: 'Good Night', emoji: '🌙', cmd: 'good night mode set karo' },
    { name: 'Good Morning', emoji: '☀️', cmd: 'good morning mode set karo' },
    { name: 'Party Mode', emoji: '🎉', cmd: 'party mode chalao' },
    { name: 'Focus Mode', emoji: '🎯', cmd: 'focus mode on karo' },
    { name: 'Relax Mode', emoji: '😌', cmd: 'relax mode activate karo' },
  ];

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-xl font-bold text-white mb-6">Smart Home Control</h2>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {scenes.map((scene) => (
          <motion.button
            key={scene.name}
            onClick={() => onCommand(scene.cmd)}
            className="glass-panel rounded-2xl p-6 text-center hover:bg-gray-800 transition-colors"
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
          >
            <span className="text-4xl block mb-2">{scene.emoji}</span>
            <p className="text-sm font-medium text-white">{scene.name}</p>
          </motion.button>
        ))}
      </div>

      <div className="glass-panel rounded-2xl p-4">
        <p className="text-sm text-gray-400 mb-3">Quick Commands</p>
        <div className="space-y-2">
          {[
            "Saari lights off karo",
            "Living room ki lights dim karo",
            "AC 22 degree pe set karo",
            "Main door lock karo",
          ].map((cmd) => (
            <motion.button
              key={cmd}
              onClick={() => onCommand(cmd)}
              className="w-full text-left px-4 py-3 bg-gray-800/50 hover:bg-gray-700 rounded-xl text-sm text-gray-300 transition-colors"
              whileHover={{ x: 4 }}
            >
              💡 {cmd}
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
};
