import os
import dearpygui.dearpygui as dpg
from services.logger import Logger
from config import Config

class FontManager:
    def __init__(self):
        self.cfg = Config
        self.base_font_size = 16
        self.size_offsets = {1: 0, 2: 4, 3: 10, 4: 16}
        self._loaded_fonts = set()
        
        # Explicit unique tag for our main application font container
        self.registry_tag = "app_global_font_registry"

    def _ensure_font_loaded(self, font_name, style, size_idx):
        """Internal helper that explicitly targets the main font registry."""
        suffix = "" if size_idx == 1 else str(size_idx)
        tag = f"{font_name}{style}{suffix}"
        
        if tag in self._loaded_fonts:
            return tag
            
        file_mapping = {
            "Roboto": f"Roboto-{style}.ttf",
            "Merriweather": f"Merriweather_24pt-{style}.ttf",
            "Montserrat": f"Montserrat-{style}.ttf",
            "OpenSans": f"OpenSans-{style}.ttf"
        }
        
        filename = file_mapping.get(font_name, f"OpenSans-{style}.ttf")
        font_path = os.path.join(Config.FONTS_DIR, filename)
        pixel_size = self.base_font_size + self.size_offsets.get(size_idx, 0)
        
        try:
            # FIX: Use add_font with the explicit parent target instead of context manager
            dpg.add_font(font_path, pixel_size, tag=tag, parent=self.registry_tag)
            self._loaded_fonts.add(tag)
            Logger.info(f"Dynamically generated font asset: {tag}")
        except Exception as e:
            Logger.error(f"Failed to load dynamic font {tag}: {e}")
            return f"{self.cfg.DEFAULT_FONT}Regular"
            
        return tag

    def get_font_name(self, size=1, bold=False, font_name=None):
        """Returns the font tag, generating it on-the-fly if missing."""
        if font_name is None:
            font_name = self.cfg.DEFAULT_FONT
            
        style = "Bold" if bold else "Regular"
        return self._ensure_font_loaded(font_name, style, size)

    def bind_load_fonts(self):
        """Initializes the named registry container and links the initial font."""
        Logger.info(f"Initializing master font container from: {Config.FONTS_DIR}")
        
        # Create the primary registry and pin it with a hardcoded tag
        dpg.add_font_registry(tag=self.registry_tag)
        
        default_family = "OpenSans"
        if self.cfg.DEFAULT_FONT in self.cfg.VALID_FONTS:
            default_family = self.cfg.DEFAULT_FONT
            Logger.info(f"Default font set to {default_family}")
        else:
            Logger.warning(f"Default font {self.cfg.DEFAULT_FONT} not found, using OpenSans")
            
        # Bootstrap just the single default font configuration for app startup
        default_tag = self._ensure_font_loaded(default_family, "Regular", 1)
        dpg.bind_font(default_tag)

    def dpg_preload_then_bind(self, item, size=1, bold=False, font_name=None):
        """Public method to bind a font to an item, ensuring it's loaded first."""
        tag = self.get_font_name(size=size, bold=bold, font_name=font_name)
        dpg.bind_item_font(item, tag)