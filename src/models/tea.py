import uuid

from services.score_converter import ScoreConverter
from .review import Review
from .adjustment import Adjustment
import datetime as dt
from services.date_helper import parse_flexible_date


class Tea:
    def __init__(self, name: str, vendor: str, tea_type: str, cost: float = 0.0, catalog_price: float = 0.0, 
                 quantity: float = 0.0, purchase_date: 'dt.datetime' = None, year: int = 0,
                   purchase_note: str = "", reviews: list[Review] = [], adjustments: list[Adjustment] = [], id: str = None):
        self.id = id if id else str(uuid.uuid4())
        self.name = name
        self.vendor = vendor
        self.tea_type = tea_type # Green, Black, Oolong, etc.
        self.reviews: list[Review] = reviews
        self.cost = cost  # Cost in USD
        self.catalog_price = catalog_price  # Cata cost in USD (before discounts/freebies)
        self.quantity = quantity  # Quantity in grams
        self.purchase_date = purchase_date if purchase_date else dt.datetime.now() # Date of the purchase
        self.year = year
        self.purchase_note = purchase_note
        self.adjustments: list[Adjustment] = adjustments

        # Assign review session_num to reviews, sort reviews by oldest first
        self.reviews.sort(key=lambda r: r.date)
        i = 1
        for review in self.reviews:
            review.session_num = i
            i += 1
        # Rearrange to newest first
        self.reviews.sort(key=lambda r: r.date, reverse=True)

    @classmethod
    def from_dict_or_yaml(cls, data: dict):
        """Wrapper to handle both dict and YAML formats."""
        use_which = "dict" if "attributes" in data else "yaml"
        if use_which == "dict":
            return cls.from_dict(data)
        else:
            # Handle YAML parsing if needed
            return cls.from_yaml(data)

    @classmethod
    def from_yaml(cls, data: dict):
        """Initialize from a YAML dictionary."""
        id = str(uuid.uuid4())

        reviews = []
        adjustments = []
        for r in data.get("reviews", []):
            rev = Review.from_dict_or_yaml(r)
            rev.tea_id = id  # Ensure the review links back to this tea
            reviews.append(rev)

        for a in data.get("adjustments", []):
            adj = Adjustment(
                id=a.get("id", str(uuid.uuid4())),
                tea_id=id,
                amount=a.get("amount", 0.0),
                cost=a.get("cost", 0.0),
                adjustment_type=a.get("adjustment_type", "")
            )
            adjustments.append(adj)

        purchase_dt = _get_value_with_flexible_key(data, ["purchase_date", "purchase_date", "date"], None)
        if isinstance(purchase_dt, str):
            purchase_dt = parse_flexible_date(purchase_dt)

        instance = cls(
            name=_get_value_with_flexible_key(data, ["name", "Name"], ""),
            vendor=_get_value_with_flexible_key(data, ["vendor", "Vendor"], ""),
            tea_type=_get_value_with_flexible_key(data, ["tea_type", "Type"], ""),
            cost=_get_value_with_flexible_key(data, ["cost", "Cost"], 0.0),
            catalog_price=_get_value_with_flexible_key(data, ["catalog_price", "catalog_price"], 0.0),
            quantity=_get_value_with_flexible_key(data, ["quantity", "Quantity"], 0.0),
            purchase_date=purchase_dt,
            year=_get_value_with_flexible_key(data, ["year", "Year"], 0),
            purchase_note=_get_value_with_flexible_key(data, ["purchase_note", "Purchase Note", "Notes (Long)", "purchase_note"], ""),
            reviews=reviews,
            adjustments=adjustments,
            id=id if "id" not in data else data["id"]
        )
        return instance

    # Legacy handler for older dict format with "attributes" and "reviews" keys,
    #  where attributes is a dict of the tea's main properties, and reviews is a list of review dicts. 
    # Adjustments can be either a dict of type->amount or a list of adjustment dicts.
    @classmethod
    def from_dict(cls, data: dict):
        """Initialize from a dictionary (like from JSON/YAML)"""
        # note, some fields are "calculated" and are defaulted to 
        '''
        attributesJson: '{"Name": "TSD Forest Fragrance Qimen", "Vendor": "The Sweetest
        Dew", "Year": 2024, "date": 1725166800.0, "Type": "Hong", "Cost": 0.01, "Amount":
        10.1, "Notes (Long)": "1st order from TSD", "Total Score": 0.0, "Remaining": 100.0,
        "Cost per Gram": 0.1, "dateAdded": 1768002795.212237}'
        '''
        attributes = data.get("attributes", {})
        raw_date = attributes.get("date", 0.0)
        purchase_dt = parse_flexible_date(raw_date)

        reviewData = data.get("reviews", [])
        adjustmentData = data.get("adjustments", [])
        adjustments = []
        id = str(uuid.uuid4())
        # If is dict, get items, if is list, get directly
        if isinstance(adjustmentData, dict):
            adjustment_items = adjustmentData.items()
            for k, v in adjustment_items:
                adjustments.append(Adjustment(
                    id=str(uuid.uuid4()),
                    tea_id=id,
                    amount=v,
                    cost=0.0,
                    adjustment_type=k
                ))
        else:
            adjustment_items = adjustmentData
            for item in adjustment_items:
                adjustments.append(Adjustment(
                    id=item.get("id", str(uuid.uuid4())),
                    tea_id=id,
                    amount=item.get("amount", 0.0),
                    cost=item.get("cost", 0.0),
                    adjustment_type=item.get("adjustment_type", "")
                ))


        reviews = []
        for r in reviewData:
            rev = Review.from_dict(r)
            rev.tea_id = id  # Ensure the review links back to this tea
            reviews.append(rev)

        instance = cls(
            name=attributes.get("Name", ""),
            vendor=attributes.get("Vendor", ""),
            tea_type=attributes.get("Type", ""),
            cost=attributes.get("Cost", 0.0),
            catalog_price=attributes.get("Cost", 0.0),
            quantity=attributes.get("Amount", 0.0),
            purchase_date=purchase_dt,
            year=attributes.get("Year", 0),
            purchase_note=attributes.get("Notes (Long)", ""),
            reviews=reviews,
            adjustments=adjustments,
            id=id
        )
        return instance


    def add_review(self, review: Review):
        print(f"Adding review to tea '{self.name}': {review}")
        # Add session_num to the review based on current count + 1
        review.session_num = self.count_reviews() + 1
        self.reviews.append(review)

    def count_reviews(self):
        return len(self.reviews)
    
    @property
    def date(self):
        return self.purchase_date
    
    @property
    def name_no_year(self):
        """Get the tea name without the year, for better grouping in stats."""
        if self.year and str(self.year) in self.name:
            return self.name.replace(str(self.year), "").strip()
        return self.name
    
    @property
    def total_amount_drunk(self):
        return sum(r.amount_drunk for r in self.reviews)
    
    @property
    def remaining(self):
        """Calculate remaining amount based on quantity and reviews."""
        total_drunk = self.total_amount_drunk
        remaining_amt = self.quantity - total_drunk - self.sum_adjustments_grams
        return max(0.0, remaining_amt)

    @property
    def average_rating(self):
        if not self.reviews:
            return 0.0
        total = sum(r.rating for r in self.reviews)
        return round(total / len(self.reviews), 2)
    
    @property
    def tier_rating(self):
        """Get letter grade equivalent of average numeric rating."""
        return ScoreConverter.score_to_letter(self.average_rating)
    @property
    def tier_rating_flat(self):
        """Get flattened letter grade (no +/-) equivalent of average numeric rating."""
        return ScoreConverter.score_to_letter(self.average_rating, flatten=True)

    @property
    def last_drank(self):
        if self.finished:
            return "Finished"
        if not self.reviews:
            return "Never"
        # Sort reviews by date and get the last one
        sorted_reviews = sorted(self.reviews, key=lambda r: r.date)
        return sorted_reviews[-1].date if isinstance(sorted_reviews[-1].date, str) else sorted_reviews[-1].date.strftime("%Y-%m-%d")
    
    @property
    def sum_adjustments_grams(self):
        """Sum adjustments related to this tea."""
        total_adjustment_grams = sum(adj.amount for adj in self.adjustments)
        return total_adjustment_grams
    
    @property
    def sum_adjustments_cost(self):
        """Sum adjustments related to this tea."""
        total_adjustment_cost = sum(adj.cost for adj in self.adjustments)
        total_adjustment_cost = -total_adjustment_cost  # Adjustments are stored as negative for costs, so negate to get the actual cost basis adjustment
        return total_adjustment_cost
    
    @property
    def steep_count(self):
        """Total number of steeps across all reviews."""
        return sum(r.steep_count for r in self.reviews)
    
    @property
    def price_per_gram(self):
        """Price per gram of the tea."""
        return self.cost / self.quantity if self.quantity > 0 else 0
    
    @property
    def catalog_price_per_gram(self):
        """Normal price per gram of the tea."""
        if not self.catalog_price or self.catalog_price <= 0.01:
            return self.price_per_gram  # Fallback to actual price if catalog price is not set
        return self.catalog_price / self.quantity if self.quantity > 0 else 0
    
    @property
    def total_real_price_and_amt_including_adjustments(self):
        """Calculate total cost basis of the tea after adjustments."""
        total_cost = self.cost + self.sum_adjustments_cost
        total_amt = self.quantity - self.sum_adjustments_grams
        return total_cost, total_amt
    
    @property
    def finished(self):
        """Whether the tea is finished (remaining <= 0). We use <= 1 to allow for small measurement errors."""
        return self.remaining <= 1

    def to_dict(self):
        """Helper for saving to JSON/YAML later"""
        return {
            "id": self.id,
            "name": self.name,
            "vendor": self.vendor,
            "tea_type": self.tea_type,
            "cost": self.cost,
            "catalog_price": self.catalog_price,
            "quantity": self.quantity,
            "adjustments": [adjustment.to_dict() for adjustment in self.adjustments],
            "purchase_date": self.purchase_date if isinstance(self.purchase_date, str) else self.purchase_date.strftime("%Y-%m-%d"),
            "year": self.year,
            "purchase_note": self.purchase_note,
            "reviews": [review.to_dict() for review in self.reviews],
        }
    
    def get(self, key, default=None):
        """Helper to allow dict-like access to attributes."""
        return getattr(self, key, default)
    
def _get_value_with_flexible_key(data: dict, possible_keys: list, default=None):
        """Helper to get a value from a dict using a list of possible keys."""
        for key in possible_keys:
            if key in data:
                return data[key]
        return default