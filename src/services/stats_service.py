import math
import matplotlib
matplotlib.use("Agg") # Force non-gpu backend to prevent warnings when generating chart

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
import dearpygui.dearpygui as dpg
from PIL import Image, ImageDraw, ImageFont
from config import Config
from models.review import Review
from models.tea import Tea
from services.score_converter import ScoreConverter
from services.text_helper import wrap_text_no_break_words
import os as os
from services.logger import Logger
import matplotlib.patheffects as pe


TEA_TYPE_COLOR_MAP = {
            "Sheng": "#1f77b4",
            "Shou": "#4e342e",
            "Hong": "#b71c1c",
            "Yancha": "#546e7a",
            "White": "#f8bbd0",
            "Dancong": "#eb7855",
            "Taiwanese Oolong": "#A92D48",
            "Ryokucha": "#388e3c",
            "Matcha": "#1c591f",
            "Fuzhuan": "#8d6e63",
            "Raw Liubao": "#78c2a4",
            "Ripe Liubao": "#5a3d38",
            "Green": "#3F8542",
            "Yellow": "#fbc02d",
            "Hua Juan": "#7b1fa2",
            "San Jian": "#074d45",
            "Futsucha": "#ff6200",
            "Anxi Oolong": "#17c1b0",
            "Green Oolong": "#85b759",
            "Heicha": "#5d4037",
            "Herbal": "#AB1CA8",
            "Other": "#9e9e9e",
            "Unknown": "#6b6b6b",
        }

