# src/ui/analytics_tab.py
import dearpygui.dearpygui as dpg
import pandas as pd
from services.stats_service import StatsService
import dearpypixl as dp
from services.score_converter import ScoreConverter
from services.logger import Logger

def draw_dashboard_tab(data_manager):
    with dpg.collapsing_header(label="Stash by Type/Vendor", default_open=False):
        dash2 = Dashboard_Stash_TypeVendor(data_manager)
        dash2.render()

    with dpg.collapsing_header(label="Dashboard Charts", default_open=False):
        with dpg.group(horizontal=True):
            
            draw_charts_2_price_vs_ratings(data_manager)
            draw_charts_3_price_percentile_vs_ratings(data_manager)
        draw_charts_1(data_manager)

def draw_charts_1(data_manager):
        total_width = dpg.get_viewport_width() - 50
        total_height = dpg.get_viewport_height() - 100
        num_charts_x = 2
        chart_width = total_width // num_charts_x
        chart_height = total_height // 2
        x_data, y_data, x_labels, y_labels = StatsService.get_consumption_plot_data(data_manager.stash.returnTeas())
        with dpg.plot(label="Grams Consumed Over Time", height=chart_height, width=chart_width):
            # Legend
            dpg.add_plot_legend()
            # X-Axis (Time)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Date", tag="x_axis")
            dpg.set_axis_ticks(dpg.last_item(), x_labels)
            # Add custom ticks for better readability
            
            # Y-Axis (Grams)
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Grams", tag="y_axis")
            #dpg.set_axis_ticks(y_axis, y_labels)

            # Add the actual data (Line Series or Bar Series)
            dpg.add_line_series(x_data, y_data, label="Monthly Total", parent=y_axis)
            #dpg.add_bar_series(x_data, y_data, label="Monthly Total", parent=y_axis, weight=-1)
            # Auto-fit the axes to the data
            dpg.fit_axis_data(x_axis)
            dpg.fit_axis_data(y_axis)

        # Additional charts can be added here following the same pattern

def draw_charts_2_price_vs_ratings(data_manager):
        total_width = dpg.get_viewport_width() - 50
        total_height = dpg.get_viewport_height() - 100
        num_charts_x = 2
        chart_width = total_width // num_charts_x
        chart_height = total_height // 2
        x_data, y_data, sizes = StatsService.get_rating_distribution_data(data_manager.stash.returnTeas())
        chart_tag_uuid = dpg.generate_uuid()

        with dpg.plot(label="Prices vs Letter Grade", height=chart_height, width=chart_width):
            # Legend
            dpg.add_plot_legend()
            # X-Axis (Average Rating)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Average Rating", tag=f"x_axis_{chart_tag_uuid}")
            rating_map = ScoreConverter.LETTER_GRADE_MAP_DPG_LABELS

            # MUST BE SET TO [x, y] format for DPG to recognize the tick positions correctly
            # MUST USE A LIST of 2 ELEMENT LISTS for DPG to recognize the tick labels correctly (one for labels, one for positions)
            if rating_map:
                dpg.set_axis_ticks(x_axis, rating_map)
            dpg.set_axis_limits(x_axis, 0, 5)
            
            # Y-Axis (Price)
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Price ($/g)", tag=f"y_axis_{chart_tag_uuid}")
            #dpg.set_axis_limits(y_axis, 0, 100)

            # Add the actual data (Scatter Series with variable point sizes)
            dpg.add_scatter_series(x_data, y_data, label="Teas", parent=y_axis, weight=-1, size=sizes)

             # Auto-fit the axes to the data
            dpg.fit_axis_data(x_axis)
            dpg.fit_axis_data(y_axis)

def draw_charts_3_price_percentile_vs_ratings(data_manager):
        total_width = dpg.get_viewport_width() - 50
        total_height = dpg.get_viewport_height() - 100
        num_charts_x = 2
        chart_width = total_width // num_charts_x
        chart_height = total_height // 2
        x_data, y_data, sizes = StatsService.get_price_percentile_distribution_data(data_manager.stash.returnTeas())
        chart_tag_uuid = dpg.generate_uuid()

        with dpg.plot(label="Price Percentile vs Letter Grade", height=chart_height, width=chart_width):
            # Legend
            dpg.add_plot_legend()
            # X-Axis (Average Rating)
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Average Rating", tag=f"x_axis_{chart_tag_uuid}")
            rating_map = ScoreConverter.LETTER_GRADE_MAP_DPG_LABELS

            # MUST BE SET TO [x, y] format for DPG to recognize the tick positions correctly
            # MUST USE A LIST of 2 ELEMENT LISTS for DPG to recognize the tick labels correctly (one for labels, one for positions)
            if rating_map:
                dpg.set_axis_ticks(x_axis, rating_map)
            dpg.set_axis_limits(x_axis, 0, 5)
            
            # Y-Axis (Price Percentile)
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Price Percentile", tag=f"y_axis_{chart_tag_uuid}")
            dpg.set_axis_limits(y_axis, 0, 100)

            # Add the actual data (Scatter Series with variable point sizes)
            dpg.add_scatter_series(x_data, y_data, label="Teas", parent=y_axis, weight=-1, size=sizes)

             # Auto-fit the axes to the data
            dpg.fit_axis_data(x_axis)
            dpg.fit_axis_data(y_axis)

        
    
