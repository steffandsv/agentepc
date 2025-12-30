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
        2. Action: click(start_box='<|box_start|>(x,y)<|box_end|>')
        3. Action: type(content='text')
        4. Action: key(content='key')
        5. (x, y) - Fallback
        """
        raw_output = raw_output.strip()
        print(f"DEBUG: Parsing raw output: {raw_output}")

        # Pattern 1: Standard UI-TARS <point>
        click_match = re.search(r"click\(point=['\"]<point>(\d+)\s+(\d+)</point>['\"]", raw_output)
        if click_match:
            x, y = int(click_match.group(1)), int(click_match.group(2))
            return {"type": "click", "x": self._scale_coord(x, self.screen_width), "y": self._scale_coord(y, self.screen_height)}

        # Pattern 2: Box format (observed in logs) - click(start_box='<|box_start|>(986,35)<|box_end|>')
        # We extract the first coordinate pair in the box string
        box_match = re.search(r"click\(start_box=['\"]<\|box_start\|>\((\d+),(\d+)\)", raw_output)
        if box_match:
            x, y = int(box_match.group(1)), int(box_match.group(2))
            # Note: Box coordinates might be top-left. Ideally we want center, but start_box usually implies x_min, y_min.
            # Without end_box, we click top-left. If the box is small (icon), this is fine.
            return {"type": "click", "x": self._scale_coord(x, self.screen_width), "y": self._scale_coord(y, self.screen_height)}

        # Pattern 3: type(content='hello world')
        type_match = re.search(r"type\(content=['\"](.*?)['\"]\)", raw_output)
        if type_match:
            return {"type": "type", "content": type_match.group(1)}

        # Pattern 4: key(content='enter')
        key_match = re.search(r"key\(content=['\"](.*?)['\"]\)", raw_output)
        if key_match:
            return {"type": "key", "content": key_match.group(1)}

        # Pattern 5: Legacy/Simple format (200, 300)
        legacy_match = re.search(r"\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\)", raw_output)
        if legacy_match:
             x_raw, y_raw = float(legacy_match.group(1)), float(legacy_match.group(2))

             final_x, final_y = 0, 0

             if x_raw <= 1 and y_raw <= 1:
                 # Normalized 0-1
                 final_x = int(x_raw * self.screen_width)
                 final_y = int(y_raw * self.screen_height)
             else:
                 # Assume 0-1000 scale
                 final_x = self._scale_coord(x_raw, self.screen_width)
                 final_y = self._scale_coord(y_raw, self.screen_height)

             return {"type": "click", "x": final_x, "y": final_y}

        # Pattern 6: Plain click(x, y)
        simple_click = re.search(r"click\((\d+),\s*(\d+)\)", raw_output)
        if simple_click:
            x, y = int(simple_click.group(1)), int(simple_click.group(2))
            return {"type": "click", "x": self._scale_coord(x, self.screen_width), "y": self._scale_coord(y, self.screen_height)}

        return None

    def _scale_coord(self, val: float, dimension: int) -> int:
        """Scales a 0-1000 coordinate to screen pixels and clamps it."""
        pixel_val = int((val / 1000.0) * dimension)
        return max(0, min(pixel_val, dimension - 1))
