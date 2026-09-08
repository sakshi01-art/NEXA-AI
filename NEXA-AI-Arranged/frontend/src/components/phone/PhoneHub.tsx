import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smartphone, Wifi, Usb, Battery, BatteryCharging,
  HardDrive, Signal, Monitor, MessageSquare, Phone,
  Bell, Music, Camera, Map, Settings, Download,
  Upload, Zap, Power, Volume2, Sun, Bluetooth,
  RefreshCw, Mic, Lock, Unlock, Grid, List,
  Search, Plus, Trash2, Send, Image, File,
  Play, Pause, SkipForward, SkipBack, Square,
  ChevronLeft, ChevronRight, X, Check, AlertTriangle
} from 'lucide-react';

interface Device {
  id: string;
  name: string;
  model: string;
  manufacturer: string;
  connection_type: 'usb' | 'wifi';
  battery_level: number;
  is_charging: boolean;
  is_online: boolean;
  android_version: string;
  storage_total_gb: number;
  storage_free_gb: number;
  screen_width: number;
  screen_height: number;
}

interface Notification {
  id: string;
  app_name: string;
  icon: string;
  title: string;
  text: string;
  timestamp: string;
  can_reply: boolean;
  package: string;
}

interface Message {
  id: string;
  address: string;
  body: string;
  date: string;
  type: 'sent' | 'received';
  read: boolean;
}

type PhoneTab = 'overview' | 'mirror' | 'files' | 'apps' | 
               'messages' | 'calls' | 'notifications' | 
               'media' | 'settings';

