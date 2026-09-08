import os
import zipfile
from pathlib import Path

def create_nexa_zip():
    """Create complete NEXA AI project ZIP"""
    
    zip_name = "NEXA-AI-Complete.zip"
    
    # All files to include
    files_to_include = {
        
        # ROOT FILES
        "README.md": "README.md",
        ".env.example": ".env.example",
        ".gitignore": ".gitignore",
        "requirements.txt": "requirements.txt",
        "install.bat": "install.bat",
        "start.bat": "start.bat",
        "start_dev.bat": "start_dev.bat",
        
        # BACKEND
        "backend/main.py": "backend/main.py",
        "backend/config.py": "backend/config.py",
        "backend/schemas.py": "backend/schemas.py",
        "backend/websocket_server.py": "backend/websocket_server.py",
        
        # Agent
        "backend/agent/__init__.py": "backend/agent/__init__.py",
        "backend/agent/brain.py": "backend/agent/brain.py",
        "backend/agent/planner.py": "backend/agent/planner.py",
        "backend/agent/executor.py": "backend/agent/executor.py",
        "backend/agent/context.py": "backend/agent/context.py",
        "backend/agent/hinglish_engine.py": "backend/agent/hinglish_engine.py",
        "backend/agent/persona.py": "backend/agent/persona.py",
        "backend/agent/proactive.py": "backend/agent/proactive.py",
        "backend/agent/multimodal_agent.py": "backend/agent/multimodal_agent.py",
        "backend/agent/neural_shortcuts.py": "backend/agent/neural_shortcuts.py",
        "backend/agent/time_travel.py": "backend/agent/time_travel.py",
        "backend/agent/ambient_intelligence.py": "backend/agent/ambient_intelligence.py",
        "backend/agent/emotion_engine.py": "backend/agent/emotion_engine.py",
        "backend/agent/dream_mode.py": "backend/agent/dream_mode.py",
        
        # AI Providers
        "backend/ai/__init__.py": "backend/ai/__init__.py",
        "backend/ai/factory.py": "backend/ai/factory.py",
        "backend/ai/prompts.py": "backend/ai/prompts.py",
        "backend/ai/providers/__init__.py": "backend/ai/providers/__init__.py",
        "backend/ai/providers/interface.py": "backend/ai/providers/interface.py",
        "backend/ai/providers/openai_provider.py": "backend/ai/providers/openai_provider.py",
        "backend/ai/providers/anthropic_provider.py": "backend/ai/providers/anthropic_provider.py",
        "backend/ai/providers/gemini_provider.py": "backend/ai/providers/gemini_provider.py",
        
        # Voice
        "backend/voice/__init__.py": "backend/voice/__init__.py",
        "backend/voice/pipeline.py": "backend/voice/pipeline.py",
        "backend/voice/stt/__init__.py": "backend/voice/stt/__init__.py",
        "backend/voice/stt/interface.py": "backend/voice/stt/interface.py",
        "backend/voice/stt/openai_whisper.py": "backend/voice/stt/openai_whisper.py",
        "backend/voice/stt/google_speech.py": "backend/voice/stt/google_speech.py",
        "backend/voice/tts/__init__.py": "backend/voice/tts/__init__.py",
        "backend/voice/tts/interface.py": "backend/voice/tts/interface.py",
        "backend/voice/tts/elevenlabs.py": "backend/voice/tts/elevenlabs.py",
        "backend/voice/tts/openai_tts.py": "backend/voice/tts/openai_tts.py",
        "backend/voice/tts/custom_voice.py": "backend/voice/tts/custom_voice.py",
        "backend/voice/wake_word/__init__.py": "backend/voice/wake_word/__init__.py",
        "backend/voice/wake_word/detector.py": "backend/voice/wake_word/detector.py",
        
        # Tools
        "backend/tools/__init__.py": "backend/tools/__init__.py",
        "backend/tools/registry.py": "backend/tools/registry.py",
        "backend/tools/permissions.py": "backend/tools/permissions.py",
        "backend/tools/windows/__init__.py": "backend/tools/windows/__init__.py",
        "backend/tools/windows/applications.py": "backend/tools/windows/applications.py",
        "backend/tools/filesystem/__init__.py": "backend/tools/filesystem/__init__.py",
        "backend/tools/filesystem/operations.py": "backend/tools/filesystem/operations.py",
        "backend/tools/system/__init__.py": "backend/tools/system/__init__.py",
        "backend/tools/system/monitor.py": "backend/tools/system/monitor.py",
        "backend/tools/browser/__init__.py": "backend/tools/browser/__init__.py",
        "backend/tools/browser/advanced_web.py": "backend/tools/browser/advanced_web.py",
        "backend/tools/terminal/__init__.py": "backend/tools/terminal/__init__.py",
        "backend/tools/terminal/executor.py": "backend/tools/terminal/executor.py",
        "backend/tools/clipboard/__init__.py": "backend/tools/clipboard/__init__.py",
        "backend/tools/clipboard/smart_clipboard.py": "backend/tools/clipboard/smart_clipboard.py",
        "backend/tools/vision/__init__.py": "backend/tools/vision/__init__.py",
        "backend/tools/vision/screen_analyzer.py": "backend/tools/vision/screen_analyzer.py",
        "backend/tools/code/__init__.py": "backend/tools/code/__init__.py",
        "backend/tools/code/code_intelligence.py": "backend/tools/code/code_intelligence.py",
        
        # Phone
        "backend/phone/__init__.py": "backend/phone/__init__.py",
        "backend/phone/device_manager.py": "backend/phone/device_manager.py",
        "backend/phone/adb_engine.py": "backend/phone/adb_engine.py",
        "backend/phone/screen_mirror.py": "backend/phone/screen_mirror.py",
        "backend/phone/notification_bridge.py": "backend/phone/notification_bridge.py",
        "backend/phone/sms_manager.py": "backend/phone/sms_manager.py",
        "backend/phone/call_manager.py": "backend/phone/call_manager.py",
        "backend/phone/app_controller.py": "backend/phone/app_controller.py",
        "backend/phone/file_sync.py": "backend/phone/file_sync.py",
        "backend/phone/media_controller.py": "backend/phone/media_controller.py",
        "backend/phone/contacts_manager.py": "backend/phone/contacts_manager.py",
        "backend/phone/location_tracker.py": "backend/phone/location_tracker.py",
        "backend/phone/phone_voice_commands.py": "backend/phone/phone_voice_commands.py",
        
        # Features
        "backend/features/__init__.py": "backend/features/__init__.py",
        "backend/features/meeting_assistant.py": "backend/features/meeting_assistant.py",
        "backend/features/smart_home.py": "backend/features/smart_home.py",
        "backend/features/voice_keyboard.py": "backend/features/voice_keyboard.py",
        "backend/features/ar_overlay.py": "backend/features/ar_overlay.py",
        
        # Memory
        "backend/memory/__init__.py": "backend/memory/__init__.py",
        "backend/memory/vector_store.py": "backend/memory/vector_store.py",
        "backend/memory/storage.py": "backend/memory/storage.py",
        "backend/memory/context.py": "backend/memory/context.py",
        "backend/memory/preferences.py": "backend/memory/preferences.py",
        
        # Security
        "backend/security/__init__.py": "backend/security/__init__.py",
        "backend/security/validator.py": "backend/security/validator.py",
        "backend/security/permissions.py": "backend/security/permissions.py",
        "backend/security/audit.py": "backend/security/audit.py",
        "backend/security/voice_dna.py": "backend/security/voice_dna.py",
        
        # Automation
        "backend/automation/__init__.py": "backend/automation/__init__.py",
        "backend/automation/scheduler.py": "backend/automation/scheduler.py",
        "backend/automation/workflows.py": "backend/automation/workflows.py",
        
        # Digital Twin
        "backend/digital_twin/__init__.py": "backend/digital_twin/__init__.py",
        "backend/digital_twin/twin_engine.py": "backend/digital_twin/twin_engine.py",
        
        # Plugins
        "backend/plugins/__init__.py": "backend/plugins/__init__.py",
        "backend/plugins/plugin_manager.py": "backend/plugins/plugin_manager.py",
        "backend/plugins/example_plugin/manifest.json": "backend/plugins/example_plugin/manifest.json",
        "backend/plugins/example_plugin/main.py": "backend/plugins/example_plugin/main.py",
        
        # FRONTEND
        "frontend/package.json": "frontend/package.json",
        "frontend/tsconfig.json": "frontend/tsconfig.json",
        "frontend/tailwind.config.js": "frontend/tailwind.config.js",
        "frontend/postcss.config.js": "frontend/postcss.config.js",
        "frontend/public/index.html": "frontend/public/index.html",
        "frontend/src/index.tsx": "frontend/src/index.tsx",
        "frontend/src/main.tsx": "frontend/src/main.tsx",
        "frontend/src/App.tsx": "frontend/src/App.tsx",
        "frontend/src/types/index.ts": "frontend/src/types/index.ts",
        "frontend/src/store/useNexaStore.ts": "frontend/src/store/useNexaStore.ts",
        "frontend/src/hooks/useWebSocket.ts": "frontend/src/hooks/useWebSocket.ts",
        "frontend/src/hooks/useVoice.ts": "frontend/src/hooks/useVoice.ts",
        "frontend/src/hooks/useSystemStats.ts": "frontend/src/hooks/useSystemStats.ts",
        "frontend/src/styles/globals.css": "frontend/src/styles/globals.css",
        "frontend/src/styles/theme.ts": "frontend/src/styles/theme.ts",
        
        # Components
        "frontend/src/components/MainDashboard.tsx": "frontend/src/components/MainDashboard.tsx",
        "frontend/src/components/core/AIOrb.tsx": "frontend/src/components/core/AIOrb.tsx",
        "frontend/src/components/core/VoiceInput.tsx": "frontend/src/components/core/VoiceInput.tsx",
        "frontend/src/components/core/Waveform.tsx": "frontend/src/components/core/Waveform.tsx",
        "frontend/src/components/layout/Sidebar.tsx": "frontend/src/components/layout/Sidebar.tsx",
        "frontend/src/components/layout/TopBar.tsx": "frontend/src/components/layout/TopBar.tsx",
        "frontend/src/components/layout/RightPanel.tsx": "frontend/src/components/layout/RightPanel.tsx",
        "frontend/src/components/features/CommandTimeline.tsx": "frontend/src/components/features/CommandTimeline.tsx",
        "frontend/src/components/features/SystemDashboard.tsx": "frontend/src/components/features/SystemDashboard.tsx",
        "frontend/src/components/features/NotificationCenter.tsx": "frontend/src/components/features/NotificationCenter.tsx",
        "frontend/src/components/features/WorkflowBuilder.tsx": "frontend/src/components/features/WorkflowBuilder.tsx",
        "frontend/src/components/features/MissionControl.tsx": "frontend/src/components/features/MissionControl.tsx",
        "frontend/src/components/phone/PhoneHub.tsx": "frontend/src/components/phone/PhoneHub.tsx",
        "frontend/src/components/phone/ScreenMirror.tsx": "frontend/src/components/phone/ScreenMirror.tsx",
        "frontend/src/components/phone/SMSPanel.tsx": "frontend/src/components/phone/SMSPanel.tsx",
        "frontend/src/components/phone/NotificationFeed.tsx": "frontend/src/components/phone/NotificationFeed.tsx",
        "frontend/src/utils/helpers.ts": "frontend/src/utils/helpers.ts",
        
        # Data directories
        "data/.gitkeep": "data/.gitkeep",
        "data/memory/.gitkeep": "data/memory/.gitkeep",
        "data/twins/.gitkeep": "data/twins/.gitkeep",
        "data/meetings/.gitkeep": "data/meetings/.gitkeep",
        "data/sessions/.gitkeep": "data/sessions/.gitkeep",
        
        # Tests
        "tests/__init__.py": "tests/__init__.py",
        "tests/test_agent.py": "tests/test_agent.py",
        "tests/test_tools.py": "tests/test_tools.py",
        "tests/test_voice.py": "tests/test_voice.py",
        "tests/test_phone.py": "tests/test_phone.py",
        "tests/test_hinglish.py": "tests/test_hinglish.py",
        
        # Docs
        "docs/SETUP.md": "docs/SETUP.md",
        "docs/VOICE_COMMANDS.md": "docs/VOICE_COMMANDS.md",
        "docs/PHONE_CONTROL.md": "docs/PHONE_CONTROL.md",
        "docs/SMART_HOME.md": "docs/SMART_HOME.md",
        "docs/API.md": "docs/API.md",
    }
    
    print(f"Creating {zip_name}...")
    print(f"Total files: {len(files_to_include)}")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for src_path, zip_path in files_to_include.items():
            full_path = Path(src_path)
            zip_full_path = f"NEXA-AI/{zip_path}"
            
            if full_path.exists():
                zf.write(full_path, zip_full_path)
                print(f"  ✓ Added: {zip_path}")
            else:
                # Create empty file placeholder
                zf.writestr(zip_full_path, f"# {zip_path}\n# TODO: Add content\n")
                print(f"  ○ Created placeholder: {zip_path}")
    
    size_mb = os.path.getsize(zip_name) / 1024 / 1024
    print(f"\n✅ ZIP created: {zip_name} ({size_mb:.2f} MB)")
    print(f"📁 Total files: {len(files_to_include)}")

if __name__ == "__main__":
    create_nexa_zip()
