from openai import OpenAI
from core.config import config
from core.brain.memory import ShortTermMemory

class Planner:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL
        )
        self.model = config.MODEL_BRAIN

    def plan_next_step(self, objective: str, memory: ShortTermMemory, screen_text: str) -> str:
        """
        Asks DeepSeek for the next high-level instruction.
        Returns a concise instruction string for the Vision model.
        """
        system_prompt = f"""
        You are an Autonomous Computer Control Agent.
        Your goal is to achieve the user's OBJECTIVE by planning one atomic step at a time.

        CURRENT STATE (OCR):
        "{screen_text[:3000]}"

        {memory.get_context()}

        CRITICAL SAFETY PROTOCOLS:
        1. SELF-AWARENESS: You are running inside a terminal window (look for 'main.py', 'Sovereign Agent').
        2. FORBIDDEN ZONE: Do NOT type commands into the terminal that shows your own logs. This is your own brain.
        3. STARTING A TASK: If you need to run a command, ALWAYS open a NEW terminal first (Ctrl+Alt+T).

        INSTRUCTIONS:
        1. SELF-REFLECTION: If the screen is dominated by text like "ENTER OBJECTIVE", "Sovereign Agent", or "NEW CYCLE", you are looking at your own internal logs.
           - Action: "Press keys 'super+h'" (Minimize) OR "Wait".
           - DO NOT open a new terminal if one is already open but obscured by your logs. Minimize first.
        2. UNLOCKING: If screen locked ("Password"), -> "Type '{config.PC_PASSWORD}'" -> "Press key 'enter'".
        3. IDLE: If you have no clear next step or are waiting for a process, output "Wait".
        4. OUTPUT FORMAT: Plain text instruction. No Markdown.

        Example outputs:
        - "Press keys 'ctrl+alt+t'"
        - "Type 'sudo apt update'"
        - "Click on the Firefox icon"
        """

        user_prompt = f"OBJECTIVE: {objective}\nWhat is the next step?"

        try:
            print("🧠 DeepSeek Thinking...")
            print(f"DEBUG: Sending Prompt to Brain:\n{system_prompt[:200]}...[snip]...{user_prompt}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            plan = response.choices[0].message.content.strip()
            print(f"🧠 Plan (Raw Response): {plan}")
            return plan
        except Exception as e:
            print(f"Brain Error: {e}")
            return "Wait"
