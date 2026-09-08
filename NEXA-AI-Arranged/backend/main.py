import asyncio
import json
import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from schemas import AgentState
from websocket_server import NexaWebSocketServer
from agent.brain import AgentBrain
from agent.hinglish_engine import HinglishEngine
from agent.persona import NexaPersona
from agent.proactive import ProactiveAssistant
from agent.emotion_engine import EmotionEngine
from agent.ambient_intelligence import AmbientIntelligence
from agent.dream_mode import DreamModeEngine
from agent.neural_shortcuts import NeuralShortcutSystem
from agent.time_travel import TimeTravelDebugger
from agent.digital_twin.twin_engine import DigitalTwinEngine
from ai.factory import AIProviderFactory
from voice.pipeline import VoicePipeline
from voice.stt.openai_whisper import OpenAIWhisperSTT
from voice.tts.elevenlabs import ElevenLabsTTS
from tools.registry import ToolRegistry
from tools.windows.applications import WindowsApplicationTools
from tools.filesystem.operations import FileSystemTools
from tools.system.monitor import SystemMonitorTools
from tools.browser.advanced_web import AdvancedWebAutomation
from tools.terminal.executor import TerminalExecutor
from tools.clipboard.smart_clipboard import SmartClipboardManager
from tools.vision.screen_analyzer import ScreenAnalyzer
from tools.code.code_intelligence import CodeIntelligenceEngine
from phone.device_manager import DeviceManager
from phone.adb_engine import ADBEngine
from phone.screen_mirror import ScreenMirrorEngine
from phone.notification_bridge import NotificationBridge
from phone.sms_manager import SMSManager
from features.meeting_assistant import MeetingAssistant
from features.smart_home import SmartHomeController
from features.voice_keyboard import VoiceKeyboard
from memory.vector_store import VectorMemoryStore
from security.validator import SecurityValidator
from security.permissions import PermissionManager
from security.audit import AuditLogger
from automation.scheduler import TaskScheduler
from plugins.plugin_manager import PluginManager

