# Score is kept in a 0-5 point system that can represent stars or letter grades. This file helps convert raw scores to letter grades and vice versa.


# src/services/score_converter.py

from services.logger import Logger

class ScoreConverter:
    LETTER_GRADE_MAP = {
        "S": 5.0,
        "A+": 4.33,
        "A":  4.0,
        "A-": 3.66,
        "B+": 3.33,
        "B":  3.0,
        "B-": 2.66,
        "C+": 2.33,
        "C":  2.0,
        "C-": 1.66,
        "D+": 1.33,
        "D":  1.0,
        "D-": 0.66,
        "F":  0.0
    }
    # list of 2 element lists for DPG to recognize the tick labels correctly (one for labels, one for positions)
    LETTER_GRADE_MAP_DPG_LABELS = [
        ["S", 5.0],
        ["A+", 4.33],
        ["A",  4.0],
        ["A-", 3.66],
        ["B+", 3.33],
        ["B",  3.0],
        ["B-", 2.66],
        ["C+", 2.33],
        ["C",  2.0],
        ["C-", 1.66],
        ["D+", 1.33],
        ["D",  1.0],
        ["D-", 0.66],
        ["F",  0.0]
    ]

    grade_meanings_alternate = {
        "S":  "S (X) Outstanding.  -> Must try. Strongly consider dedicated order, rebuy.",
        
        "A+": "A (+) Notably Good (High). -> Strong sample, rebuyable.",
        "A":  "A (X) Notably Good (Mid).  -> Strong sample, rebuyable.",
        "A-": "A (-) Notably Good (Low).  -> Strong sample, rebuyable.",
        
        "B+": "B (+) Above Average (High). -> Consider sample.",
        "B":  "B (X) Above Average (Mid).  -> Consider sample.",
        "B-": "B (-) Above Average (Low).  -> Consider sample.",
        
        "C+": "C (+) Drinkable/Unremarkable (High). -> Wouldn't rebuy/sample.",
        "C":  "C (X) Drinkable/Unremarkable (Mid).  -> Wouldn't rebuy/sample.",
        "C-": "C (-) Drinkable/Unremarkable (Low).  -> Wouldn't rebuy/sample.",
        
        "D+": "D (+) Bad (High). -> Avoid.",
        "D":  "D (X) Bad (Mid).  -> Avoid.",
        "D-": "D (-) Bad (Low).  -> Avoid.",
        
        "F":  "Dumped"
    }


    @classmethod
    def score_to_letter(cls, score: float, flatten: bool = False) -> str:
        """Convert a numeric score (0-5) to a letter grade."""
        if score is None:
            return "F"
        for letter, threshold in sorted(cls.LETTER_GRADE_MAP.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                if flatten:
                    # Flatten to just letter without +/-
                    return letter[0]  # Return the first character (e.g., "A" from "A+")
                return letter
        return "F"  # Default to "F" if score is below all thresholds

    @classmethod
    def letter_to_score(cls, letter: str) -> float:
        """Convert a letter grade to a numeric score (0-5)."""
        converted = cls.LETTER_GRADE_MAP.get(letter.upper())
        Logger.debug(f"Converting letter '{letter}' to score: {converted}")
        return converted if converted is not None else 0.0

    @classmethod
    def get_grade_meaning(cls, letter: str) -> str:
        """Get the meaning/description of a letter grade."""
        return cls.grade_meanings_alternate.get(letter.upper(), "Unknown Grade")
    
    @classmethod
    def get_grade_meaning_numeric(cls, score: float) -> str:
        """Get the meaning/description of a numeric score."""
        letter = cls.score_to_letter(score)
        return cls.get_grade_meaning(letter)
    
    @classmethod
    def is_valid_letter(cls, letter: str) -> bool:
        """Check if the provided letter grade is valid."""
        return letter.upper() in cls.LETTER_GRADE_MAP.keys()
    