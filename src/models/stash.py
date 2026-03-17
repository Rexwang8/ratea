import pandas as pd

from services.logger import Logger
from .tea import Tea

class TeaStash:
    def __init__(self, teas: list[Tea] = None):
        self.teas: list[Tea] = teas if teas is not None else []

    def add_tea(self, tea: Tea):
        self.teas.append(tea)

    def get_tea_by_id(self, tea_id):
        for tea in self.teas:
            if tea.id == tea_id:
                return tea
        return None
    
    def get_review_by_id(self, review_id):
        for tea in self.teas:
            for review in tea.reviews:
                if review.id == review_id:
                    return tea, review
        return None, None
    
    def remove_tea(self, tea: Tea, dry=True):
        if dry:
            Logger.info(f"Dry run: would remove tea: {tea.name}")
            return
        if tea in self.teas:
            self.teas.remove(tea)
            Logger.info(f"Removed tea: {tea.name}")
        else:
            Logger.warning(f"Attempted to remove tea that was not found: {tea.name}")
    
    def get_tea_by_review_id(self, review_id):
        for tea in self.teas:
            for review in tea.reviews:
                if review.id == review_id:
                    return tea
        return None
    
    def get_last_tea_entry(self):
        if not self.teas:
            return None
        return self.teas[-1]
    
    def get_last_review_entry(self):
        last_review = None
        last_review_tea = None
        for tea in self.teas:
            for review in tea.reviews:
                if last_review is None or review.date > last_review.date:
                    last_review = review
                    last_review_tea = tea
        return last_review_tea, last_review
    
    def returnTeas(self):
        # get teas and sort by purchase date, oldest first, then by vendor, then by name
        self.teas.sort(key=lambda t: (t.purchaseDate or pd.Timestamp.min, t.vendor.lower(), t.name.lower()), reverse=False)
        return self.teas

    def returnFlatReviews(self):
        reviews = []
        for tea in self.teas:
            for review in tea.reviews:
                reviews.append((tea, review))
        # Sort reviews by date, oldest first
        reviews.sort(key=lambda tr: tr[1].date, reverse=False)
        return reviews
    
    def toDict(self):
        return [tea.to_dict() for tea in self.teas]
    
    def get_tea_by_uuid(self, tea_uuid: str) -> Tea | None:
        for tea in self.teas:
            if tea.id == tea_uuid:
                return tea
        return None
    
    def get_most_common_tea_types(self, top_n=30):
        returnAll = False
        if top_n <= 0:
            returnAll = True

        type_counts = {}
        for tea in self.teas:
            if tea.tea_type not in type_counts:
                type_counts[tea.tea_type] = 0
            type_counts[tea.tea_type] += 1
        
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        if top_n > len(sorted_types):
            top_n = len(sorted_types)
        return sorted_types[:top_n] if not returnAll else sorted_types
    
    def get_most_common_tea_vendors(self, top_n=30):
        returnAll = False
        if top_n <= 0:
            returnAll = True

        vendor_counts = {}
        for tea in self.teas:
            if tea.vendor not in vendor_counts:
                vendor_counts[tea.vendor] = 0
            vendor_counts[tea.vendor] += 1
        
        sorted_vendors = sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True)
        if top_n > len(sorted_vendors):
            top_n = len(sorted_vendors)
        return sorted_vendors[:top_n] if not returnAll else sorted_vendors
    
    def operation_reorder_teas_by_purchase_date(self, newest_first=True, dry=True):
        if dry:
            Logger.info(f"Dry run: would reorder teas by purchase date. (num teas: {len(self.teas)})")
            return
        self.teas.sort(key=lambda t: t.purchaseDate or pd.Timestamp.min, reverse=newest_first)

        # Resave after reordering to ensure the new order is reflected in the YAML file and UI
        Logger.info(f"Reordered teas by purchase date. (num teas: {len(self.teas)})")

    # --- THE PANDAS MAGIC ---
    def get_as_dataframe(self, includeCalculatedFields: bool = True) -> pd.DataFrame:
        """
        Converts the current object list into a Pandas DataFrame 
        perfect for sorting, filtering, and stats.
        """
        data = []
        for tea in self.teas:
            if not includeCalculatedFields:
                tea_data = {
                    "ID": tea.id,
                    "Name": tea.name,
                    "Vendor": tea.vendor,
                    "Type": tea.tea_type,
                    "Cost (USD)": tea.cost,
                    "Catalog Price (USD)": tea.catalogPrice,
                    "Quantity (g)": tea.quantity,
                    "Purchase Date": tea.purchaseDate.strftime("%Y-%m-%d") if tea.purchaseDate else None,
                    "Year": tea.year,
                    "Purchase Note": tea.purchaseNote,
                }
                data.append(tea_data)
                continue

            tea_data = {
                "ID": tea.id,
                "Name": tea.name,
                "Vendor": tea.vendor,
                "Type": tea.tea_type,
                "Average Rating": tea.average_rating,
                "Review Count": len(tea.reviews),
                "Last Drank": tea.last_drank,
                "Total Amount Drunk (g)": tea.total_amount_drunk,
                "Cost (USD)": tea.cost,
                "Catalog Price (USD)": tea.catalogPrice,
                "Quantity (g)": tea.quantity,
                "Purchase Date": tea.purchaseDate.strftime("%Y-%m-%d") if tea.purchaseDate else None,
                "Year": tea.year,
                "Purchase Note": tea.purchaseNote,
                "Total Adjustments (g)": tea.sum_adjustments_grams,
                "Total Adjustments Cost (USD)": tea.sum_adjustments_cost
            }
            data.append(tea_data)
        
        return pd.DataFrame(data)

    def get_reviews_dataframe(self):
        """
        Returns a flat dataframe of ALL reviews, useful for 
        plotting 'consumption over time'.
        """
        data = []
        for tea in self.teas:
            for review in tea.reviews:
                data.append({
                    "Tea Name": tea.name,
                    "Vendor": tea.vendor,
                    "Date": review.date,
                    "Rating": review.rating,
                    "Notes": review.text,
                    "Amount Drunk (g)": review.amount_drunk,
                    "Vessel Size (ml)": review.vesselSize,
                    "Method": review.method,
                    "Is Free Sample": review.isFreeSample
                })
        return pd.DataFrame(data)