# src/ui/modals/template_modal.py
"""Template modal — copy this file to create a new modal dialog.

Replace all "Template" / "template" placeholders with your modal's name.

Usage in app.py:
    from ui.modals.template_modal import show_template_modal
    # ...
    dpg.add_menu_item(label="Open Template", callback=lambda: show_template_modal(fonts=self.fonts))
"""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import dearpypixl as dp

from config import Config
from services.logger import Logger


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def show_template_modal(fonts=None, data_manager=None):
    """Open the template modal."""
    modal = TemplateModal(fonts=fonts, data_manager=data_manager)
    modal._show()


# ---------------------------------------------------------------------------
# Modal class
# ---------------------------------------------------------------------------

class TemplateModal:
    """Modal dialog for [describe purpose].

    Follows the same patterns as other modals in this directory:
      - Public module-level function to instantiate and show.
      - Class with _show() / close() methods.
      - Uses dearpypixl dp.Window for proper modal stacking.
      - Callbacks prefixed with underscore.
    """

    def __init__(self, fonts=None, data_manager=None):
        self.fonts = fonts
        self.data_manager = data_manager
        self.win = None

    def _bind_font(self, item, size=2, bold=False):
        """Bind a font to the last created item, if fonts are available."""
        if self.fonts:
            dpg.bind_item_font(item, self.fonts.get_font_name(size=size, bold=bold))

    # ── UI building ────────────────────────────────────────────────────

    def _show(self):
        width = int(500 * Config.UI_SCALE)
        height = int(400 * Config.UI_SCALE)

        self.win = dp.Window(
            label="Template Window",
            modal=True,
            no_close=False,
            width=width,
            height=height,
        )
        with self.win:
            # Header
            dpg.add_text("Template Modal")
            self._bind_font(dpg.last_item(), size=3, bold=True)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # Body — scrollable content area
            body_height = int((height - 150) * Config.UI_SCALE)
            with dpg.child_window(width=-1, height=body_height, border=True):
                dpg.add_text("Your content goes here.")
                self._bind_font(dpg.last_item(), size=2, bold=False)

            # Footer — action buttons
            dpg.add_separator()
            with dpg.group(horizontal=True):
                bw = int(120 * Config.UI_SCALE)
                bh = int(40 * Config.UI_SCALE)
                dpg.add_button(
                    label="Confirm",
                    callback=self._on_confirm,
                    width=bw,
                    height=bh,
                )
                self._bind_font(dpg.last_item(), size=2, bold=True)
                dpg.add_button(
                    label="Cancel",
                    callback=self.close,
                    width=bw,
                    height=bh,
                )
                self._bind_font(dpg.last_item(), size=2, bold=True)

    # ── Callbacks ──────────────────────────────────────────────────────

    def _on_confirm(self):
        """Handle the confirm/save action."""
        Logger.info("Template modal: Confirm pressed.")
        # TODO: implement your save logic here
        # 1. Read widget values with dpg.get_value(tag)
        # 2. Update data_manager or models
        # 3. Export/save if needed
        # 4. Refresh UI
        self.close()

    # ── Close / cleanup ────────────────────────────────────────────────

    def close(self):
        if self.win:
            self.win.delete()
            self.win = None

    # ── Helpers ────────────────────────────────────────────────────────