# ─────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────
app = FastAPI(
    title="NEXA AI Backend",
    version="1.0.0",
    description="NEXA AI - Intelligent Desktop Agent"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = Config()
connected_clients = set()

# ─────────────────────────────────────────
# Initialize All Systems
# ─────────────────────────────────────────

async def initialize_nexa():
    """Initialize all NEXA subsystems"""

    print("\n" + "="*50)
    print("  NEXA AI - Initializing...")
    print("="*50)

    # AI Provider
    ai_provider = AIProviderFactory.create(
        provider=config.AI_PROVIDER,
        api_key=config.AI_API_KEY,
        model=config.AI_MODEL
    )
    print(f"  ✓ AI Provider: {config.AI_PROVIDER}")

    # Voice Pipeline
    stt = OpenAIWhisperSTT(api_key=config.OPENAI_API_KEY)
    tts = ElevenLabsTTS(api_key=config.ELEVENLABS_API_KEY)
    voice_pipeline = VoicePipeline(stt_provider=stt, tts_provider=tts)
    print("  ✓ Voice Pipeline ready")

    # Memory Store
    memory_store = VectorMemoryStore(
        persist_directory=config.VECTOR_DB_PATH
    )
    print("  ✓ Memory Store ready")

    # Tool Registry
    tool_registry = ToolRegistry()
    _register_all_tools(tool_registry, ai_provider)
    print(f"  ✓ Tools registered: {len(tool_registry.tools)}")

    # Security
    security = SecurityValidator()
    permissions = PermissionManager()
    audit_logger = AuditLogger()
    print("  ✓ Security systems ready")

    # Agent Brain
    agent_brain = AgentBrain(
        ai_provider=ai_provider,
        tool_registry=tool_registry,
    )
    print("  ✓ Agent Brain ready")

    # Hinglish Engine
    hinglish = HinglishEngine()

    # Persona
    persona = NexaPersona(default_mood='friendly')

    # Digital Twin
    digital_twin = DigitalTwinEngine(
        ai_provider=ai_provider,
        memory_store=memory_store
    )

    # Phone Control
    adb_engine = ADBEngine()
    phone_manager = DeviceManager(
        adb_engine=adb_engine,
        ios_controller=None,
        notification_callback=_global_notify
    )
    screen_mirror = ScreenMirrorEngine(
        adb_engine=adb_engine,
        websocket_server=None
    )
    notification_bridge = NotificationBridge(
        adb_engine=adb_engine,
        notification_callback=_global_notify
    )
    sms_manager = SMSManager(adb_engine=adb_engine)
    print("  ✓ Phone Control ready")

    # Features
    meeting_assistant = MeetingAssistant(
        ai_provider=ai_provider,
        stt_provider=stt,
        notification_callback=_global_notify
    )
    smart_home = SmartHomeController(
        ai_provider=ai_provider,
        notification_callback=_global_notify
    )
    voice_keyboard = VoiceKeyboard(
        stt_provider=stt,
        ai_provider=ai_provider,
        notification_callback=_global_notify
    )
    print("  ✓ Features ready")

    # Proactive Assistant
    proactive = ProactiveAssistant(
        memory_store=memory_store,
        notification_callback=_global_notify
    )

    # Emotion Engine
    emotion_engine = EmotionEngine(
        ai_provider=ai_provider,
        notification_callback=_global_notify
    )

    # Ambient Intelligence
    ambient = AmbientIntelligence(
        ai_provider=ai_provider,
        notification_callback=_global_notify,
        tool_executor=tool_registry
    )

    # Neural Shortcuts
    shortcuts = NeuralShortcutSystem(ai_provider=ai_provider)

    # Time Travel
    time_travel = TimeTravelDebugger()

    # Dream Mode
    dream_mode = DreamModeEngine(
        tool_executor=tool_registry,
        ai_provider=ai_provider,
        notification_callback=_global_notify
    )

    # Automation Scheduler
    scheduler = TaskScheduler()

    # Plugin Manager
    plugin_manager = PluginManager(
        plugins_dir=config.PLUGINS_PATH,
        tool_registry=tool_registry
    )

    print("  ✓ All systems initialized!")
    print("="*50)
    print("  NEXA AI is ready! 🚀")
    print("="*50 + "\n")

    return {
        'ai_provider': ai_provider,
        'voice_pipeline': voice_pipeline,
        'memory_store': memory_store,
        'tool_registry': tool_registry,
        'agent_brain': agent_brain,
        'hinglish': hinglish,
        'persona': persona,
        'digital_twin': digital_twin,
        'adb_engine': adb_engine,
        'phone_manager': phone_manager,
        'screen_mirror': screen_mirror,
        'notification_bridge': notification_bridge,
        'sms_manager': sms_manager,
        'meeting_assistant': meeting_assistant,
        'smart_home': smart_home,
        'voice_keyboard': voice_keyboard,
        'proactive': proactive,
        'emotion_engine': emotion_engine,
        'ambient': ambient,
        'shortcuts': shortcuts,
        'time_travel': time_travel,
        'dream_mode': dream_mode,
        'scheduler': scheduler,
        'plugin_manager': plugin_manager,
        'security': security,
        'permissions': permissions,
        'audit_logger': audit_logger,
    }

def _register_all_tools(registry: ToolRegistry, ai_provider):
    """Register all available tools"""

    from schemas import PermissionLevel

    # Windows Application Tools
    app_tools = WindowsApplicationTools()
    registry.register(
        name="open_application",
        description="Open any Windows application by name",
        category="windows",
        permission=PermissionLevel.SAFE,
        schema={
            "type": "object",
            "properties": {
                "application": {"type": "string"},
                "arguments": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["application"]
        },
        handler=app_tools.open_application
    )

    registry.register(
        name="close_application",
        description="Close a running application",
        category="windows",
        permission=PermissionLevel.SAFE,
        schema={
            "type": "object",
            "properties": {
                "application": {"type": "string"}
            },
            "required": ["application"]
        },
        handler=app_tools.close_application
    )

    registry.register(
        name="list_running_applications",
        description="List all currently running applications",
        category="windows",
        permission=PermissionLevel.SAFE,
        schema={"type": "object", "properties": {}},
        handler=app_tools.list_running_applications
    )

    # File System Tools
    fs_tools = FileSystemTools()
    registry.register(
        name="list_files",
        description="List files in a directory",
        category="filesystem",
        permission=PermissionLevel.SAFE,
        schema={
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "pattern": {"type": "string"},
                "file_type": {"type": "string"}
            },
            "required": ["directory"]
        },
        handler=fs_tools.list_files
    )

    registry.register(
        name="read_file",
        description="Read contents of a text file",
        category="filesystem",
        permission=PermissionLevel.SAFE,
        schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "max_lines": {"type": "integer"}
            },
            "required": ["path"]
        },
        handler=fs_tools.read_text_file
    )

    registry.register(
        name="create_folder",
        description="Create a new folder",
        category="filesystem",
        permission=PermissionLevel.SAFE,
        schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        },
        handler=fs_tools.create_folder
    )

    registry.register(
        name="delete_file",
        description="Delete a file (requires confirmation)",
        category="filesystem",
        permission=PermissionLevel.DESTRUCTIVE,
        schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "confirm": {"type": "boolean"}
            },
            "required": ["path", "confirm"]
        },
        handler=fs_tools.delete_file
    )

    registry.register(
        name="copy_file",
        description="Copy a file to a new location",
        category="filesystem",
        permission=PermissionLevel.SAFE,
        schema={
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "destination": {"type": "string"}
            },
            "required": ["source", "destination"]
        },
        handler=fs_tools.copy_file
    )

    registry.register(
        name="move_file",
        description="Move a file to a new location",
        category="filesystem",
        permission=PermissionLevel.SENSITIVE,
        schema={
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "destination": {"type": "string"}
            },
            "required": ["source", "destination"]
        },
        handler=fs_tools.move_file
    )

    # System Monitor Tools
    sys_tools = SystemMonitorTools()
    registry.register(
        name="get_system_stats",
        description="Get CPU, RAM, disk, battery stats",
        category="system",
        permission=PermissionLevel.SAFE,
        schema={"type": "object", "properties": {}},
        handler=sys_tools.get_system_stats
    )

    registry.register(
        name="get_process_list",
        description="Get list of running processes",
        category="system",
        permission=PermissionLevel.SAFE,
        schema={
            "type": "object",
            "properties": {"limit": {"type": "integer"}}
        },
        handler=sys_tools.get_process_list
    )

    # Terminal
    terminal = TerminalExecutor()
    registry.register(
        name="run_command",
        description="Execute a shell command",
        category="terminal",
        permission=PermissionLevel.SENSITIVE,
        schema={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "working_dir": {"type": "string"}
            },
            "required": ["command"]
        },
        handler=terminal.execute
    )

    # Screen Analyzer
    screen = ScreenAnalyzer()
    registry.register(
        name="take_screenshot",
        description="Take a screenshot of the desktop",
        category="vision",
        permission=PermissionLevel.SAFE,
        schema={
            "type": "object",
            "properties": {"save_path": {"type": "string"}}
        },
        handler=screen.capture_screen
    )

    registry.register(
        name="extract_screen_text",
        description="Extract text visible on screen using OCR",
        category="vision",
        permission=PermissionLevel.SAFE,
        schema={"type": "object", "properties": {}},
        handler=screen.extract_text
    )

    print(f"  Registered {len(registry.tools)} tools")

