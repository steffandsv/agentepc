from openai import OpenAI
from core.config import config
from core.brain.memory import ShortTermMemory
import difflib

class Planner:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL
        )
        self.model = config.MODEL_BRAIN

        # Stagnation Watchdog State
        self.previous_plan = ""
        self.previous_screen_text = ""
        self.stagnation_counter = 0

    def _check_stagnation(self, current_plan: str, current_screen_text: str) -> bool:
        """
        Detects if the agent is stuck in a loop (same plan, same screen).
        Returns True if stuck.
        """
        # 1. Check if plan is identical
        plan_match = (current_plan.strip().lower() == self.previous_plan.strip().lower())

        # 2. Check if screen content is very similar (>90%)
        # Using difflib for similarity ratio
        matcher = difflib.SequenceMatcher(None, self.previous_screen_text, current_screen_text)
        screen_similarity = matcher.ratio()

        is_stagnant = plan_match and screen_similarity > 0.90

        if is_stagnant:
            self.stagnation_counter += 1
            print(f"(!) WATCHDOG: Stagnation detected ({self.stagnation_counter}/3). Plan={current_plan}, ScreenSim={screen_similarity:.2f}")
        else:
            self.stagnation_counter = 0

        # Update history
        self.previous_plan = current_plan
        self.previous_screen_text = current_screen_text

        return self.stagnation_counter >= 3

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
           - Action: "Press keys 'super+d'" (Show Desktop - Hides All Windows) OR "Wait".
           - DO NOT open a new terminal if one is already open but obscured by your logs. HIDE YOURSELF FIRST.
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

            # Watchdog Check
            if self._check_stagnation(plan, screen_text):
                print("(!) WATCHDOG TRIGGERED: Forcing ESCAPE action.")
                return "Press key 'esc'"

            return plan
        except Exception as e:
            print(f"Brain Error: {e}")
            return "Wait"
