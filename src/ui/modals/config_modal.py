# src/ui/modals/config_modal.py
"""Configuration editing modal — WORK IN PROGRESS."""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import dearpypixl as dp

from config import Config
from services.logger import Logger


def show_config_modal(fonts=None):
    """Open the settings modal (WIP)."""
    modal = ConfigModal(fonts=fonts)
    modal._show()


class ConfigModal:
    """Modal for editing application settings — placeholder until implemented."""

    def __init__(self, fonts=None):
        self.fonts = fonts
        self.win = None

    def _show(self):
        width = int(500 * Config.UI_SCALE)
        height = int(350 * Config.UI_SCALE)

        self.win = dp.Window(
            label="Settings", modal=True, no_close=False,
            width=width, height=height,
        )
        with self.win:
            dpg.add_text("Application Settings")
            dpg.bind_item_font(
                dpg.last_item(),
                self.fonts.get_font_name(size=3, bold=True) if self.fonts else 0,
            )
            dpg.add_separator()
            dpg.add_spacer(height=20)

            dpg.add_text("Work in progress — settings editing coming soon.")
            dpg.bind_item_font(
                dpg.last_item(),
                self.fonts.get_font_name(size=2, bold=False) if self.fonts else 0,
            )

            dpg.add_spacer(height=40)

            bw = int(120 * Config.UI_SCALE)
            bh = int(40 * Config.UI_SCALE)
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Save Settings (Placeholder)",
                    callback=self._on_dummy_save,
                    width=bw,
                    height=bh,
                )
                dpg.bind_item_font(
                    dpg.last_item(),
                    self.fonts.get_font_name(size=2, bold=True) if self.fonts else 0,
                )
                dpg.add_button(
                    label="Close",
                    callback=self._close,
                    width=bw,
                    height=bh,
                )
                dpg.bind_item_font(
                    dpg.last_item(),
                    self.fonts.get_font_name(size=2, bold=True) if self.fonts else 0,
                )

    def _on_dummy_save(self):
        """Placeholder save — does nothing yet."""
        Logger.info("Config modal: Save pressed (no-op — WIP).")

    def _close(self):
        if self.win:
            self.win.delete()
            self.win = None