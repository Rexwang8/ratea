# src/ui/app.py
import os
import dearpygui.dearpygui as dpg
from config import Config
from models.stash import TeaStash
from models.tea import Tea
from models.review import Review
from services.data_manager import DataManager, ensure_folders_exist
import datetime as dt
from services.text_helper import wrap_text_no_break_words
from ui.fonts import FontManager
from services.logger import Logger
import dearpypixl as dp
from services.stats_service import ReportService, StatsService
from services.score_converter import ScoreConverter
from ui.modals.tea_add_edit_modal import _show_tea_modal
from ui.modals.tea_review_modal import _show_tea_review_modal
from ui.modals.tea_view_modal import _show_tea_view_modal
from ui.modals.config_modal import show_config_modal
from ui.modals.reference_reader_modal import show_reference_reader
import dearpygui.demo as demo
from connectors.teadb.connect_teadb import dummy_funct, upload_ratea_review_to_teadb

class TeaApp:
    selectable_tags = []
    selected_tea_id = None
    selected_tea_idx = None

    selectable_tags_reviews = []
    selected_review_id = None
    selected_review_idx = None


    table_parent = None
    review_table_parent = None
    search_column = "Name"
    search_column_reviews = "Tea Name"
    selected_text_display = None
    selected_text_display_reviews = None
    current_query = ""
    current_query_reviews = ""
    hide_finished = Config.SEARCH_DEFAULTS_HIDE_FINISHED
    hide_unreviewed = Config.SEARCH_DEFAULTS_HIDE_UNREVIEWED
    hide_reviewed = Config.SEARCH_DEFAULTS_HIDE_REVIEWED
    hide_finished_reviews = Config.SEARCH_DEFAULTS_HIDE_FINISHED_REVIEWS

    def __init__(self):
        self.primary_window_tag = "Primary Window"
        self.is_running = False

        # Track sort state across refreshes
        self.sort_column = None
        self.sort_ascending = True

        # Double check that necessary folders exist
        ensure_folders_exist()

        self.data_manager = DataManager()
        self.data_manager.load_from_yaml(f"{Config.DATA_DIR}/{Config.DATA_SAVE_FILE}")  # Load initial data

        dataSavePath = f"{Config.DATA_DIR}/{Config.DATA_SAVE_FILE}"
        self.data_manager.export_to_yaml(dataSavePath)

        self.fonts = FontManager()

        self.data_manager.refresh_all()

        self.tea_lookup = {
            row["UUID"]: (row["IDX"], row["Name"])
            for _, row in self.data_manager.df.iterrows()
        }

        self.review_lookup = {
            row["Review UUID"]: (row["IDX"], row["Tea Name"], row["Session Number"])
            for _, row in self.data_manager._get_stash_reviews_dataframe().iterrows()
        }

    def _setup_fonts(self):
        """Private method to load fonts."""
        self.fonts.bind_load_fonts()
        dpg.set_global_font_scale(2)

    def setup_dpg(self):
        """Initialize the DPG context and viewport."""
        dpg.create_context()
        
        # Load fonts, themes, or layouts here
        self._setup_fonts()
        self._setup_theme()

        # Create the Viewport (The OS Window)
        dpg.create_viewport(
            title=Config.APP_NAME, 
            width=Config.DEFAULT_WIDTH, 
            height=Config.DEFAULT_HEIGHT
        )
        dpg.setup_dearpygui()

        # Set the icon (Optional)
        # dpg.set_viewport_small_icon("assets/icon.ico")

    def _setup_theme(self):
        """Global theme settings."""
        pass

    def _on_row_selected(self, sender, app_data, user_data):
        """Called when a user clicks any row."""

        # 1. Manually deselect all other selectables (Radio-button behavior)
        #self.selectable_tags = [tag for tag in self.selectable_tags if dpg.does_item_exist(tag)]
        #for tag in self.selectable_tags:
        #    if tag != sender:
        #        dpg.set_value(tag, False)
        #    else:
        #        dpg.set_value(tag, True) # Ensure the clicked one stays on

        if hasattr(self, "last_selected_tag") and self.last_selected_tag != sender:
            if dpg.does_item_exist(self.last_selected_tag):
                dpg.set_value(self.last_selected_tag, False)

        dpg.set_value(sender, True)
        self.last_selected_tag = sender

        # If the same row is clicked again, deselect it
        if self.selected_tea_id == user_data:
            dpg.set_value(sender, False)
            self.selected_tea_id = None
            self.selected_tea_idx = None
            dpg.set_value(self.selected_text_display, "No tea selected")
            Logger.info("UI: Active Tea selection cleared")
            return

        # 2. Update the App state
        self.selected_tea_id = user_data
        #df = self.data_manager.df
        #tea_row = df[df["UUID"] == self.selected_tea_id]
        #self.selected_tea_idx = tea_row.iloc[0]["IDX"] if not tea_row.empty else None

        tea_data = self.tea_lookup.get(self.selected_tea_id)

        if tea_data:
            self.selected_tea_idx, tea_name = tea_data
        else:
            self.selected_tea_idx = None
            tea_name = None

        # 3. Update any UI elements that depend on the selection
        display_text = "No tea selected"
        if self.selected_tea_idx is not None:
            # Find the tea name from the DataFrame
            #if not tea_row.empty:
            #    tea_name = tea_row.iloc[0]["Name"]
            if tea_name:
                display_text = f"Selected Tea: {tea_name} (IDX: {self.selected_tea_idx} UUID: {self.selected_tea_id})"
            else:
                display_text = f"Selected Tea ID: {self.selected_tea_idx}"

        dpg.set_value(self.selected_text_display, display_text)

        Logger.info(f"UI: Active Tea selection set to {user_data}")

    def _on_row_selected_reviews(self, sender, app_data, user_data):
        """Called when a user clicks any row."""
        # 1. Manually deselect all other selectables (Radio-button behavior)
        #self.selectable_tags_reviews = [tag for tag in self.selectable_tags_reviews if dpg.does_item_exist(tag)]
        #for tag in self.selectable_tags_reviews:
        #    if tag != sender:
        #        dpg.set_value(tag, False)
        #    else:
        #        dpg.set_value(tag, True) # Ensure the clicked one stays on

        if hasattr(self, "last_selected_review_tag") and self.last_selected_review_tag != sender:
            if dpg.does_item_exist(self.last_selected_review_tag):
                dpg.set_value(self.last_selected_review_tag, False)
        
        dpg.set_value(sender, True)
        self.last_selected_review_tag = sender

        # If the same row is clicked again, deselect it
        if self.selected_review_id == user_data:
            dpg.set_value(sender, False)
            self.selected_review_id = None
            self.selected_review_idx = None
            dpg.set_value(self.selected_text_display_reviews, "No review selected")
            Logger.info("UI: Active Review selection cleared")
            return

        # 2. Update the App state
        self.selected_review_id = user_data
        #tea, review = self.data_manager.stash.get_review_by_id(self.selected_review_id)
        #df_reviews = self.data_manager._get_stash_reviews_dataframe()
        #review_row = df_reviews[df_reviews["Review UUID"] == user_data]
        #self.selected_review_idx = review_row.iloc[0]["IDX"] if not review_row.empty else None
        review_data = self.review_lookup.get(self.selected_review_id)

        if review_data:
            self.selected_review_idx = review_data[0]
        else:
            self.selected_review_idx = None

        # 3. Update any UI elements that depend on the selection
        display_text = "No review selected"
        if review_data:
            tea_name, session_num = review_data[1], review_data[2]
            display_text = f"Selected Review: {tea_name} (Session: {session_num}, IDX: {self.selected_review_idx} UUID: {self.selected_review_id})"
        else:
            display_text = f"Selected Review UUID: {self.selected_review_idx} (Match not found!)"
        dpg.set_value(self.selected_text_display_reviews, display_text)

        Logger.info(f"UI: Active Review selection set to {user_data}")

    def _on_edit_click_reviews(self, sender, app_data, user_data):
        tea, review = self.data_manager.stash.get_review_by_id(self.selected_review_id)
        """Called when the 'Edit' button is pressed."""
        if self.selected_review_idx is None:
            Logger.warning("No review selected! Click a row in the table first.")
            return

        Logger.info(f"Opening editor for review: {self.selected_review_idx}")
        # Here you would call your modal window function:
        # Show the review modal
        _show_tea_review_modal(tea, review, self.data_manager, self.fonts)

    def _on_edit_click_tea(self):
        """Called when the 'Edit' button is pressed."""
        if self.selected_tea_idx is None:
            Logger.warning("No tea selected! Click a row in the table first.")
            return
        
        Logger.info(f"Opening editor for tea: {self.selected_tea_idx}")
        this_tea = self.data_manager.stash.get_tea_by_id(self.selected_tea_id)
        _show_tea_modal(this_tea, self.data_manager, self.fonts)

    def _on_add_click_tea(self):
        """Called when the 'Add Tea' button is pressed."""
        Logger.info("Opening Add Tea modal")
        # Here you would call your modal window function:
        # We want to get the last entry for tea in order to pre-populate the add form with the last used values (except name)
        last_tea = self.data_manager.stash.get_last_tea_entry()
        _show_tea_modal(None, self.data_manager, self.fonts, pre_populate=last_tea)

    def _on_duplicate_add_click_tea(self):
        """Called when the 'Duplicate Add Tea' button is pressed."""
        Logger.info("Opening Duplicate Add Tea modal")
        # We want to get the currently selected tea and pre-populate the add form with its values (except name)
        if self.selected_tea_idx is None:
            Logger.warning("No tea selected! Click a row in the table first.")
            return
        
        current_tea = self.data_manager.stash.get_tea_by_id(self.selected_tea_id)
        _show_tea_modal(None, self.data_manager, self.fonts, pre_populate=current_tea)

    def _on_save_click(self):
        """Called when the 'Save' menu item is clicked."""
        save_path = f"{Config.DATA_DIR}/{Config.DATA_SAVE_FILE}"
        self.data_manager.export_to_yaml(save_path)
        Logger.info(f"Data saved to {save_path}")

    def _on_save_backup_click(self):
        """Called when the 'Save Backup' menu item is clicked."""
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder_path = f"{Config.BACKUP_DIR}/data_backups_{timestamp}"
        os.makedirs(backup_folder_path, exist_ok=True)

        # Tea backup
        backup_path = f"{backup_folder_path}/data_backup_{timestamp}.yaml"
        self.data_manager.export_to_yaml(backup_path)
        Logger.info(f"Data backup saved to {backup_path}")

    
        


    

    def _refresh_data(self):
        """Public method to refresh data and re-render tables."""
        Logger.info("Refreshing data and re-rendering tables...")
        self.data_manager.refresh_all()
        self.data_manager._filter_data()
        self.data_manager._filter_reviews_data()
        self._on_search_change(None, None)
        self._on_search_change_reviews()
        # Re-apply the saved sort state after refresh (must be after _on_search_change
        # since _filter_data resets filtered_df to an unsorted copy)
        if self.sort_column is not None:
            self.data_manager._sort_data(self.sort_column, self.sort_ascending)
        self.render_table_rows(parent=self.table_parent)
        self._render_reviews_table_rows(parent=self.review_table_parent)

        self.tea_lookup = {
            row["UUID"]: (row["IDX"], row["Name"])
            for _, row in self.data_manager.df.iterrows()
        }

        self.review_lookup = {
            row["Review UUID"]: (row["IDX"], row["Tea Name"], row["Session Number"])
            for _, row in self.data_manager._get_stash_reviews_dataframe().iterrows()
        }

    def render_table_rows(self, parent=None):
        """Renders the table rows based on the current DataFrame."""
        # 1. Clear existing rows (we target the children of the table)
        # slot 1 in a table contains the rows
        if parent is None:
            parent = self.table_parent
        for child in dpg.get_item_children(parent, slot=1):
            dpg.delete_item(child)

        Logger.info(f"Rendering table rows for main table...")

        # 2. Get the current DataFrame from manager
        
        df_to_show = self.data_manager.filtered_df
        Logger.info(f"DataFrame retrieved: {df_to_show.shape[0]} rows")

        self.tea_lookup = {
            row["UUID"]: (row["IDX"], row["Name"])
            for _, row in self.data_manager.df.iterrows()
        }

        # 3. Build the rows
        for i in range(len(df_to_show)):
            row_data = df_to_show.iloc[i]
            row_id = row_data.get("UUID", i)
            with dpg.table_row(parent=parent):
                for j,col in enumerate(df_to_show.columns):
                    # 0th column is uuid, skip displaying it
                    if col == "UUID":
                        continue

                    # Access cell value from DataFrame
                    # In your App UI loop
                    val = row_data[col]
                    color = None
                    if col == "Amount":
                        # Amount f"{remaining_amt:.1f}g / {purchase_amt:.1f}g",
                        # greater than 70% green, not out, light blue, out, light yellow
                        remaining_amt, purchase_amt = map(float, val.replace("g","").split("/"))
                        perc = remaining_amt / purchase_amt if purchase_amt > 0 else 0

                        if perc > 0.6:
                            color = Config.Colors.CELL_DARK_GREEN
                        elif perc > 0:
                            color = Config.Colors.CELL_LIGHT_BLUE
                        elif perc == 0:
                            color = Config.Colors.CELL_LIGHT_YELLOW
                            

                    val = row_data[col]
                    display_text = str(format_cell(val, col))

                    sel_height = 25 * Config.UI_SCALE
                    if j == 1:
                        # The first column is the "anchor" for selection
                        tag = dpg.add_selectable(
                            label=display_text + "\n",  # Add newline to give some padding
                            span_columns=True, 
                            user_data=row_id, 
                            callback=self._on_row_selected,
                            height=sel_height
                        )
                        self.selectable_tags.append(tag)
                    else:
                        # Regular text for subsequent columns
                        dpg.add_text(display_text)
                        # If we have notes, we want to be able to hover to see them
                        if "Note" in col and isinstance(val, str) and val.strip():
                            dpg.add_tooltip(dpg.last_item())
                            val, _ = wrap_text_no_break_words(val, width=160)
                            dpg.add_text(val, parent=dpg.last_item())
                    
                        if color is not None and j > 1:
                            dpg.highlight_table_cell(parent, color=color, row=i, column=j-1)
                        elif color is not None and j == 1:
                            # seems to error if we try to highlight the first column cell, so if it's the first column, we want to highlight the entire row instead
                            dpg.highlight_table_row(parent, color=color, row=i)

    
    def _render_reviews_table_rows(self, parent=None):
        """Renders the reviews table rows based on the current DataFrame."""
        # 1. Clear existing rows (we target the children of the table)
        # slot 1 in a table contains the rows
        if parent is None:
            parent = self.review_table_parent
        for child in dpg.get_item_children(parent, slot=1):
            dpg.delete_item(child)

        Logger.info(f"Rendering table rows for reviews table...")

        # 2. Get the current DataFrame from manager
        
        df_to_show = self.data_manager.filtered_reviews_df
        Logger.info(f"DataFrame retrieved: {df_to_show.shape[0]} rows")

        self.review_lookup = {
            row["Review UUID"]: (row["IDX"], row["Tea Name"], row["Session Number"])
            for _, row in self.data_manager._get_stash_reviews_dataframe().iterrows()
        }

        # 3. Build the rows
        for i in range(len(df_to_show)):
            row_data = df_to_show.iloc[i]
            row_id = row_data.get("Review UUID", i)
            with dpg.table_row(parent=parent):
                for j,col in enumerate(df_to_show.columns):
                    # 0th 1th column is uuid, skip displaying it
                    if col == "Review UUID":
                        continue

                    # Access cell value from DataFrame
                    # In your App UI loop
                    val = row_data[col]
                    display_text = str(format_cell(val, col))
                    sel_height = 25 * Config.UI_SCALE
                    if j == 0:
                        # The first column is the "anchor" for selection
                        tag = dpg.add_selectable(
                            label=display_text + "\n",  # Add newline to give some padding
                            span_columns=True, 
                            user_data=row_id, 
                            callback=self._on_row_selected_reviews,
                            height=sel_height
                        )
                        self.selectable_tags_reviews.append(tag)
                    else:
                        # Regular text for subsequent columns
                        dpg.add_text(display_text)
                        # If we have notes, we want to be able to hover to see them
                        if "Note" in col and isinstance(val, str) and val.strip():
                            dpg.add_tooltip(dpg.last_item())
                            val, _ = wrap_text_no_break_words(val, width=160)
                            dpg.add_text(val, parent=dpg.last_item())
    
    # placeholder deletes
    def _on_delete_click(self, sender, app_data, user_data):
        """Called when the 'Delete' button is pressed."""
        if user_data == "tea":
            if self.selected_tea_idx is None:
                Logger.warning("No tea selected! Click a row in the table first.")
                return

            Logger.info(f"Deleting tea: {self.selected_tea_idx} (UUID: {self.selected_tea_id})")
            self.data_manager.delete_tea_by_id(self.selected_tea_id)
            # Then refresh the table
            self.render_table_rows()
        elif user_data == "review":
            if self.selected_review_idx is None:
                Logger.warning("No review selected! Click a row in the table first.")
                return

            Logger.info(f"Deleting review: {self.selected_review_idx} (UUID: {self.selected_review_id})")
            self.data_manager.delete_review_by_id(self.selected_review_id)
            # Then refresh the table
            self._render_reviews_table_rows()


    def _review_selected_tea(self, sender, app_data, user_data):
        """Opens the review modal for the selected tea."""
        if self.selected_tea_idx is None:
            Logger.warning("No tea selected to review!")
            return
        # Match uuid to tea
        uuid = self.selected_tea_id
        tea = self.data_manager.stash.get_tea_by_uuid(uuid)
        Logger.info(f"Reviewing tea: {self.selected_tea_idx} - {tea.name if tea else 'Unknown Tea'}")

        # Create a modal window to show tea review details
        if tea is None:
            Logger.error("Selected tea not found in stash!")
            return

        # Show the review modal
        _show_tea_review_modal(tea, None, self.data_manager, self.fonts)

    def _view_selected_tea(self, sender, app_data, user_data):
        """View details of the selected tea."""
        if self.selected_tea_idx is None:
            Logger.warning("No tea selected to view!")
            return
        # Match uuid to tea
        uuid = self.selected_tea_id
        tea = self.data_manager.stash.get_tea_by_uuid(uuid)
        Logger.info(f"Viewing tea: {self.selected_tea_idx} - {tea.name if tea else 'Unknown Tea'}")

        # Create a modal window to show tea details
        if tea is None:
            Logger.error("Selected tea not found in stash!")
            return
        
        _show_tea_view_modal(tea, self.fonts, self.data_manager)

    def _on_clear_selection(self):
        """Clears the current selection."""
        if self.selected_tea_id is not None:
            # Deselect the currently selected row
            for tag in self.selectable_tags:
                if dpg.does_item_exist(tag):
                    dpg.set_value(tag, False)

        self.selected_tea_id = None
        self.selected_tea_idx = None
        dpg.set_value(self.selected_text_display, "No tea selected")
        Logger.info("UI: Active Tea selection cleared")

    def _on_clear_selection_reviews(self):
        """Clears the current review selection."""
        if self.selected_review_id is not None:
            # Deselect the currently selected row
            for tag in self.selectable_tags_reviews:
                if dpg.does_item_exist(tag):
                    dpg.set_value(tag, False)

        self.selected_review_id = None
        self.selected_review_idx = None
        dpg.set_value(self.selected_text_display_reviews, "No review selected")
        Logger.info("UI: Active Review selection cleared")

    def _on_hide_finished_change(self, sender, app_data):
        self.hide_finished = app_data
        self.data_manager.set_filter_flag("hide_finished", self.hide_finished)
        self._refresh_data()
    
    def _on_hide_unreviewed_change(self, sender, app_data):
        self.hide_unreviewed = app_data
        self.data_manager.set_filter_flag("hide_unreviewed", self.hide_unreviewed)
        self._refresh_data()

    def _on_hide_reviewed_change(self, sender, app_data):
        self.hide_reviewed = app_data
        self.data_manager.set_filter_flag("hide_reviewed", self.hide_reviewed)
        self._refresh_data()

    def _on_hide_finished_reviews_change(self, sender, app_data):
        self.hide_finished_reviews = app_data
        self.data_manager.set_filter_flag("hide_finished_reviews", self.hide_finished_reviews)
        self._refresh_data()


    def _on_search_change(self, sender=None, filter_string=None):
        """Triggered every time the user types in the search bar."""
        # 1. Update the filtered subset in the manager
        if filter_string is None:
            filter_string = self.current_query  # Use existing query if not provided (e.g., when changing filter column)
        self.current_query = filter_string
        self.data_manager._filter_data(filter_string, self.search_column)

        # 2. Refresh the UI
        self.render_table_rows()

    def _on_search_change_reviews(self, sender=None, filter_string=None):
        """Triggered every time the user types in the reviews search bar."""
        # 1. Update the filtered subset in the manager
        if filter_string is None:
            filter_string = self.current_query_reviews  # Use existing query if not provided (e.g., when changing filter column)
        self.current_query_reviews = filter_string
        self.data_manager._filter_reviews_data(filter_string, self.search_column_reviews)

        # 2. Refresh the UI
        self._render_reviews_table_rows()

    def _on_sort_click(self, sender, sort_spec):
        if not sort_spec: return

        column_id, direction = sort_spec[0]
        column_name = dpg.get_item_label(column_id)

        # Save sort state for re-application after refresh
        self.sort_column = column_name
        self.sort_ascending = direction < 0

        # Sort the already filtered data
        self.data_manager._sort_data(column_name, self.sort_ascending)

        # Refresh the UI
        self.render_table_rows()

    def _on_sort_click_reviews(self, sender, sort_spec):
        if not sort_spec: return

        column_id, direction = sort_spec[0]
        column_name = dpg.get_item_label(column_id)

        # Sort the already filtered data
        self.data_manager._sort_reviews_data(column_name, direction < 0)

        # Refresh the UI
        self._render_reviews_table_rows()


    def _on_filter_col_change(self, sender, app_data):
        """Triggered when the Radio Button selection changes."""
        # app_data is the string label of the selected radio button (e.g., "Vendor")
        self.search_column = app_data
        # Re-apply the filter with the same text but the new column target
        self._on_search_change(None, self.current_query)

    def _on_filter_col_change_reviews(self, sender, app_data):
        """Triggered when the Radio Button selection changes."""
        # app_data is the string label of the selected radio button (e.g., "Vendor")
        self.search_column_reviews = app_data
        # Re-apply the filter with the same text but the new column target
        self._on_search_change_reviews(None, self.current_query_reviews)

    

    def _copy_selected_tea_uuid(self, sender, app_data, user_data):
        """Copy the selected tea's UUID to clipboard."""
        if self.selected_tea_id is None:
            Logger.warning("No tea selected to copy UUID!")
            return
        
        dpg.set_clipboard_text(self.selected_tea_id)
        Logger.info(f"Copied UUID to clipboard: {self.selected_tea_id}")

    def _generate_chart_for_selected_review(self, sender, app_data, user_data):
        # Main body of function is in ReportService
        
        # Get uuid of tea and of review
        if self.selected_review_id is None:
            Logger.warning("No review selected to generate chart!")
            return
        report = ReportService.generate_review_report(self.data_manager, self.selected_review_id)

    def _generate_tierlist_for_selected_vendor(self, sender, app_data, user_data):
        # Main body of function is in ReportService
        
        # Get vendor name from selected tea
        if self.selected_tea_id is None:
            Logger.warning("No tea selected to generate tierlist!")
            return
        
        tea = self.data_manager.stash.get_tea_by_uuid(self.selected_tea_id)
        if tea is None:
            Logger.error("Selected tea not found in stash for tierlist generation!")
            return
        
        vendor_name = tea.vendor
        ReportService.generate_tierlist_vendor(self.data_manager, this_vendor=vendor_name, user_data=user_data)

    def _connect_teadb_review(self, sender, app_data, user_data):
        # Send teadb full tea and review data for import/export
        tea, review = self.data_manager.stash.get_review_by_id(self.selected_review_id)
        if tea is None or review is None:
            Logger.error("Selected review or its tea not found in stash for Teadb connector!")
            return
        upload_ratea_review_to_teadb(tea, review, create_purchase_first=False, dry_run=False, add_custom_tea_if_not_found=True)

    def build_ui(self):
        """Constructs the actual widgets."""
        df = self.data_manager._get_stash_dataframe()  # Example of getting data for UI display
        df_reviews = self.data_manager._get_stash_reviews_dataframe()
        with dpg.window(tag=self.primary_window_tag) as main_window:
            
            # 1. The Menu Bar
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Save", callback=self._on_save_click)
                    dpg.add_menu_item(label="Save Backup", callback=self._on_save_backup_click)
                    dpg.add_menu_item(label="Settings", callback=lambda: show_config_modal(fonts=self.fonts))
                    dpg.add_menu_item(label="Exit", callback=dpg.destroy_context)
                
                with dpg.menu(label="View"):
                    dpg.add_menu_item(label="Tea Stash")
                    dpg.add_menu_item(label="Reviews")
                # Seperate each report into a different folder with multiple report buttons with different args prefilled for different report types, e.g. tierlist for selected vendor, chart of scores over time for selected tea, etc.
                with dpg.menu(label="Reports"):
                    # Folder
                    with dpg.menu(label="Selected Tea:"):
                        dpg.add_menu_item(label="Chart: Sel. Tea Vendor Tierlist", callback=self._generate_tierlist_for_selected_vendor, user_data={"adjust_size": "auto"})
                    with dpg.menu(label="Selected Review:"):
                        dpg.add_menu_item(label="Report: Generate Review Chart", callback=self._generate_chart_for_selected_review)
                    with dpg.menu(label="By Type:"):
                        dpg.add_menu_item(label="Chart: $/g over time by type", callback=lambda: ReportService.generate_cost_per_gram_over_time_reviews_report(self.data_manager))
                        dpg.add_menu_item(label="Chart: gram over time by type", callback=lambda: ReportService.generate_consumption_by_type_report(self.data_manager))
                        dpg.add_menu_item(label="Chart: Abs. grams cu. by type", callback=lambda: ReportService.generate_cu_stashed_by_type_report(self.data_manager))
                with dpg.menu(label="Connectors"):
                    # Teadb folder, for tea and review export and import
                    dpg.add_menu_item(label="Export Teadb Review", callback=self._connect_teadb_review)

            # 2. The Main Content Area (Tabs are great for this app)
            with dpg.tab_bar(tag="main_tab_bar"):
                with dpg.tab(label="My Stash"):
                    dpg.add_text("Tea Stash Viewer")

                    # Foldable section for filter flags
                    with dpg.collapsing_header(label="Actions", default_open=False):
                        # Actions that perform an operation across the entire stash.
                        # Zero negative tea amounts and cost
                        dpg.add_button(label="Zero Negative Amounts", callback=self.data_manager._zero_negative_amounts)
                        dpg.add_button(label="Zero Negative Costs", callback=self.data_manager._zero_negative_costs)
                        
                        # Round to nearest 2 decimal places for amounts and costs
                        dpg.add_button(label="Round Amounts/Costs", callback=self.data_manager._round_amounts_and_costs)

                    with dpg.collapsing_header(label="Filters", default_open=True):
                        dpg.add_checkbox(label="Hide finished teas", callback=self._on_hide_finished_change, default_value=self.hide_finished)
                        dpg.add_checkbox(label="Hide Unreviewed teas", callback=self._on_hide_unreviewed_change, default_value=self.hide_unreviewed)
                        dpg.add_checkbox(label="Hide Reviewed teas", callback=self._on_hide_reviewed_change, default_value=self.hide_reviewed)

                    with dpg.collapsing_header(label="Sort Options", default_open=False):
                        dpg.add_radio_button(items=["Name", "Vendor", "Type", "Amount", "Avg Score", "Reviews", "Cost"], label="Sort by:", horizontal=True, callback=self._on_filter_col_change)
                        dpg.add_checkbox(label="Descending Order")

                    # Search bar
                    dpg.add_input_text(
                        label="Search Stash", 
                        callback=self._on_search_change,
                        hint="Type name",
                        width=350 * Config.UI_SCALE,
                        height=50 * Config.UI_SCALE
                    )
                        
                    

                    # Stash operations (edit)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Add Tea", callback=self._on_add_click_tea)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Duplicate Add Selected", callback=self._on_duplicate_add_click_tea)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Edit Selected", callback=self._on_edit_click_tea)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Delete Selected", callback=self._on_delete_click, user_data="tea")
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Clear Selected", callback=self._on_clear_selection)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="View Selected", callback=self._view_selected_tea)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Copy UUID", callback=self._copy_selected_tea_uuid)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Review Selected", callback=self._review_selected_tea)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Refresh Data", callback=self._refresh_data)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)

                    # Stats display for ui, could be fun
                    with dpg.group(horizontal=True):
                        stats = self.data_manager.get_stash_stats_summary()
                        dpg.add_text(f"Total Teas: {stats['total_teas']} (Reviewed/Fin: {stats['total_reviewed']}, Unreviewed: {stats['total_unreviewed']})")
                        dpg.add_text(f"Finished Teas: {stats['total_finished']}")
                        dpg.add_text(f"Total Weight: {stats['total_remaining']:.1f}g/{stats['total_weight']:.1f}g")
                        dpg.add_text(f"Average Rating: {stats['avg_rating']}")


                    # Selected ID and name display
                    self.selected_text_display = dpg.add_text("No tea selected")
                    
                    bind_item_font(self.fonts, self.selected_text_display, size=2, bold=True)


                    # Create Table
                    filter_table_id = dpg.generate_uuid()
                    with dpg.child_window(width=-1, height=-1):
                        tea_table = dp.Table(header_row=True, resizable=True, policy=dpg.mvTable_SizingFixedFit,
                                       row_background=True, borders_innerV=True, borders_outerV=True, 
                                       borders_innerH=True, borders_outerH=True, sortable=True, delay_search=True, callback=self._on_sort_click, tag=filter_table_id)
                        self.table_parent = tea_table

                        with tea_table:
                            # Create Headers based on DataFrame columns
                            for col in df.columns:
                                # pass uuid column
                                if col == "UUID":
                                    continue
                                dpg.add_table_column(label=col)



                            # Fill Rows
                            self.data_manager._filter_data()
                            self.selectable_tags.clear() # Reset list before rebuilding table
                            self.render_table_rows(parent=tea_table)

                with dpg.tab(label="Reviews"):
                    dpg.add_text("Review list goes here")

                    # Foldable section for filter flags
                    with dpg.collapsing_header(label="Filters", default_open=False):
                        dpg.add_checkbox(label="Hide finished teas", callback=self._on_hide_finished_reviews_change)

                    with dpg.collapsing_header(label="Sort Options", default_open=False):
                        dpg.add_radio_button(items=["Tea Name", "Tea Vendor", "Tea Type", "Avg Rating", "Date", "Tea UUID"], label="Sort by:", horizontal=True, callback=self._on_filter_col_change_reviews)
                        dpg.add_checkbox(label="Descending Order")

                    # Search bar
                    dpg.add_input_text(
                        label="Search Stash", 
                        callback=self._on_search_change_reviews,
                        hint="Type name",
                        width=300,
                    )

                    # Stash operations (edit)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Edit Selected", callback=self._on_edit_click_reviews)
                        
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Delete Selected", callback=self._on_delete_click, user_data="review")
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Clear Selected", callback=self._on_clear_selection_reviews)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="View Selected", callback=self._view_selected_tea)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Chart Selected", callback=self._generate_chart_for_selected_review)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)
                        dpg.add_button(label="Refresh Data", callback=self._refresh_data)
                        bind_item_font(self.fonts, dpg.last_item(), size=2, bold=True)

                    # Selected ID and name display
                    self.selected_text_display_reviews = dp.Text("No review selected")
                    bind_item_font(self.fonts, self.selected_text_display_reviews, size=2, bold=True)

                    # Create Table
                    filter_table_id_reviews = dpg.generate_uuid()
                    with dpg.child_window(width=-1, height=-1):
                        tea_reviews_table = dp.Table(header_row=True, resizable=True, policy=dpg.mvTable_SizingFixedFit,
                                       row_background=True, borders_innerV=True, borders_outerV=True, 
                                       borders_innerH=True, borders_outerH=True, sortable=True, delay_search=True, callback=self._on_sort_click_reviews, tag=filter_table_id_reviews)
                        self.review_table_parent = tea_reviews_table

                        with tea_reviews_table:
                            # Create Headers based on DataFrame columns
                            for col in df_reviews.columns:
                                # pass uuid column
                                if col == "Tea UUID":
                                    dpg.add_table_column(label=col, width=100 * Config.UI_SCALE)
                                elif col == "Review UUID":
                                    continue
                                else:
                                    dpg.add_table_column(label=col)

                            # Fill Rows
                            self.data_manager._filter_reviews_data()
                            self.selectable_tags.clear() # Reset list before rebuilding table
                            self._render_reviews_table_rows(parent=tea_reviews_table)

                with dpg.tab(label="Dashboard"):
                    from ui.dashboard_tab import draw_dashboard_tab
                    draw_dashboard_tab(self.data_manager)

                with dpg.tab(label="Analytics"):
                    from ui.analytics_tab import draw_analytics_tab, draw_water_analytics
                    draw_analytics_tab(self.data_manager)

                with dpg.tab(label="References"):
                    with dpg.tab_bar():
                    
                        # ------------------------------------------------------------------
                        # Getting Started, specifically beginner oriented articles.
                        # ------------------------------------------------------------------
                        with dpg.tab(label="Getting Started"):
                            with dpg.tab_bar():
                                with dpg.tab(label="General"):
                                    dpg.add_text("Beginner Guides")
                                    bind_item_font(self.fonts,dpg.last_item(),size=2,bold=True)
                
                                    _make_ref_button(self,
                                        "[Teadb] Puerh for Beginners",
                                        "references\\teadb\\puerh_for_beginners\\puerh_for_beginners.md")
                
                            
                                with dpg.tab(label="Buying"):
                                    dpg.add_text("Beginner Buying Guides")
                                    bind_item_font(self.fonts,dpg.last_item(),size=2,bold=True)


                                    _make_ref_button(self,
                                        "[FILLER] First Sheng Purchase Guide",
                                        r"references\getting_started\puerh\first_sheng_purchase.md")

                                    _make_ref_button(self,
                                        "[FILLER] Basic Gongfu Setup",
                                        r"references\getting_started\general\basic_gongfu_setup.md")

                        # ------------------------------------------------------------------
                        # Drinking & Brewing, specific guides for drinking, brewing, storage, etc.
                        # ------------------------------------------------------------------
                        with dpg.tab(label="Drinking & Brewing"):
                            with dpg.tab_bar():
                                with dpg.tab(label="General"):
                                
                                    _make_ref_button(self,
                                        "[External] Experience Huigan",
                                        "references\\external\\orientalleaf\\experience_huigan\\experience_huigan.md")
                            
                                with dpg.tab(label="Puerh"):
                                
                                    _make_ref_button(self,
                                        "[FILLER] Sheng Brewing Guide",
                                        r"references\drinking\puerh\sheng_brewing_guide.md")

                                    _make_ref_button(self,
                                        "[FILLER] Shou Brewing Guide",
                                        r"references\drinking\puerh\shou_brewing_guide.md")

                                with dpg.tab(label="Hongcha"):
                                    _make_ref_button(self,
                                        "[FILLER] Gongfu Hongcha Guide",
                                        r"references\drinking\hongcha\gongfu_hongcha_guide.md")

                                    _make_ref_button(self,
                                        "[FILLER] Western Hongcha Guide",
                                        r"references\drinking\hongcha\western_hongcha_guide.md")

                        # ------------------------------------------------------------------
                        # Tea Knowledge, more generalized and references
                        # ------------------------------------------------------------------
                        with dpg.tab(label="Tea Knowledge"):
                            with dpg.tab_bar():
                                with dpg.tab(label="Puerh"):
                                
                                    _make_ref_button(self,
                                        "[FILLER] Puerh Types Overview",
                                        r"references\knowledge\puerh\types_overview.md")

                                    _make_ref_button(self,
                                        "[FILLER] Puerh Region Guide",
                                        r"references\knowledge\puerh\region_guide.md")

                                with dpg.tab(label="Hongcha"):
                                
                                    _make_ref_button(self,
                                        "[FILLER] Hongcha Types Overview",
                                        r"references\knowledge\hongcha\types_overview.md")

                        # ------------------------------------------------------------------
                        # Tea Blogs, curated list of blogs and articles about tea
                        # ------------------------------------------------------------------
                        with dpg.tab(label="Tea Blogs"):
                            with dpg.tab_bar():
                                with dpg.tab(label="Teadb"):
                                    dpg.add_text("teadb.org . Run by James and Denny, experienced and grounded tea drinkers with a focus on puerh.")
                                    _make_ref_button(self,
                                        "[Teadb] Puerh for Beginners",
                                        "references\\teadb\\puerh_for_beginners\\puerh_for_beginners.md")

                                    _make_ref_button(self,
                                        "[Teadb] 7542!!!! The Most Famous Digits in the Pu'erh World!",
                                        "references\\teadb\\7542_the_most_famous_digits_in_the_puerh_world\\7542_the_most_famous_digits_in_the_puerh_world.md")
                            
                                with dpg.tab(label="Marshaln"):
                                    dpg.add_text("marshaln.com . Run by Marshaln, a very experienced tea drinker.")
                                    _make_ref_button(self,
                                        "[Marshaln] Wuyishan",
                                        "references\\external\\marshaln\\wuyishan\\wuyishan.md")
                                    _make_ref_button(self,
                                        "[Marshaln] Objectively good tea",
                                        "references\\external\\marshaln\\objectively_good_tea\\objectively_good_tea.md")
                                    
                        # ------------------------------------------------------------------
                        # Research Library, papers and other academic materials
                        # ------------------------------------------------------------------
                        with dpg.tab(label="Research Library"):
                            with dpg.tab_bar():
                                with dpg.tab(label="Papers"):
                                    _make_ref_button(self,
                                        "[FILLER] Why Some Sheng Ages Better",
                                        r"references\research\blogs\sheng_aging.md")

                                with dpg.tab(label="Academic"):
                                    _make_ref_button(self,
                                        "[FILLER] Polyphenols and Aging",
                                        r"references\research\academic\polyphenols.md")
                                    

        dpg.set_primary_window(self.primary_window_tag, True)

    def run(self):
        """Start the render loop."""
        self.setup_dpg()
        self.build_ui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()


def format_cell(value, col=None):
    """Format the cell value for display."""
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d")  # Just the date
    
    if col == "Avg Rating":
        return f"{value} ({ScoreConverter.score_to_letter(value)})"
    
    max_len = 35

    # if it is a string, wrap it if it is longer than 40 chars
    if isinstance(value, str) and len(value) > max_len:
        return value[:max_len-3] + "..."
    return str(value)


def _make_ref_button(app: TeaApp, label: str, filepath: str):
    """Create an 'Open' button for a reference document in the References tab."""
    dpg.add_button(
        label=label,
        width=-1,
        height=30 * Config.UI_SCALE,
        callback=lambda: show_reference_reader(
            filepath=filepath,
            fonts=app.fonts,
            data_manager=app.data_manager,
        ),
    )
    if app.fonts:
        app.fonts.dpg_preload_then_bind(dpg.last_item(), size=2, bold=False)
    dpg.add_spacer(height=3)



def bind_item_font(fonts: FontManager, item, size=2, bold=False):
    """Bind a font to a DearPyGui item, ensuring the font is loaded first."""
    if fonts:
        fonts.dpg_preload_then_bind(item, size=size, bold=bold)