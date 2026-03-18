import dearpygui.dearpygui as dpg


from services.logger import Logger
from config import Config

class FontManager:
    def __init__(self):
        self.cfg = Config


    def getFontName(self, size=1, bold=False, fontName=None):
        # Get the current font name and size
        if fontName is None:
            fontName = self.cfg.DEFAULT_FONT
        style = "Bold" if bold else "Regular"
        # Map your size indices (1, 2, 3) to the suffix used in tags
        suffix = "" if size == 1 else str(size)

        return f"{fontName}{style}{suffix}"


    def bindLoadFonts(self):
        # Load fonts
        base_font_size = 16
        Logger.info(f"Loading fonts with base size: {base_font_size}")
        
        with dpg.font_registry():
            dpg.add_font("src/fonts/Roboto-Regular.ttf", base_font_size, tag="RobotoRegular")
            dpg.add_font("src/fonts/Roboto-Regular.ttf", base_font_size + 4, tag="RobotoRegular2")
            dpg.add_font("src/fonts/Roboto-Regular.ttf", base_font_size + 10, tag="RobotoRegular3")
            dpg.add_font("src/fonts/Roboto-Bold.ttf", base_font_size, tag="RobotoBold")
            dpg.add_font("src/fonts/Roboto-Bold.ttf", base_font_size + 4, tag="RobotoBold2")
            dpg.add_font("src/fonts/Roboto-Bold.ttf", base_font_size + 10, tag="RobotoBold3")
            # Merriweather 24pt regular
            dpg.add_font("src/fonts/Merriweather_24pt-Regular.ttf", base_font_size, tag="MerriweatherRegular")
            dpg.add_font("src/fonts/Merriweather_24pt-Regular.ttf", base_font_size + 4, tag="MerriweatherRegular2")
            dpg.add_font("src/fonts/Merriweather_24pt-Regular.ttf", base_font_size + 10, tag="MerriweatherRegular3")
            # Merriweather 24pt bold
            dpg.add_font("src/fonts/Merriweather_24pt-Bold.ttf", base_font_size, tag="MerriweatherBold")
            dpg.add_font("src/fonts/Merriweather_24pt-Bold.ttf", base_font_size + 4, tag="MerriweatherBold2")
            dpg.add_font("src/fonts/Merriweather_24pt-Bold.ttf", base_font_size + 10, tag="MerriweatherBold3")
            # Montserrat-regular
            dpg.add_font("src/fonts/Montserrat-Regular.ttf", base_font_size, tag="MontserratRegular")
            dpg.add_font("src/fonts/Montserrat-Regular.ttf", base_font_size + 4, tag="MontserratRegular2")
            dpg.add_font("src/fonts/Montserrat-Regular.ttf", base_font_size + 10, tag="MontserratRegular3")
            # Montserrat-bold
            dpg.add_font("src/fonts/Montserrat-Bold.ttf", base_font_size, tag="MontserratBold")
            dpg.add_font("src/fonts/Montserrat-Bold.ttf", base_font_size + 4, tag="MontserratBold2")
            dpg.add_font("src/fonts/Montserrat-Bold.ttf", base_font_size + 10, tag="MontserratBold3")
            # Opensans regular
            dpg.add_font("src/fonts/OpenSans-Regular.ttf", base_font_size, tag="OpenSansRegular")
            dpg.add_font("src/fonts/OpenSans-Regular.ttf", base_font_size + 4, tag="OpenSansRegular2")
            dpg.add_font("src/fonts/OpenSans-Regular.ttf", base_font_size + 10, tag="OpenSansRegular3")
            # Opensans bold
            dpg.add_font("src/fonts/OpenSans-Bold.ttf", base_font_size, tag="OpenSansBold")
            dpg.add_font("src/fonts/OpenSans-Bold.ttf", base_font_size + 4, tag="OpenSansBold2")
            dpg.add_font("src/fonts/OpenSans-Bold.ttf", base_font_size + 10, tag="OpenSansBold3")

            # Set the default font to specified in settings
            if self.cfg.DEFAULT_FONT is not None and self.cfg.DEFAULT_FONT in self.cfg.VALID_FONTS:
                dpg.bind_font(f"{self.cfg.DEFAULT_FONT}Regular")
                Logger.info(f"Default font set to {self.cfg.DEFAULT_FONT}")
            else:
                
                dpg.bind_font("OpenSansRegular")
                Logger.warning(f"Default font {self.cfg.DEFAULT_FONT} not found, using OpenSansRegular")