async def _global_notify(notification: dict):
    """Send notification to all connected WebSocket clients"""
    message = json.dumps({
        'type': 'notification',
        'notification': notification
    })
    for client in list(connected_clients):
        try:
            await client.send_text(message)
        except Exception:
            connected_clients.discard(client)

# ─────────────────────────────────────────
# WebSocket Handler
# ─────────────────────────────────────────

nexa_systems = {}

@app.websocket("/")
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)

    # Send welcome message
    await websocket.send_text(json.dumps({
        'type': 'connected',
        'message': 'NEXA AI connected!',
        'version': '1.0.0'
    }))

    try:
        ws_server = NexaWebSocketServer(
            websocket=websocket,
            systems=nexa_systems,
            notify_callback=_global_notify
        )
        await ws_server.handle()

    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)

# Phone WebSocket
@app.websocket("/phone")
async def phone_websocket(websocket: WebSocket):
    await websocket.accept()

    phone_mgr = nexa_systems.get('phone_manager')
    screen_mirror = nexa_systems.get('screen_mirror')

    if screen_mirror:
        screen_mirror.add_client(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await _handle_phone_command(msg, websocket)

    except WebSocketDisconnect:
        pass
    finally:
        if screen_mirror:
            screen_mirror.remove_client(websocket)

async def _handle_phone_command(msg: dict, websocket: WebSocket):
    """Handle phone control commands"""

    cmd_type = msg.get('type', '')
    device_id = msg.get('device_id')
    adb = nexa_systems.get('adb_engine')
    phone_mgr = nexa_systems.get('phone_manager')
    sms_mgr = nexa_systems.get('sms_manager')
    mirror = nexa_systems.get('screen_mirror')

    async def respond(data: dict):
        await websocket.send_text(json.dumps(data))

    if cmd_type == 'scan_devices':
        if phone_mgr:
            result = await phone_mgr._scan_all_devices()
            devices = [
                {
                    'id': d.id, 'name': d.name, 'model': d.model,
                    'connection_type': d.connection_type.value,
                    'battery_level': d.battery_level,
                    'is_charging': d.is_charging,
                    'is_online': d.is_online,
                    'android_version': d.android_version,
                    'storage_total_gb': d.storage_total_gb,
                    'storage_free_gb': d.storage_free_gb,
                    'screen_width': d.screen_width,
                    'screen_height': d.screen_height,
                }
                for d in phone_mgr.get_all_devices()
            ]
            await respond({'type': 'devices_list', 'devices': devices})

    elif cmd_type == 'start_mirror' and device_id and mirror:
        result = await mirror.start_stream_mirror(
            device_id=device_id,
            fps=msg.get('fps', 15),
            quality=msg.get('quality', 75)
        )
        await respond({'type': 'mirror_started', 'result': result})

    elif cmd_type == 'stop_mirror' and mirror:
        result = await mirror.stop_mirror()
        await respond({'type': 'mirror_stopped', 'result': result})

    elif cmd_type == 'screenshot' and device_id and adb:
        import time
        path = f"./temp/phone_ss_{int(time.time())}.png"
        result = await adb.take_screenshot(device_id, path)
        await respond({'type': 'screenshot_taken', 'result': result})

    elif cmd_type == 'tap' and device_id and adb:
        result = await adb.tap(device_id, msg.get('x', 0), msg.get('y', 0))
        await respond({'type': 'tap_result', 'result': result})

    elif cmd_type == 'key' and device_id and adb:
        result = await adb.press_key(device_id, msg.get('key', ''))
        await respond({'type': 'key_result', 'result': result})

    elif cmd_type == 'get_messages' and device_id and sms_mgr:
        result = await sms_mgr.get_messages(device_id)
        await respond({'type': 'messages', **result})

    elif cmd_type == 'send_sms' and device_id and sms_mgr:
        result = await sms_mgr.send_sms(
            device_id,
            msg.get('phone_number', ''),
            msg.get('message', '')
        )
        await respond({'type': 'sms_sent', 'result': result})

    elif cmd_type == 'get_notifications' and device_id:
        notif_bridge = nexa_systems.get('notification_bridge')
        if notif_bridge:
            notifs = notif_bridge.get_active_notifications()
            await respond({'type': 'notifications', 'notifications': notifs})

    elif cmd_type == 'media_control' and device_id and adb:
        action_map = {
            'play': 'KEYCODE_MEDIA_PLAY',
            'pause': 'KEYCODE_MEDIA_PAUSE',
            'play_pause': 'KEYCODE_MEDIA_PLAY_PAUSE',
            'next': 'KEYCODE_MEDIA_NEXT',
            'previous': 'KEYCODE_MEDIA_PREVIOUS',
        }
        keycode = action_map.get(msg.get('action', ''))
        if keycode:
            result = await adb.press_key(device_id, keycode)
            await respond({'type': 'media_result', 'result': result})

    elif cmd_type == 'set_volume' and device_id and adb:
        level = msg.get('level', 8)
        for _ in range(15):
            await adb.press_key(device_id, 'KEYCODE_VOLUME_DOWN')
        for _ in range(level):
            await adb.press_key(device_id, 'KEYCODE_VOLUME_UP')
        await respond({'type': 'volume_set', 'level': level})

    elif cmd_type == 'brightness' and device_id and adb:
        result = await adb.set_screen_brightness(device_id, msg.get('level', 200))
        await respond({'type': 'brightness_set', 'result': result})

# ─────────────────────────────────────────
# REST API Endpoints
# ─────────────────────────────────────────

@app.get("/api/status")
async def get_status():
    return {
        "status": "running",
        "version": "1.0.0",
        "systems": list(nexa_systems.keys())
    }

@app.get("/api/tools")
async def get_tools():
    registry = nexa_systems.get('tool_registry')
    if registry:
        return {"tools": registry.get_all_tools()}
    return {"tools": []}

@app.get("/api/system-stats")
async def get_system_stats():
    sys_tools = SystemMonitorTools()
    return sys_tools.get_system_stats()

@app.get("/api/meetings")
async def get_meetings():
    meeting_asst = nexa_systems.get('meeting_assistant')
    if meeting_asst:
        return {"meetings": meeting_asst.get_all_meetings()}
    return {"meetings": []}

@app.get("/api/shortcuts")
async def get_shortcuts():
    shortcuts = nexa_systems.get('shortcuts')
    if shortcuts:
        return shortcuts.get_shortcuts_summary()
    return {}

# ─────────────────────────────────────────
# Startup / Shutdown
# ─────────────────────────────────────────

@app.on_event("startup")
async def startup():
    global nexa_systems
    nexa_systems = await initialize_nexa()

    # Start background tasks
    phone_mgr = nexa_systems.get('phone_manager')
    if phone_mgr:
        await phone_mgr.start_monitoring()

@app.on_event("shutdown")
async def shutdown():
    phone_mgr = nexa_systems.get('phone_manager')
    if phone_mgr:
        phone_mgr.stop_monitoring()

# ─────────────────────────────────────────
# Run Server
# ─────────────────────────────────────────

if __name__ == "__main__":
    import os
    os.makedirs("./temp", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    os.makedirs("./data", exist_ok=True)

    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )
