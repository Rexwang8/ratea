"""Generic toast/notification system for ratEA.

Pops up a small window in a corner of the viewport, stays for a few seconds,
then auto-dismisses. Clicking anywhere on the notification dismisses it
immediately.

Usage:
    from ui.notifications import notify

    notify("Data saved successfully.")
    notify("Tea added!", title="Stash Update", level="success")
    notify("Export failed", level="error", corner="top_right", duration=2.5)
"""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import dearpypixl as dp

from config import Config
from services.logger import Logger


def notify(message: str, title: str = "Notification", level: str = "info",
           duration: float = 3.0, corner: str = "bottom_right") -> None:
    """Show a temporary notification in a corner of the viewport.

    Args:
        message: The notification body text.
        title: Short title shown above the message.
        level: One of "info", "success", "warning", "error".
        duration: How long to display, in seconds.
        corner: One of "top_left", "top_right", "bottom_left", "bottom_right".
    """
    NotificationManager.get().show(message, title=title, level=level,
                                   duration=duration, corner=corner)


class NotificationManager:
    """Singleton manager for stacking, positioning, and expiring notifications.

    Only one manager exists per process (accessed via ``get()``). It must be
    initialized once with the app's fonts (``init(fonts=...)``).

    Expiry uses one-shot ``dpg.set_frame_callback(frame, cb)`` per notification
    — the correct way to use that API (it fires once at the requested frame).
    A continuous self-re-arming frame callback is NOT reliable in this stack.
    """

    # Max notifications shown simultaneously in a single corner.
    MAX_ON_SCREEN = 3
    # Pixels between stacked notifications.
    STACK_SPACING = 10 * Config.UI_SCALE
    # Corner inset from the viewport edges.
    VIEWPORT_INSET = 20 * Config.UI_SCALE
    # Notification window size.
    WIDTH = int(340 * Config.UI_SCALE)
    HEIGHT = int(96 * Config.UI_SCALE)

    # Accent colors per level (RGBA). Reuses existing Config.Colors values.
    LEVEL_COLORS = {
        "info": Config.Colors.CELL_LIGHT_BLUE,
        "success": Config.Colors.CELL_LIGHT_GREEN,
        "warning": Config.Colors.CELL_LIGHT_YELLOW,
        "error": Config.Colors.TEXT_RED,
    }

    VALID_CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")

    # ------------------------------------------------------------------
    # Singleton access
    # ------------------------------------------------------------------

    _instance = None

    @classmethod
    def get(cls) -> "NotificationManager":
        """Return the process-wide NotificationManager instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.fonts = None
        self._frames_per_second = 60.0  # DPG default render rate
        self._corner = "bottom_right"
        # List of active notification windows (oldest first).
        self._active = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def init(self, fonts=None) -> None:
        """Initialize the manager with the app's font registry."""
        self.fonts = fonts
        Logger.info("NotificationManager initialized.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self, message: str, title: str = "Notification", level: str = "info",
             duration: float = 5.0, corner: str = "bottom_right") -> None:
        """Display a notification window.

        If more than MAX_ON_SCREEN notifications are active, the oldest is
        dismissed first.
        """
        if corner not in self.VALID_CORNERS:
            Logger.warning(f"Invalid notification corner '{corner}'; using 'bottom_right'.")
            corner = "bottom_right"
        if level not in self.LEVEL_COLORS:
            level = "info"

        self._corner = corner

        # Enforce the stack limit: dismiss the oldest first.
        while len(self._active) >= self.MAX_ON_SCREEN:
            self._delete_window(self._active[0])

        window = self._build_window(message, title, level)
        self._active.append(window)

        # Schedule a one-shot expiry for this notification.
        expiry_frame = dpg.get_frame_count() + max(1, int(duration * self._frames_per_second))
        dpg.set_frame_callback(
            expiry_frame,
            lambda: self._on_notification_expired(window),
        )

        self._reposition_all()
        Logger.info(f"Notification shown: '{title}' ({level}), expires frame {expiry_frame}.")

    # ------------------------------------------------------------------
    # Internal callbacks
    # ------------------------------------------------------------------

    def _on_notification_expired(self, window) -> None:
        """The scheduled expiry fired — dismiss the notification if still alive."""
        if window is not None and dpg.does_item_exist(window):
            self._delete_window(window)

    def _on_notification_clicked(self, window) -> None:
        """The user clicked a notification: dismiss it immediately."""
        if window is not None and dpg.does_item_exist(window):
            self._delete_window(window)

    def _delete_window(self, window) -> None:
        """Delete a notification window and remove it from the active list."""
        if window is not None and dpg.does_item_exist(window):
            window.delete()
        while window in self._active:
            self._active.remove(window)
        self._reposition_all()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_window(self, message: str, title: str, level: str):
        """Create the DPG window for a notification and return its tag."""
        accent = self.LEVEL_COLORS[level]
        accent = list(accent) if isinstance(accent, tuple) else list(accent)

        win = dp.Window(
            label="",
            width=self.WIDTH,
            height=self.HEIGHT,
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            no_close=True,
            no_scrollbar=True,
            no_saved_settings=True,
            no_focus_on_appearing=True,
        )
        with win:
            # Left accent bar, absolutely-positioned in the top-left corner.
            dpg.add_color_edit(
                default_value=accent,
                no_inputs=True,
                width=8,
                height=self.HEIGHT - 8,
                pos=(4, 4),
            )
            # Full-size button covering the rest of the window — clicking
            # anywhere on the notification dismisses it. Explicit pos avoids
            # layout ambiguity so the button truly fills the body.
            dpg.add_button(
                label=f"{title}\n{message}",
                width=self.WIDTH - 16,
                height=self.HEIGHT - 8,
                pos=(14, 4),
                callback=lambda: self._on_notification_clicked(win),
            )
            self._bind_font(dpg.last_item(), size=2, bold=True)

        return win

    def _reposition_all(self) -> None:
        """Stack the active notifications in the configured corner."""
        active = [w for w in self._active if w is not None and dpg.does_item_exist(w)]
        vp_w = dpg.get_viewport_width()
        vp_h = dpg.get_viewport_height()

        for i, window in enumerate(active):
            x_local = vp_w - self.WIDTH - self.VIEWPORT_INSET
            y_local = vp_h - (self.HEIGHT + self.VIEWPORT_INSET) * (i + 1) - self.STACK_SPACING * i

            # Clamp so we never go off-screen.
            if x_local < self.VIEWPORT_INSET:
                x_local = self.VIEWPORT_INSET
            if y_local < self.VIEWPORT_INSET:
                y_local = self.VIEWPORT_INSET

            dpg.set_item_pos(window, [x_local, y_local])

    def _bind_font(self, item, size=2, bold=False):
        """Bind a font to an item, if fonts are available."""
        if self.fonts:
            dpg.bind_item_font(item, self.fonts.get_font_name(size=size, bold=bold))