# src/ui/analytics_tab.py
import dearpygui.dearpygui as dpg
import pandas as pd


def draw_analytics_tab(data_manager):
    with dpg.collapsing_header(label="Water Consumption Analytics", default_open=True):
        draw_water_analytics(data_manager)
    

def draw_water_analytics(data_manager):
    total, df, df_review = data_manager.water_stats
    average = total / len(df) if len(df) > 0 else 0

    # Only calculate averages if at least 2 reviews exist to avoid division by zero and meaningless averages
    average_monthly = 0
    average_daily = 0
    average_last_full_month = 0

    if not df_review.empty and len(df_review) > 1:
        average_monthly = total / ((df_review['Date'].max() - df_review['Date'].min()).days / 30.44) if not df_review.empty else 0
        average_daily = total / ((df_review['Date'].max() - df_review['Date'].min()).days) if not df_review.empty else 0
        average_last_full_month = df_review[df_review['Date'] >= (df_review['Date'].max() - pd.DateOffset(months=1))]['WaterAmount'].sum() if not df_review.empty else 0

    with dpg.group():
        total_liters = total / 1000
        average_liters = average / 1000
        average_monthly_liters = average_monthly / 1000
        average_daily_liters = average_daily / 1000
        average_last_full_month_liters = average_last_full_month / 1000

        dpg.add_text(f"Total Water Consumed: {total_liters:.2f} Liters", color=(100, 200, 255))
        dpg.add_text(f"Average Water per Tea: {average_liters:.2f} Liters", color=(100, 200, 255))
        dpg.add_text(f"Average Monthly Water: {average_monthly_liters:.2f} Liters", color=(100, 200, 255))
        dpg.add_text(f"Average Daily Water: {average_daily_liters:.2f} Liters", color=(100, 200, 255))
        dpg.add_text(f"Average Water Last Full Month: {average_last_full_month_liters:.2f} Liters", color=(100, 200, 255))

        with dpg.plot(label="Water by Tea", width=-1, height=600):
            x_ticks = [[df.iloc[i]["Name"], i] for i in range(len(df))]
            
            dpg.add_plot_axis(dpg.mvXAxis, label="Tea Name")
            dpg.set_axis_ticks(dpg.last_item(), x_ticks)
            
            with dpg.plot_axis(dpg.mvYAxis, label="mL"):
                total_water = [0] * len(df)
                if not df.empty:
                    total_water = df["TotalWater"].tolist()

                dpg.add_bar_series(list(range(len(df))), total_water)