class StatsService:
    @staticmethod
    def get_consumption_plot_data(teas):
        """Processes tea reviews into DPG-ready plot lists."""
        reviews_data = []
        for tea in teas:
            for rev in tea.reviews:
                reviews_data.append({
                    "date": pd.to_datetime(rev.date),
                    "amount": rev.amount_drunk
                })

        if not reviews_data:
            return [], [], [], []

        df = pd.DataFrame(reviews_data)
        # Resample and Sum
        df_monthly = df.set_index('date').resample('ME')['amount'].sum().fillna(0)

        # X/Y Primary Data
        x_data = [float(d.timestamp()) for d in df_monthly.index]
        y_data = df_monthly.values.tolist()

        # Generate Ticks
        labels = [d.strftime("%Y-%m") for d in df_monthly.index]
        tick_data = [[labels[i], x_data[i]] for i in range(len(labels))]
        
        # Format Y Axis Labels
        y_labels = [[f"{amt:.1f}g", amt] for amt in y_data]

        # Cull logic
        max_labels = 12
        if len(tick_data) > max_labels:
            step = len(tick_data) // max_labels
            tick_data = tick_data[::step] # Use slicing for cleaner code

        return x_data, y_data, tick_data, y_labels
    
    @staticmethod
    # Data for distributions of ratings vs letter grades, to be shown in the dashboard
    # Will be a scatter plot with average rating on the x axis, percentile on the y axis, and size of bubble representing number of teas at that point
    def get_rating_distribution_data(teas):
        all_ratings = []
        for tea in teas:
            if tea.average_rating > 0 and tea.catalog_price_per_gram is not None:
                all_ratings.append((tea.average_rating, tea.catalog_price_per_gram))
        if not all_ratings:
            return [], [], []

        df = pd.DataFrame(all_ratings, columns=["AvgRating", "PricePerGram"])
        
        x_data = df["AvgRating"].tolist()
        y_data = df["PricePerGram"].tolist()
        sizes = df["PricePerGram"].apply(lambda x: x * 10).tolist()  # Bubble size based on price

        return x_data, y_data, sizes
    
    @staticmethod
    # Same as above, but instead of straight price, we use price percentile to show how expensive a tea is relative to the stash
    def get_price_percentile_distribution_data(teas):
        all_ratings = []
        for tea in teas:
            if tea.average_rating > 0 and tea.catalog_price_per_gram is not None:
                all_ratings.append((tea.average_rating, tea.catalog_price_per_gram))
        if not all_ratings:
            return [], [], []

        df = pd.DataFrame(all_ratings, columns=["AvgRating", "PricePerGram"])
        df["PricePercentile"] = df["PricePerGram"].rank(pct=True) * 100

        x_data = df["AvgRating"].tolist()
        y_data = df["PricePercentile"].tolist()
        sizes = df["PricePerGram"].apply(lambda x: x * 10).tolist()  # Bubble size based on price

        return x_data, y_data, sizes

    @staticmethod
    def get_water_stats(teas):
        """
        Calculates water totals.
        Returns: (overall_total, per_tea_df)
        """
        per_tea_data = []
        per_review_data = []
        overall_total = 0
        
        for tea in teas:
            # Sum up water from all reviews for this specific tea
            # Assuming 'water_amount' exists in your Review model
            sum_water = sum(rev.steep_count * rev.vesselSize for rev in tea.reviews)
            
            per_tea_data.append({
                "UUID": tea.id,
                "Name": tea.name,
                "TotalWater": sum_water,
                "Type": tea.tea_type,
                "Vendor": tea.vendor,
            })
            overall_total += sum_water

            for rev in tea.reviews:
                per_review_data.append({
                    "TeaName": tea.name,
                    "Date": rev.date,
                    "WaterAmount": rev.steep_count * rev.vesselSize,
                })

        if not per_tea_data:
            return 0, pd.DataFrame(), pd.DataFrame()
        
        df = pd.DataFrame(per_tea_data).sort_values(by="TotalWater", ascending=False)
        df_review = pd.DataFrame(per_review_data)
        return overall_total, df, df_review
    
    @staticmethod
    # Gets total amounts, sum, counts of teas across types/vendors in grams and number of reviews
    # Returns a dataframe with all relavent data which will be parsed again for plotting to get axis data and labels
    # Returns a second custom object with min/max/avg/etc for summary display
    def get_df_summary_by_type_vendor(teas):
        # 1. Create the base log
        raw_data = []
        for t in teas:
            raw_data.append({
                "Type": t.tea_type,
                "Vendor": t.vendor,
                "Quantity": t.quantity,
                "ReviewCount": len(t.reviews),
                "AverageRating": t.average_rating,
                "TotalTeas": 1,
                "TotalTeasReviewed": 1 if len(t.reviews) > 0 else 0
            })
        if not raw_data:
            return pd.DataFrame(), {}
        df = pd.DataFrame(raw_data)
        df["AverageRating"] = df["AverageRating"].replace(0, np.nan)

        # 2. Aggregation Helper
        def aggregate_by(dataframe, column_name):
            # Determine the "other" column (if grouping by Vendor, we count Types)
            other_col = "Type" if column_name == "Vendor" else "Vendor"

            # Build a clean agg dict without any 'None' values
            agg_dict = {
                "Quantity": "sum",
                "ReviewCount": "sum",
                "AverageRating": "mean",
                "TotalTeas": "sum",
                "TotalTeasReviewed": "sum",
                other_col: "count"
            }

            # Perform the group by and aggregation
            agg = dataframe.groupby(column_name).agg(agg_dict).reset_index()

            # Standardize names: Label is the X-axis name, Count is how many unique items
            agg = agg.rename(columns={
                column_name: "Label", 
                other_col: "Count"
            })
    
            agg["Dimension"] = column_name 
            return agg

        # 3. Create both views and combine
        vendor_df = aggregate_by(df, "Vendor")
        type_df = aggregate_by(df, "Type")

        # This combined DF has a 'Dimension' column to switch between views easily
        cleaned_df = pd.concat([vendor_df, type_df], ignore_index=True)

        # 4. Global Stats
        stats = {
            "total_grams": df["Quantity"].sum(),
            "total_reviews": df["ReviewCount"].sum(),
            "total_unique_teas": len(df),
            "num_types": df["Type"].nunique(),
            "num_teas": len(df),
            "num_vendors": df["Vendor"].nunique(),
            "top_vendor": vendor_df.loc[vendor_df["Quantity"].idxmax(), "Label"] if not vendor_df.empty else "N/A",
            "top_vendor_amt": vendor_df["Quantity"].max() if not vendor_df.empty else 0,
            "top_type": type_df.loc[type_df["Quantity"].idxmax(), "Label"] if not type_df.empty else "N/A",
            "top_type_amt": type_df["Quantity"].max() if not type_df.empty else 0
        }

        cleaned_df.sort_values(by="Quantity", ascending=False, inplace=True)

        return cleaned_df, stats
    
    # Input the above function and get back data for a bar chart of total grams by type/vendor (argument)
    def get_bar_chart_grams_data(teas, dimension_shown="Type"):
        df, stats = StatsService.get_df_summary_by_type_vendor(teas)
        if df.empty:
            return [], [], [], []
        plot_df = df[df["Dimension"] == dimension_shown]
        # Sort by quantity so the chart looks professional
        plot_df = plot_df.sort_values("Quantity", ascending=False)
        labels = plot_df["Label"].tolist()
        values = plot_df["Quantity"].tolist()
    
        # Standard DPG coordinate mapping
        x_coords = list(range(len(labels)))
        x_ticks = [[labels[i], i] for i in range(len(labels))]
        y_data = []

        for _, row in plot_df.iterrows():
            y_data.append(float(row["Quantity"]))

        # Generate Ticks
        y_labels = [[f"{amt:.1f}g", amt] for amt in y_data]

        return x_coords, y_data, x_ticks, y_labels

    @staticmethod
    # Gets average ratings across types/vendors, also gets percentiles, and cost analysis
    # Returns a dataframe with all relavent data which will be parsed again for plotting to get axis data and labels
    # Returns a second custom object with min/max/avg/etc for summary display
    def get_df_rating_cost_by_type_vendor(teas):
        data = []
        for t in teas:
            data.append({
                "Type": t.tea_type,
                "Vendor": t.vendor,
                "AvgRating": t.average_rating,
                "PricePerGram": t.catalog_price_per_gram,
                "Cost": t.cost
            })
        if not data:
            return pd.DataFrame(), {}

        df = pd.DataFrame(data).dropna(subset=["AvgRating"])

        # Calculate Percentiles stash-wide
        df["RatingPercentile"] = df["AvgRating"].rank(pct=True) * 100
        df["RatingPercentile"] = df["RatingPercentile"].round(1)
        df["RatingPercentile"] = df["RatingPercentile"].fillna(0)

        # Cost Percentiles
        df["CostPercentile"] = df["Cost"].rank(pct=True) * 100
        df["CostPercentile"] = df["CostPercentile"].round(1)
        df["CostPercentile"] = df["CostPercentile"].fillna(0)

        df["PricePerGram"] = df["PricePerGram"].fillna(0)


        analysis_df = df.groupby(["Type", "Vendor"]).agg({
            "AvgRating": "mean",
            "PricePerGram": "mean",
            "RatingPercentile": "mean",
            "CostPercentile": "mean"
        }).reset_index()

        stats = {
            "stash_avg_rating": df["AvgRating"].mean(),
            "most_expensive_type": analysis_df.loc[analysis_df["PricePerGram"].idxmax()]["Type"],
            "least_expensive_type": analysis_df.loc[analysis_df["PricePerGram"].idxmin()]["Type"]
        }
        return analysis_df, stats
    


    @staticmethod
    # Gets Purchasing history across time, types/vendors, inclusive of adjustments
    # Returns a dataframe with all relavent data which will be parsed again for plotting to get axis data and labels
    # Returns a second custom object with min/max/avg/etc for summary display
    def get_df_purchasing_history_by_type_vendor(teas):
        data = []
        for t in teas:
            # Base purchase
            data.append({
                "Date": t.purchaseDate,
                "Type": t.tea_type,
                "Vendor": t.vendor,
                "Amount": t.quantity,
                "Spend": t.cost
            })
            # Add adjustments (Restocking/Losses)
            for adj in t.adjustments:
                data.append({
                    "Date": adj.date, 
                    "Type": t.tea_type,
                    "Vendor": t.vendor,
                    "Amount": adj.amount,
                    "Spend": adj.cost if hasattr(adj, 'cost') else 0
                })
        if not data:
            return pd.DataFrame(), {}
    
        df = pd.DataFrame(data)
        df["Date"] = pd.to_datetime(df["Date"])
        df["Date"] = df["Date"].dt.date

        history_df = df.sort_values("Date")
        
        stats = {
            "total_spent": df["Spend"].sum(),
            "max_purchase_event": df["Spend"].max(),
            "first_purchase": df["Date"].min()
        }
        return history_df, stats

    @staticmethod
    # Gets review frequency across time, types/vendors, as well as consumed amounts
    # Returns a dataframe with all relavent data which will be parsed again for plotting to get axis data and labels
    # Returns a second custom object with min/max/avg/etc for summary display
    def get_df_review_frequency_by_type_vendor(teas):
        review_logs = []
        for t in teas:
            for r in t.reviews:
                review_logs.append({
                    "Date": r.date,
                    "Type": t.tea_type,
                    "Vendor": t.vendor,
                    "LeafUsed": r.amount_drunk,
                    "WaterUsed": r.water_used_ml,
                    "Method": r.method
                })
        if not review_logs:
            return pd.DataFrame(), {}

        df = pd.DataFrame(review_logs)
        df["Date"] = pd.to_datetime(df["Date"])

        # Aggregate by Month for the frequency analysis
        freq_df = df.groupby([pd.Grouper(key="Date", freq="ME"), "Type"]).agg({
            "LeafUsed": "sum",
            "WaterUsed": "sum",
            "Date": "count"
        }).rename(columns={"Date": "SessionCount"}).reset_index()

        stats = {
            "most_used_method": df["Method"].mode()[0] if not df.empty else "N/A",
            "total_water_liters": df["WaterUsed"].sum() / 1000,
            "avg_leaf_per_session": df["LeafUsed"].mean()
        }
        return freq_df, stats
    
    # Gets the data for the first report image relating to tea rating vs price percentile bubble chart
    # Items are returned as datapoints of (x, y, size) where x is rating, y is price percentile, size is count of teas at that point
    @staticmethod
    def get_report_image_comparison_1_data(teas, thisReview: Review=None, thisTea: Tea=None, by="All", exp=1.1, scale=4.0):
        if by not in ["All", "Type", "Vendor", "All_Under_20"]:
            raise ValueError("Invalid 'by' argument. Must be one of: 'All', 'Type', 'Vendor', 'All_Under_20'")
        teas_same_type = [t for t in teas if thisTea and t.tea_type == thisTea.tea_type] if thisTea else []
        if by == "All_Under_20":
            if len(teas_same_type) > 20:
                by = "Type"
            else:
                by = "All"

        data = []
        for t in teas:
            t: Tea
            if by == "Type" and thisTea and t.tea_type != thisTea.tea_type:
                continue
            if by == "Vendor" and thisTea and t.vendor != thisTea.vendor:
                continue
            data.append({
                "Type": t.tea_type,
                "Vendor": t.vendor,
                "AvgRating": t.average_rating,
                "PricePerGram": t.catalog_price_per_gram,
            })
        if not data:
            return [], {}, None
        df = pd.DataFrame(data).dropna(subset=["AvgRating", "PricePerGram"])

        # Calculate Percentiles stash-wide
        df["RatingPercentile"] = df["AvgRating"].rank(pct=True) * 100
        df["RatingPercentile"] = df["RatingPercentile"].round(1)
        df["RatingPercentile"] = df["RatingPercentile"].fillna(0)

        # Cost Percentiles
        df["PricePercentile"] = df["PricePerGram"].rank(pct=True) * 100
        df["PricePercentile"] = df["PricePercentile"].round(1)
        df["PricePercentile"] = df["PricePercentile"].fillna(0)

        # Remove based on by argument
        if by == "Type":
            df = df[df["Type"] == thisTea.tea_type]
        elif by == "Vendor":
            df = df[df["Vendor"] == thisTea.vendor]

        # Group by rating and price percentile to get counts
        grouped = df.groupby(["AvgRating", "PricePercentile"]).size().reset_index(name='Count')

        datapoints = []
        for _, row in grouped.iterrows():
            datapoints.append( (row["AvgRating"], row["PricePercentile"], row["Count"]) )

        # Cluster amount
        clusterRange = 2 # 2% range for clustering in terms of price percentile
        clusterRangeRating = 0.25 # 0.25 rating range for clustering in terms of rating
        clustered_datapoints = {}
        max_cluster_size = 0

        for x, y, size in datapoints:
            # Find the cluster key
            cluster_key = (round(x / clusterRangeRating) * clusterRangeRating, round(y / clusterRange) * clusterRange)
            if cluster_key not in clustered_datapoints:
                clustered_datapoints[cluster_key] = 0
            clustered_datapoints[cluster_key] += size
            max_cluster_size = max(max_cluster_size, clustered_datapoints[cluster_key])

        # We need this to add the current review's tea point if provided, it will be unclustered
        thisReview_point = None
        if thisReview and thisTea:
            price = None # We want the greater of normal price or actual price
            if thisTea.catalog_price_per_gram is not None and thisTea.catalog_price_per_gram > 0:
                price = thisTea.catalog_price_per_gram
            elif thisTea.price_per_gram is not None and thisTea.price_per_gram > 0:
                price = thisTea.price_per_gram

            if thisReview and thisReview.rating is not None and price is not None:
                # Rating percentile
                rating_pct = (
                    (df["AvgRating"] < thisReview.rating).mean() * 100
                )
            
                # Price percentile
                price_pct = (
                    (df["PricePerGram"] < price).mean() * 100
                )

                thisReview_point = (
                    round(thisReview.rating, 1),
                    round(price_pct, 1),
                    round(rating_pct, 1)
                )

        final_clustered_datapoints = []
        for (x, y), size in clustered_datapoints.items():
            # We use the percentile data but ignore the untried teas for clustering. 
            # If it is 0 reviews, we skip it.
            if x == 0:
                continue
            final_clustered_datapoints.append( (x, y, size * scale * (size ** (exp - 1))) )

        return final_clustered_datapoints, max_cluster_size, thisReview_point
    
    @staticmethod
    def get_report_image_1_percentile_data(teas, thisReview=None, thisTea=None, by="All"):
        # Helper that gets the 0-100 percentile of the price percentile pct[0-100] and assigns an exact price to it in a tuple list
        # for example pct[0] might be $0.01/g, pct[25] might be $0.10/g, pct[50] might be $0.50/g, pct[75] might be $1.00/g, pct[100] might be $5.00/g
        data = []
        for pct in range(0, 101, 25):
            price = StatsService.get_price_percentile(teas, pct, by=by, thisTea=thisTea)
            data.append((pct, price))
        return data

    @staticmethod
    def get_price_percentile(teas, percentile, by="All", thisTea=None):
        # Helper that gets the price at a given percentile for the report image
        prices = []
        for t in teas:
            t: Tea
            if by == "Type" and thisTea and t.tea_type != thisTea.tea_type:
                continue
            if t.catalogPrice is not None and t.quantity is not None and t.quantity > 0:
                price = t.catalogPrice / t.quantity
                prices.append(price)
        if not prices:
            return 0.0
        return np.percentile(prices, percentile)

