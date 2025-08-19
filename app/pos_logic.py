import re
from typing import Dict, Tuple,List


NUM_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'to':2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
}

def parse_multi_items(text: str) -> List[Tuple[int, str]]:
    """
    Parse commands like:
    'add two apples and one banana'
    'remove all oranges'
    Returns a list of (qty, item_name)
    """
    text = text.lower()
    text = text.replace(",", " and ")  # normalize commas
    parts = re.split(r"\s+and\s+", text)
    items = []

    for part in parts:
        match = re.match(r"(add|remove)?\s*((\d+)|(" + "|".join(NUM_WORDS.keys()) + "))\s+(.+)", part)
        if match:
            qty_raw = match.group(2)
            item_name = match.group(5).strip()

            # convert quantity
            if qty_raw.isdigit():
                qty = int(qty_raw)
            else:
                qty = NUM_WORDS.get(qty_raw, 1)

            items.append((qty, item_name))
        else:
            # fallback: just item name, assume 1
            item_name = re.sub(r"^(add|remove)\s+", "", part).strip()
            if item_name:
                items.append((1, item_name))

    return items

def normalize_item(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())

class Cart:
    def __init__(self):
        self.items: Dict[str, int] = {}

    def add(self, sku: str, qty: int):
        self.items[sku] = self.items.get(sku, 0) + qty

    def remove(self, sku: str, qty: int):
        if sku in self.items:
            self.items[sku] = max(0, self.items[sku] - qty)
            if self.items[sku] == 0:
                del self.items[sku]

    def total(self, inventory):
        t = 0.0
        for sku, q in self.items.items():
            price = next((x['price'] for x in inventory if x['sku'] == sku), 0.0)
            t += price * q
        return round(t, 2)

    def snapshot(self):
        return dict(self.items)
