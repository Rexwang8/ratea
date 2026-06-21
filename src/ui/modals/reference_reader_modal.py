# src/ui/modals/reference_reader_modal.py
"""Reference Reader modal — displays markdown/text files with basic formatting.

Supports:
  - .txt and .md files (others rejected with error)
  - Headers: # ## ###
  - Inline images: ![alt](path/to/image.png) or ![alt](path/to/image.jpg)
  - Images loaded as DPG static textures, properly cleaned up on close

Usage in app.py:
    from ui.modals.reference_reader_modal import show_reference_reader
    # ...
    dpg.add_menu_item(label="Open Reference",
        callback=lambda: show_reference_reader(
            filepath="references/drinking/puerh/sheng_brewing_guide.txt",
            fonts=self.fonts))
"""

from __future__ import annotations

import os
import re
import dearpygui.dearpygui as dpg
import dearpypixl as dp

from config import Config
from ui.fonts import FontManager
from services.logger import Logger
from services.text_helper import wrap_text_no_break_words


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def show_reference_reader(filepath: str, fonts=None, data_manager=None):
    """Open the reference reader modal for a given text/markdown file."""
    # Resolve path relative to project root if not absolute
    if not os.path.isabs(filepath):
        # __file__ is src/ui/modals/reference_reader_modal.py
        # Go up 4 levels to reach project root:
        #   src/ui/modals/ -> src/ui/ -> src/ -> project root (ratea/)
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
        filepath = os.path.join(project_root, filepath)

    # Validate file extension
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in (".txt", ".md"):
        Logger.error(f"Reference reader: unsupported file type '{ext}' for {filepath}")
        _show_error_modal(
            f"Unsupported file type: {ext}\n\nOnly .txt and .md files are supported.",
            fonts=fonts,
        )
        return

    if not os.path.exists(filepath):
        Logger.error(f"Reference reader: file not found: {filepath}")
        _show_error_modal(f"File not found:\n{filepath}", fonts=fonts)
        return

    modal = ReferenceReaderModal(filepath, fonts=fonts, data_manager=data_manager)
    modal._show()


def _show_error_modal(message: str, fonts=None):
    """Show a simple error popup."""
    win = dp.Window(label="Error", modal=True, no_close=False,
                    width=int(400 * Config.UI_SCALE), height=int(200 * Config.UI_SCALE))
    with win:
        dpg.add_text(message)
        if fonts:
            fonts.dpg_preload_then_bind(dpg.last_item(), size=2, bold=False)
        dpg.add_spacer(height=10)
        dpg.add_button(label="OK", width=100, height=30,
                       callback=lambda: win.delete())


# ---------------------------------------------------------------------------
# Modal class
# ---------------------------------------------------------------------------

