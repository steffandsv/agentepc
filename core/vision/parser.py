import re
from typing import Tuple, Optional, Dict, Any

class ActionParser:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

    def parse(self, raw_output: str) -> Optional[Dict[str, Any]]:
        """
        Parses the raw output from UI-TARS.
        Supports formats:
        1. Action: click(point='<point>x y</point>')
        2. Action: type(content='text')
        3. Action: key(content='key')
        4. (x, y) - Fallback
        """
        raw_output = raw_output.strip()
        print(f"DEBUG: Parsing raw output: {raw_output}")

        # Normalize UI-TARS factor (usually 1000)
        # Note: Some models might output normalized 0-1, others 0-1000.
        # We assume 0-1000 based on common UI-TARS usage.

        # Pattern 1: click(point='<point>234 567</point>')
        click_match = re.search(r"click\(point=['\"]<point>(\d+)\s+(\d+)</point>['\"]", raw_output)
        if click_match:
            x, y = int(click_match.group(1)), int(click_match.group(2))
            return {"type": "click", "x": self._scale_coord(x, self.screen_width), "y": self._scale_coord(y, self.screen_height)}

        # Pattern 2: type(content='hello world')
        type_match = re.search(r"type\(content=['\"](.*?)['\"]\)", raw_output)
        if type_match:
            return {"type": "type", "content": type_match.group(1)}

        # Pattern 3: key(content='enter')
        key_match = re.search(r"key\(content=['\"](.*?)['\"]\)", raw_output)
        if key_match:
            return {"type": "key", "content": key_match.group(1)}

        # Pattern 4: Legacy/Simple format (200, 300)
        legacy_match = re.search(r"\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\)", raw_output)
        if legacy_match:
             x_raw, y_raw = float(legacy_match.group(1)), float(legacy_match.group(2))
             # Heuristic: if <= 1, it's normalized 0-1. If > 1, check if it's 0-1000 or pixels.
             # Assuming 0-1000 if not pixels.

             final_x, final_y = 0, 0

             if x_raw <= 1 and y_raw <= 1:
                 final_x = int(x_raw * self.screen_width)
                 final_y = int(y_raw * self.screen_height)
             else:
                 # Assume 0-1000 scale if it looks like it (e.g. < 1000 and screen is > 1000)
                 # Or just treat as 0-1000 normalized
                 final_x = self._scale_coord(x_raw, self.screen_width)
                 final_y = self._scale_coord(y_raw, self.screen_height)

             return {"type": "click", "x": final_x, "y": final_y}

        # Pattern 5: Plain click(x, y) - sometimes hallucinated
        simple_click = re.search(r"click\((\d+),\s*(\d+)\)", raw_output)
        if simple_click:
            x, y = int(simple_click.group(1)), int(simple_click.group(2))
            return {"type": "click", "x": self._scale_coord(x, self.screen_width), "y": self._scale_coord(y, self.screen_height)}

        return None

    def _scale_coord(self, val: float, dimension: int) -> int:
        """Scales a 0-1000 coordinate to screen pixels."""
        return int((val / 1000.0) * dimension)
