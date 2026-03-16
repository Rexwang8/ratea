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
        Logger.info(("Loading fonts..."))
        with dpg.font_registry():
            dpg.add_font("src/fonts/Roboto-Regular.ttf", 16, tag="RobotoRegular")
            dpg.add_font("src/fonts/Roboto-Regular.ttf", 20, tag="RobotoRegular2")
            dpg.add_font("src/fonts/Roboto-Regular.ttf", 26, tag="RobotoRegular3")
            dpg.add_font("src/fonts/Roboto-Bold.ttf", 16, tag="RobotoBold")
            dpg.add_font("src/fonts/Roboto-Bold.ttf", 20, tag="RobotoBold2")
            dpg.add_font("src/fonts/Roboto-Bold.ttf", 26, tag="RobotoBold3")
            # Merriweather 24pt regular
            dpg.add_font("src/fonts/Merriweather_24pt-Regular.ttf", 16, tag="MerriweatherRegular")
            dpg.add_font("src/fonts/Merriweather_24pt-Regular.ttf", 20, tag="MerriweatherRegular2")
            dpg.add_font("src/fonts/Merriweather_24pt-Regular.ttf", 26, tag="MerriweatherRegular3")
            # Merriweather 24pt bold
            dpg.add_font("src/fonts/Merriweather_24pt-Bold.ttf", 16, tag="MerriweatherBold")
            dpg.add_font("src/fonts/Merriweather_24pt-Bold.ttf", 20, tag="MerriweatherBold2")
            dpg.add_font("src/fonts/Merriweather_24pt-Bold.ttf", 26, tag="MerriweatherBold3")
            # Montserrat-regular
            dpg.add_font("src/fonts/Montserrat-Regular.ttf", 16, tag="MontserratRegular")
            dpg.add_font("src/fonts/Montserrat-Regular.ttf", 20, tag="MontserratRegular2")
            dpg.add_font("src/fonts/Montserrat-Regular.ttf", 26, tag="MontserratRegular3")
            # Montserrat-bold
            dpg.add_font("src/fonts/Montserrat-Bold.ttf", 16, tag="MontserratBold")
            dpg.add_font("src/fonts/Montserrat-Bold.ttf", 20, tag="MontserratBold2")
            dpg.add_font("src/fonts/Montserrat-Bold.ttf", 26, tag="MontserratBold3")
            # Opensans regular
            dpg.add_font("src/fonts/OpenSans-Regular.ttf", 18, tag="OpenSansRegular")
            dpg.add_font("src/fonts/OpenSans-Regular.ttf", 20, tag="OpenSansRegular2")
            dpg.add_font("src/fonts/OpenSans-Regular.ttf", 26, tag="OpenSansRegular3")
            # Opensans bold
            dpg.add_font("src/fonts/OpenSans-Bold.ttf", 18, tag="OpenSansBold")
            dpg.add_font("src/fonts/OpenSans-Bold.ttf", 20, tag="OpenSansBold2")
            dpg.add_font("src/fonts/OpenSans-Bold.ttf", 26, tag="OpenSansBold3")

            # Set the default font to specified in settings
            if self.cfg.DEFAULT_FONT is not None and self.cfg.DEFAULT_FONT in self.cfg.VALID_FONTS:
                dpg.bind_font(f"{self.cfg.DEFAULT_FONT}Regular")
                Logger.info(f"Default font set to {self.cfg.DEFAULT_FONT}")
            else:
                
                dpg.bind_font("OpenSansRegular")
                Logger.warning(f"Default font {self.cfg.DEFAULT_FONT} not found, using OpenSansRegular")