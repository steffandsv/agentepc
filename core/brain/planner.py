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
        1. SELF-AWARENESS: You are running inside a terminal window.
        2. FORBIDDEN ZONE: Do NOT type commands into the terminal that shows 'main.py', 'Sovereign Agent', or these instructions. This is your own brain.
        3. STARTING A TASK: If you need to run a command, ALWAYS open a NEW terminal first.
           - Preferred Method: "Press keys 'ctrl+alt+t'" (Global Shortcut).
           - Alternative: "Click on Terminal icon" (Only if specific icon is visible and distinct from current window).

        INSTRUCTIONS:
        1. Analyze the OCR text. If you see "ENTER OBJECTIVE" or "NEW CYCLE", you are looking at yourself.
           - Action: "Press keys 'ctrl+alt+t'" (to spawn a fresh environment) OR "Press keys 'super+h'" (to minimize).
        2. UNLOCKING: If screen locked ("Password"), -> "Type '{config.PC_PASSWORD}'" -> "Press key 'enter'".
        3. OUTPUT FORMAT: Plain text instruction. No Markdown.

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
