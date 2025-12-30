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
        "{screen_text[:2000]}"

        {memory.get_context()}

        INSTRUCTIONS:
        1. Analyze the screen text to understand the current state.
        2. Decide the absolute next step. Be extremely specific.
        3. If the screen is locked (contains "Password", "Unlock"), instruction MUST be "Unlock the screen by typing password".
        4. If you need to open a terminal and don't see one, instruction is "Open terminal".
        5. If you need to type something, specify "Type 'text'".
        6. OUTPUT FORMAT: Just the plain instruction string. No JSON, no markdown.

        Example outputs:
        - "Click on the Firefox icon"
        - "Type 'sudo apt update' into the terminal"
        - "Press the Enter key"
        """

        user_prompt = f"OBJECTIVE: {objective}\nWhat is the next step?"

        try:
            print("🧠 DeepSeek Thinking...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3 # Low temperature for consistent planning
            )
            plan = response.choices[0].message.content.strip()
            print(f"🧠 Plan: {plan}")
            return plan
        except Exception as e:
            print(f"Brain Error: {e}")
            return "Wait"