# GraphService handles generation of graphs using DearPyGui based on stats from StatsService
class GraphService:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.table_tag = "stats_table_rows"

    def render_bar_chart(self, dimension="Type", width=600, height=400):
        """Renders a bar chart for the given dimension ('Type' or 'Vendor')."""
        x_data, y_data, x_labels, y_labels = StatsService.get_bar_chart_grams_data(
            self.data_manager.stash.teas, 
            dimension_shown=dimension
        )

# ReportService handles generation of reports based on stats from StatsService. Reports differ from 
# graphs in that they are composited graphs and text meant to be exported to a png via pyplot and pillow.
class ReportService:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def dummy_method(self):
        """A placeholder method for future report generation."""
        Logger.info("ReportService dummy method called.")

    @staticmethod
    def generate_review_report(data_manager, review_id):
        stash = data_manager.stash
        """Generates a report for a specific tea's reviews."""
        tea, review = stash.get_review_by_id(review_id)
        if not review:
            Logger.error(f"Review with ID {review_id} not found for report generation.")
            return None

        # Gather data
        reviews = tea.reviews
        review_dates = [pd.to_datetime(rev.date) for rev in reviews]
        ratings = [rev.rating for rev in reviews]
        amounts = [rev.amount_drunk for rev in reviews]
        tea_name = tea.name
        tea_year = tea.year
        tea_vendor = tea.vendor
        display_name = ""
        if str(tea_year) in tea_name:
            display_name = f"{tea_name} via {tea_vendor}"
        else:
            display_name = f"{tea_year} {tea_name} via {tea_vendor}"
        num_session_current = len(reviews)
        date_of_review = pd.to_datetime(review.date).strftime("%m/%d/%Y")
        amount_of_review = review.amount_drunk
        cost_per_gram = tea.price_per_gram
        cost_per_gram_normal = tea.catalog_price_per_gram
        cost_per_gram_str = f""
        if cost_per_gram <= 0.02:
            cost_per_gram_str = f"Free Sample!"
        else:
            cost_per_gram_str = f"${cost_per_gram:.2f}/g"
        if cost_per_gram_normal != cost_per_gram:
            cost_per_gram_str += f" (Catalog: ${cost_per_gram_normal:.2f}/g)"
        vessel_size = review.vesselSize
        method = review.method
        review_notes = review.notes if review.notes else "No notes provided."
        review_notes_wrapped, review_notes_len = wrap_text_no_break_words(review_notes, width=85)
        font_size = 20
        notes_line_height = font_size - 4  # matches body_font_small size

        # Create plots and text report using matplotlib/pillow (not implemented here)
        # ...
        # Will auto-size based on content and format nicely for export.
        # We start with base image height and width and then expand height with content as needed, trimming at the end.
        base_width = 800
        # We add extra height based on the length of the review notes, since that is the most variable content. We will trim later if we have extra space.
        base_height = 1400 + (review_notes_len * 20) # Add extra height based on notes length, will trim later if not needed

        display_name_sanitized = display_name.replace(" ", "_").replace("/", "_")
        current_dt_str = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = f"review_report_{display_name_sanitized}_{num_session_current}s_{current_dt_str}.png"

        save_path_graph1_temp = f"{Config.DATA_DIR}/temp_graph1_{display_name_sanitized}.png"

        # Generate a blank report for now
        fig, ax = plt.subplots(figsize=(base_width / 100, base_height / 100))
        ax.axis("off")
        plt.tight_layout()

        plt.savefig(save_path, bbox_inches='tight', dpi=100)
        plt.close(fig)

        # Confirm the file was created before proceeding
        if not os.path.exists(save_path):
            Logger.error(f"Failed to create report image at {save_path}")
            return None

        # Convert to pillow then add name and save
        img = Image.open(save_path)
        draw = ImageDraw.Draw(img)
        font_size = 20
        font_bold = ImageFont.truetype("arialbd.ttf", font_size + 4)
        font_bold_larger = ImageFont.truetype("arialbd.ttf", font_size + 6)
        body_font = ImageFont.truetype("arial.ttf", font_size)
        body_font_small = ImageFont.truetype("arial.ttf", font_size - 4)
        padding_x = 20
        padding_y = 24
        offset_y = 0
        line_spacing = 15
        use_title_larger = True
        if len(display_name) > 25:
            use_title_larger = False

        vendor = tea.vendor if tea.vendor else ""
        title = f"Session {num_session_current}: {display_name}"
        if vendor in title:
            title = title.replace(vendor, "").strip()
            title = title.replace("via", "via " + vendor).strip()
        titleLines = 1
        if len(title) > 40:
            title, titleLines = wrap_text_no_break_words(title, width=40)
        
        draw_tag_value(draw, padding_x, padding_y + offset_y, "", title, font_bold if use_title_larger else font_bold_larger, font_bold if use_title_larger else font_bold_larger, "black", "black")
        offset_y += (10 + ((12 + line_spacing) * titleLines)) # Adjust offset based on title height
        draw.line((padding_x, padding_y + offset_y, base_width - padding_x, padding_y + offset_y), fill="black", width=2)
        offset_y += 15 + line_spacing
        draw_tag_value(draw, padding_x, padding_y + offset_y, "Review Date: ", f"{date_of_review}", body_font, body_font)
        offset_y += 15 + line_spacing
        draw_tag_value(draw, padding_x, padding_y + offset_y, "Amount Drunk: ", f"{amount_of_review}g using {vessel_size}ml via {method}", body_font, body_font)
        offset_y += 15 + line_spacing
        draw_tag_value(draw, padding_x, padding_y + offset_y, "Cost per Gram: ", f"{cost_per_gram_str}, Session cost: ${amount_of_review * cost_per_gram_normal:.2f}", body_font, body_font)
        offset_y += 15 + line_spacing
        # Draw notes as a label + multi-line block so each wrapped line
        # starts at the left margin, not indented by the tag width.
        draw.text((padding_x, padding_y + offset_y), "Notes:", font=body_font, fill=(80, 80, 80))
        offset_y += 2 * notes_line_height  # one line for the label
        draw.text((padding_x + 5, padding_y + offset_y), review_notes_wrapped, font=body_font_small, fill="black")
        offset_y += math.ceil(notes_line_height * review_notes_len * 1.2)  # actual height of the wrapped block
        offset_y += 15 + line_spacing
        # Rating of this session
        draw_tag_value(draw, padding_x, padding_y + offset_y, "Rating this session: ", f"{review.rating_letter}", body_font, body_font)
        
        # Tea cross-review comparison section
        if len(reviews) > 1 and False: # Hiding for now since it's not fully implemented and can be confusing without context, will add back in future
            offset_y += 30 + line_spacing
            draw.line((padding_x, padding_y + offset_y, base_width - padding_x, padding_y + offset_y), fill="black", width=2)
            offset_y += line_spacing
            draw.text((padding_x, padding_y + offset_y), f"Cross-Review Comparisons:", font=font_bold, fill="black")
            offset_y += 20 + line_spacing
            # TODO: Add cross-review comparison content here in future
        
        # Charts section
        offset_y += 25 + line_spacing
        draw.line((padding_x, padding_y + offset_y, base_width - padding_x, padding_y + offset_y), fill="black", width=2)
        offset_y += line_spacing + 5
        draw.text((padding_x, padding_y + offset_y), f"Rating vs Price Percentile", font=font_bold, fill="black")
        offset_y += line_spacing + 17
        col_dark_gray = (70, 70, 70)
        # Write subtitle to explain what a percentile is since apparently people don't understand it even with the axis labels, unfortunately
        draw.text((padding_x + 5, padding_y + offset_y), f"If the point is at 80% percentile for price, that means this tea is more expensive than 80% of all teas", font=body_font_small, fill=col_dark_gray)

        placeholder_1_path = ReportService.generate_report_image_comparison_1(data_manager, thisReview=review, thisTea=tea)
        placeholder_1_img = Image.open(placeholder_1_path)
        # resize
        width = base_width - (4 * padding_x)
        aspect_ratio = placeholder_1_img.height / placeholder_1_img.width
        new_height = int(width * aspect_ratio)
        placeholder_1_img = placeholder_1_img.resize((width, new_height))
        offset_y += 0.1 * new_height
        img.paste(placeholder_1_img, (2*padding_x, int(offset_y)))
        offset_y += placeholder_1_img.height * 1
        # Few lines of text here about the graph
        num_total_teas = len(data_manager.stash.teas)
        num_total_teas_reviewed = len([t for t in data_manager.stash.teas if t.finished or len(t.reviews) > 0])
        num_teas_of_same_type = len([t for t in data_manager.stash.teas if t.tea_type == tea.tea_type])
        num_teas_of_same_type_reviewed = len([t for t in data_manager.stash.teas if t.tea_type == tea.tea_type and (t.finished or len(t.reviews) > 0)])
        draw.text((padding_x, padding_y + offset_y), f"Num Teas reviewed/total: {num_total_teas_reviewed}/{num_total_teas} (blue), Same type ({tea.tea_type}): {num_teas_of_same_type_reviewed}/{num_teas_of_same_type} (orange)", font=body_font_small, fill="black")
        offset_y += line_spacing

        # Final footer
        offset_y += line_spacing
        draw.line((padding_x, padding_y + offset_y, base_width - padding_x, padding_y + offset_y), fill="black", width=2)
        tailingStatement = Config.DEFAULT_TAILING_STATEMENT
        footerStatement = Config.DEFAULT_FOOTER_STATEMENT
        if tailingStatement:
            draw.text((padding_x, padding_y + offset_y+5), tailingStatement, font=body_font_small, fill="gray")
            offset_y += line_spacing * 1.5
        if footerStatement:
            draw.text((padding_x, padding_y + offset_y+5), footerStatement, font=body_font_small, fill="gray")

        # Trim image to used height
        img = img.crop((0, 0, base_width, padding_y + offset_y + 50))

        # Save final image
        img.save(save_path)
        Logger.info(f"Saved review report to {save_path}")



        # Clean up temp files
        try:
            if os.path.exists(save_path_graph1_temp):
                os.remove(save_path_graph1_temp)
        except Exception as e:
            Logger.error(f"Error cleaning up temp files: {e}")

        return None
    

    @staticmethod
    # Generates a comparison between ratings vs log(price per gram) as a bubble chart
    # X axis = rating
    # Y axis = log10(price per gram)
    # Bubble size = clustered count of teas at that rating/price point
    def experimental_generate_report_image_comparison_log_price(data_manager, thisReview=None, thisTea=None):
        Logger.info("Report image comparison LOG PRICE generation called.")
    
        teas = data_manager.stash.teas
    
        # ---- Build dataframe ----
        data = []
        for t in teas:
            data.append({
                "Type": t.tea_type,
                "Vendor": t.vendor,
                "AvgRating": t.average_rating,
                "PricePerGram": t.catalog_price_per_gram,
            })
    
        df = pd.DataFrame(data).dropna(subset=["AvgRating", "PricePerGram"])
        df = df[df["PricePerGram"] > 0]
    
        # log price
        df["LogPrice"] = np.log10(df["PricePerGram"])
    
        # ---- CLUSTERING ----
        grouped = df.groupby(["AvgRating", "LogPrice"]).size().reset_index(name='Count')
    
        clusterRangeRating = 0.25
        clusterRangeLog = 0.05
    
        clustered = {}
        max_cluster_size = 0
    
        for _, row in grouped.iterrows():
            x = row["AvgRating"]
            y = row["LogPrice"]
            size = row["Count"]
    
            key = (
                round(x / clusterRangeRating) * clusterRangeRating,
                round(y / clusterRangeLog) * clusterRangeLog
            )
    
            clustered[key] = clustered.get(key, 0) + size
            max_cluster_size = max(max_cluster_size, clustered[key])
    
        clustered_datapoints = [(x, y, s*4.0) for (x,y), s in clustered.items() if x != 0]
    
        # ---- TYPE FILTERED DATA ----
        def get_filtered(by):
            if by == "Type" and thisTea:
                return df[df["Type"] == thisTea.tea_type]
            if by == "Vendor" and thisTea:
                return df[df["Vendor"] == thisTea.vendor]
            return df
    
        df_type = get_filtered("Type")
    
        grouped_type = df_type.groupby(["AvgRating", "LogPrice"]).size().reset_index(name='Count')
        clustered_type = {}
    
        for _, row in grouped_type.iterrows():
            key = (
                round(row["AvgRating"]/clusterRangeRating)*clusterRangeRating,
                round(row["LogPrice"]/clusterRangeLog)*clusterRangeLog
            )
            clustered_type[key] = clustered_type.get(key, 0) + row["Count"]
    
        clustered_datapoints_type = [(x,y,s*4.0) for (x,y),s in clustered_type.items() if x!=0]
    
        # ---- CURRENT TEA POINT ----
        this_point = None
        if thisReview and thisTea and thisReview.rating is not None:
            price = thisTea.price_per_gram or thisTea.catalog_price_per_gram
            if price and price > 0:
                this_point = (thisReview.rating, np.log10(price))
    
        # ---- PLOT ----
        fig, ax = plt.subplots(figsize=(8,6))
    
        ax.scatter(
            [x for x,y,s in clustered_datapoints],
            [y for x,y,s in clustered_datapoints],
            s=[s*10 for x,y,s in clustered_datapoints],
            alpha=0.40
        )
    
        ax.scatter(
            [x for x,y,s in clustered_datapoints_type],
            [y for x,y,s in clustered_datapoints_type],
            s=[s*10 for x,y,s in clustered_datapoints_type],
            alpha=0.75,
            color="orange",
            label="Same Type"
        )
    
        # ---- Trendline ----
        if len(clustered_datapoints) > 2:
            xvals = np.array([x for x,y,s in clustered_datapoints])
            yvals = np.array([y for x,y,s in clustered_datapoints])
            weights = np.array([s for x,y,s in clustered_datapoints])
    
            z = np.polyfit(xvals, yvals, 2, w=weights)
            p = np.poly1d(z)
    
            xs = np.linspace(0,5,200)
            ax.plot(xs, p(xs), color=(0,0.45,0,0.7), linewidth=2, label="Price Trend")

        # ---- Trendline (linear) ----
        if len(clustered_datapoints) > 1:
            xvals = np.array([x for x,y,s in clustered_datapoints])
            yvals = np.array([y for x,y,s in clustered_datapoints])
            weights = np.array([s for x,y,s in clustered_datapoints])

            # Linear weighted fit
            m, b = np.polyfit(xvals, yvals, 1, w=weights)

            xs = np.linspace(0,5,200)
            ys = m*xs + b

            # Print equation to console/log
            Logger.info(f"Trendline equation: y = {m:.4f}x + {b:.4f}")

            # Plot line
            ax.plot(
                xs,
                ys,
                color=(0,0.45,1,0.7),
                linewidth=2,
                label=f"Trend: y={m:.2f}x+{b:.2f}"
            )
    
        # ---- highlight tea ----
        if this_point:
            ax.scatter(
                [this_point[0]],
                [this_point[1]],
                s=150,
                color="red",
                edgecolors="black",
                label="This Tea"
            )
    
        # ---- Labels ----
        ax.set_xlabel("Rating", fontsize=14)
        ax.set_ylabel("Price per gram (log scale)", fontsize=14)
    
        # ---- X ticks ----
        ax.set_xticks([0,0.5,1.5,2.5,3.5,4.5,5])
        ax.set_xticklabels(['F','D','C','B','A','S','S+'])
        ax.set_xlim(0,5.25)
    
        # ---- Y ticks (show real price values) ----
        y_min, y_max = ax.get_ylim()
        ticks = np.linspace(y_min, y_max, 5)
        ax.set_yticks(ticks)
        ax.set_yticklabels([f"${10**t:.2f}/g" for t in ticks])
    
        # ---- size legend ----
        max_size_rounded = math.ceil(max_cluster_size/10)*10
        legend_sizes = [max_size_rounded, max_size_rounded//2, max(1,max_size_rounded//4)]
    
        handles = [
            ax.scatter([],[],s=size*4,edgecolors="black",facecolors="none")
            for size in legend_sizes
        ]
        labels = [f"{int(s)} teas" for s in legend_sizes]
    
        ax.legend(handles, labels, title="Cluster size", loc="lower right", frameon=True)
    
        # ---- grid ----
        plt.grid(True)
        ax.xaxis.grid(False)
        ax.yaxis.grid(True)
    
        temp_path = f"{Config.DATA_DIR}/tmp/report_comparison_log_price.png"
        plt.savefig(temp_path, bbox_inches="tight", dpi=100)
        plt.close(fig)
    
        return temp_path
    
    @staticmethod
    # Generates a comparison between the ratings of this tea vs all other teas in the stash as a bubble chart
    # The X axis is the rating, the Y axis is the percentile of price per gram. Bubble size is the clustered count of teas at that rating/price point
    def generate_report_image_comparison_1(data_manager, thisReview=None, thisTea=None, by="All_Under_20"):
        Logger.info("Report image comparison 1 generation called.")

        # For scaling of the size of bubbles.
        scaleFactor = 4.0
        expFactor = 1
        
        # vars
        #by = "All"
        INCLUDE_BACKGROUND_DISTRIBUTION = True
        # 4 works well for my screen with max size of ~60. You may need to adjust on your end.
        legendSizeMultiplier = 4 # Multiplier for the size of the legend bubbles, can adjust based on how it looks visually
        color_type = 'darkorange'


        clustered_datapoints, max_size, this_review_point = StatsService.get_report_image_comparison_1_data(teas=data_manager.stash.teas, by=by, thisReview=thisReview, thisTea=thisTea, exp=expFactor, scale=scaleFactor)
        clustered_datapoints_type, _, _ = StatsService.get_report_image_comparison_1_data(teas=data_manager.stash.teas, by="Type", thisReview=thisReview, thisTea=thisTea, exp=expFactor, scale=scaleFactor)

        num_all_teas = sum([size for x, y, size in clustered_datapoints])
        num_type_teas = sum([size for x, y, size in clustered_datapoints_type])
        Logger.info(f"Total teas in comparison (ALL): {num_all_teas}, (Type): {num_type_teas}")

        num_teas_same_type = len([t for t in data_manager.stash.teas if t.tea_type == thisTea.tea_type])
        if num_teas_same_type > 20 and by == "All_Under_20":
            by = "Type"
            Logger.info(f"Switching to Type filter for comparison since there are {num_teas_same_type} teas of the same type as this tea, which is above the threshold of 20.")

        # Create the bubble chart using matplotlib
        #fig = plt.figure(figsize=(8, 7))
        ## Main plot
        #ax = fig.add_axes([0.1, 0.1, 0.8, 0.6])
        ratings = []
        fig, ax = None, None
        if INCLUDE_BACKGROUND_DISTRIBUTION:
            fig, (ax, ax_dist) = plt.subplots(
                2, 1,
                figsize=(10, 8),
                sharex=True,
                gridspec_kw={"height_ratios": [3, 1]}
            )
            # make subplot

            for tea in data_manager.stash.teas:
                if by == "Type" and thisTea and tea.tea_type != thisTea.tea_type:
                    continue
                for r in tea.reviews:
                    if r.rating is not None:
                        ratings.append(r.rating)


            # Build histogram bins from letter-grade boundary midpoints so each bar
            # represents one grade and there are no empty columns between grades.
            grade_values = sorted(ScoreConverter.LETTER_GRADE_MAP.values())
            bins = []
            for i in range(len(grade_values) - 1):
                bins.append((grade_values[i] + grade_values[i+1]) / 2)
            # Pad below F (0.0) and above S+ (5.0) so edge bins have width
            bins = [-0.2] + bins + [5.2]
            hist, edges = np.histogram(ratings, bins=bins)
            centers = [(edges[i] + edges[i+1]) / 2 for i in range(len(hist))]
            #hist_scaled = hist / hist.max() * 90 # Don't scale to 100% height, we want it to be more like 90% so that it doesn't overpower the main graph
            hist_counts = hist
            ax_dist.set_ylabel("Count", fontsize=14)
            ax_dist.set_xlabel("Rating", fontsize=14)
            ax.tick_params(labelbottom=False)

            # bar graph for distribution
            ax_dist.bar(
                centers,
                hist_counts,
                width=0.2,
                color=color_type,
                alpha=0.7,
                zorder=0,
            )
            ax_dist.set_ylim(0, max(hist_counts)*1.2)  # Add some padding to the top of the distribution graph
            

            # Lin interp for smooth curve
            #x_smooth = np.linspace(0, 5, 200)
            #y_smooth = np.interp(x_smooth, centers, hist_scaled)

            # create dense x grid
            #x_smooth = np.linspace(0, 5, 300)

            # bandwidth controls smoothness
            #bandwidth = 0.17
            #y_smooth = np.zeros_like(x_smooth)
            #for r in ratings:
            #    y_smooth += np.exp(-0.5 * ((x_smooth - r) / bandwidth) ** 2)
            ## normalize to 0–80 (100 is too tall visually, we want it to be more like 80% of the height of the graph)
            #y_smooth = y_smooth / y_smooth.max() * 80
            #ax.fill_between(
            #    x_smooth,
            #    y_smooth,
            #    color='gray',
            #    alpha=0.2,
            #    zorder=0
            #)
            #ax.plot(
            #    x_smooth,
            #    y_smooth,
            #    color='gray',
            #    alpha=0.3,
            #    linewidth=1,
            #    zorder=1
            #)
        else:
            fig = plt.figure(figsize=(8, 7))
            # Main plot
            ax = fig.add_axes([0.1, 0.1, 0.8, 0.6])

        assert ax is not None, "Main axis not created properly."
        if INCLUDE_BACKGROUND_DISTRIBUTION:
            assert ax_dist is not None, "Distribution axis not created properly."
            plt.subplots_adjust(hspace=0.07)
            ax_dist.tick_params(axis='x', labelsize=13)
            ax_dist.tick_params(axis='y', labelsize=12)

        ax.grid(True)

            

        scatter = ax.scatter(
            x=[x for x, y, size in clustered_datapoints],
            y=[y for x, y, size in clustered_datapoints],
            s=[size * 10 for x, y, size in clustered_datapoints],  # Scale bubble size
            alpha=0.40,
            edgecolors='none'
        )

        # Don't label the type scatter if we're only showing type, to avoid confusion in the legend. We can add a label for the type filter in the title instead.
        if by=="All" or by=="All_Under_20":
            scatter_type = ax.scatter(
                x=[x for x, y, size in clustered_datapoints_type],
                y=[y for x, y, size in clustered_datapoints_type],
                s=[size * 10 for x, y, size in clustered_datapoints_type],  # Scale bubble size
                alpha=0.7,
                color=color_type,
                label='Same Type',
                edgecolors='none'
            )
        else:
            scatter_type = ax.scatter(
                x=[x for x, y, size in clustered_datapoints_type],
                y=[y for x, y, size in clustered_datapoints_type],
                s=[size * 10 for x, y, size in clustered_datapoints_type],  # Scale bubble size
                alpha=0.7,
                color=color_type
                )

        # Plot a red line for average for all teas
        avg_rating = np.mean([x for x, y, size in clustered_datapoints])
        ax.axvline(avg_rating, color='red', linestyle='--', label=f'Average ({ScoreConverter.score_to_letter(avg_rating)})')

        # Plot a faint green line quadratic curve for average price percentile by rating (trendline)
        if len(clustered_datapoints) > 2:
            z = np.polyfit([x for x, y, size in clustered_datapoints], [y for x, y, size in clustered_datapoints], 2)
            p = np.poly1d(z)
            x_trend = np.linspace(0, 5, 100)
            # Cut off the trendline at the max rating in the data to avoid extrapolation beyond the data range
            max_rating_in_data = max([x for x, y, size in clustered_datapoints]) + 0.25 # Add a small buffer to the max rating for better visualization of the trendline endpoint
            min_rating_in_data = min([x for x, y, size in clustered_datapoints]) - 0.25 # Add a small buffer to the min rating for better visualization of the trendline startpoint
            x_trend = np.linspace(min_rating_in_data, max_rating_in_data, 100)
            # clamp at 0 and 5
            x_trend = np.clip(x_trend, 0, 5)
            col_faint_green = (0.0, 0.5, 0.0, 0.3)  # RGBA with alpha for faintness
            ax.plot(x_trend, p(x_trend), color=col_faint_green, linestyle='-', label='Price Trend')

        type_legend = ax.legend(
            loc='lower left',
            frameon=True
        )
        ax.add_artist(type_legend)
        # If we have a this_review_point, plot it distinctly with red
        if this_review_point:
            ax.scatter(
                x=[this_review_point[0]],
                y=[this_review_point[1]],
                s=150,
                color='red',
                label='This Tea',
                edgecolors='black'
            )

        # Larger font
        if not INCLUDE_BACKGROUND_DISTRIBUTION:
            ax.set_xlabel("Rating", fontsize=14)

        by_text = f"ALL"
        if by == "Type":
            by_text = f"{thisTea.tea_type}"
        elif by == "Vendor":
            by_text = f"{thisTea.vendor}"
        ylabel = "Price Percentile" if by in ["All", "All_Under_20"] else f"Price Percentile ({by_text})"
        ax.set_ylabel(ylabel, fontsize=14)
        ax.set_title("")
        # Create size legend instead of colorbar
        # Round max size to nearest 10 for cleaner legend        
        max_size_rounded = math.ceil(max_size / 10) * 10
        legend_sizes = [
            max_size_rounded,
            max_size_rounded // 2,
            max(1, max_size_rounded // 4),
        ]

        sizes = [size for x, y, size in clustered_datapoints]
        Logger.info(f"Cluster sizes in data: min={min(sizes) if sizes else 0}, max={max(sizes) if sizes else 0}, avg={np.mean(sizes) if sizes else 0:.2f}")

        legend_handles = [
            ax.scatter(
                [], [],
                s=size * legendSizeMultiplier,  # Scale legend bubble size
                edgecolors="black",
                facecolors="none"
            )
            for size in legend_sizes
        ]

        legend_labels = [f"{str(int(size))} teas" for size in legend_sizes]

        ax.legend(
            legend_handles,
            legend_labels,
            title="Cluster size",
            scatterpoints=1,
            frameon=True,
            labelspacing=1.2,
            loc="lower right"
        )

        # Custom X axis label for letter grades
        ax.set_xticks([0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.0])
        ax.set_xticklabels(['F', 'D', 'C', 'B', 'A', 'S', 'S+'])
        ax.set_xlim(0.0, 5.25)
        ax.tick_params(axis='x', labelsize=13) # Change x-axis tick font size
        
        # Custom Y axis ticks, 0, 25, 50, 75, 100 with labels
        # Get data for these percentiles to show as horizontal lines
        percentile_data = StatsService.get_report_image_1_percentile_data(data_manager.stash.teas, by=by, thisTea=thisTea)
        yticklabels = []
        for pct, price in percentile_data:
            yticklabels.append(f"{int(pct)}%\n${price:.2f}/g")
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_yticklabels(yticklabels)
        ax.tick_params(axis='y', labelsize=12) # Change y-axis tick font size

        # Vertical grid lines should be removed to reduce clutter, horizontal grid lines can stay
        plt.grid(True)
        # put xaxis labels on top to make them more visible without vertical grid lines
        ax.tick_params(axis='x', which='both', bottom=False, top=True, labeltop=True, labelbottom=False)
        #ax.xaxis.grid(False)
        #ax.yaxis.grid(True)
        #ax.grid(axis="y", linestyle="--", alpha=0.4)
        #ax.grid(axis="x", linestyle=":", alpha=0.2)
        
        temp_path = f"{Config.DATA_DIR}/tmp/report_comparison1.png"
        plt.savefig(temp_path, bbox_inches='tight', dpi=100)
        plt.close(fig)
        return temp_path

    @staticmethod
    def generate_tierlist_for_vendor(data_manager, thisVendor, highlight_recent_review=True):


        Logger.info(f"Generating tier list for vendor: {thisVendor}")
        # We can use a similar approach to the bubble chart but categorize teas into tiers (S, A, B, C, D, F) based on rating and price percentile
        # Then we can create a visual tier list with teas placed in their respective tiers along with their names and prices.
        teas_only_this_vendor = [t for t in data_manager.stash.teas if t.vendor == thisVendor and t.average_rating is not None and t.catalog_price_per_gram is not None]
        
        # Exclude teas without reviews.
        teas_only_this_vendor = [t for t in teas_only_this_vendor if t.reviews]
        if not teas_only_this_vendor:
            Logger.warning(f"No teas found for vendor {thisVendor} with complete data for tier list.")
            return None
        
        # Sort in-place by rating (highest first) and then by price (lowest first)
        teas_only_this_vendor.sort(key=lambda t: (t.average_rating, -t.catalog_price_per_gram), reverse=True)

        # Highlight most recent review if flag is set
        most_recent_review = None
        if highlight_recent_review:
            most_recent_review = max(
                (rev for tea in teas_only_this_vendor for rev in tea.reviews),
                key=lambda r: pd.to_datetime(r.date),
                default=None
            )
            if most_recent_review:
                Logger.info(f"Most recent review date: {most_recent_review.date}")
            else:
                Logger.info("No reviews found to highlight.")
        
        # we want to create a blank image, then draw tier sections (S, A, B, C, D, F) and place teas in the appropriate section based on their rating and price percentile
        # Each tea should have the name, price per gram and rating displayed. Do not use percentile

        # Strip acronyms from vendor name for cleaner display
        thisVendorDisplay = thisVendor
        strippedAcronyms = []
        if "Jesse" in thisVendorDisplay:
            strippedAcronyms.append("JTH")

        # Fast tally all tiered teas to know how many we have in each tier for spacing purposes
        tiers_base_flat = ["S", "A", "B", "C", "D", "F"]
        tiers_base_expanded = ScoreConverter.LETTER_GRADE_MAP.keys()
        tiers = tiers_base_flat
        tierlist_colors = {
            "S": "#cc6666",   # muted red
            "A": "#d9a066",   # muted orange
            "B": "#d9c266",   # muted gold
            "C": "#d9d966",   # muted yellow
            "D": "#99cc99",   # muted light green
            "F": "#66a366"    # muted green
        }
        num_per_tier_spacing = {tier: 0 for tier in tiers_base_expanded}
        for tea in teas_only_this_vendor:
            tier_flat = tea.tier_rating_flat
            if tier_flat in num_per_tier_spacing:
                num_per_tier_spacing[tier_flat] += 1


        max_tier_size = max(num_per_tier_spacing.values()) if num_per_tier_spacing else 0
        use_expanded_tiers = False
        if max_tier_size > 16:
            use_expanded_tiers = True
            tiers = tiers_base_expanded
            num_per_tier_spacing = {tier: 0 for tier in tiers_base_expanded}

        base_height_per_tier = 120  # Base height per tier, will multiply by number of tiers plus extra for vendor header
        num_rows = len(tiers) + 1  # Number of tiers (S, A, B, C, D, F) + 1 for vendor header
        base_height = base_height_per_tier * num_rows  # Base height based on number of tiers plus extra for vendor header

        Logger.info(f"Max tier size for vendor {thisVendor}: {max_tier_size}, tier distribution: {num_per_tier_spacing}")
        print(f"Using {'expanded' if use_expanded_tiers else 'flat'} tiers for vendor {thisVendor} based on max tier size.")

        # Create blank image
        xpadding = 100
        base_width = max(800, (max_tier_size * base_height_per_tier) + (2 * xpadding))  # Base width or enough to fit all teas in the largest tier with padding
        font = ImageFont.truetype("arial.ttf", 13)
        font2 = ImageFont.truetype("arial.ttf", 15)
        font_larger = ImageFont.truetype("arial.ttf", 28)
        font_large = ImageFont.truetype("arial.ttf", 40)
        img = Image.new("RGB", (base_width, base_height), color="white")
        draw = ImageDraw.Draw(img)

        # Draw tier sections
        box_dim = base_height_per_tier  # Height of the box for each tea, with some padding
        
        num_per_tier = {tier: 0 for tier in tiers}
        # Draw the first row for the vendor name
        draw.rectangle([0, 0, base_width, base_height_per_tier], outline="black", fill="lightgray", width=2)
        draw.text((30, 30), f"Vendor: {thisVendorDisplay}", fill="black", font=font_larger)
        draw.text((30, 70), f"Total teas: {len(teas_only_this_vendor)}", fill="black", font=font2)
        draw.text((30, 95), f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d')}", fill="black", font=font2)

        # Sample indicator for number of reviews per tea in a circle
        draw.ellipse([base_width - 180, 40, base_width - 150, 70], outline="black", fill="lightblue")
        draw.text((base_width - 210, 18), f"ex: # Reviews", fill="black", font=font2)
        draw.text((base_width - 168, 47), "4", fill="black", font=font2)
        if highlight_recent_review and most_recent_review:
            # Draw red star example
            cx = base_width - 80
            cy = 55
            star_points = create_star(cx, cy, outer_radius=16, inner_radius=6)
            draw.polygon(star_points, fill="firebrick", outline="black", width=1)
            draw.text((base_width - 140, 80), f"ex: Most recent", fill="black", font=font2)
        
        r = 1
        for tier in tiers:
            col = tierlist_colors.get(tier[0], "lightgray")
            draw.rectangle([0, r * base_height_per_tier, base_width, (r + 1) * base_height_per_tier], outline="black", fill=col, width=2)
            draw.text((40, r * base_height_per_tier + 40), tier, fill="black", font=font_large)
            r += 1

        # Place teas in their respective tiers
        for tea in teas_only_this_vendor:
            tea: Tea
            # Determine tier based on rating
            tier, tier_flat = tea.tier_rating, tea.tier_rating_flat
            if use_expanded_tiers:
                tier_flat = tier

            # Get the tier's y-coordinate
            tier_idx = list(tiers).index(tier_flat)+1  # +1 to account for vendor row
            y = tier_idx * base_height_per_tier
            num_per_tier[tier_flat] += 1

            x = xpadding + ((num_per_tier[tier_flat] - 1) * box_dim)  # Space out teas horizontally within the tier

            # Draw tea information
            teaname = tea.name_no_year
            teayear = tea.year
            teaname = teaname.replace(thisVendor, "").strip()  # Remove vendor name from tea name for cleaner display
            for acronym in strippedAcronyms:
                teaname = teaname.replace(acronym, "").strip()  # Remove any other common acronyms
            # Strip out name of type of tea if it's in the name since we already have a separate line for tea type and it can be redundant
            if tea.tea_type and tea.tea_type in teaname:
                teaname = teaname.replace(tea.tea_type, "").strip()

            # Wrap if too long
            if len(teaname) > 12:
                teaname, _ = wrap_text_no_break_words(teaname, width=14)
            if len(teaname) > 24:
                teaname = teaname[:24] + "..."
            draw.text((x+10, y+10), f"{teaname}", fill="black", font=font)
            
            draw.text((x+10, y+10 + box_dim - 80), f"{teayear}", fill="black", font=font2)
            draw.text((x+10, y+10 + box_dim - 60), f"{tier}   ${tea.catalog_price_per_gram:.2f}/g", fill="black", font=font2)
            draw.text((x+10, y+10 + box_dim - 40), f"{tea.tea_type}", fill="black", font=font)
            
            
            # draw a small grey bubble in the box on a corner for number of reviews
            draw.ellipse([x + box_dim - 40, y + 40, x + box_dim - 20, y + 60], outline="black", fill="lightblue")
            draw.text((x + box_dim - 34, y + 43), f"{len(tea.reviews)}", fill="black", font=font2)

            # Draw box around tea name
            draw.rectangle([x, y, x + box_dim, y + box_dim], outline="black", width=1)

            # If this tea has the most recent review, draw a red star on it
            if highlight_recent_review and most_recent_review and any(rev for rev in tea.reviews if rev.date == most_recent_review.date):
                cx = x + box_dim - 22   # center near right side of box
                cy = y + box_dim - 22   # center near bottom of box

                star_points = create_star(cx, cy, outer_radius=16, inner_radius=6)
                draw.polygon(star_points, fill="firebrick", outline="black", width=1)

        # Draw vertical line to separate tea boxes from tier labels
        draw.line((xpadding, box_dim, xpadding, base_height), fill="black", width=2)

        # Save image to path
        current_dt_str = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = f"tierlist_{thisVendor.replace(' ', '_')}_{current_dt_str}.png"
        img.save(save_path)

    @staticmethod
    def template_generate_placeholder_chart(path: str):
        """Create and save a placeholder matplotlib chart."""
        fig, ax = plt.subplots(figsize=(8, 10))
        ax.text(0.5, 0.5, "Report Image Placeholder", fontsize=24, ha='center')
        ax.axis("off")
        plt.savefig(path, bbox_inches='tight', dpi=100)
        plt.close(fig)

    @staticmethod
    def template_generate_report_image_placeholder(width=800, height=1000):
        Logger.info("Report image generation placeholder called.")

        import os

        report_shorthand = "placeholder"
        tmp_dir = f"{Config.DATA_DIR}/tmp"
        os.makedirs(tmp_dir, exist_ok=True)

        placeholder_path = f"{tmp_dir}/report_placeholder_{report_shorthand}.png"
        final_path = f"./report_{report_shorthand}_{pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"

        # Generate placeholder chart (ONLY if needed)
        if not os.path.exists(placeholder_path):
            ReportService.template_generate_placeholder_chart(placeholder_path)

        # Composite final image
        img = Image.new("RGB", (width, height), color="white")

        placeholder_img = Image.open(placeholder_path)
        img.paste(placeholder_img, (0, 0))

        img.save(final_path)

        return final_path
    
    @staticmethod
    def generate_cost_per_gram_over_time_reviews_report(datamanager, width=800, height=600):
        Logger.info("Generating cost per gram over time report.")
    
        report_shorthand = "cpg_over_time_type"
        tmp_dir = f"{Config.DATA_DIR}/tmp"
        os.makedirs(tmp_dir, exist_ok=True)
    
        placeholder_path = f"{tmp_dir}/report_placeholder_{report_shorthand}.png"
        final_path = f"./report_{report_shorthand}_{pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
    
        # -------------------------
        # Flatten data
        # -------------------------
        rows = []
    
        for tea in datamanager.teas:
            if tea.quantity == 0:
                continue
                
            for r in tea.reviews:
                if r.amount_drunk <= 0:
                    continue
                
                rows.append({
                    "date": pd.to_datetime(r.date),
                    "tea_type": tea.tea_type,
                    "amount": r.amount_drunk,
                    "cpg": tea.catalog_price_per_gram,
                    "session_cost": r.amount_drunk * tea.catalog_price_per_gram
                })
    
        df = pd.DataFrame(rows)
        if df.empty:
            raise ValueError("No valid review data to plot.")
    
        df = df.sort_values("date")

        # total spend per tea type
        type_totals = df.groupby("tea_type")["session_cost"].sum()

        # keep only meaningful ones
        top_types = type_totals[type_totals > type_totals.sum() * 0.02].index  # 2% threshold

        df["tea_type_grouped"] = df["tea_type"].where(
            df["tea_type"].isin(top_types),
            "Other"
        )
        # debug print all sums
        Logger.info("Total spend by tea type:")
        for tea_type, total in type_totals.items():
            Logger.info(f"  {tea_type}: ${total:.2f}")
        Logger.info(f"  Other: ${type_totals[~type_totals.index.isin(top_types)].sum():.2f}")
        Logger.info(f"  Total: ${type_totals.sum():.2f}")
    
        # -------------------------
        # Monthly % spend by tea type
        # -------------------------
        df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    
        monthly = df.groupby(["month", "tea_type_grouped"])["session_cost"].sum().reset_index()
    
        total_monthly = monthly.groupby("month")["session_cost"].sum().reset_index()
        total_monthly = total_monthly.rename(columns={"session_cost": "total"})
    
        monthly = monthly.merge(total_monthly, on="month")
        monthly["pct"] = 100 * monthly["session_cost"] / monthly["total"]
    
        pivot = monthly.pivot(index="month", columns="tea_type_grouped", values="pct").fillna(0)
        pivot.index = pivot.index + pd.offsets.Day(15)
        pivot = pivot[pivot.mean().sort_values(ascending=False).index]
        pivot = pivot.rolling(2).mean()
    
        # -------------------------
        # Rolling 30-day avg $/g
        # -------------------------
        df["weighted_cpg"] = df["cpg"] * df["amount"]
    
        df = df.set_index("date").sort_index()

        rolling = (
            (df["cpg"] * df["amount"]).rolling("30D", min_periods=5).sum() /
            df["amount"].rolling("30D", min_periods=5).sum()
        )

        rolling = rolling.dropna()
    
        # -------------------------
        # Plot
        # -------------------------
        fig, ax1 = plt.subplots(figsize=(18, 10))

        # Move other to end if it exists
        cols = list(pivot.columns)
        if "Other" in cols:
            cols.remove("Other")
            cols.append("Other")

        pivot = pivot[cols]
    
        # Stacked area
        ax1.stackplot(
            pivot.index,
            pivot.values.T,
            labels=pivot.columns,
            colors=[TEA_TYPE_COLOR_MAP.get(x, "#9E9E9E") for x in pivot.columns],
            linewidth=0.5
        )
    
        ax1.set_ylim(0, 100)
        start = pivot.index.min()
        end = pivot.index.max() + pd.offsets.MonthEnd(1)

        ax1.set_xlim(start, end)
        ax1.margins(x=0)
        ax1.set_ylabel("Percent of Spend, Drinking (%)")
        ax1.set_title("Tea Spend Composition + Rolling Cost")

        ax1.legend(
        labels=[trim_label(l) for l in pivot.columns],
        loc="center left",
        bbox_to_anchor=(1.08, 0.5),
        borderaxespad=0,
        frameon=False
        )
    
        # Secondary axis for rolling cost
        ax2 = ax1.twinx()
        line = ax2.plot(
            rolling.index,
            rolling.values,
            linewidth=2.5,
            color="red",
        )[0]

        line.set_path_effects([
            pe.Stroke(linewidth=5, foreground='white'),
            pe.Normal()
        ])
        ax2.set_ylabel("Cost ($/g, 30D rolling avg)")

        ax2.yaxis.set_major_formatter(
            FuncFormatter(lambda x, pos: f"${x:.2f}/g")
        )
    
        # Get size of image in width and height
        width, height = fig.get_size_inches() * fig.dpi
        # convert numpy.float64 to int for width and height
        width = int(width)
        height = int(height)

        plt.subplots_adjust(top=0.95, left=0.05, bottom=0.1, right=0.82)  # Adjust to make room for legend
        plt.savefig(placeholder_path, dpi=100)
        plt.close(fig)
    
        # -------------------------
        # Composite image
        # -------------------------
        img = Image.new("RGB", (width, height + 20), color="white")
        placeholder_img = Image.open(placeholder_path)
        xoffset = 15
        yoffset = 15
        draw = ImageDraw.Draw(img)
        tag_font = ImageFont.truetype("arial.ttf", 24)
        tag_font_body = ImageFont.truetype("arial.ttf", 18)
        # Black
        tag_color = (0, 0, 0)
        draw.text((xoffset, yoffset), "Tea Spend Analysis", font=tag_font, fill=tag_color)
        yoffset += 30

        draw.text((xoffset, yoffset), "This chart shows the composition of your tea spending over time by tea type, along with a rolling average of cost per gram.", font=tag_font_body, fill=tag_color)
        yoffset += 20

        img.paste(placeholder_img, (xoffset-10, yoffset))
        img.save(final_path)
    
        return final_path
    
    @staticmethod
    def generate_cu_stashed_by_type_report(data_manager):
        """Generate a stacked area chart showing absolute grams of each tea type
        remaining in the stash over time, factoring in purchases, consumption,
        and adjustments.

        Returns: path to the saved PNG image, or None if no data.
        """
        Logger.info("Generating cumulative stash-by-type report.")

        teas: list[Tea] = data_manager.stash.teas

        # ------------------------------------------------------------------
        # 1. Build a timeline of events (purchase, review consumption,
        #    adjustment) for every tea, keyed by date.
        # ------------------------------------------------------------------
        events = []  # list of (date, type, delta_grams)

        for tea in teas:
            inv = round(tea.quantity, 2)
            ttype = tea.tea_type if tea.tea_type else "Unknown"

            if tea.quantity > 0:
                events.append((pd.to_datetime(tea.purchaseDate), ttype, round(tea.quantity, 2)))

            for rev in tea.reviews:
                events.append((pd.to_datetime(rev.date), ttype, -rev.amount_drunk))
                inv -= round(rev.amount_drunk, 2)

            for adj in tea.adjustments:
                if hasattr(adj, 'date') and adj.date:
                    events.append((pd.to_datetime(adj.date), ttype, round(adj.amount, 2)))
                else:
                    # Place the adjustment 1 week after the most recent review or purchase to ensure it appears in the timeline, since we don't have an exact date for it. This is a bit of a hack but allows us to include adjustments without losing them.
                    if tea.reviews:
                        latest_review_date = max(pd.to_datetime(rev.date) for rev in tea.reviews)
                        adj_date = latest_review_date + pd.Timedelta(days=7)
                    else:
                        adj_date = pd.to_datetime(tea.purchaseDate) + pd.Timedelta(days=7)
                    events.append((adj_date, ttype, -round(adj.amount, 2)))  # Assuming adj.amount is positive for additions and negative for removals, we negate it here to reflect the actual change in inventory
                    inv -= round(adj.amount, 2)  # Adjust inventory for the sake of any subsequent adjustments

            # Print quantity sanity check for this tea
            #if inv != tea.remaining:
            #    print(f"Tea: {tea.name}, Final Inventory after reviews and adjustments: {inv}g (Initial: {tea.quantity}g). Tea info remaining: {tea.remaining}g")

            

        if not events:
            Logger.warning("No stash events found — nothing to plot.")
            return None
        
        print(f"[CHART] Number of events: {len(events)}, Sum of all deltas: {sum(delta for _, _, delta in events):.2f}g")
        print(f"[CHART] Event types and counts: {pd.Series([etype for _, etype, _ in events]).value_counts().to_dict()}")
        print(f"[CHART] Date range: {min(date for date, _, _ in events).date()} to {max(date for date, _, _ in events).date()}")
        lastMonth = pd.Timestamp.now() - pd.Timedelta(days=30)
        last6Months = pd.Timestamp.now() - pd.Timedelta(days=182)
        lastYear = pd.Timestamp.now() - pd.Timedelta(days=365)
        print(f"[CHART] Delta of last month: {sum(delta for date, _, delta in events if date >= lastMonth):.2f}g")
        print(f"[CHART] Delta of last 6 months: {sum(delta for date, _, delta in events if date >= last6Months):.2f}g")
        print(f"[CHART] Delta of last year: {sum(delta for date, _, delta in events if date >= lastYear):.2f}g")

        df_events = pd.DataFrame(events, columns=["date", "type", "delta"])
        df_events = df_events.sort_values("date").reset_index(drop=True)

        # ------------------------------------------------------------------
        # 2. Build daily running total per tea type.
        # ------------------------------------------------------------------
        start_date = df_events["date"].min().floor("D")
        end_date = df_events["date"].max().floor("D")

        all_types = sorted(df_events["type"].unique())
        daily_idx = pd.date_range(start_date, end_date, freq="D")
        
        # Collapse all events occurring on the same day
        daily_changes = (
           df_events.assign(date=df_events["date"].dt.floor("D"))
           .pivot_table(
               index="date",
               columns="type",
               values="delta",
               aggfunc="sum",
               fill_value=0.0,
           )
           .reindex(columns=all_types, fill_value=0.0)

        )
        # Ensure every day exists
        daily_changes = daily_changes.reindex(daily_idx, fill_value=0.0)
        
        # Running stash total
        zero_df = daily_changes.cumsum()
        
        # Remove types that never have any inventory
        final_amounts = zero_df.iloc[-1]

        active_types = (
            final_amounts.sort_values(ascending=False)
            .index
            .tolist()
        )

        zero_df = zero_df[active_types]

        # ------------------------------------------------------------------
        # 3. Stable colour palette per tea type.
        # ------------------------------------------------------------------
        colors = [TEA_TYPE_COLOR_MAP.get(t, "#9E9E9E") for t in active_types]

        # ------------------------------------------------------------------
        # 4. Stacked area chart (absolute grams, not %).
        # ------------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(30, 15))

        ax.stackplot(
            zero_df.index,
            zero_df.values.T,
            labels=active_types,
            colors=colors,
            linewidth=0.5,
        )

        ax.set_ylabel("Grams Remaining")
        ax.set_title("Cumulative Stash by Tea Type Over Time")


        handles, labels = ax.get_legend_handles_labels()

        ax.legend(
            handles[::-1],
            labels[::-1],
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
        )

        ax.grid(True, alpha=0.3)
        ax.set_xlim(zero_df.index.min(), zero_df.index.max())
        ax.margins(x=0)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}g"))

        # ------------------------------------------------------------------
        # 5. Save and return.
        # ------------------------------------------------------------------
        current_dt_str = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = f"stash_by_type_{current_dt_str}.png"

        plt.tight_layout()
        plt.savefig(save_path, dpi=100)
        plt.close(fig)

        Logger.info(f"Saved stash-by-type report to {save_path}")
        return save_path


def draw_tag_value(draw, x, y, tag, value, tag_font, value_font, tag_color=(80, 80, 80), value_color="black"):
    """Helper to draw a tag and value pair on an image at specified coordinates."""
    # Draw tag
    draw.text((x, y), tag, font=tag_font, fill=tag_color)
    # Measure tag width
    bbox = draw.textbbox((x, y), tag, font=tag_font)
    tag_width = bbox[2] - bbox[0]
    if tag_font != value_font:
        tag_width += 10  # Small padding if fonts differ
        y += 4   # Adjust y slightly for visual alignment
    # Draw value immediately after tag
    draw.text((x + tag_width, y), value, font=value_font, fill=value_color)



def create_star(cx, cy, outer_radius, inner_radius, points=5):
    star_points = []
    angle = math.pi / 2  # start at top

    step = math.pi / points  # half step (outer → inner)

    for i in range(points * 2):
        if i % 2 == 0:
            r = outer_radius
        else:
            r = inner_radius

        x = cx + r * math.cos(angle)
        y = cy - r * math.sin(angle)
        star_points.append((x, y))

        angle += step

    return star_points

def trim_label(label, max_len=14):
    return label if len(label) <= max_len else label[:max_len-1] + "…"