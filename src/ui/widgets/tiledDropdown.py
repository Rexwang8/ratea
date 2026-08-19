"""Reusable tiled dropdown widget for DearPyGui.

A collapsible dropdown that presents its options as a grid of tiled buttons
instead of a flat listbox. The header button shows the currently selected
value; clicking it toggles the tile grid below.

The selected value is also stored in a hidden input widget so callers can
read it with ``dpg.get_value(tag)``, making this a drop-in replacement for
``dp.Combo`` in forms that collect a single choice.
"""

from __future__ import annotations

import dearpygui.dearpygui as dpg
from ui.fonts import FontManager


class TiledDropdown:
    """Collapsible dropdown whose options are displayed as tiled buttons.

    Args:
        rows: List of rows, each a list of option strings. Each row renders as
            a horizontal row of tiles.
        label: Optional text shown above the header button.
        default_value: Initially selected value (must exist inside ``rows``).
        width: Header button width in pixels.
        tile_width: Width of each tile (pixels).
        tile_height: Height of each tile (pixels).
        tile_spacing: Horizontal gap between tiles in a row (pixels).
        row_spacing: Vertical gap between rows of tiles (pixels).
        fonts: Optional ``FontManager`` used to bind fonts at the requested
            ``font_size`` / ``font_bold``. Pass None to use the app default.
        font_size: FontManager size index (1=base, 2=+4, 3=+10, 4=+16).
        font_bold: Bind the bold font variant.
        on_change: Optional callback ``callable(value: str)`` fired when a tile
            is clicked to select a new value.
        tooltip_fn: Optional ``callable(value: str) -> str | None`` returning a
            tooltip string shown while hovering a tile.
    """

    def __init__(
        self,
        *,
        rows: list[list[str]],
        label: str = "",
        default_value: str = "",
        width: int = 200,
        tile_width: int = 48,
        tile_height: int = 32,
        tile_spacing: int = 4,
        row_spacing: int = 4,
        fonts: FontManager | None = None,
        font_size: int = 2,
        font_bold: bool = False,
        on_change=None,
        tooltip_fn=None,
    ):
        self.rows = rows
        self._fonts = fonts
        self._font_size = font_size
        self._font_bold = font_bold
        self._on_change = on_change
        self._tooltip_fn = tooltip_fn

        self._all_values = [v for row in rows for v in row]
        self._value = (
            default_value
            if default_value in self._all_values
            else (self._all_values[0] if self._all_values else "")
        )
        self._panel_open = False

        self._tile_tags: list[list[int]] = []  # mirror of self.rows
        self.value_tag: int = dpg.generate_uuid()

        # Theme used to highlight the currently selected tile.
        with dpg.theme() as self._selected_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button, (60, 110, 190, 255),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered, (80, 130, 210, 255),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonActive, (45, 90, 170, 255),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_Text, (255, 255, 255, 255),
                    category=dpg.mvThemeCat_Core,
                )

        self.tag = dpg.generate_uuid()
        self._button_tag = dpg.generate_uuid()
        self._panel_tag = dpg.generate_uuid()

        # ---- UI ----
        with dpg.group(tag=self.tag):
            if label:
                dpg.add_text(label)
                self._bind_font(dpg.last_item())

            dpg.add_button(
                tag=self._button_tag,
                label=self._header_text(),
                width=width,
                callback=self._on_header_clicked,
            )
            self._bind_font(self._button_tag)

            with dpg.child_window(
                tag=self._panel_tag,
                width=self._panel_width(width, tile_width, tile_spacing),
                height=self._panel_height(tile_height, row_spacing),
                border=True,
            ):
                self._build_tiles(tile_width, tile_height, tile_spacing, row_spacing)

            # Hidden value slot: lets callers read the selection via
            # dpg.get_value(self.value_tag), just like a combo widget.
            dpg.add_input_text(
                tag=self.value_tag,
                default_value=self._value,
                show=False,
            )

        dpg.hide_item(self._panel_tag)
        self._apply_selected_highlight()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def value(self) -> str:
        """Currently selected tile value."""
        return self._value

    def set_value(self, value: str):
        """Set the selected value and refresh the UI."""
        if value not in self._all_values:
            return
        self._value = value
        dpg.set_value(self.value_tag, value)
        dpg.configure_item(self._button_tag, label=self._header_text())
        self._apply_selected_highlight()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _header_text(self) -> str:
        arrow = "V" if self._panel_open else ">"
        return f"{self._value}  {arrow}"

    def _bind_font(self, item):
        if self._fonts:
            self._fonts.dpg_preload_then_bind(
                item,
                size=self._font_size,
                bold=self._font_bold,
            )

    def _panel_width(self, button_width: int, tile_width: int, tile_spacing: int) -> int:
        content_width = 0
        for row in self.rows:
            if not row:
                continue
            row_width = len(row) * tile_width + (len(row) - 1) * tile_spacing
            content_width = max(content_width, row_width)
        # +8 to account for the child window border and small breathing room.
        return max(button_width, content_width) + 8

    def _panel_height(self, tile_height: int, row_spacing: int) -> int:
        if not self.rows:
            return 30
        num_rows = len(self.rows)
        return num_rows * tile_height + (num_rows - 1) * row_spacing + 8

    def _build_tiles(
        self,
        tile_width: int,
        tile_height: int,
        tile_spacing: int,
        row_spacing: int,
    ):
        for row_idx, row in enumerate(self.rows):
            row_tags: list[int] = []
            with dpg.group(horizontal=True, horizontal_spacing=tile_spacing):
                for value in row:
                    tile = dpg.add_button(
                        label=str(value),
                        width=tile_width,
                        height=tile_height,
                        callback=self._on_tile_clicked,
                        user_data=value,
                    )
                    self._bind_font(tile)

                    if self._tooltip_fn:
                        tip = self._tooltip_fn(value)
                        if tip:
                            with dpg.tooltip(tile):
                                dpg.add_text(tip)

                    row_tags.append(tile)

            self._tile_tags.append(row_tags)

            if row_idx < len(self.rows) - 1:
                dpg.add_spacer(height=row_spacing)

    def _toggle_panel(self):
        self.set_panel_open(not self._panel_open)

    def set_panel_open(self, open_state: bool):
        """Show or hide the tile panel, updating the header arrow."""
        self._panel_open = open_state
        if open_state:
            dpg.show_item(self._panel_tag)
        else:
            dpg.hide_item(self._panel_tag)
        dpg.configure_item(self._button_tag, label=self._header_text())

    def _on_header_clicked(self, sender=None, app_data=None):
        self._toggle_panel()

    def _on_tile_clicked(self, sender=None, app_data=None, user_data=None):
        self.set_value(user_data)
        self.set_panel_open(False)
        if self._on_change:
            self._on_change(user_data)

    def _apply_selected_highlight(self):
        """Highlight the tile matching the current value, clearing others."""
        for row_tags in self._tile_tags:
            for tag in row_tags:
                dpg.bind_item_theme(tag, 0)

        if not self._value or not self._tile_tags:
            return

        for row_tags, values in zip(self._tile_tags, self.rows):
            for tag, val in zip(row_tags, values):
                if val == self._value:
                    dpg.bind_item_theme(tag, self._selected_theme)
                    return
