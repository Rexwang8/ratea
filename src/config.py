# src/config.py
import os

class Config:
    # Things you can easily change to customize the app without digging through the code
    # --- Review Defaults ---
    DEFAULT_RATING = 'B'  # Default letter grade for new reviews
    DEFAULT_AMOUNT_DRUNK = 5.0  # Default amount drunk in grams
    DEFAULT_STEEPS = 5  # Default number of steeps
    DEFAULT_VESSEL_SIZE = 100.0  # Default vessel size in ml


    # --- UI Settings ---
    THEME = "Dark"  # Options: Dark
    LANGUAGE = "en"  # Default language
    UI_SCALE = 2.0  # UI scaling factor
    
    # Display Defaults
    DEFAULT_WIDTH = 1800 * 2
    DEFAULT_HEIGHT = 1000 * 2

    


    # Things you shouldn't change unless you know what you're doing, as they are more fundamental to how the app works
    # --- App Settings ---
    APP_NAME = "Ratea Tea Reviewer"
    VERSION = "2.0.0"

    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")
    BACKUP_DIR = os.path.join(BASE_DIR, "..", "backup")
    SRC_DIR = os.path.join(BASE_DIR, "..", "src")
    FONTS_DIR = os.path.join(SRC_DIR, "fonts") # Default: src/fonts

    # TEADB INTEGRATION (EXPERIMENTAL)
    TEADB_API_BASE_URL = "https://my.teadb.org/api/user"
    TEADB_TOKEN = "your-api-token"  # Replace with your actual token
    TEADB_INTEGRATION_ENABLED = True  # Set to False to disable Teadb integration
    # under src/connectors/teadb
    TEADB_MAPPING_FILE_PATH = os.path.join(SRC_DIR, "connectors", "teadb", "teadb_mapping.json")  # Path to the tea mapping file
    TEADB_RAW_DATA_FILE_PATH = os.path.join(SRC_DIR, "connectors", "teadb", "teadb_raw_data.json")  # Path to the raw tea data file

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
    