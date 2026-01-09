import asyncio
import base64
import json
import os
import shutil
import logging
from typing import Optional, List, Dict, Any, Callable
from pydantic import BaseModel

from browser_use import Agent, Browser, BrowserProfile, AgentHistoryList
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentService")

class TaskRequest(BaseModel):
    task: str

class AgentService:
    _instance = None

    def __init__(self):
        self.agent: Optional[Agent] = None
        self.browser: Optional[Browser] = None
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.current_task: Optional[str] = None
        self.is_running = False
        self.subscribers: List[Callable[[Dict], None]] = []
        self._loop_task: Optional[asyncio.Task] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AgentService()
        return cls._instance

    def add_subscriber(self, callback: Callable[[Dict], None]):
        self.subscribers.append(callback)

    def remove_subscriber(self, callback: Callable[[Dict], None]):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def broadcast(self, message: Dict):
        for callback in self.subscribers:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error broadcasting to subscriber: {e}")

    async def start_task(self, task_text: str):
        if self.is_running:
            return {"status": "error", "message": "Agent is already running"}

        self.current_task = task_text
        self.is_running = True

        # Start the processing loop in background
        self._loop_task = asyncio.create_task(self._run_agent(task_text))
        return {"status": "started", "task": task_text}

    async def stop_task(self):
        if self.agent:
            self.agent.stop()
            self.is_running = False
            await self.broadcast({"type": "status", "status": "stopped"})
            return {"status": "stopped"}
        return {"status": "not_running"}

    async def _run_agent(self, task_text: str):
        try:
            await self.broadcast({"type": "status", "status": "initializing"})

            # Browser configuration
            # Use --disable-gpu as requested in README to save VRAM for LLM
            profile = BrowserProfile(
                headless=True, # Headless is better for server, we will stream screenshots
                args=["--disable-gpu", "--no-sandbox"],
                is_local=True
            )

            self.browser = Browser(browser_profile=profile)

            # LLM Configuration
            # Pointing to local LLM running on port 8080
            llm = ChatOpenAI(
                base_url='http://127.0.0.1:8080/v1',
                api_key='sk-no-key-required',
                model='Qwen_Qwen3-8B-Q4_K_M.gguf',
                temperature=0.0
            )

            self.agent = Agent(
                task=task_text,
                llm=llm,
                browser=self.browser,
                use_judge=False, # Disable judge to save tokens/time if not needed
            )

            await self.broadcast({"type": "status", "status": "running"})
            await self.broadcast({"type": "log", "message": f"Started task: {task_text}"})

            # Run the agent with callback
            await self.agent.run(
                max_steps=50,
                on_step_end=self._on_step_end
            )

            await self.broadcast({"type": "status", "status": "completed"})
            await self.broadcast({"type": "log", "message": "Task completed successfully."})

        except Exception as e:
            logger.error(f"Error running agent: {e}", exc_info=True)
            await self.broadcast({"type": "error", "message": str(e)})
            await self.broadcast({"type": "status", "status": "error"})
        finally:
            self.is_running = False
            if self.browser:
                await self.browser.close()
            self.agent = None
            self.browser = None

    async def _on_step_end(self, agent: Agent):
        """Callback called after each step"""
        try:
            if not agent.history.history:
                return

            last_history_item = agent.history.history[-1]

            # Extract thought/model output
            thought = "Processing..."
            if last_history_item.model_output:
                # model_output is usually an AgentStructuredOutput object or similar
                # We try to convert it to string or access fields
                try:
                    thought = str(last_history_item.model_output)
                except:
                    thought = "Unknown thought"

            # Extract screenshot
            screenshot_b64 = None
            if last_history_item.state.screenshot_path:
                # If path exists, read it
                path = last_history_item.state.screenshot_path
                if os.path.exists(path):
                    with open(path, "rb") as img_file:
                        screenshot_b64 = base64.b64encode(img_file.read()).decode('utf-8')

            # Send update
            update = {
                "type": "step",
                "step": agent.state.n_steps,
                "thought": thought,
                "screenshot": screenshot_b64,
                "url": last_history_item.state.url
            }
            await self.broadcast(update)

        except Exception as e:
            logger.error(f"Error in on_step_end: {e}")
