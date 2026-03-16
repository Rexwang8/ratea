import uuid
import datetime as dt
from services.date_helper import parse_flexible_date
from services.score_converter import ScoreConverter

class Review:
    def __init__(self, id: str, tea_id: str, rating: float, notes: str, date: dt.datetime = None, amount_drunk: float = 0.0, steeps: int = 0, vesselSize: float = 0.0, method: str = "gongfu", isFreeSample: bool = False):
        self.id = id if id else str(uuid.uuid4())
        self.tea_id = tea_id # Link back to the parent tea
        self.rating = rating # Rating of the tea out of 5 points, corresponding to either stars or letter grades
        self.notes = notes # Textual review of the tea
        self.date = date if date else dt.datetime.now() # Date of the review
        self.amount_drunk = round(amount_drunk, 2)  # Amount drunk in grams, rounded to 2 decimal places
        self.vesselSize = round(vesselSize, 1)  # Size of the vessel used in milliliters, rounded to 1 decimal place
        self.method = method  # Brewing method used
        self.isFreeSample = isFreeSample  # Whether this review is for a free sample
        self.steep_count = int(steeps)  # Number of steeps for this review, stored as an integer


    @property
    def water_used_ml(self):
        """Calculate total water used in milliliters."""
        return self.vesselSize * self.steep_count
    
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
        # You would implement your YAML parsing logic here
        id = str(uuid.uuid4())
        datetime_str = data.get("date", "")
        review_dt = parse_flexible_date(datetime_str)
        instance = cls(
            id=data.get("id", id),
            tea_id=data.get("tea_id", ""),
            rating=data.get("rating", 0.0),
            notes=data.get("notes", ""),
            date=review_dt,
            amount_drunk=data.get("amount_drunk", 0.0),
            vesselSize=data.get("vesselSize", 0.0),
            method=data.get("method", "gongfu"),
            isFreeSample=data.get("isFreeSample", False),
            steeps=data.get("steeps", 0)
        )
        return instance

    '''
    attributesJson: '{"Amount": 7.0, "Final Score": 4.0, "Method": "Gongfu", "Name":
      "TSD Forest Fragrance Qimen", "Notes (Long)": "TSD Forest Fragrance Qimen\n7.4g
      150ml\n15, 25, 45, 75, 120, 300\n\nVery tiny leaves, perhaps qimen gongfu (congou)?\nSmells
      malty and sweet\nSweet, malty, woody, sappy profile. rich and mildly oily and
      coating texturally. Slightly orangey. Some fruity back notes. Later steeps lean
      more floral.\n\nSome of the woody sappy notes remind me of ORTs 2024 gatekeeper
      with its heirloom gongmei varietal but this is better.\n\nSurprisingly good,
      price is fairly good for quality.  (~60c/g)\nI think this outperforms B grade
      hongs handily, so giving it an A.\n\nA+", "Notes (short)": "None Needed", "Steeps":
      6, "Vessel size": 120, "date": 1767852000.0, "dateAdded": 1768002865.80064}'
    '''
    @classmethod
    def from_dict(cls, data: dict):
        """Initialize from a dictionary (like from JSON/YAML)"""
        attributes = data.get("attributes", {})
        raw_date = attributes.get("date", 0.0)
        purchase_dt = parse_flexible_date(raw_date)

        instance = cls(
            id=data.get("id", str(uuid.uuid4())),
            tea_id=data.get("tea_id", ""),
            rating=attributes.get("Final Score", 0.0),
            notes=attributes.get("Notes (Long)", ""),
            date=purchase_dt,
            amount_drunk=attributes.get("Amount", 0.0),
            vesselSize=attributes.get("Vessel size", 0.0),
            steeps=attributes.get("Steeps", 0),
            method=attributes.get("Method", "gongfu"),
            isFreeSample=attributes.get("Is Free Sample", False)
        )
        return instance


    def to_dict(self):
        """Helper for saving to JSON/YAML later"""
        return {
            "id": self.id,
            "tea_id": self.tea_id,
            "rating": self.rating,
            "date": self.date if isinstance(self.date, str) else self.date.strftime("%Y-%m-%d"),
            "amount_drunk": self.amount_drunk,
            "vesselSize": self.vesselSize,
            "method": self.method,
            "steeps": self.steep_count,
            "isFreeSample": self.isFreeSample,
            
            "notes": self.notes,
        }
    
    # aliases
    @property
    def steeps(self):
        return self.steep_count
    @property
    def vessel_size(self):
        return self.vesselSize
    @property
    def amount(self):
        return self.amount_drunk
        
    @property
    def rating_letter(self):
        """Get letter grade equivalent of numeric rating."""
        return ScoreConverter.score_to_letter(self.rating)
    
    def __str__(self):
        return f"Review for {self.tea_id} (date: {self.date}): {self.amount_drunk}g {self.rating_letter} - {self.notes[:30]}..."
