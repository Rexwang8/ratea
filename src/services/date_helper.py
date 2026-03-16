import datetime as dt

def parse_flexible_date(date_val):
    """
    Handles: 
    1. Floats/Ints (Timestamps)
    2. Strings (ISO format)
    3. None/Empty
    """
    if not date_val:
        return dt.datetime.now()

    # Case 1: Already a number or looks like one
    try:
        return dt.datetime.fromtimestamp(float(date_val))
    except (ValueError, TypeError):
        pass # Not a number, try string parsing

    # Case 2: ISO String (e.g. '2025-05-21 22:57:10...')
    if isinstance(date_val, str):
        try:
            # This handles most standard formats including the one in your error
            # We strip the timezone info for basic compatibility if needed
            clean_str = date_val.split('+')[0].strip()
            return dt.datetime.fromisoformat(clean_str)
        except ValueError:
            # Fallback for other formats if necessary
            return dt.datetime.now()

    return dt.datetime.now()

def datetime_to_dearpygui_dt(dt_obj):
    """Convert a datetime object to a timestamp for DearPyGui."""
    if isinstance(dt_obj, dt.datetime):
        #value={'month_day': 8, 'year':93, 'month':5})
        year = dt_obj.year - 1900  # DearPyGui expects years since 1900
        dtobj = {
            "month_day": dt_obj.day,
            "month": dt_obj.month-1, 
            "year": year,
        }
        print(f"Converted datetime {dt_obj} to DearPyGui format: {dtobj}")
        return dtobj
    else:
        print(f"Warning: Expected datetime object, got {type(dt_obj)}. Returning default date.")
        return {
            "month_day": 1,
            "month": 1,
            "year": 0
        }
    
def dearpygui_dt_to_datetime(dp_dt):
    """Convert a DearPyGui date dictionary back to a datetime object."""
    try:
        year = dp_dt.get("year", 0) + 1900  # Convert back to full year
        month = dp_dt.get("month", 1)+1  # DearPyGui months are 0-indexed
        day = dp_dt.get("month_day", 1)
        return dt.datetime(year, month, day)
    except Exception as e:
        print(f"Error converting DearPyGui date to datetime: {e}. Returning current datetime.")
        return dt.datetime.now()