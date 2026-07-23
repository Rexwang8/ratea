"""Data query service — filter and sort operations for stash DataFrames.

Extracted from DataManager to isolate DataFrame filtering/sorting logic
with column-name mapping and data-cleaning helpers.
All methods are static — they take DataFrames as input and return new DataFrames.
"""

import pandas as pd
from services.logger import Logger


class DataQueryService:
    """Static methods for filtering and sorting tea/review DataFrames."""

    # Map UI radio-button labels to actual DataFrame column names
    TEA_COLUMN_MAP = {
        "Avg Score": "Avg Rating",
        "Cost": "Actual Cost (USD)",
        "Amount": "Amount",
        "Reviews": "Reviews",
        "Name": "Name",
        "Vendor": "Vendor",
        "Type": "Type",
    }

    # Columns that use numeric comparison instead of string search
    TEA_NUMERIC_COLUMNS = {"Amount", "Avg Score", "Reviews", "Cost"}

    # ------------------------------------------------------------------
    # Tea-level filtering & sorting
    # ------------------------------------------------------------------

    @staticmethod
    def filter_data(df: pd.DataFrame, query: str = None, query_type: str = "Name") -> pd.DataFrame:
        """Filter the tea DataFrame by a query string or numeric threshold.

        For numeric columns (Amount, Avg Score, Reviews, Cost) the query
        is parsed as a number and used for "≤ threshold" comparison
        (except Reviews which uses strict "less than").
        For text columns a case-insensitive substring match is performed.
        Invalid numeric input resets the filter, returning the unfiltered df.

        Returns a new DataFrame (the caller owns the copy).
        """
        Logger.info(f"Filtering data with query: '{query}' on type: '{query_type}'")
        if not query:
            return df.copy()

        actual_column = DataQueryService.TEA_COLUMN_MAP.get(query_type, query_type)

        if query_type in DataQueryService.TEA_NUMERIC_COLUMNS:
            try:
                threshold = float(query.strip())
            except (ValueError, TypeError):
                Logger.info(f"Invalid numeric input for {query_type}: '{query}'. Resetting filter.")
                return df.copy()

            mask = DataQueryService._build_numeric_mask(df, query_type, threshold)
        else:
            # Text columns: case-insensitive substring search
            mask = df[actual_column].str.contains(query, case=False, na=False)

        return df[mask].copy()

    @staticmethod
    def sort_data(df: pd.DataFrame, column_name: str, ascending: bool) -> pd.DataFrame:
        """Sort the filtered tea DataFrame by *column_name* with data cleaning.

        Returns a new DataFrame sorted in-place for consistency.
        """
        if df.empty:
            return df

        sorted_df = df.sort_values(
            by=column_name,
            ascending=ascending,
            key=lambda col: DataQueryService._clean_sort_key(col, column_name),
        )
        return sorted_df

    # ------------------------------------------------------------------
    # Review-level filtering & sorting
    # ------------------------------------------------------------------

    @staticmethod
    def filter_reviews_data(reviews_df: pd.DataFrame, query: str = None, query_type: str = "Tea Name") -> pd.DataFrame:
        """Filter the reviews DataFrame by a string query (case-insensitive)."""
        Logger.info(f"Filtering reviews data with query: '{query}' on type: '{query_type}'")
        if not query:
            return reviews_df.copy()

        mask = reviews_df[query_type].astype(str).str.contains(query, case=False, na=False)
        return reviews_df[mask].copy()

    @staticmethod
    def sort_reviews_data(reviews_df: pd.DataFrame, column_name: str, ascending: bool) -> pd.DataFrame:
        """Sort the filtered reviews DataFrame with data cleaning."""
        if reviews_df.empty:
            return reviews_df

        sorted_df = reviews_df.sort_values(
            by=column_name,
            ascending=ascending,
            key=DataQueryService._clean_reviews_sort_key,
        )
        return sorted_df

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_numeric_mask(df: pd.DataFrame, query_type: str, threshold: float) -> pd.Series:
        """Build a boolean mask for numeric comparison columns."""
        if query_type == "Amount":
            # Format: "45.0g / 100.0g" — extract first number (remaining grams)
            numeric_values = pd.to_numeric(
                df["Amount"].str.split('/').str[0].str.replace('g', '', case=False).str.strip(),
                errors='coerce',
            )
            mask = numeric_values <= threshold
        elif query_type == "Avg Score":
            numeric_values = pd.to_numeric(df["Avg Rating"], errors='coerce').fillna(0)
            mask = numeric_values <= threshold
        elif query_type == "Reviews":
            # Strict "fewer than" for review count
            mask = df["Reviews"] < threshold
        elif query_type == "Cost":
            # Format: "$25.00" — strip $ and convert
            numeric_values = pd.to_numeric(
                df["Actual Cost (USD)"].str.replace('$', '', regex=False).str.strip(),
                errors='coerce',
            )
            mask = numeric_values <= threshold
        else:
            # Fallback: match nothing
            mask = pd.Series(False, index=df.index)

        return mask

    @staticmethod
    def _clean_sort_key(col_series: pd.Series, column_name: str) -> pd.Series:
        """Clean a sort column so numeric values sort numerically."""
        if column_name == "Amount":
            return pd.to_numeric(
                col_series.str.split('/').str[0].str.replace('g', '', case=False).str.strip(),
                errors='coerce',
            )
        elif "Rating" in column_name:
            if col_series.isna().any():
                col_series = col_series.fillna("0")

        s_clean = col_series.astype(str).str.lower()
        s_clean = s_clean.str.replace(r'[^a-z0-9.]', '', regex=True)
        s_clean = s_clean.str.strip().str.replace('$', '', regex=False).str.replace('g', '', regex=False)

        try:
            numeric_series = pd.to_numeric(s_clean, errors='raise')
            if numeric_series.notna().any():
                return numeric_series
        except Exception:
            return s_clean
        return s_clean

    @staticmethod
    def _clean_reviews_sort_key(col_series: pd.Series) -> pd.Series:
        """Clean a reviews sort column."""
        s_clean = col_series.astype(str).str.lower()
        s_clean = s_clean.str.replace(r'[^a-z0-9.]', '', regex=True)
        s_clean = s_clean.str.strip().str.replace('$', '', regex=False).str.replace('g', '', regex=False)
        numeric_series = pd.to_numeric(s_clean, errors='coerce')
        if numeric_series.notna().any():
            return numeric_series
        return s_clean