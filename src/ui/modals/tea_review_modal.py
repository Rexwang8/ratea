import uuid
import dearpygui.dearpygui as dpg
import dearpypixl as dp
from config import Config
from models.review import Review
from services.date_helper import datetime_to_dearpygui_dt, dearpygui_dt_to_datetime
from services.logger import Logger
from services.score_converter import ScoreConverter
import datetime as dt
from ui.widgets.dropdown_autocomplete import add_autocomplete_input

# Modal for viewing tea details
def show_tea_review_modal(tea, review, data_manager, fonts=None):
    modal = TeaReviewModal(tea=tea, review=review, data_manager=data_manager, fonts=fonts)
    modal.show()



class TeaReviewModal:
    def __init__(self, tea, review, data_manager, fonts=None):
        self.tea = tea
        self.review = review
        self.data_manager = data_manager
        self.fonts = fonts
        self.win = None


    def show(self):
        width = 550 * Config.UI_SCALE
        height = 700 * Config.UI_SCALE
        self.win = dp.Window(label=self.tea.name, modal=True, no_close=False, width=width, height=height)
        with self.win:
            dpg.add_text("Tea Details")
            # The action is to either add a new review or edit an existing review.
            action = "Edit Review" if self.review else "Add Review"
            dpg.bind_item_font(dpg.last_item(), self.fonts.getFontName(size=3, bold=True) if self.fonts else 0)
            dpg.add_separator()
            dpg.add_text(f"Tea: {self.tea.name}")
            dpg.bind_item_font(dpg.last_item(), self.fonts.getFontName(size=3, bold=False) if self.fonts else 0)
            dpg.add_text(f"Vendor: {self.tea.vendor}")
            dpg.bind_item_font(dpg.last_item(), self.fonts.getFontName(size=2, bold=False) if self.fonts else 0)
            dpg.add_text(f"Type: {self.tea.tea_type}")
            dpg.bind_item_font(dpg.last_item(), self.fonts.getFontName(size=2, bold=False) if self.fonts else 0)

            # If review exists, show details, otherwise show form to add new review
            newDataFields = {}
            is_editing = self.review is not None
            review = self.review

            dpg.add_text("Edit Review" if is_editing else "Add Review")

            with dpg.child_window(width=-1, height=450 * Config.UI_SCALE, border=True):
            
                validRatings = ScoreConverter.LETTER_GRADE_MAP
                itemsSequence = list(validRatings.keys())

                rating_default = itemsSequence[8]  # Default to the 8th item if not editing (B)
                if is_editing:
                    # Find the letter grade corresponding to the numeric rating
                    for letter, score in validRatings.items():
                        if score == review.rating:
                            rating_default = letter
                            break
                newDataFields['rating'] = dp.Combo(label="Rating", items=itemsSequence, default_value=rating_default)

                date_default = datetime_to_dearpygui_dt(review.date) if is_editing else datetime_to_dearpygui_dt(dt.datetime.now())
                dateField = dp.DatePicker(label="Review Date", default_value=date_default)
                dpg.bind_item_font(dateField, self.fonts.getFontName(size=2, bold=False) if self.fonts else 0)
                newDataFields['date'] = dateField

                newDataFields['amount'] = dp.InputFloat(label="Amount Drunk (g)", width=150 * Config.UI_SCALE, default_value=review.amount_drunk if is_editing else 6, format="%.2f")
                newDataFields['vessel'] = dp.InputFloat(label="Vessel Size (ml)", width=150 * Config.UI_SCALE, default_value=review.vesselSize if is_editing else 150, format="%.1f")

                methodOptions = ["Gongfu", "Western", "Cold Brew", "Japanese Western", "Thermos", "Boiled", "Mugged", "Usucha", "Koicha", "Other"]
                newDataFields['method'] = add_autocomplete_input(
                    tag="method",
                    label="Brew Method",
                    items=methodOptions,
                    default_value=review.method if is_editing else methodOptions[0],
                    width=250 * Config.UI_SCALE
                )
                
                #newDataFields['method'] = dp.Combo(label="Brew Method", items=methodOptions, default_value=review.method if is_editing else methodOptions[0])

                newDataFields['steeps'] = dp.InputInt(label="Steep Count", width=150 * Config.UI_SCALE, default_value=int(review.steep_count) if is_editing else 6)
                newDataFields['notes'] = dp.InputText(label="Notes", multiline=True, width=-1, height=150 * Config.UI_SCALE, default_value=review.notes if is_editing else "")

                # padding
                dpg.add_spacer(height=10 * Config.UI_SCALE)
                
            # Confirm action button
            dpg.add_separator()
            with dpg.group(horizontal=True):
                bwidth = 120 * Config.UI_SCALE
                bheight = 40 * Config.UI_SCALE
                dpg.add_button(label=action, callback=self.execute_action, user_data=(newDataFields, action), width=bwidth, height=bheight)
                dpg.add_button(label="Cancel", callback=self.close, width=bwidth, height=bheight)


    def execute_action(self, sender=None, app_data=None, user_data=None):
        action = user_data[1]  # "Add Review" or "Edit Review"
        newDataFields = user_data[0]  # The data fields for the review
        # Here you would implement the logic to either add a new review or edit the existing review based on the action.
        # You would gather the data from newDataFields, validate it, and then update your data model accordingly.
        Logger.info(f"Executing action: {action}")
        if action == "Add Review":
            self.add_new_review(newDataFields)
        elif action == "Edit Review":
            self.edit_review(newDataFields)
        else:
            Logger.error(f"Unknown action: {action}")
        # After processing, close the modal
        self.close()

    def add_new_review(self, newDataFields):
        Logger.info("Adding new review with data:")
        # Convert dearpygui to datetime
        rating = ScoreConverter.letter_to_score(dpg.get_value(newDataFields['rating']))
        new_review = Review(
            id=str(uuid.uuid4()),
            tea_id=self.tea.id,
            rating=rating,
            notes=dpg.get_value(newDataFields['notes']),
            date=dearpygui_dt_to_datetime(dpg.get_value(newDataFields['date'])),
            amount_drunk=round(dpg.get_value(newDataFields['amount']), 2),
            vesselSize=round(dpg.get_value(newDataFields['vessel']), 1),
            method=dpg.get_value(newDataFields['method']),
            steeps=dpg.get_value(newDataFields['steeps'])
        )
        Logger.info(f"New review created: {new_review}")

        self.tea.add_review(new_review)
        self.data_manager.export_to_yaml(self.data_manager.data_save_path)  # Save changes immediately
        self.data_manager.export_to_yaml(self.data_manager.data_save_path)  # Save changes immediately
        #self.data_manager.refresh_all(save_after_refresh=True) Don't refresh, allow manual refresh to avoid unnecessary reloads and potential modal conflicts

    def edit_review(self, newDataFields):
        Logger.info(f"Editing review {self.review.id}")
        datetimeobj = dearpygui_dt_to_datetime(dpg.get_value(newDataFields['date']))
        print(f"Converted date: {datetimeobj} from dearpygui value: {dpg.get_value(newDataFields['date'])}")

        self.review.rating = ScoreConverter.letter_to_score(dpg.get_value(newDataFields['rating']))
        self.review.notes = dpg.get_value(newDataFields['notes'])
        self.review.date = datetimeobj
        self.review.amount_drunk = round(dpg.get_value(newDataFields['amount']), 2)
        self.review.vesselSize = round(dpg.get_value(newDataFields['vessel']), 1)
        self.review.method = dpg.get_value(newDataFields['method'])
        self.review.steep_count = dpg.get_value(newDataFields['steeps'])

        Logger.info(f"Review updated: {self.review}")
        self.data_manager.export_to_yaml(self.data_manager.data_save_path)  # Save changes immediately
        #self.data_manager.refresh_all(save_after_refresh=True) Don't refresh, allow manual refresh to avoid unnecessary reloads and potential modal conflicts

    def close(self):
        Logger.info(f"Closing tea review modal for: {self.tea.name}")
        Logger.info(f"info for self.win: {self.win}")
        if self.win:
            self.win.delete()
            self.win = None