class ReferenceReaderModal:
    """Modal dialog that displays the contents of a text/markdown file."""

    def __init__(self, filepath: str, fonts=None, data_manager=None):
        self.filepath = filepath
        self.fonts: FontManager = fonts
        self.data_manager = data_manager
        self.win = None
        # Track loaded texture tags for cleanup
        self._texture_tags: list[str] = []

    # ── UI building ────────────────────────────────────────────────────

    def _show(self):
        # Should open close to full screen, get full screen size
        monitor_width, monitor_height = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()

        width = int(monitor_width * 0.9)
        height = int(monitor_height * 0.95)

        label = os.path.splitext(os.path.basename(self.filepath))[0]
        label = label.replace("_", " ").replace("-", " ").title()

        self.win = dp.Window(
            label=label,
            modal=True,
            no_close=False,
            width=width,
            height=height,
        )
        Logger.info(f"[References] Opening reference reader modal for '{self.filepath}' with title '{label}'")
        with self.win:
            # Header, Go up two levels because 1 level is the folder containing the file, and we want to show the parent folder of that as well for context
            dpg.add_text(f"Reference: {label} | Parent directory: {os.path.basename(os.path.dirname((os.path.dirname(self.filepath))))}")
            self._bind_font(dpg.last_item(), size=3, bold=True)
            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Body — rendered inline so the window handles scrolling naturally
            with dpg.group(horizontal=True):
                # Add a vertical spacer to the left for padding
                dpg.add_spacer(width=10)
                # We must put it in its own group because the content is multi-object.
                with dpg.group(horizontal=False):
                        self._render_content()

            # Footer — always visible at the bottom of the scroll
            dpg.add_separator()
            with dpg.group(horizontal=True):
                bw = int(120 * Config.UI_SCALE)
                bh = int(40 * Config.UI_SCALE)
                dpg.add_button(
                    label="Close",
                    callback=self.close,
                    width=bw,
                    height=bh,
                )
                self._bind_font(dpg.last_item(), size=2, bold=True)

    def _render_content(self):
        """Parse the file and render its contents as DPG widgets."""
        with open(self.filepath, "r", encoding="utf-8") as f:
            raw = f.read()

        lines = raw.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]

            # --- Image on its own line: ![alt](path) ---
            img_match = re.match(r"^!\[.*?\]\((.+?)\)\s*$", line.strip())
            if img_match:
                self._render_image(img_match.group(1))
                i += 1
                continue

            # --- Header: ### / ## / # ---
            header_match = re.match(r"^(#{1,3})\s+(.+)$", line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2)
                size_map = {1: 4, 2: 3, 3: 2}
                bold_map = {1: True, 2: True, 3: True}
                dpg.add_text(text)
                self._bind_font(
                    dpg.last_item(),
                    size=size_map.get(level, 2),
                    bold=bold_map.get(level, False),
                    font_name="Huninn",
                )
                dpg.add_spacer(height=3)
                i += 1
                continue

            # --- Empty line ---
            if not line.strip():
                dpg.add_spacer(height=5)
                i += 1
                continue

            # --- Three "---" for a horizontal separator ---
            if re.match(r"^---+\s*$", line):
                dpg.add_separator()
                i += 1
                continue

            # --- Regular paragraph text ---
            # Check for inline images within the paragraph
            parts = re.split(r"(!\[.*?\]\((.+?)\))", line)
            max_line_length = 150  # Adjust as needed for readability/performance
            if len(parts) > 1:
                # Has inline image(s) — render text segments and images
                for part in parts:
                    inline_img = re.match(r"^!\[.*?\]\((.+?)\)$", part)
                    if inline_img:
                        self._render_image(inline_img.group(1))
                    elif part.strip():
                        # Split text into multiple lines if it's too long, to avoid DPG rendering issues with very long text
                        if len(part) > max_line_length:
                            # Use text splitting that tries to split on spaces for better readability, textwrap.
                            wrapped, wrapped_len = wrap_text_no_break_words(part, max_line_length)
                            # Wrapped text has inserted newlines, so we can render it as-is without further splitting
                            dpg.add_text(wrapped)
                        else:
                            dpg.add_text(part)
                        self._bind_font(dpg.last_item(), size=2, bold=False, font_name="Huninn")
            else:
                if len(line) > max_line_length:
                    wrapped, wrapped_len = wrap_text_no_break_words(line, max_line_length)
                    dpg.add_text(wrapped)
                else:
                    dpg.add_text(line)
                self._bind_font(dpg.last_item(), size=2, bold=False, font_name="Huninn")

            i += 1

    def _render_image(self, rel_path: str):
        """Load and display an image from a path relative to the file's directory."""
        # Resolve relative to the file's directory
        base_dir = os.path.dirname(self.filepath)
        abs_path = os.path.normpath(os.path.join(base_dir, rel_path))

        if not os.path.exists(abs_path):
            dpg.add_text(f"[Image not found: {rel_path}]")
            self._bind_font(dpg.last_item(), size=1, bold=False, font_name="Huninn")
            return

        ext = os.path.splitext(abs_path)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg"):
            dpg.add_text(f"[Unsupported image format: {ext}]")
            self._bind_font(dpg.last_item(), size=1, bold=False, font_name="Huninn")
            return

        try:
            width, height, channels, data = dpg.load_image(abs_path)
            texture_tag = f"_ref_img_{len(self._texture_tags)}_{os.path.basename(abs_path)}"
            Logger.info(f"[References] Loaded image '{abs_path}' with size {width}x{height} and {channels} channels as texture '{texture_tag}'")

            # Handle RGBA vs RGB
            # Normalize byte values (0-255) to float values (0.0-1.0)
            # as required by dpg.add_static_texture
            if channels == 4:
                with dpg.texture_registry(show=False):
                    dpg.add_static_texture(
                        tag=texture_tag,
                        width=width,
                        height=height,
                        default_value=data,
                    )
            else:
                # Convert RGB to RGBA (add alpha channel at 1.0)
                normalized = []
                for i in range(0, len(data), 3):
                    normalized.extend([data[i], data[i + 1], data[i + 2], 1.0])
                with dpg.texture_registry(show=False):
                    dpg.add_static_texture(
                        tag=texture_tag,
                        width=width,
                        height=height,
                        default_value=normalized,
                    )

            self._texture_tags.append(texture_tag)

            # Display the image, scaled to fit within the content area
            max_display_width = int(600 * Config.UI_SCALE)
            max_display_height = int(400 * Config.UI_SCALE)
            dpg.add_image(texture_tag, width=min(width, max_display_width), height=min(height, max_display_height))
            dpg.add_spacer(height=5)
        except Exception as e:
            Logger.error(f"Reference reader: failed to load image {abs_path}: {e}")
            dpg.add_text(f"[Failed to load image: {rel_path}]")
            self._bind_font(dpg.last_item(), size=1, bold=False, font_name="Huninn")

    # ── Close / cleanup ────────────────────────────────────────────────

    def close(self):
        """Close the modal and clean up all loaded textures."""
        # Remove all loaded textures to free GPU memory
        for tag in self._texture_tags:
            if dpg.does_item_exist(tag):
                try:
                    dpg.delete_item(tag)
                except Exception:
                    pass
        self._texture_tags.clear()

        if self.win:
            self.win.delete()
            self.win = None

    # ── Helpers ────────────────────────────────────────────────────────

    def _bind_font(self, item, size=2, bold=False, font_name=None):
        """Bind a font to the last created item, if fonts are available."""
        if self.fonts:
            self.fonts.dpg_preload_then_bind(item, size=size, bold=bold, font_name=font_name)
