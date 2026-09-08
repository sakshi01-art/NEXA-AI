# NEXA AI - Intelligent Desktop Agent

> Your advanced AI-powered desktop assistant for Windows 11

## Features

- 🎙️ Voice control in English, Hindi & Hinglish
- 🧠 Multi-step AI agent planning
- 💻 Windows automation & control
- 📁 File system intelligence
- 🌐 Web browsing & research
- 💻 Code analysis & generation
- 📄 Document intelligence
- 🔧 Plugin system
- 🎯 Proactive assistance
- 👁️ Screen understanding (Vision AI)
- 📋 Smart clipboard manager
- 🔒 Permission-based security

## Requirements

- Windows 11 (64-bit)
- Python 3.10+
- Node.js 18+
- 8GB RAM minimum
- Internet connection (for AI features)

## Installation

### 1. Clone Repository
git clone https://github.com/your-repo/nexa-ai.git
cd nexa-ai

### 2. Setup Environment
cp .env.example .env
# Edit .env with your API keys

### 3. Install Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

### 4. Install Frontend
cd ../frontend
npm install

### 5. Install Playwright Browsers
playwright install chromium

### 6. Run Development
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm start

## API Keys Required

| Service | Purpose | Where to Get |
|---------|---------|--------------|
| OpenAI | AI reasoning + STT | platform.openai.com |
| ElevenLabs | High-quality TTS | elevenlabs.io |
| Porcupine | Wake word | picovoice.io |

## Usage Examples

> "Nexa, Chrome kholo aur YouTube open karo"
> "Downloads mein latest PDF dhund"
> "System status bata"
> "VS Code mein mera project open karo"
> "Git status check kar"
> "Screen ka screenshot le"
> "Battery kitni hai?"

## Adding Custom Tools

Create file in `backend/tools/custom/mytool.py`:

from ...schemas import PermissionLevel

def register(registry):
    registry.register(
        name="my_tool",
        description="What this tool does",
        category="custom",
        permission=PermissionLevel.SAFE,
        schema={...},
        handler=my_handler
    )

## Adding Plugins

Place plugin folder in `/plugins/`:

plugins/
my_plugin/
manifest.json
main.py

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Space | Activate voice |
| Ctrl+Shift+Space | Push to talk |
| Esc | Cancel current task |
| Ctrl+H | Command history |
| Ctrl+M | Toggle memory |
| Ctrl+F | Floating widget |

## Troubleshooting

**Microphone not working:**
- Check Windows privacy settings
- Allow microphone in app permissions

**AI not responding:**
- Verify API key in .env
- Check internet connection
- See logs in /logs folder

**Application not opening:**
- Verify app path in settings
- Check Windows PATH variable