class Dashboard_Stash_TypeVendor:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        # Specific tags to allow targeted refreshing
        self.table_tag = "summary_table_id"
        self.stats_group_tag = "stats_display_group"

    def render(self):
        """Initial build of the Dashboard UI."""
        total_width = dpg.get_viewport_width() - 50
        total_height = dpg.get_viewport_height() - 100
        chart_width = total_width // 2
        chart_height = total_height // 2

        # --- CHARTS SECTION ---
        with dpg.group(horizontal=True):
            self._draw_chart("Vendor", chart_width, chart_height)
            self._draw_chart("Type", chart_width, chart_height)

        dpg.add_separator()

        # --- STATS SECTION ---
        with dpg.group(tag=self.stats_group_tag):
            self._render_stats_text()

        # --- TABLE SECTION ---
        # Wrapping the table in a child window for scrolling
        with dpg.child_window(label="Type/Vendor Summary", width=-1, height=700):
            with dpg.table(
                header_row=True, 
                resizable=True, 
                policy=dpg.mvTable_SizingFixedFit,
                row_background=True, 
                borders_innerV=True, borders_outerV=True, 
                borders_innerH=True, borders_outerH=True, 
                sortable=True, 
                callback=self._on_sort_click,
                tag=self.table_tag
            ):
                dpg.add_table_column(label="Dimension")
                dpg.add_table_column(label="Label")
                dpg.add_table_column(label="Total Grams")
                dpg.add_table_column(label="Review Count")
                dpg.add_table_column(label="Total Teas")
                dpg.add_table_column(label="Average Rating")

                # Initial data fill
                self._render_table_rows()

            dpg.add_separator()
            # Logger
            Logger.info("Dashboard_Stash_TypeVendor rendered.")

    def _draw_chart(self, dimension, width, height):
        """Helper to draw the two charts."""
        x_data, y_data, x_labels, _ = StatsService.get_bar_chart_grams_data(
            self.data_manager.stash.returnTeas(), 
            dimension_shown=dimension
        )

        x_even, y_even = x_data[::2], y_data[::2]
        x_odd, y_odd = x_data[1::2], y_data[1::2]
        
        with dpg.plot(label=f"Grams by {dimension}", height=height, width=width):
            dpg.add_plot_legend()
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label=dimension)
            dpg.set_axis_ticks(x_axis, x_labels)
            
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Grams", lock_min=True)
            
            with dpg.theme() as even_bar_theme:
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_color(dpg.mvPlotCol_Fill, (100, 200, 100), category=dpg.mvThemeCat_Plots)
            series_even = dpg.add_bar_series(x_even, y_even, parent=y_axis)
            dpg.bind_item_theme(series_even, even_bar_theme)
            with dpg.theme() as odd_bar_theme:
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_color(dpg.mvPlotCol_Fill, (100, 100, 200), category=dpg.mvThemeCat_Plots)

            series_odd = dpg.add_bar_series(x_odd, y_odd, parent=y_axis)
            dpg.bind_item_theme(series_odd, odd_bar_theme)

            dpg.fit_axis_data(x_axis)
            dpg.fit_axis_data(y_axis)

    def _render_stats_text(self):
        """Renders the summary text area."""
        sum_stats = self.data_manager._type_vendor_stats_cache_summary
        dpg.add_text(f"Total Grams: {sum_stats['total_grams']}")
        dpg.add_text(f"Total Reviews: {sum_stats['total_reviews']}")
        dpg.add_text(f"Top Vendor: {sum_stats['top_vendor']} ({sum_stats['top_vendor_amt']}g)")
        dpg.add_text(f"Top Type: {sum_stats['top_type']} ({sum_stats['top_type_amt']}g)")
        dpg.add_text(f"Total Teas: {sum_stats['num_teas']}")
        # ... add remaining stats here

    def _render_table_rows(self):
        """Clears and re-fills table rows based on the current DataFrame state."""
        df_summary = self.data_manager._type_vendor_stats_cache
        
        for index, row in df_summary.iterrows():
            with dpg.table_row(parent=self.table_tag):
                dpg.add_text(row["Dimension"])
                dpg.add_text(row["Label"])
                dpg.add_text(f"{row['Quantity']:.1f}")
                dpg.add_text(f"{int(row['ReviewCount'])}")
                dpg.add_text(f"{int(row['TotalTeasReviewed'])} / {int(row['TotalTeas'])}")
                dpg.add_text(f"{row['AverageRating']:.2f} ({ScoreConverter.score_to_letter(row['AverageRating'])})")

    def _on_sort_click(self, sender, sort_spec):
        if not sort_spec: return

        # DPG provides sort_spec as a list of tuples: [(column_id, direction), ...]
        column_id, direction = sort_spec[0]
        column_name = dpg.get_item_label(column_id)

        # 1. Update the Data (Pandas sorting)
        # Assuming your data_manager.sort_data maps "Total Grams" -> "Quantity", etc.
        self.data_manager.sort_summary_data(column_name, direction > 0)

        # 2. Refresh the UI rows
        # Delete all existing rows (slot 1 is the table body)
        for child in dpg.get_item_children(self.table_tag, slot=1):
            dpg.delete_item(child)
        
        self._render_table_rows()