export const PhoneHub: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [activeDevice, setActiveDevice] = useState<Device | null>(null);
  const [activeTab, setActiveTab] = useState<PhoneTab>('overview');
  const [isConnecting, setIsConnecting] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isMirroring, setIsMirroring] = useState(false);
  const [mirrorFrame, setMirrorFrame] = useState<string | null>(null);
  const [mirrorFps, setMirrorFps] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [composeText, setComposeText] = useState('');
  const [apps, setApps] = useState<any[]>([]);
  const [files, setFiles] = useState<any[]>([]);
  const [currentPath, setCurrentPath] = useState('/sdcard');
  const [batteryHistory, setBatteryHistory] = useState<number[]>([]);
  
  const wsRef = useRef<WebSocket | null>(null);
  const mirrorCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // Connect to backend WebSocket
  useEffect(() => {
    const wsUrl = window.location.port === '3000' ? 'ws://localhost:8000/phone' : `ws://${window.location.host}/phone`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onopen = () => {
      sendCommand({ type: 'scan_devices' });
    };

    return () => ws.close();
  }, []);

  // Auto-scan devices every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      sendCommand({ type: 'scan_devices' });
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Battery history tracking
  useEffect(() => {
    if (activeDevice?.battery_level) {
      setBatteryHistory(prev => [...prev.slice(-20), activeDevice.battery_level]);
    }
  }, [activeDevice?.battery_level]);

  const sendCommand = useCallback((command: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(command));
    }
  }, []);

  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'devices_list':
        setDevices(data.devices || []);
        if (data.devices?.length > 0 && !activeDevice) {
          setActiveDevice(data.devices[0]);
        }
        break;

      case 'device_update':
        setDevices(prev => prev.map(d =>
          d.id === data.device.id ? { ...d, ...data.device } : d
        ));
        if (activeDevice?.id === data.device.id) {
          setActiveDevice(prev => prev ? { ...prev, ...data.device } : null);
        }
        break;

      case 'screen_frame':
        setMirrorFrame(data.frame);
        setMirrorFps(data.fps || 0);
        drawFrame(data.frame);
        break;

      case 'notifications':
        setNotifications(data.notifications || []);
        break;

      case 'new_notification':
        setNotifications(prev => [data.notification, ...prev].slice(0, 50));
        break;

      case 'messages':
        setMessages(data.messages || []);
        break;

      case 'apps_list':
        setApps(data.apps || []);
        break;

      case 'files_list':
        setFiles(data.files || []);
        break;
    }
  }, [activeDevice]);

  const drawFrame = useCallback((frameB64: string) => {
    const canvas = mirrorCanvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new window.Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
    };
    img.src = `data:image/jpeg;base64,${frameB64}`;
  }, []);

  const startMirror = useCallback(() => {
    if (!activeDevice) return;
    setIsMirroring(true);
    sendCommand({
      type: 'start_mirror',
      device_id: activeDevice.id,
      fps: 20,
      quality: 80
    });
  }, [activeDevice, sendCommand]);

  const stopMirror = useCallback(() => {
    setIsMirroring(false);
    setMirrorFrame(null);
    sendCommand({ type: 'stop_mirror' });
  }, [sendCommand]);

  const handleCanvasTap = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!activeDevice || !isMirroring) return;

    const canvas = mirrorCanvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = activeDevice.screen_width / rect.width;
    const scaleY = activeDevice.screen_height / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    sendCommand({
      type: 'tap',
      device_id: activeDevice.id,
      x, y
    });
  }, [activeDevice, isMirroring, sendCommand]);

  const sendReply = useCallback((notification: Notification) => {
    const reply = prompt(`Reply to ${notification.app_name}:`);
    if (reply && activeDevice) {
      sendCommand({
        type: 'reply_notification',
        device_id: activeDevice.id,
        package: notification.package,
        reply
      });
    }
  }, [activeDevice, sendCommand]);

  const sendMessage = useCallback(() => {
    if (!composeText.trim() || !activeDevice || !selectedConversation) return;
    
    sendCommand({
      type: 'send_sms',
      device_id: activeDevice.id,
      phone_number: selectedConversation,
      message: composeText
    });
    
    setComposeText('');
  }, [composeText, activeDevice, selectedConversation, sendCommand]);

  const tabs: { id: PhoneTab; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <Smartphone className="w-4 h-4" /> },
    { id: 'mirror', label: 'Screen', icon: <Monitor className="w-4 h-4" /> },
    { id: 'messages', label: 'Messages', icon: <MessageSquare className="w-4 h-4" /> },
    { id: 'notifications', label: 'Alerts', icon: <Bell className="w-4 h-4" /> },
    { id: 'files', label: 'Files', icon: <File className="w-4 h-4" /> },
    { id: 'apps', label: 'Apps', icon: <Grid className="w-4 h-4" /> },
    { id: 'media', label: 'Media', icon: <Music className="w-4 h-4" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-4 h-4" /> },
  ];

  if (devices.length === 0) {
    return <NoDeviceConnected onScan={() => sendCommand({ type: 'scan_devices' })} />;
  }

  return (
    <div className="h-full flex flex-col bg-gray-950">
      {/* Device Selector Header */}
      <div className="glass-panel border-b border-gray-700/50 p-4">
        <div className="flex items-center gap-4 overflow-x-auto">
          {devices.map((device) => (
            <DeviceChip
              key={device.id}
              device={device}
              isActive={activeDevice?.id === device.id}
              onClick={() => setActiveDevice(device)}
            />
          ))}

          <motion.button
            onClick={() => sendCommand({ type: 'scan_devices' })}
            className="flex-shrink-0 w-10 h-10 rounded-xl bg-gray-800 hover:bg-gray-700 flex items-center justify-center transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title="Scan for devices"
          >
            <RefreshCw className="w-4 h-4 text-gray-400" />
          </motion.button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 p-2 overflow-x-auto border-b border-gray-700/50">
        {tabs.map((tab) => (
          <motion.button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all flex-shrink-0 ${
              activeTab === tab.id
                ? 'bg-indigo-500 text-white shadow-lg'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </motion.button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && activeDevice && (
            <motion.div
              key="overview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full overflow-y-auto p-4 space-y-4"
            >
              {/* Device Status Card */}
              <div className="glass-panel rounded-2xl p-6">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      {activeDevice.name}
                    </h2>
                    <p className="text-gray-400 text-sm mt-1">
                      Android {activeDevice.android_version}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${
                      activeDevice.is_online ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className="text-sm text-gray-400">
                      {activeDevice.connection_type === 'wifi' ? (
                        <Wifi className="w-4 h-4 inline mr-1" />
                      ) : (
                        <Usb className="w-4 h-4 inline mr-1" />
                      )}
                      {activeDevice.connection_type.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <StatBox
                    icon={activeDevice.is_charging
                      ? <BatteryCharging className="w-5 h-5 text-green-400" />
                      : <Battery className="w-5 h-5 text-indigo-400" />
                    }
                    label="Battery"
                    value={`${activeDevice.battery_level}%`}
                    subtext={activeDevice.is_charging ? 'Charging' : 'Discharging'}
                    color={
                      activeDevice.battery_level < 20 ? 'red' :
                      activeDevice.battery_level < 50 ? 'yellow' : 'green'
                    }
                  />
                  <StatBox
                    icon={<HardDrive className="w-5 h-5 text-purple-400" />}
                    label="Storage"
                    value={`${activeDevice.storage_free_gb}GB`}
                    subtext="Free"
                    color="purple"
                  />
                  <StatBox
                    icon={<Signal className="w-5 h-5 text-blue-400" />}
                    label="Screen"
                    value={`${activeDevice.screen_width}p`}
                    subtext={`${activeDevice.screen_width}×${activeDevice.screen_height}`}
                    color="blue"
                  />
                </div>
              </div>

              {/* Quick Actions */}
              <div className="glass-panel rounded-2xl p-4">
                <h3 className="text-sm font-semibold text-gray-400 mb-3">
                  Quick Actions
                </h3>
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { icon: <Monitor />, label: 'Mirror', action: () => { setActiveTab('mirror'); startMirror(); } },
                    { icon: <Camera />, label: 'Screenshot', action: () => sendCommand({ type: 'screenshot', device_id: activeDevice.id }) },
                    { icon: <Power />, label: 'Home', action: () => sendCommand({ type: 'key', device_id: activeDevice.id, key: 'KEYCODE_HOME' }) },
                    { icon: <ChevronLeft />, label: 'Back', action: () => sendCommand({ type: 'key', device_id: activeDevice.id, key: 'KEYCODE_BACK' }) },
                    { icon: <Volume2 />, label: 'Vol +', action: () => sendCommand({ type: 'key', device_id: activeDevice.id, key: 'KEYCODE_VOLUME_UP' }) },
                    { icon: <Sun />, label: 'Bright', action: () => sendCommand({ type: 'brightness', device_id: activeDevice.id, level: 200 }) },
                    { icon: <Lock />, label: 'Lock', action: () => sendCommand({ type: 'key', device_id: activeDevice.id, key: 'KEYCODE_POWER' }) },
                    { icon: <Zap />, label: 'Wake', action: () => sendCommand({ type: 'key', device_id: activeDevice.id, key: 'KEYCODE_WAKEUP' }) },
                  ].map((action, i) => (
                    <QuickActionButton key={i} {...action} />
                  ))}
                </div>
              </div>

              {/* Battery Chart */}
              <div className="glass-panel rounded-2xl p-4">
                <h3 className="text-sm font-semibold text-gray-400 mb-3">
                  Battery History
                </h3>
                <MiniLineChart data={batteryHistory} color="#10B981" />
              </div>
            </motion.div>
          )}

          {/* SCREEN MIRROR TAB */}
          {activeTab === 'mirror' && (
            <motion.div
              key="mirror"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex"
            >
              {/* Mirror Canvas */}
              <div className="flex-1 flex flex-col items-center justify-center bg-black p-4">
                {isMirroring ? (
                  <div className="relative">
                    {/* Phone Frame */}
                    <div className="relative bg-gray-900 rounded-[2rem] p-3 shadow-2xl border border-gray-700">
                      <canvas
                        ref={mirrorCanvasRef}
                        className="rounded-[1.5rem] cursor-pointer"
                        style={{ maxHeight: '70vh', maxWidth: '100%' }}
                        onClick={handleCanvasTap}
                        onContextMenu={(e) => {
                          e.preventDefault();
                          sendCommand({
                            type: 'key',
                            device_id: activeDevice?.id,
                            key: 'KEYCODE_BACK'
                          });
                        }}
                      />

                      {/* FPS Badge */}
                      <div className="absolute top-4 right-4 bg-black/60 px-2 py-1 rounded-lg">
                        <span className="text-xs text-green-400 font-mono">
                          {mirrorFps} FPS
                        </span>
                      </div>
                    </div>

                    {/* Mirror Controls */}
                    <div className="flex justify-center gap-2 mt-4">
                      <MirrorButton
                        icon={<ChevronLeft />}
                        label="Back"
                        onClick={() => sendCommand({
                          type: 'key',
                          device_id: activeDevice?.id,
                          key: 'KEYCODE_BACK'
                        })}
                      />
                      <MirrorButton
                        icon={<Power />}
                        label="Home"
                        onClick={() => sendCommand({
                          type: 'key',
                          device_id: activeDevice?.id,
                          key: 'KEYCODE_HOME'
                        })}
                      />
                      <MirrorButton
                        icon={<Grid />}
                        label="Recents"
                        onClick={() => sendCommand({
                          type: 'key',
                          device_id: activeDevice?.id,
                          key: 'KEYCODE_APP_SWITCH'
                        })}
                      />
                      <MirrorButton
                        icon={<Camera />}
                        label="Screenshot"
                        onClick={() => sendCommand({
                          type: 'screenshot',
                          device_id: activeDevice?.id
                        })}
                      />
                      <MirrorButton
                        icon={<Square />}
                        label="Stop"
                        onClick={stopMirror}
                        color="red"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="text-center">
                    <motion.div
                      animate={{ y: [0, -10, 0] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      <Smartphone className="w-24 h-24 text-gray-700 mx-auto mb-6" />
                    </motion.div>
                    <h3 className="text-white text-xl font-semibold mb-2">
                      Screen Mirror
                    </h3>
                    <p className="text-gray-400 mb-6">
                      Phone ki screen yahan dikhao
                    </p>
                    <motion.button
                      onClick={startMirror}
                      disabled={!activeDevice}
                      className="px-8 py-4 bg-indigo-500 hover:bg-indigo-600 text-white rounded-2xl font-semibold flex items-center gap-3 mx-auto transition-colors disabled:opacity-50"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <Monitor className="w-5 h-5" />
                      Start Mirroring
                    </motion.button>
                    <p className="text-gray-600 text-sm mt-4">
                      Click anywhere on screen to tap • Right-click to go back
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* MESSAGES TAB */}
          {activeTab === 'messages' && (
            <motion.div
              key="messages"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex"
            >
              {/* Conversations List */}
              <div className="w-72 border-r border-gray-700/50 flex flex-col">
                <div className="p-3 border-b border-gray-700/50">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search messages..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-gray-800 text-white pl-10 pr-4 py-2 rounded-lg text-sm outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto">
                  {messages.length === 0 ? (
                    <div className="p-4 text-center">
                      <MessageSquare className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                      <p className="text-gray-500 text-sm">
                        No messages loaded
                      </p>
                      <button
                        onClick={() => sendCommand({
                          type: 'get_messages',
                          device_id: activeDevice?.id
                        })}
                        className="mt-2 text-indigo-400 text-sm hover:text-indigo-300"
                      >
                        Load messages
                      </button>
                    </div>
                  ) : (
                    messages.map((msg) => (
                      <motion.div
                        key={msg.id}
                        onClick={() => setSelectedConversation(msg.address)}
                        className={`p-3 cursor-pointer hover:bg-gray-800/50 transition-colors border-b border-gray-700/30 ${
                          selectedConversation === msg.address
                            ? 'bg-gray-800'
                            : ''
                        } ${!msg.read ? 'bg-indigo-500/5' : ''}`}
                        whileHover={{ x: 2 }}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-indigo-500/30 flex items-center justify-center flex-shrink-0">
                            <span className="text-indigo-300 text-sm font-bold">
                              {msg.address.slice(-4)}
                            </span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start">
                              <p className="text-sm font-medium text-white truncate">
                                {msg.address}
                              </p>
                              <p className="text-xs text-gray-500 flex-shrink-0 ml-2">
                                {msg.date}
                              </p>
                            </div>
                            <p className={`text-xs truncate mt-0.5 ${
                              !msg.read ? 'text-white font-medium' : 'text-gray-400'
                            }`}>
                              {msg.type === 'sent' ? '↑ ' : ''}{msg.body}
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    ))
                  )}
                </div>

                {/* New Message Button */}
                <div className="p-3 border-t border-gray-700/50">
                  <motion.button
                    className="w-full py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl flex items-center justify-center gap-2 text-sm transition-colors"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Plus className="w-4 h-4" />
                    New Message
                  </motion.button>
                </div>
              </div>

              {/* Message Thread */}
              <div className="flex-1 flex flex-col">
                {selectedConversation ? (
                  <>
                    {/* Thread Header */}
                    <div className="p-4 border-b border-gray-700/50 flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-indigo-500/30 flex items-center justify-center">
                        <span className="text-indigo-300 text-sm font-bold">
                          {selectedConversation.slice(-4)}
                        </span>
                      </div>
                      <div>
                        <p className="text-white font-medium">{selectedConversation}</p>
                        <p className="text-xs text-gray-400">via Phone</p>
                      </div>
                      <div className="ml-auto flex gap-2">
                        <motion.button
                          onClick={() => sendCommand({
                            type: 'make_call',
                            device_id: activeDevice?.id,
                            phone_number: selectedConversation
                          })}
                          className="p-2 rounded-lg bg-green-500/20 hover:bg-green-500/30 transition-colors"
                          whileHover={{ scale: 1.05 }}
                        >
                          <Phone className="w-4 h-4 text-green-400" />
                        </motion.button>
                      </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                      {messages
                        .filter(m => m.address === selectedConversation)
                        .map((msg) => (
                          <div
                            key={msg.id}
                            className={`flex ${
                              msg.type === 'sent' ? 'justify-end' : 'justify-start'
                            }`}
                          >
                            <div className={`max-w-xs px-4 py-2 rounded-2xl ${
                              msg.type === 'sent'
                                ? 'bg-indigo-500 text-white rounded-br-sm'
                                : 'bg-gray-800 text-gray-100 rounded-bl-sm'
                            }`}>
                              <p className="text-sm">{msg.body}</p>
                              <p className={`text-xs mt-1 ${
                                msg.type === 'sent'
                                  ? 'text-indigo-200'
                                  : 'text-gray-500'
                              }`}>
                                {msg.date}
                              </p>
                            </div>
                          </div>
                        ))
                      }
                    </div>

                    {/* Compose */}
                    <div className="p-4 border-t border-gray-700/50">
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={composeText}
                          onChange={(e) => setComposeText(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                          placeholder="Type a message..."
                          className="flex-1 bg-gray-800 text-white px-4 py-3 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
                        />
                        <motion.button
                          onClick={sendMessage}
                          disabled={!composeText.trim()}
                          className="px-4 py-3 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white rounded-xl transition-colors"
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <Send className="w-4 h-4" />
                        </motion.button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                      <MessageSquare className="w-12 h-12 text-gray-700 mx-auto mb-3" />
                      <p className="text-gray-500">
                        Select a conversation
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* NOTIFICATIONS TAB */}
          {activeTab === 'notifications' && (
            <motion.div
              key="notifications"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex flex-col"
            >
              <div className="p-4 border-b border-gray-700/50 flex justify-between">
                <h3 className="font-semibold text-white">
                  Phone Notifications ({notifications.length})
                </h3>
                <motion.button
                  onClick={() => sendCommand({
                    type: 'dismiss_all_notifications',
                    device_id: activeDevice?.id
                  })}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                  whileHover={{ scale: 1.05 }}
                >
                  Clear All
                </motion.button>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                <AnimatePresence>
                  {notifications.map((notif) => (
                    <motion.div
                      key={notif.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="glass-panel rounded-xl p-4 flex items-start gap-3"
                    >
                      <span className="text-2xl flex-shrink-0">
                        {notif.icon}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start">
                          <p className="text-xs font-medium text-indigo-400">
                            {notif.app_name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {notif.timestamp}
                          </p>
                        </div>
                        <p className="text-sm font-semibold text-white mt-0.5">
                          {notif.title}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">
                          {notif.text}
                        </p>
                        {notif.can_reply && (
                          <motion.button
                            onClick={() => sendReply(notif)}
                            className="mt-2 flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
                            whileHover={{ scale: 1.05 }}
                          >
                            <Send className="w-3 h-3" />
                            Reply
                          </motion.button>
                        )}
                      </div>
                      <motion.button
                        onClick={() => sendCommand({
                          type: 'dismiss_notification',
                          device_id: activeDevice?.id,
                          notification_id: notif.id
                        })}
                        className="p-1 rounded-lg hover:bg-gray-700 transition-colors flex-shrink-0"
                        whileHover={{ scale: 1.1 }}
                      >
                        <X className="w-3 h-3 text-gray-400" />
                      </motion.button>
                    </motion.div>
                  ))}

                  {notifications.length === 0 && (
                    <div className="text-center py-12">
                      <Bell className="w-12 h-12 text-gray-700 mx-auto mb-3" />
                      <p className="text-gray-500">No notifications</p>
                      <button
                        onClick={() => sendCommand({
                          type: 'get_notifications',
                          device_id: activeDevice?.id
                        })}
                        className="mt-2 text-indigo-400 text-sm hover:text-indigo-300"
                      >
                        Refresh
                      </button>
                    </div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )}

          {/* MEDIA TAB */}
          {activeTab === 'media' && (
            <motion.div
              key="media"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex flex-col items-center justify-center p-8"
            >
              <div className="w-full max-w-sm">
                {/* Album Art Placeholder */}
                <div className="w-48 h-48 mx-auto rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-6 shadow-2xl">
                  <Music className="w-16 h-16 text-white/50" />
                </div>

                <div className="text-center mb-8">
                  <p className="text-white font-semibold text-lg">
                    Media Controller
                  </p>
                  <p className="text-gray-400 text-sm mt-1">
                    Phone pe media control karo
                  </p>
                </div>

                {/* Media Controls */}
                <div className="flex items-center justify-center gap-4">
                  <MediaButton
                    icon={<SkipBack className="w-5 h-5" />}
                    onClick={() => sendCommand({
                      type: 'media_control',
                      device_id: activeDevice?.id,
                      action: 'previous'
                    })}
                  />
                  <MediaButton
                    icon={<Play className="w-6 h-6" />}
                    size="lg"
                    onClick={() => sendCommand({
                      type: 'media_control',
                      device_id: activeDevice?.id,
                      action: 'play_pause'
                    })}
                  />
                  <MediaButton
                    icon={<SkipForward className="w-5 h-5" />}
                    onClick={() => sendCommand({
                      type: 'media_control',
                      device_id: activeDevice?.id,
                      action: 'next'
                    })}
                  />
                </div>

                {/* Volume Slider */}
                <div className="mt-6">
                  <div className="flex items-center gap-3">
                    <Volume2 className="w-4 h-4 text-gray-400" />
                    <input
                      type="range"
                      min="0"
                      max="15"
                      defaultValue="8"
                      className="flex-1 accent-indigo-500"
                      onChange={(e) => sendCommand({
                        type: 'set_volume',
                        device_id: activeDevice?.id,
                        level: parseInt(e.target.value)
                      })}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

// Sub Components
const DeviceChip: React.FC<{
  device: Device;
  isActive: boolean;
  onClick: () => void;
}> = ({ device, isActive, onClick }) => (
  <motion.button
    onClick={onClick}
    className={`flex items-center gap-3 px-4 py-2 rounded-xl flex-shrink-0 transition-all ${
      isActive
        ? 'bg-indigo-500 text-white'
        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
    }`}
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
  >
    <Smartphone className="w-4 h-4" />
    <div className="text-left">
      <p className="text-sm font-medium">{device.model}</p>
      <p className="text-xs opacity-70">
        {device.battery_level}% •
        {device.connection_type === 'wifi' ? ' WiFi' : ' USB'}
      </p>
    </div>
    <div className={`w-2 h-2 rounded-full ${
      device.is_online ? 'bg-green-400' : 'bg-red-400'
    }`} />
  </motion.button>
);

const StatBox: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string;
  subtext: string;
  color: string;
}> = ({ icon, label, value, subtext, color }) => (
  <div className={`bg-${color}-500/10 border border-${color}-500/20 rounded-xl p-3`}>
    <div className="flex items-center gap-2 mb-1">
      {icon}
      <span className="text-xs text-gray-400">{label}</span>
    </div>
    <p className="text-2xl font-bold text-white">{value}</p>
    <p className="text-xs text-gray-400">{subtext}</p>
  </div>
);

const QuickActionButton: React.FC<{
  icon: React.ReactNode;
  label: string;
  action: () => void;
}> = ({ icon, label, action }) => (
  <motion.button
    onClick={action}
    className="flex flex-col items-center gap-1 p-3 rounded-xl bg-gray-800/50 hover:bg-gray-700 transition-colors"
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
  >
    <span className="text-indigo-400">{icon}</span>
    <span className="text-xs text-gray-400">{label}</span>
  </motion.button>
);

const MirrorButton: React.FC<{
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  color?: string;
}> = ({ icon, label, onClick, color = 'gray' }) => (
  <motion.button
    onClick={onClick}
    className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl ${
      color === 'red'
        ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400'
        : 'bg-gray-800 hover:bg-gray-700 text-gray-400'
    } transition-colors`}
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
  >
    {icon}
    <span className="text-xs">{label}</span>
  </motion.button>
);

const MediaButton: React.FC<{
  icon: React.ReactNode;
  onClick: () => void;
  size?: 'sm' | 'lg';
}> = ({ icon, onClick, size = 'sm' }) => (
  <motion.button
    onClick={onClick}
    className={`flex items-center justify-center rounded-full transition-colors ${
      size === 'lg'
        ? 'w-16 h-16 bg-indigo-500 hover:bg-indigo-600 text-white'
        : 'w-12 h-12 bg-gray-800 hover:bg-gray-700 text-gray-300'
    }`}
    whileHover={{ scale: 1.1 }}
    whileTap={{ scale: 0.9 }}
  >
    {icon}
  </motion.button>
);

const MiniLineChart: React.FC<{
  data: number[];
  color: string;
}> = ({ data, color }) => {
  if (data.length < 2) return (
    <div className="h-12 flex items-center justify-center text-gray-600 text-sm">
      Collecting data...
    </div>
  );

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((val, i) => ({
    x: (i / (data.length - 1)) * 100,
    y: 100 - ((val - min) / range) * 100
  }));

  const pathD = points.reduce((d, pt, i) =>
    i === 0 ? `M ${pt.x} ${pt.y}` : `${d} L ${pt.x} ${pt.y}`,
    ''
  );

  return (
    <svg viewBox="0 0 100 100" className="h-12 w-full" preserveAspectRatio="none">
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
      <circle
        cx={points[points.length - 1]?.x}
        cy={points[points.length - 1]?.y}
        r="3"
        fill={color}
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
};

const NoDeviceConnected: React.FC<{ onScan: () => void }> = ({ onScan }) => (
  <div className="h-full flex flex-col items-center justify-center p-8 text-center">
    <motion.div
      animate={{ y: [0, -15, 0] }}
      transition={{ duration: 3, repeat: Infinity }}
    >
      <Smartphone className="w-24 h-24 text-gray-700 mx-auto mb-6" />
    </motion.div>

    <h2 className="text-2xl font-bold text-white mb-2">
      No Phone Connected
    </h2>
    <p className="text-gray-400 max-w-sm mb-8">
      Android phone connect karo via USB ya WiFi
    </p>

    <div className="space-y-4 text-left max-w-sm w-full mb-8">
      {[
        { icon: <Usb className="w-5 h-5" />, title: 'USB Connection', desc: 'Phone ko USB se connect karo aur USB Debugging enable karo (Settings → Developer Options)' },
        { icon: <Wifi className="w-5 h-5" />, title: 'WiFi Connection', desc: 'Same WiFi pe hona chahiye. Pehle USB se connect karo phir wireless enable karo.' },
      ].map((step, i) => (
        <div key={i} className="glass-panel rounded-xl p-4 flex gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0 text-indigo-400">
            {step.icon}
          </div>
          <div>
            <p className="text-sm font-semibold text-white">{step.title}</p>
            <p className="text-xs text-gray-400 mt-0.5">{step.desc}</p>
          </div>
        </div>
      ))}
    </div>

    <motion.button
      onClick={onScan}
      className="px-8 py-4 bg-indigo-500 hover:bg-indigo-600 text-white rounded-2xl font-semibold flex items-center gap-3 transition-colors"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <RefreshCw className="w-5 h-5" />
      Scan for Devices
    </motion.button>
  </div>
);
