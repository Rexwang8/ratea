# src/config.py
import os

class Config:
    # --- App Settings ---
    APP_NAME = "Ratea Tea Reviewer"
    VERSION = "2.0.0"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    BACKUP_DIR = os.path.join(BASE_DIR, "..", "backup")
    SRC_DIR = os.path.join(BASE_DIR, "..", "src")
    FONTS_DIR = os.path.join(SRC_DIR, "fonts") # Default: src/fonts

    # --- UI Settings ---
    THEME = "Dark"  # Options: Dark
    LANGUAGE = "en"  # Default language
    UI_SCALE = 2.0  # UI scaling factor
    
    # Display Defaults
    DEFAULT_WIDTH = 1800 * 2
    DEFAULT_HEIGHT = 1000 * 2

    # --- Colors (RGBA) ---
    # Using a nested class or dict for grouping makes it readable
    class Colors:
        TEXT_WHITE = (255, 255, 255, 255)
        TEXT_RED = (255, 0, 0, 200)
        TEXT_GREEN = (0, 255, 0, 200)
        
        # Table Colors
        CELL_AUTOCALC = (0, 100, 0, 60)
        CELL_INVALID = (100, 0, 0, 100)

        CELL_LIGHT_BLUE = (100, 150, 255, 50)
        CELL_LIGHT_YELLOW = (255, 255, 100, 50)
        CELL_LIGHT_GREEN = (100, 255, 100, 40)
        CELL_DARK_GREEN = (0, 150, 0, 100)
        
    # --- Logging ---
    DEBUG_LEVEL = "INFO" # ALL, INFO, WARNING, ERROR, CRITICAL

    # --- Font Settings ---
    DEFAULT_FONT = "OpenSans"
    VALID_FONTS = ["OpenSans", "Roboto", "Merriweather", "Montserrat"]

    # --- Other Settings ---
    TYPES_OF_ADJUSTMENTS_TO_TEA = ["Standard", "Gift", "Sale", "Other"]  # Example adjustment types
    