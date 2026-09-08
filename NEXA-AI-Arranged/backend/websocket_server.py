import json
import asyncio
import time
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

class NexaWebSocketServer:
    """Handles real-time WebSocket communication with NEXA AI Frontend"""
    
    def __init__(self, websocket: WebSocket, systems: Dict[str, Any], notify_callback=None):
        self.websocket = websocket
        self.systems = systems
        self.notify = notify_callback
        self.current_task: Optional[str] = None
        self.is_cancelled = False
        
    async def send(self, data: Dict[str, Any]):
        try:
            await self.websocket.send_text(json.dumps(data))
        except Exception:
            pass
            
    async def handle(self):
        try:
            while True:
                data = await self.websocket.receive_text()
                try:
                    msg = json.loads(data)
                    await self._process_message(msg)
                except json.JSONDecodeError:
                    await self.send({"type": "error", "message": "Invalid JSON format"})
                except Exception as e:
                    await self.send({"type": "error", "message": str(e)})
        except WebSocketDisconnect:
            pass

    async def _process_message(self, msg: Dict[str, Any]):
        msg_type = msg.get("type", "")
        
        if msg_type == "get_status":
            await self.send({
                "type": "agent_state",
                "state": "idle"
            })
            
        elif msg_type == "get_system_stats":
            stats = self._get_system_stats()
            await self.send({
                "type": "system_stats",
                "stats": stats
            })
            
        elif msg_type == "start_listening":
            await self.send({"type": "listening_started"})
            await self.send({"type": "agent_state", "state": "listening"})
            
        elif msg_type == "stop_listening":
            await self.send({"type": "listening_stopped"})
            await self.send({"type": "agent_state", "state": "idle"})
            
        elif msg_type == "cancel_task":
            self.is_cancelled = True
            self.current_task = None
            await self.send({"type": "task_end"})
            await self.send({"type": "agent_state", "state": "idle"})
            
        elif msg_type == "process_audio":
            audio_base64 = msg.get("audio")
            voice_pipe = self.systems.get("voice_pipeline")
            transcript_text = ""
            if voice_pipe and audio_base64:
                try:
                    import base64
                    audio_bytes = base64.b64decode(audio_base64)
                    res = await voice_pipe.start_listening(audio_bytes)
                    transcript_text = res.get("text", "")
                except Exception as e:
                    transcript_text = ""
            
            if transcript_text:
                await self.send({"type": "transcript", "text": transcript_text})
                await self._handle_text_command(transcript_text)
            else:
                await self.send({"type": "agent_state", "state": "idle"})
                
        elif msg_type == "text_command":
            text = msg.get("text", "")
            if text:
                await self._handle_text_command(text)

    async def _handle_text_command(self, text: str):
        self.is_cancelled = False
        self.current_task = text
        
        await self.send({"type": "task_start", "task": text})
        await self.send({"type": "agent_state", "state": "thinking"})
        await self.send({
            "type": "timeline_update",
            "event": {
                "id": str(int(time.time() * 1000)),
                "type": "info",
                "message": f"Analyzing user intent: {text}",
                "timestamp": int(time.time() * 1000)
            }
        })
        
        brain = self.systems.get("agent_brain")
        registry = self.systems.get("tool_registry")
        ai_provider = self.systems.get("ai_provider")
        
        timeline_events = []
        tools_used = []
        response_content = ""
        
        try:
            if brain:
                intent_info = await brain.understand_intent(text)
                await self.send({"type": "agent_state", "state": "executing"})
                
                plan = await brain.plan_execution(intent_info, text)
                
                execution_results = []
                for step in plan:
                    if self.is_cancelled:
                        break
                        
                    step_type = step.get("type")
                    if step_type == "tool":
                        tool_name = step.get("tool")
                        tool_input = step.get("input", {})
                        tools_used.append(tool_name)
                        
                        event_id = str(int(time.time() * 1000))
                        evt = {
                            "id": event_id,
                            "type": "info",
                            "message": f"Executing tool: {tool_name}",
                            "details": tool_input,
                            "timestamp": int(time.time() * 1000)
                        }
                        timeline_events.append(evt)
                        await self.send({"type": "timeline_update", "event": evt})
                        
                        # Execute tool if found in registry
                        tool = registry.get_tool(tool_name) if registry else None
                        if tool and tool.handler:
                            try:
                                import inspect
                                if inspect.iscoroutinefunction(tool.handler):
                                    res = await tool.handler(**tool_input)
                                else:
                                    res = tool.handler(**tool_input)
                                execution_results.append({tool_name: res})
                                
                                success_evt = {
                                    "id": str(int(time.time() * 1000) + 1),
                                    "type": "success",
                                    "message": f"Completed {tool_name}",
                                    "details": res,
                                    "timestamp": int(time.time() * 1000)
                                }
                                timeline_events.append(success_evt)
                                await self.send({"type": "timeline_update", "event": success_evt})
                            except Exception as ex:
                                err_evt = {
                                    "id": str(int(time.time() * 1000) + 1),
                                    "type": "error",
                                    "message": f"Error in {tool_name}: {str(ex)}",
                                    "timestamp": int(time.time() * 1000)
                                }
                                timeline_events.append(err_evt)
                                await self.send({"type": "timeline_update", "event": err_evt})
                        else:
                            execution_results.append({tool_name: "Tool not found"})
                    elif step_type == "response":
                        response_content = step.get("content", "")
                
                if not response_content:
                    response_content = await brain.generate_response(text, execution_results)
            else:
                response_content = f"NEXA AI Response: Received '{text}'."
        except Exception as err:
            response_content = f"Kuch dikkat aayi: {str(err)}"
            err_evt = {
                "id": str(int(time.time() * 1000)),
                "type": "error",
                "message": str(err),
                "timestamp": int(time.time() * 1000)
            }
            timeline_events.append(err_evt)
            await self.send({"type": "timeline_update", "event": err_evt})
            
        await self.send({
            "type": "message",
            "role": "assistant",
            "content": response_content,
            "timeline": timeline_events,
            "tools_used": tools_used
        })
        
        await self.send({"type": "task_end"})
        await self.send({"type": "agent_state", "state": "idle"})
        self.current_task = None

    def _get_system_stats(self) -> Dict[str, Any]:
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            net_io = psutil.net_io_counters()
            battery_pct = None
            if hasattr(psutil, "sensors_battery"):
                batt = psutil.sensors_battery()
                if batt:
                    battery_pct = batt.percent
                    
            return {
                "cpu": cpu,
                "memory": mem,
                "disk": disk,
                "network": {
                    "sent": net_io.bytes_sent,
                    "received": net_io.bytes_recv
                },
                "battery": battery_pct
            }
        except Exception:
            return {
                "cpu": 25,
                "memory": 45,
                "disk": 60,
                "network": {"sent": 1024, "received": 2048},
                "battery": 95
            }
