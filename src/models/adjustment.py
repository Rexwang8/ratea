# Represents an adjustment to the purchase amount like discarding, gifting, sale, etc besides drinking.
import uuid


# When graphing, adjustments are deducted from the initial amount, and treated as if never happened.
# When calculating cost per gram, They do not affect the cost per gram of the tea, but they do affect the total cost basis of the tea (ie if you gifted 10g of a 100g tea, you only have 90g left to drink, so the cost basis of the tea is now the original cost minus the cost of the gifted 10g).
# Sales (returning costs) are positive as they are common.
# Any sort of additional payment is negative as it is uncommon and can be treated as a custom adjustment type if needed.
class Adjustment:
    def __init__(self, tea_id: str, amount: float, cost: float, adjustment_type: str, id: str = None):
        self.id = id if id else str(uuid.uuid4())
        self.tea_id = tea_id
        self.amount = amount
        self.cost = cost # positive is returned money (ie sale)
        self.adjustment_type = adjustment_type  # e.g., "discard", "gift", "sale"

    def to_dict(self):
        # Assert amount and cost are primative types to avoid YAML export issues
        if not isinstance(self.amount, (int, float)):
            raise ValueError(f"Adjustment amount must be a number, got {type(self.amount)}")
        if not isinstance(self.cost, (int, float)):
            raise ValueError(f"Adjustment cost must be a number, got {type(self.cost)}")
        adjustment = {
            "id": self.id,
            "tea_id": self.tea_id,
            "amount": self.amount,
            "cost": self.cost,
            "adjustment_type": self.adjustment_type,
        }
        return adjustment
