import dearpygui.dearpygui as dpg
import dearpypixl as dp
from config import Config
from models.adjustment import Adjustment
from models.tea import Tea
from services.data_manager import DataManager
from services.logger import Logger
from services.score_converter import ScoreConverter
from ui.notifications import NotificationManager, notify

# Modal for viewing tea details
def _show_tea_view_modal(tea, fonts=None, data_manager=None):
    modal = Modal(tea=tea, fonts=fonts, data_manager=data_manager)
    modal.show()


class Modal:
    def __init__(self, tea: Tea, fonts=None, data_manager=None):
        self.tea: Tea = tea
        self.fonts = fonts
        self.win = None
        self.data_manager: DataManager = data_manager

    def _bind_font(self, item, size=2, bold=False):
        if self.fonts:
            dpg.bind_item_font(item, self.fonts.get_font_name(size=size, bold=bold))


    def show(self):
        width = 550 * Config.UI_SCALE
        height = 700 * Config.UI_SCALE
        self.win = dp.Window(label=self.tea.name, modal=True, no_close=False, width=width, height=height)
        with self.win:
            dpg.add_text("Tea Details")
            self._bind_font(dpg.last_item(), size=3, bold=True)
            dpg.add_separator()
            dpg.add_text(f"Name: {self.tea.year} {self.tea.name}")
            self._bind_font(dpg.last_item(), size=3, bold=False)
            dpg.add_text(f"Type: {self.tea.tea_type}")
            self._bind_font(dpg.last_item(), size=2, bold=False)
            dpg.add_text(f"Vendor: {self.tea.vendor}")
            self._bind_font(dpg.last_item(), size=2, bold=False)
            dpg.add_text(f"Cost (USD): ${self.tea.cost:.2f} for {self.tea.quantity:.1f}g (Catalog: {self.tea.catalog_price_per_gram:.2f}/g)")
            self._bind_font(dpg.last_item(), size=2, bold=False)
            dpg.add_text(f"Purchase Date: {self.tea.purchase_date.strftime('%Y-%m-%d') if self.tea.purchase_date else 'N/A'}")
            self._bind_font(dpg.last_item(), size=2, bold=False)
            dpg.add_separator()
            dpg.add_text(f"Purchase Note: {self.tea.purchase_note}")
            dpg.add_separator()

            # Reviews (summary)
            r = 1
            max_width_child = width - 65 * Config.UI_SCALE
            with dpg.child_window(width=-1, height=300 * Config.UI_SCALE, border=True, max_width=max_width_child):
                dpg.add_text("Reviews:")
                self._bind_font(dpg.last_item(), size=2, bold=True)
                if not self.tea.reviews:
                    dpg.add_text(" No reviews available.")
                else:
                    for review in self.tea.reviews:
                        # Abridged review with session number, date, rating and amount
                        dpg.add_text(f" - Review {r}: {review.date.strftime('%Y-%m-%d')}, Rating: {review.rating}, Amount Drunk: {review.amount_drunk:.1f}g")
                        self._bind_font(dpg.last_item(), size=2, bold=False)
                        dpg.add_separator()
                        r += 1
            dpg.add_text(f"Total Reviews: {r - 1}")
            self._bind_font(dpg.last_item(), size=2, bold=False)
            if self.tea.average_rating is not None:
                dpg.add_text(f"Average Rating: {self.tea.average_rating:.2f} ({ScoreConverter.score_to_letter(self.tea.average_rating)} | {ScoreConverter.get_grade_meaning_numeric(self.tea.average_rating)})")
            else:
                dpg.add_text(f"Average Rating: N/A")
            self._bind_font(dpg.last_item(), size=2, bold=False)
            dpg.add_separator()

            
            # Adjustments
            dpg.add_text(f"Total Adjustments (g): {self.tea.sum_adjustments_grams:.1f}g")
            self._bind_font(dpg.last_item(), size=2, bold=False)
            for adj in self.tea.adjustments:
                dpg.add_text(f"{adj.adjustment_type}: {adj.amount:.1f}g, Cost: ${adj.cost:.2f}")
                self._bind_font(dpg.last_item(), size=2, bold=False)

            # Change adjustments. Nest in a collapse header, allow editing with its own confirm button that updates the tea and refreshes the modal.
            with dpg.collapsing_header(label="Adjustments", default_open=True):
                types_of_adjustments = Config.TYPES_OF_ADJUSTMENTS_TO_TEA
                data_adjustments = {}
                # Mark remaining as Standard deduction or gift deduction buttons
                dpg.add_text(f"Remaining Amount (g): {self.tea.remaining:.2f}g")
                self._bind_font(dpg.last_item(), size=2, bold=False)
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Mark remaining as Standard", callback=self._mark_all_as_adjustment, user_data="Standard Deduction", width=200 * Config.UI_SCALE, height=40 * Config.UI_SCALE)
                    self._bind_font(dpg.last_item(), size=2, bold=False)
                    dpg.add_button(label="Mark remaining as Gift", callback=self._mark_all_as_adjustment, user_data="Gift Deduction", width=200 * Config.UI_SCALE, height=40 * Config.UI_SCALE)
                    self._bind_font(dpg.last_item(), size=2, bold=False)
                    dpg.add_button(label="Unmark all adjustments", callback=self._unmark_all_adjustments, user_data=None, width=200 * Config.UI_SCALE, height=40 * Config.UI_SCALE)
                    self._bind_font(dpg.last_item(), size=2, bold=False)
                for adj in types_of_adjustments:
                    # tuples of (adjustment_type, amount, cost) in tea.adjustments
                    amt_adj = 0.0
                    cost_adj = 0.0
                    for a in self.tea.adjustments:
                        if a.adjustment_type == adj:
                            amt_adj = a.amount
                            cost_adj = a.cost
                    dpg.add_text(f"{adj}: {amt_adj:.1f}g, Cost: ${cost_adj:.2f}")
                    self._bind_font(dpg.last_item(), size=2, bold=False)
                    data_adjustments[adj] = dp.InputFloat(label=f"{adj} Adjustment (g)", default_value=amt_adj, width=200 * Config.UI_SCALE, format="%.2f", height=40 * Config.UI_SCALE)
                    data_adjustments[f"{adj}_cost"] = dp.InputFloat(label=f"{adj} Adjustment Cost (USD)", default_value=cost_adj, width=200 * Config.UI_SCALE, format="%.2f", height=40 * Config.UI_SCALE)

                # Confirm button for all adjustments that updates the tea and refreshes the modal
                dpg.add_button(label="Update Adjustments", callback=self._update_adjustments, user_data=data_adjustments, width=200 * Config.UI_SCALE, height=40 * Config.UI_SCALE)
                self._bind_font(dpg.last_item(), size=2, bold=False)
            dpg.add_separator()
            
            # Total remaining
            dpg.add_text(f"Remaining Amount (g): {self.tea.remaining:.2f}g")
            self._bind_font(dpg.last_item(), size=2, bold=False)

            dpg.add_button(label="Close", callback=self.close)
            self._bind_font(dpg.last_item(), size=3, bold=False)

    def close(self):
        Logger.debug(("Closing tea view modal for:", self.tea.name))
        Logger.debug(f"info for self.win: {self.win}")
        if self.win:
            self.win.delete()
            self.win = None

    def _mark_all_as_adjustment(self, sender, app_data, user_data):
        # Wrap around _update_adjustments and set remaining amount as the amount for the given adjustment type, and cost as 0
        remaining_amount = self.tea.remaining
        new_user_data = dict()
        if user_data == "Standard Deduction":
            new_user_data["Standard"] = remaining_amount
            new_user_data["Standard_cost"] = 0.0
        elif user_data == "Gift Deduction":
            new_user_data["Gift"] = remaining_amount
            new_user_data["Gift_cost"] = 0.0
        else:
            Logger.error(f"Unknown adjustment type: {user_data}")
            notify("Error", f"Unknown adjustment type: {user_data}", level="error", duration=3.0)
            return
        self._update_adjustments(None, None, new_user_data)

    def _unmark_all_adjustments(self, sender, app_data, user_data):
        # Wrap around _update_adjustments and set all adjustments to 0
        new_user_data = dict()
        for adj in Config.TYPES_OF_ADJUSTMENTS_TO_TEA:
            new_user_data[adj] = 0.0
            new_user_data[f"{adj}_cost"] = 0.0
        self._update_adjustments(None, None, new_user_data)

    def _update_adjustments(self, sender, app_data, user_data):
        # If user_data is not none, we check if they are integers first, if not, we try to get the values from the data_adjustments inputs. This allows us to use the same function for both the "Mark remaining as adjustment" buttons and the "Update Adjustments" button.
        for adj in Config.TYPES_OF_ADJUSTMENTS_TO_TEA:
            amount = 0
            cost = 0

            # Because dearpygui uses ints as identifiers for items, we have to check if the user_data is an int and corresponds to the input field for the adjustment amount or cost. If it does, we get the value from the input field instead of using the user_data directly. This allows us to use the same function for both the "Mark remaining as adjustment" buttons and the "Update Adjustments" button.
            if user_data and adj in user_data and f"{adj}_cost" in user_data:
                    amount = user_data[adj].get_value() if hasattr(user_data[adj], "get_value") else user_data[adj] if isinstance(user_data[adj], (int, float)) else 0.0
            if user_data and f"{adj}_cost" in user_data:
                    cost = user_data[f"{adj}_cost"].get_value() if hasattr(user_data[f"{adj}_cost"], "get_value") else user_data[f"{adj}_cost"] if isinstance(user_data[f"{adj}_cost"], (int, float)) else 0.0

            Logger.info(f"Adjustment '{adj}': amount={amount}, cost={cost}")
            # Assert that amount is not a mvInputFloat
            assert not isinstance(amount, dp.mvInputFloat), f"Adjustment '{adj}' has an invalid amount type."
            assert not isinstance(cost, dp.mvInputFloat), f"Adjustment '{adj}' has an invalid cost type."

            # Check if adjustment already exists for this tea
            existing_adj = next((a for a in self.tea.adjustments if a.adjustment_type == adj), None)
            if existing_adj:
                existing_adj.amount = amount
                # if amount is greater than the amount in the tea, set it to the tea quantity to avoid negative remaining
                if existing_adj.amount > self.tea.quantity:
                    existing_adj.amount = self.tea.quantity
                existing_adj.cost = cost
                Logger.info("Updated existing adjustment: " + str(existing_adj.to_dict()))
            else:
                # If it doesn't exist, create a new adjustment and add it to the tea
                amt = amount if amount is not None else 0.0
                cst = cost if cost is not None else 0.0
                if amt > self.tea.quantity:
                    amt = self.tea.quantity
                new_adjustment = Adjustment(adjustment_type=adj, amount=amt, cost=cst, tea_id=self.tea.id)
                self.tea.adjustments.append(new_adjustment)
                Logger.info("Added new adjustment: " + str(new_adjustment.to_dict()))

        # After updating adjustments, refresh the modal to show updated values
        self.close()
        self.show()

        # Notify
        notify("Adjustments updated successfully.")

        # Save
        self.data_manager.export_to_yaml(self.data_manager.data_save_path)