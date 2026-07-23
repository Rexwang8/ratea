from math import erf
import os
import uuid
import yaml
import pandas as pd
from config import Config
from models.tea import Tea
from services.logger import Logger
from models.stash import TeaStash
from services.score_converter import ScoreConverter
from services.stats_service import StatsService


class DataManager:
    def __init__(self):
        self.teas = []
        self.stash: TeaStash = TeaStash()
        self.df = pd.DataFrame() # Initialize empty DataFrame
        self.filtered_df = pd.DataFrame() # What the UI sees
        self.reviews_df = pd.DataFrame() # Reviews DataFrame
        self.filtered_reviews_df = pd.DataFrame() # Filtered Reviews DataFrame
        self.water_stats_cache = None
        self.type_vendor_stats_cache = None
        self.type_vendor_stats_cache_summary = None
        self.data_save_path = f"{Config.DATA_DIR}/{Config.DATA_SAVE_FILE}" # Path to the YAML file for saving/loading tea data
        self.dropdown_tea_types = set()  # To be populated based on stash data
        self.dropdown_tea_vendors = set()  # To be populated based on stash data

        self.filter_flags = {
            "hide_finished": Config.SEARCH_DEFAULTS_HIDE_FINISHED,
            "hide_unreviewed": Config.SEARCH_DEFAULTS_HIDE_UNREVIEWED,
            "hide_reviewed": Config.SEARCH_DEFAULTS_HIDE_REVIEWED,
            "hide_finished_reviews": Config.SEARCH_DEFAULTS_HIDE_FINISHED_REVIEWS
        }

        self.check_yaml_file_exists()

    def check_yaml_file_exists(self):
        """Checks if the YAML file exists, and creates it if it doesn't."""
        if not os.path.exists(self.data_save_path):
            Logger.warning(f"YAML file not found at {self.data_save_path}. Creating a new one.")
            with open(self.data_save_path, 'w') as f:
                yaml.safe_dump([], f)  # Start with an empty list of teas
        else:
            Logger.info(f"YAML file found at {self.data_save_path}.")

    def set_filter_flag(self, key, value):
        Logger.info(f"Filter flag changed: {key} set to {value}")
        self.filter_flags[key] = value
        print(f"Updated filter flags: {self.filter_flags}")
        #self.apply_filters()

    def delete_tea_by_id(self, tea_id):
        """Deletes a tea from the stash by its UUID."""
        tea_to_delete = next((tea for tea in self.teas if tea.id == tea_id), None)
        if tea_to_delete:
            self.stash.remove_tea(tea_to_delete, dry=False)  # Remove tea from stash and save immediately
            self.refresh_all(save_after_refresh=True)  # Refresh data and save after deletion
            Logger.info(f"Deleted tea with ID: {tea_id}")
        else:
            Logger.warning(f"Tea with ID {tea_id} not found for deletion.")

    def delete_review_by_id(self, review_id):
        """Deletes a review from the stash by its UUID."""
        tea, review_to_delete = self.stash.get_review_by_id(review_id)
        if review_to_delete and tea:
            #tea.reviews.remove(review_to_delete)
            self.refresh_all(save_after_refresh=True)  # Refresh data and save after deletion
            Logger.info(f"Deleted review with ID: {review_id} from tea: {tea.name}")
        else:
            Logger.warning(f"Review with ID {review_id} not found for deletion.")

    def _operation_reorder_teas_by_purchase_date(self, newest_first=True):
        """Reorders the teas in the stash by their purchase date."""
        self.stash._operation_reorder_teas_by_purchase_date(newest_first=newest_first)
        self.refresh_all(save_after_refresh=True)  # Refresh data and save after reordering

    def _operation_validate_and_fix_duplicate_ids(self):
        """Checks for duplicate tea IDs and fixes them if found."""
        seen_ids = set()
        duplicates_found = False

        for tea in self.teas:
            if tea.id in seen_ids:
                Logger.warning(f"Duplicate ID found: {tea.id}. Generating a new unique ID.")
                tea.id = str(uuid.uuid4())  # Assign a new unique ID
                duplicates_found = True
            seen_ids.add(tea.id)

        seen_review_ids = set()
        for tea in self.teas:
            for review in tea.reviews:
                if review.id in seen_review_ids:
                    Logger.warning(f"Duplicate Review ID found: {review.id} in tea {tea.name}. Generating a new unique ID.")
                    review.id = str(uuid.uuid4())  # Assign a new unique ID
                    duplicates_found = True
                seen_review_ids.add(review.id)

        if duplicates_found:
            Logger.info("Duplicate IDs were found and fixed. Saving changes to YAML.")
            self.export_to_yaml(self.data_save_path)  # Save the changes after fixing duplicates
        else:
            Logger.info("No duplicate IDs found in the stash.")

        

    def _refresh_dropdown_data(self):
        """Refreshes any dropdown options based on current stash data."""
        self.dropdown_tea_types = self.stash.get_most_common_tea_types(top_n=-1)
        self.dropdown_tea_vendors = self.stash.get_most_common_tea_vendors(top_n=-1)

        Logger.info(f"Dropdown tea types refreshed: {len(self.dropdown_tea_types)} types available.")
        if len(self.dropdown_tea_types) > 5:
            Logger.info(f"Top tea types: {[t[0] for t in self.dropdown_tea_types[:5]]}...")
        Logger.info(f"Dropdown tea vendors refreshed: {len(self.dropdown_tea_vendors)} vendors available.")
        if len(self.dropdown_tea_vendors) > 5:
            Logger.info(f"Top tea vendors: {[v[0] for v in self.dropdown_tea_vendors[:5]]}...")

    def _refresh_stats(self):
        """Manually trigger a recalculation only when needed."""
        self.water_stats_cache = StatsService.get_water_stats(self.teas)
        self.type_vendor_stats_cache, self.type_vendor_stats_cache_summary = StatsService.get_df_summary_by_type_vendor(self.teas)
        Logger.info("Refreshed statistics caches.")

    def _refresh_stash_dfs(self, refresh_teas=True, refresh_reviews=True):
        """Manually trigger a refresh of the stash DataFrames."""
        if refresh_teas:
            self.df = self._build_stash_dataframe()
        if refresh_reviews:
            self.reviews_df = self._build_stash_reviews_dataframe()
        # Reset filtered views to match the new data
        self.filtered_df = self.df.copy()
        self.filtered_reviews_df = self.reviews_df.copy()
        Logger.info("Refreshed stash DataFrames.")

    def refresh_all(self, save_after_refresh=False):
        """Convenience method to refresh both stats and stash DataFrames."""
        
        self._refresh_stats()
        self._refresh_stash_dfs()
        self._refresh_dropdown_data()
        if save_after_refresh:
            self.export_to_yaml()  # Save the current state to YAML after refreshing
        Logger.info("Refreshed all data and statistics.")

    def get_stash_stats_summary(self):
        """Returns a summary of the stash statistics for display in the UI."""
        # This will just be number of teas, number of teas finished, total weight
        # number reviewed/unreviewed, average rating, etc. We can expand this as needed.
        total_teas = len(self.stash.return_teas())
        total_finished = len([tea for tea in self.stash.return_teas() if tea.finished])
        total_weight = sum(tea.quantity for tea in self.stash.return_teas())
        total_reviewed = len([tea for tea in self.stash.return_teas() if len(tea.reviews) > 0 or tea.finished])
        total_unreviewed = total_teas - total_reviewed
        # avg rating is only if rated with reviews, otherwise excluded. It is returned in letter string format
        rated_teas = [tea for tea in self.stash.return_teas() if tea.average_rating is not None]
        avg_rating = sum(tea.average_rating for tea in rated_teas) / len(rated_teas) if rated_teas else None
        avg_rating_string = ScoreConverter.score_to_letter(avg_rating) if avg_rating is not None else "N/A"
        total_remaining = sum(tea.remaining for tea in self.stash.return_teas())
        return {
            "total_teas": total_teas,
            "total_finished": total_finished,
            "total_weight": total_weight,
            "total_reviewed": total_reviewed,
            "total_unreviewed": total_unreviewed,
            "avg_rating": avg_rating_string,
            "total_remaining": total_remaining
        }

    def load_from_yaml(self, filepath):
        with open(filepath, 'r') as f:
            raw_data = yaml.safe_load(f)
            # Your YAML is a list of teas at the top level
            teas = []
            try:
                teas = [Tea.from_dict_or_yaml(item) for item in raw_data]
            except Exception as e:
                Logger.error(f"Error loading teas from YAML: {e}")
                Logger.error(f"Raw data that caused the error: {raw_data}")
                raise e  # Re-raise after logging
            self.teas = teas
            
        self.stash = TeaStash(self.teas)
        Logger.info(f"Loaded {len(self.teas)} teas from {filepath}")

    # Stash df is a simplified view for UI display
    def _get_stash_dataframe(self):
        Logger.info("Building stash dataframe...")
        if self.df.empty:
            Logger.info("Creating new stash dataframe...")
            self.df = self._build_stash_dataframe()
            Logger.info("Stash dataframe created with length: " + str(len(self.df)))
        return self.df
    
    def _get_stash_reviews_dataframe(self):
        Logger.info("Building stash reviews dataframe...")
        if self.reviews_df.empty:
            Logger.info("Creating new stash reviews dataframe...")
            self.reviews_df = self._build_stash_reviews_dataframe()
            Logger.info("Stash reviews dataframe created with length: " + str(len(self.reviews_df)))
        return self.reviews_df

    def _build_stash_dataframe(self):
        data = []
        i = 0
        for tea in self.stash.return_teas():
            # Filter flags
            if self.filter_flags["hide_finished"] and tea.finished:
                continue
            if self.filter_flags["hide_unreviewed"] and len(tea.reviews) == 0:
                continue
            if self.filter_flags["hide_reviewed"] and len(tea.reviews) > 0:
                continue
            purchase_amt = tea.quantity
            remaining_amt = tea.remaining

            data.append({
                "UUID": tea.id,
                "Name": tea.name,
                "Year": tea.year,
                "Vendor": tea.vendor,
                "Type": tea.tea_type,
                "Amount": f"{remaining_amt:.1f}g / {purchase_amt:.1f}g",
                "Catalog Price (USD)": f"${tea.catalog_price:.2f}",
                "Remaining Value (USD)": f"${remaining_amt * (tea.catalog_price / tea.quantity):.2f}" if tea.quantity > 0 else "$0.00",
                "Actual Cost (USD)": f"${tea.cost:.2f}",
                "Catalog $/g": round(tea.catalog_price / tea.quantity, 2) if tea.quantity > 0 else 0,
                "Date Purchased": tea.purchase_date if isinstance(tea.purchase_date, str) else tea.purchase_date.strftime("%Y-%m-%d"),
                "Avg Rating": tea.average_rating,
                "Purchase Note": tea.purchase_note,
                "Last Drank": tea.last_drank,
                "Reviews": len(tea.reviews),
                "Adjustments (g)": tea.sum_adjustments_grams,
            })
            i += 1
        if not data or i == 0:
            Logger.warning("No teas to display after applying filters. Returning empty dataframe.")
            return pd.DataFrame(columns=self.df.columns)

        df = pd.DataFrame(data)
        df.insert(1, "IDX", range(len(df)))
        # Add stats columns
        if not df.empty:
            df['PCT Score'] = df['Avg Rating'].rank(pct=True).mul(100).round(1).fillna(0)
            df['PCT Cost'] = df['Catalog $/g'].rank(pct=True).mul(100).round(1).fillna(0)
        # $/g to string
        df['Catalog $/g'] = df['Catalog $/g'].apply(lambda x: f"${x:.2f}")
        return df

    def _filter_data(self, query: str = None, query_type: str = "Name"):
        """Filters the dataframe based on a query string or numeric comparison."""
        Logger.info(f"Filtering data with query: '{query}' on type: '{query_type}'")
        if not query:
            self.filtered_df = self.df.copy()
            return

        # Map radio button labels to actual DataFrame column names
        column_map = {
            "Avg Score": "Avg Rating",
            "Cost": "Actual Cost (USD)",
            "Amount": "Amount",
            "Reviews": "Reviews",
            "Name": "Name",
            "Vendor": "Vendor",
            "Type": "Type",
        }
        actual_column = column_map.get(query_type, query_type)

        # Determine if this is a numeric comparison column
        numeric_columns = {"Amount", "Avg Score", "Reviews", "Cost"}

        if query_type in numeric_columns:
            try:
                threshold = float(query.strip())
            except (ValueError, TypeError):
                # Invalid numeric input — reset to show all
                Logger.info(f"Invalid numeric input for {query_type}: '{query}'. Resetting filter.")
                self.filtered_df = self.df.copy()
                return

            if query_type == "Amount":
                # Amount column format: "45.0g / 100.0g" — extract remaining amount (first number)
                numeric_values = pd.to_numeric(
                    self.df["Amount"].str.split('/').str[0].str.replace('g', '', case=False).str.strip(),
                    errors='coerce'
                )
                mask = numeric_values <= threshold
            elif query_type == "Avg Score":
                # Avg Rating column is numeric (float) or NaN
                numeric_values = pd.to_numeric(self.df["Avg Rating"], errors='coerce').fillna(0)
                mask = numeric_values <= threshold
            elif query_type == "Reviews":
                # Reviews column is integer count — "filter fewer than" (strict less than)
                mask = self.df["Reviews"] < threshold
            elif query_type == "Cost":
                # Actual Cost (USD) column format: "$25.00" — strip $ and convert
                numeric_values = pd.to_numeric(
                    self.df["Actual Cost (USD)"].str.replace('$', '', regex=False).str.strip(),
                    errors='coerce'
                )
                mask = numeric_values <= threshold

            self.filtered_df = self.df[mask].copy()
        else:
            # String contains search for text columns (Name, Vendor, Type)
            mask = (
                self.df[actual_column].str.contains(query, case=False, na=False)
            )
            self.filtered_df = self.df[mask].copy()

    def _filter_reviews_data(self, query: str = None, query_type: str = "Tea Name"):
        """Filters the reviews dataframe based on a string query."""
        Logger.info(f"Filtering reviews data with query: '{query}' on type: '{query_type}'")
        if not query:
            self.filtered_reviews_df = self.reviews_df.copy()
        else:
            # Searches across specified column (case-insensitive)
            mask = (
                self.reviews_df[query_type].astype(str).str.contains(query, case=False, na=False)
            )
            self.filtered_reviews_df = self.reviews_df[mask].copy()

    def _sort_data(self, column_name, ascending):
        """Sorts the currently filtered view with data cleaning."""
        if self.filtered_df.empty:
            return

        def _clean_key(col_series):
            """Cleans the column data for sorting."""
            if column_name == "Amount":
            # 1. Split by '/' and take the first part
            # 2. Remove 'g' and any whitespace
            # 3. Convert to numeric for proper math sorting
                return pd.to_numeric(
                    col_series.str.split('/').str[0].str.replace('g', '', case=False).str.strip(),
                    errors='coerce'
                )
            elif "Rating" in column_name:
                # presence of nan string means 0
                if col_series.isna().any():
                    col_series = col_series.fillna("0")
            
            # 1. Convert to string and lowercase
            s_clean = col_series.astype(str).str.lower()
            # 2. Remove non-alphanumeric characters (equivalent to your regex)
            s_clean = s_clean.str.replace(r'[^a-z0-9.]', '', regex=True)
            # 3. Strip specific characters ($ prefix or g suffix)
            s_clean = s_clean.str.strip().str.replace('$', '', regex=False).str.replace('g', '', regex=False)
            try:
                # 4. Try converting to numeric where possible
                # errors='coerce' turns non-numeric into NaN, keeping the sort logical
                numeric_series = pd.to_numeric(s_clean, errors='raise')
                # If the whole column is effectively numeric, return the numeric version
                # Otherwise, return the cleaned strings
                if numeric_series.notna().any():
                    return numeric_series
            except Exception as e:
                return s_clean  # If conversion fails, return the cleaned string series for sorting
            return s_clean

        # Perform the sort
        self.filtered_df.sort_values(
            by=column_name,
            ascending=ascending,
            inplace=True,
            key=_clean_key
        )

    def _zero_negative_amounts(self):
        """Sets any negative amounts in the stash to zero."""
        for tea in self.stash.return_teas():
            if tea.quantity < 0:
                Logger.info(f"Zeroing negative quantity for tea: {tea.name} (was {tea.quantity}g)")
                tea.quantity = 0
            if tea.remaining < 0:
                Logger.info(f"Zeroing negative remaining amount for tea: {tea.name} (was {tea.remaining}g)")
                tea.remaining = 0
        self.refresh_all(save_after_refresh=True)

    def _zero_negative_costs(self):
        """Sets any negative costs in the stash to zero."""
        for tea in self.stash.return_teas():
            if tea.cost < 0:
                Logger.info(f"Zeroing negative cost for tea: {tea.name} (was ${tea.cost:.2f})")
                tea.cost = 0
        self.refresh_all(save_after_refresh=True)

    def _round_amounts_and_costs(self):
        """Rounds all amounts and costs to 2 decimal places."""
        for tea in self.stash.return_teas():
            if tea.quantity is not None:
                rounded_quantity = round(tea.quantity, 2)
                if rounded_quantity != tea.quantity:
                    Logger.info(f"Rounding quantity for tea: {tea.name} from {tea.quantity}g to {rounded_quantity}g")
                    tea.quantity = rounded_quantity
            if tea.cost is not None:
                rounded_cost = round(tea.cost, 2)
                if rounded_cost != tea.cost:
                    Logger.info(f"Rounding cost for tea: {tea.name} from ${tea.cost:.2f} to ${rounded_cost:.2f}")
                    tea.cost = rounded_cost
            if tea.catalog_price is not None:
                rounded_catalog_price = round(tea.catalog_price, 2)
                if rounded_catalog_price != tea.catalog_price:
                    Logger.info(f"Rounding catalog price for tea: {tea.name} from ${tea.catalog_price:.2f} to ${rounded_catalog_price:.2f}")
                    tea.catalog_price = rounded_catalog_price
        self.refresh_all(save_after_refresh=True)

    def _sort_reviews_data(self, column_name, ascending):
        """Sorts the reviews dataframe."""
        if self.filtered_reviews_df is None or self.filtered_reviews_df.empty:
            return
        
        def _clean_key(col_series):
            """Cleans the column data for sorting."""
            s_clean = col_series.astype(str).str.lower()
            s_clean = s_clean.str.replace(r'[^a-z0-9.]', '', regex=True)
            s_clean = s_clean.str.strip().str.replace('$', '', regex=False).str.replace('g', '', regex=False)
            numeric_series = pd.to_numeric(s_clean, errors='coerce')
            if numeric_series.notna().any():
                return numeric_series
            return s_clean
        
        # Perform the sort
        self.filtered_reviews_df.sort_values(
            by=column_name,
            ascending=ascending,
            inplace=True,
            key=_clean_key
        )



    def _build_stash_reviews_dataframe(self):
        data = []
        flat_reviews = self.stash.returnFlatReviews()
        Logger.info(f"Building reviews dataframe from {len(flat_reviews)} total reviews...")
        i = 0
        for tea, review in flat_reviews:
            if self.filter_flags["hide_finished_reviews"] and tea.remaining <= 0:
                continue

            data.append({
                "IDX": i,
                "Date": review.date,
                "Tea Name": tea.name,
                "Tea Year": tea.year,
                "Tea Vendor": tea.vendor,
                "Tea Type": tea.tea_type,
                "Avg Rating": review.rating,
                "Notes": review.notes,
                "Amount Drunk": review.amount_drunk,
                "Vessel Size": review.vessel_size,
                "Method": review.method,
                "Steeps": review.steeps,
                "Session Number": review.session_num,
                "Tea UUID": tea.id,
                "Review UUID": review.id,
            })
            i += 1

        return pd.DataFrame(data)

    def export_to_yaml(self, filepath=None):
        """Exports the current teas to a YAML file."""
        if filepath is None:
            filepath = self.data_save_path
        with open(filepath, 'w') as f:
            data_to_save = [tea.to_dict() for tea in self.teas]
            try:
                yaml.safe_dump(data_to_save, f, sort_keys=False)
            except Exception as e:
                for item in data_to_save:
                    for key, value in item.items():
                        try:
                            yaml.safe_dump({key: value})
                        except yaml.representer.RepresenterError as re:
                            print(f"Failing to export YAML field: {key} with type {type(value)}")
                            print(f"Value contents: {value}")
                            print(f"Representer error details: {re}")
                Logger.error(f"Error exporting teas to YAML: {e}")
                raise e  # Re-raise after logging
        Logger.info(f"Exported {len(self.teas)} teas to {filepath}")

    def export_to_csv(self, filepath=None):
        """Exports the current teas to a CSV file."""
        if filepath is None:
            filepath = self.data_save_path.replace('.yaml', '.csv')
        df = self.stash.get_as_dataframe(includeCalculatedFields=False)
        df.to_csv(filepath, index=False)
        Logger.info(f"Exported stash dataframe to {filepath}")

    @property
    def water_stats(self):
        if self.water_stats_cache is None:
            self._refresh_stats()
        return self.water_stats_cache

    def sort_summary_data(self, ui_column_name, ascending):
        mapping = {
            "Dimension": "Dimension",
            "Label": "Label",
            "Total Grams": "Quantity",
            "Review Count": "ReviewCount",
            "Total Teas": "TotalTeas",
            "Average Rating": "AverageRating"
        }
        col = mapping.get(ui_column_name)
        if col:
            self.type_vendor_stats_cache.sort_values(by=col, ascending=ascending, inplace=True)




# Ensure folders exist
# /data
# /backup
# /src

def ensure_folders_exist():
    """Ensures that the necessary folders exist."""
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(f"{Config.DATA_DIR}/tmp", exist_ok=True)  # Subfolder for temporary files
    os.makedirs(Config.BACKUP_DIR, exist_ok=True)
    os.makedirs(Config.SRC_DIR, exist_ok=True)
    os.makedirs(Config.FONTS_DIR, exist_ok=True)

