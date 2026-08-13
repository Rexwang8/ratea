import uuid
import dearpygui.dearpygui as dpg
import dearpypixl as dp
from config import Config
from models.review import Review
from services.date_helper import datetime_to_dearpygui_dt, dearpygui_dt_to_datetime
from services.logger import Logger
from services.score_converter import ScoreConverter
from services.stats_service import ReportService
import datetime as dt
from ui.widgets.dropdown_autocomplete import add_autocomplete_input
from ui.notifications import NotificationManager, notify

# Modal for viewing tea details
def _show_tea_review_modal(tea, review, data_manager, fonts=None):
    modal = TeaReviewModal(tea=tea, review=review, data_manager=data_manager, fonts=fonts)
    modal.show()



class TeaReviewModal:
    def __init__(self, tea, review, data_manager, fonts=None):
        self.tea = tea
        self.review = review
        self.data_manager = data_manager
        self.fonts = fonts
        self.win = None

    def _bind_font(self, item, size=2, bold=False):
        if self.fonts:
            dpg.bind_item_font(item, self.fonts.get_font_name(size=size, bold=bold))


    def show(self):
        width = 550 * Config.UI_SCALE
        height = 700 * Config.UI_SCALE
        self.win = dp.Window(label=self.tea.name, modal=True, no_close=False, width=width, height=height)
        with self.win:
            dpg.add_text("Tea Details")
            # The action is to either add a new review or edit an existing review.
            action = "Edit Review" if self.review else "Add Review"
            self._bind_font(dpg.last_item(), size=3, bold=True)
            dpg.add_separator()
            dpg.add_text(f"Tea: {self.tea.name}")
            self._bind_font(dpg.last_item(), size=3, bold=False)
            dpg.add_text(f"Vendor: {self.tea.vendor}")
            self._bind_font(dpg.last_item(), size=2, bold=False)
            dpg.add_text(f"Type: {self.tea.tea_type}")
            self._bind_font(dpg.last_item(), size=2, bold=False)

            # If review exists, show details, otherwise show form to add new review
            new_data_fields = {}
            is_editing = self.review is not None
            review = self.review

            dpg.add_text("Edit Review" if is_editing else "Add Review")

            with dpg.child_window(width=-1, height=450 * Config.UI_SCALE, border=True):
                valid_ratings = ScoreConverter.LETTER_GRADE_MAP
                items_sequence = list(valid_ratings.keys())

                rating_default = items_sequence[8]  # Default to the 8th item if not editing (B-)
                # If config has a default rating, use that instead
                if hasattr(Config, "DEFAULT_RATING") and Config.DEFAULT_RATING in valid_ratings:
                    rating_default = Config.DEFAULT_RATING

                if is_editing:
                    # Find the letter grade corresponding to the numeric rating
                    for letter, score in valid_ratings.items():
                        if score == review.rating:
                            rating_default = letter
                            break


                new_data_fields['rating'] = dp.Combo(label="Rating", items=items_sequence, default_value=rating_default)

                date_default = datetime_to_dearpygui_dt(review.date) if is_editing else datetime_to_dearpygui_dt(dt.datetime.now())
                dateField = dp.DatePicker(label="Review Date", default_value=date_default)
                self._bind_font(dateField, size=2, bold=False)
                new_data_fields['date'] = dateField

                default_amount = review.amount_drunk if is_editing else Config.DEFAULT_AMOUNT_DRUNK if hasattr(Config, "DEFAULT_AMOUNT_DRUNK") else 5.0
                new_data_fields['amount'] = dp.InputFloat(label="Amount Drunk (g)", width=150 * Config.UI_SCALE, default_value=default_amount, format="%.2f")
                
                defaultVessel = review.vessel_size if is_editing else Config.DEFAULT_VESSEL_SIZE if hasattr(Config, "DEFAULT_VESSEL_SIZE") else 100.0
                new_data_fields['vessel'] = dp.InputFloat(label="Vessel Size (ml)", width=150 * Config.UI_SCALE, default_value=defaultVessel, format="%.1f")

                method_options = ["Gongfu", "Western", "Cold Brew", "Japanese Western", "Thermos", "Boiled", "Mugged", "Usucha", "Koicha", "Other"]
                new_data_fields['method'] = add_autocomplete_input(
                    tag="method",
                    label="Brew Method",
                    items=method_options,
                    default_value=review.method if is_editing else method_options[0],
                    width=250 * Config.UI_SCALE
                )
                
                default_steeps = review.steep_count if is_editing else Config.DEFAULT_STEEPS if hasattr(Config, "DEFAULT_STEEPS") else 5
                new_data_fields['steeps'] = dp.InputInt(label="Steep Count", width=150 * Config.UI_SCALE, default_value=default_steeps)
                new_data_fields['notes'] = dp.InputText(label="Notes", multiline=True, width=-1, height=150 * Config.UI_SCALE, default_value=review.notes if is_editing else "")

                # padding
                dpg.add_spacer(height=10 * Config.UI_SCALE)

            # Confirm action button
            dpg.add_separator()
            with dpg.group(horizontal=True):
                bwidth = 120 * Config.UI_SCALE
                bheight = 40 * Config.UI_SCALE
                dpg.add_button(label=action, callback=self._execute_action, user_data=(new_data_fields, action), width=bwidth, height=bheight)
                dpg.add_button(label="Cancel", callback=self.close, width=bwidth, height=bheight)


    def _execute_action(self, sender=None, app_data=None, user_data=None):
        action = user_data[1]  # "Add Review" or "Edit Review"
        new_data_fields = user_data[0]  # The data fields for the review
        # Here you would implement the logic to either add a new review or edit the existing review based on the action.
        # You would gather the data from new_data_fields, validate it, and then update your data model accordingly.
        Logger.debug(f"Executing action: {action}")
        if action == "Add Review":
            self._add_new_review(new_data_fields)
        elif action == "Edit Review":
            self._edit_review(new_data_fields)
        else:
            Logger.error(f"Unknown action: {action}")
            notify("Error", f"Unknown action: {action}", level="error", duration=3.0)
        # After processing, close the modal
        self.close()

    def _add_new_review(self, new_data_fields):
        Logger.debug("Adding new review with data:")
        # Convert dearpygui to datetime
        rating = ScoreConverter.letter_to_score(dpg.get_value(new_data_fields['rating']))
        new_review = Review(
            id=str(uuid.uuid4()),
            tea_id=self.tea.id,
            rating=rating,
            notes=dpg.get_value(new_data_fields['notes']),
            date=dearpygui_dt_to_datetime(dpg.get_value(new_data_fields['date'])),
            amount_drunk=round(dpg.get_value(new_data_fields['amount']), 2),
            vessel_size=round(dpg.get_value(new_data_fields['vessel']), 1),
            method=dpg.get_value(new_data_fields['method']),
            steeps=dpg.get_value(new_data_fields['steeps'])
        )
        Logger.info(f"New review created: {new_review}")

        self.tea.add_review(new_review)
        self.data_manager.export_to_yaml(self.data_manager.data_save_path)  # Save changes immediately

        if Config.GENERATE_REPORT_ON_REVIEW:
            review_id = new_review.id
            ReportService.generate_review_report(self.data_manager, review_id)

            notify("Review Added With Report", f"Review for tea '{self.tea.name}' has been added and report generated.", level="success", duration=3.0)
            Logger.debug(f"Notification sent for new review with report: '{self.tea.name}', review ID: {review_id}.")

            Logger.info(f"Report generated for review ID: {review_id} based on config GENERATE_REPORT_ON_REVIEW={Config.GENERATE_REPORT_ON_REVIEW}")
        else:
            notify("Review Added", f"Review for tea '{self.tea.name}' has been added successfully.", level="success", duration=3.0)
            Logger.debug(f"Notification sent for new review: '{self.tea.name}'.")

    def _edit_review(self, new_data_fields):
        Logger.info(f"Editing review {self.review.id}")
        datetimeobj = dearpygui_dt_to_datetime(dpg.get_value(new_data_fields['date']))

        self.review.rating = ScoreConverter.letter_to_score(dpg.get_value(new_data_fields['rating']))
        self.review.notes = dpg.get_value(new_data_fields['notes'])
        self.review.date = datetimeobj
        self.review.amount_drunk = round(dpg.get_value(new_data_fields['amount']), 2)
        self.review.vessel_size = round(dpg.get_value(new_data_fields['vessel']), 1)
        self.review.method = dpg.get_value(new_data_fields['method'])
        self.review.steep_count = dpg.get_value(new_data_fields['steeps'])

        notify("Review Updated", f"Review for tea '{self.tea.name}' has been updated successfully.", level="success", duration=3.0)
        Logger.debug(f"Notification sent for review update: '{self.tea.name}'.")

        Logger.info(f"Review updated: {self.review}")
        self.data_manager.export_to_yaml(self.data_manager.data_save_path)  # Save changes immediately

    def close(self):
        Logger.debug(f"Closing tea review modal for: {self.tea.name}")
        Logger.debug(f"info for self.win: {self.win}")
        if self.win:
            self.win.delete()
            self.win = None