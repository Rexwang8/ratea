import csv
import datetime as dt
from io import BytesIO
import json
import random
from statistics import stdev
import time
import uuid
import dearpypixl as dp
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import os
import re
from matplotlib import pyplot as plt
import numpy as np
from rich.console import Console as RichConsole
import screeninfo
import yaml
import threading
import pyperclip
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageTk
from thefuzz import fuzz


# From local files
import RateaTexts

# Reminders
'''
TODO: Features: Add in functionality for flags: isRequiredForTea, isRequiredForAll
TODO: Validation: Validate that name and other important fields are not empty
TODO: Features: Fill out or remove review tabs
TODO: Menus: Update settings menu with new settings
TODO: Files: Persistant windows in settings
TODO: fix monitor ui sizing
TODO: Button to re-order reviews and teas based on current view
TODO: save table sort state
TODO: Sold: Support adjustment
TODO: Optional refresh on add tea/ review
TODO: Section off autocalculate functions, account for remaining=0 or naegative values
TODO: review window
TODO: move delete category to popup or add confirmation
TODO: Documentation: Add ? tooltips to everything
TODO: Customization: Add color themes
TODO: Feature: Some form of category migration
TODO: Code: Centralize tooltips and other large texts
TODO: Tables: Non-tea items, like teaware, shipping, etc.
TODO: Category: Write in description for each category role
TODO: Slider for textbox size for notepad, wrap too
TODO: Confirmation window for deleting tea/review
TODO: Optional non-refreshing table updates, limit number of items on first load
TODO: Windows list to manage open windows
TODO: Reset to default buttons
TODO: 1-5 as stars for rating system
TODO: Visualization: Single-tea reports
TODO: Documentation: Write in blog window
TODO: Documentation: Add Image Support to blog window.
TODO: Visualizeation: Pie chart for consumption of amount and types of tea, split over all, over years
TODO: Visualization: Solid fill line graph for consumption of types of tea over years
TODO: Summary: User preference visualization for types of tea, amount of tea, etc.
TODO: File: Import from CSV: Add in functionality to import from CSV
TODO: Optional Override of autocalculated fields
TODO: Adjustments of quantities including sells and purchases
TODO: Highlight color customization
TODO: Make a clean default page for new users
TODO: Alternate calculation methods and a flag for that
TODO: Visualization: Network graph, word cloud, tier list
TODO: Allow copying of table cells on right 
TODO: Some sort of tea linking system, or review linking system.
'''


# ALL - All messages
# INFO - Informational messages that are not errors
# WARNING - Warning messages that may indicate a problem or alteration
# ERROR - Error messages that indicate a problem
# (SUCCESS) - Success messages that indicate a successful operation, minor for operation that is part of a larger operation 
# CRITICAL - Critical error messages that indicate a serious problem that may cause the program to crash
DEBUG_LEVEL = "ERROR"  # ALL, INFO, WARNING, ERROR, CRITICAL

#region Constants

# light green
COLOR_AUTOCALCULATED_TABLE_CELL = (0, 100, 0, 60)
# light red
COLOR_INVALID_EMPTY_TABLE_CELL = (100, 0, 0, 100)
# Red
COLOR_REQUIRED_TEXT = (255, 0, 0, 200)
COLOR_RED_TEXT = (255, 0, 0, 200)
COLOR_LIGHT_RED_TEXT = (255, 0, 0, 150)  # Light red
# green
COLOR_AUTO_CALCULATED_TEXT = (0, 255, 0, 200)
COLOR_GREEN_TEXT = (0, 255, 0, 200)
COLOR_LIGHT_GREEN_TEXT = (0, 255, 0, 150)  # Light green
# blue
COLOR_BLUE_TEXT = (0, 0, 255, 200)
# Light blue
COLOR_LIGHT_BLUE_TEXT = (140, 140, 230, 150)  # Light blue
COLOR_AUTOCALCULATED_2 =  COLOR_LIGHT_BLUE_TEXT  # Light blue for autocalculated fields

CONSTANT_DELAY_MULTIPLIER = 120 # +1frame per X items for the table
#endregion

#region Global Variables
backupThread = False
backupStopEvent = threading.Event()
# Global variables


#region Helpers

richPrintConsole = RichConsole()
terminalConsoleLogs = []

def MakeFilePath(path):
    # Make sure the folder exists
    if not os.path.exists(path):
        os.makedirs(path)
        RichPrintSuccessMinor(f"Made {path} folder")
    else:
        RichPrintWarning(f"{path} folder already exists")
        
def WriteFile(path, content):
    with open(path, "w") as file:
        file.write(content)
    RichPrintSuccessMinor(f"Written {path} to file")
    
def ReadFile(path):
    with open(path, "r") as file:
        RichPrintSuccessMinor(f"Read {path} from file")
        return file.read()

def ListFiles(path):
    return os.listdir(path)

def WriteYaml(path, data):
    with open(path, "w") as file:
        yaml.dump(data, file)
    RichPrintSuccessMinor(f"Written {path} to file")

def ReadYaml(path):
    with open(path, "r") as file:
        RichPrintSuccessMinor(f"Read {path} from file")
        return yaml.load(file, Loader=yaml.FullLoader)
    
def timezoneToOffset(timezone, daylightSaving=False):
    # Convert timezone to offset
    offset = 0
    if timezone == "UTC":
        offset = 0

    # Daylight saving time
    if daylightSaving and timezone != "UTC":
        offset += 1
    return offset


# Function yields the name of the current font and size
def getFontName(size=1, bold=False, fontName=None):
    # Get the current font name and size
    if fontName is None:
        fontName = settings["DEFAULT_FONT"]
    if size == 1:
        if bold:
            return f"{fontName}Bold"
        else:
            return f"{fontName}Regular"
    else:
        if bold:
            return f"{fontName}Bold{size}"
        else:
            return f"{fontName}Regular{size}"
        



def parseDTToStringWithFallback(stringOrDT, fallbackString, quiet=False):
    output = None
    try:
        output = parseDTToString(stringOrDT)
        #if output is not None:
    except Exception as e:
        RichPrintError(f"Failed to parse date string: {stringOrDT}. Error: {e}")
        # If it fails, return the fallback string
        output = fallbackString.strip()
    return output


def parseDTToString(stringOrDT):
    format = settings["DATE_FORMAT"]
    timezone = settings["TIMEZONE"]
    # Parse into datetime
    datetimeobj = None
    if isinstance(stringOrDT, dict) and "year" in stringOrDT and "month" in stringOrDT and "month_day" in stringOrDT:
        datetimeobj = DateDictToDT(stringOrDT)  # Convert dict to datetime object
    if isinstance(stringOrDT, str):
        datetimeobj = dt.datetime.strptime(stringOrDT, format)
    elif isinstance(stringOrDT, dt.datetime):
        datetimeobj = stringOrDT
    else:
        raise ValueError("Input must be a string or datetime object.")

    # Convert to timezone
    timezoneObj = dt.timezone(dt.timedelta(hours=timezoneToOffset(timezone)))
    datetimeobj = datetimeobj.astimezone(timezoneObj)
    return datetimeobj.strftime(format)

def parseDTToStringWithHoursMinutes(stringOrDT):
    # Use consistant format with no slashes or colons
    format = "%Y-%m-%d %H-%M"
    timezone = settings["TIMEZONE"]
    # Parse into datetime
    datetimeobj = None
    if isinstance(stringOrDT, str):
        datetimeobj = dt.datetime.strptime(stringOrDT, format)
    elif isinstance(stringOrDT, dt.datetime):
        datetimeobj = stringOrDT
    else:
        raise ValueError(f"Input must be a string or datetime object., got {type(stringOrDT)}")

    # Convert to timezone
    timezoneObj = dt.timezone(dt.timedelta(hours=timezoneToOffset(timezone)))
    datetimeobj = datetimeobj.astimezone(timezoneObj)
    returnedString = datetimeobj.strftime(format)

    # Clean of spaces, colons
    returnedString = re.sub(r'\s+', ' ', returnedString)
    returnedString = re.sub(r':', '', returnedString)
    returnedString = re.sub(r' ', '', returnedString)
    return returnedString

def parseStringToDT(string, default=None, format=None, silent=False):
    if type(string) is dt.datetime:
        # If it's already a datetime object, return it directly
        return string
    string: str = string.strip()
    fallbackFormats = [
        "%Y-%m-%d",  # YYYY-MM-DD
        "%m-%d-%Y",  # MM-DD-YYYY
        "%d-%m-%Y",  # DD-MM-YYYY
        "%Y/%m/%d",  # YYYY/MM/DD
        "%m/%d/%Y",  # MM/DD/YYYY
        "%d/%m/%Y",  # DD/MM/YYYY
        "%Y-%m-%d %H:%M",  # YYYY-MM-DD HH:MM (with time)
        "%m-%d-%Y %H:%M",  # MM-DD-YYYY HH:MM (with time)
        "%d-%m-%Y %H:%M",  # DD-MM-YYYY HH:MM (with time)
        "%Y/%m/%d %H:%M",  # YYYY/MM/DD HH:MM (with time)
        # With HMS
        "%Y-%m-%d %H:%M:%S",  # YYYY-MM-DD HH:MM:SS
        "%m-%d-%Y %H:%M:%S",  # MM-DD-YYYY HH:MM:SS
        "%d-%m-%Y %H:%M:%S",  # DD-MM-YYYY HH:MM:SS
        "%Y/%m/%d %H:%M:%S",  # YYYY/MM/DD HH:MM:SS
    ]

    if format is None:
        format = settings["DATE_FORMAT"]

    if type(string) is dt.datetime:
        # If it's already a datetime object, return it directly
        return string
    try:
        return dt.datetime.strptime(string, format)
    except ValueError:
        for fallback_format in fallbackFormats:
            try:
                return dt.datetime.strptime(string, fallback_format)
            except ValueError:
                continue

    # Nothing works
    if default is not None:
        if isinstance(default, dt.datetime):
            return default
        elif isinstance(default, str):
            return dt.datetime.strptime(default, format)
        else:
            raise ValueError("Default value must be a datetime object or a string in the correct format.")
    else:
        # If no valid date found and no default provided, return None
        if silent == False:
            RichPrintError(f"Failed to parse date string: {string}. No valid date found and no default provided (Silent={silent})")
    return False  # Return False if no valid date found and no default provided
    


def DTToDateDict(dt):
    # Convert datetime to date dict
    year = None
    try:
        year = dt.year
    except AttributeError as e:
        RichPrintError(f"DTToDateDict: dt is not a datetime object: {e}")
    except Exception as e:
        RichPrintError(f"DTToDateDict: {e}")
        return None
    if year > 1900:
        year = year - 1900

    # Month is 0-indexed
    # Year starts from 1900
    return {
        'month_day': dt.day,
        'year': year,
        'month': dt.month-1,
    }
    
def DateDictToDT(dateDict):
    # Convert date dict to datetime
    year = dateDict['year']
    if year < 1900:
        year += 1900  # Convert 2-digit year to 4-digit year
    return dt.datetime(year, dateDict['month']+1, dateDict['month_day'])

# Timestamp based operations

def TimeStampToDateTime(timestamp):
    # Convert timestamp to datetime
    return dt.datetime.fromtimestamp(timestamp)
def DateTimeToTimeStamp(datetime):
    # Convert datetime to timestamp
    return int(datetime.timestamp())
def TimeStampToDateDict(timestamp):
    # Convert timestamp to date dict
    datetime = TimeStampToDateTime(timestamp)
    return DTToDateDict(datetime)
def DateDictToTimeStamp(dateDict):
    # Convert date dict to timestamp
    datetime = DateDictToDT(dateDict)
    return DateTimeToTimeStamp(datetime)
def TimeStampToString(timestamp, format=None):
    # Convert timestamp to string
    if format is None:
        format = settings["DATE_FORMAT"]
    datetime = TimeStampToDateTime(timestamp)
    return parseDTToString(datetime)
def TimeStampToStringWithHoursMinutes(timestamp):
    # Convert timestamp to string with hours and minutes
    format = "%Y-%m-%d %H-%M"
    datetime = TimeStampToDateTime(timestamp)
    return parseDTToStringWithHoursMinutes(datetime, format=format)
def TimeStampToStringWithFallback(timestamp, fallbackString):
    # Convert timestamp to string with fallback
    datetime = TimeStampToDateTime(timestamp)
    return parseDTToStringWithFallback(datetime, fallbackString=fallbackString, quiet=True)
def AnyDTFormatToTimeStamp(unknownDT):
    # Convert any datetime format to timestamp
    if type(unknownDT) is dt.datetime:
        return DateTimeToTimeStamp(unknownDT)
    elif isinstance(unknownDT, str):
        return DateDictToTimeStamp(parseStringToDT(unknownDT, silent=True))
    elif isinstance(unknownDT, dict):
        return DateDictToTimeStamp(DateDictToDT(unknownDT))
    elif isinstance(unknownDT, int) or isinstance(unknownDT, float):
        # If it's a timestamp, return it directly
        return int(unknownDT)
    else:
        raise ValueError("Invalid datetime format")
def StringToTimeStamp(string, silent=False):
    # Convert string to timestamp
    dt = parseStringToDT(string, silent=silent)
    return DateTimeToTimeStamp(dt)




def RichPrint(text, color, typeText="console"):
    richPrintConsole.print(text, style=color)
    # Add to logs
    timeStr = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Remove if greater than 2500 entries
    global terminalConsoleLogs
    if len(terminalConsoleLogs) > 2500:
        terminalConsoleLogs.pop(0)
    terminalConsoleLogs.append(f"[{typeText}] {timeStr} -- {text}")

def RichPrintCritical(text):
    if DEBUG_LEVEL == "CRITICAL" or DEBUG_LEVEL == "WARNING" or DEBUG_LEVEL == "ERROR" or DEBUG_LEVEL == "CRITICAL" or DEBUG_LEVEL == "ALL" or DEBUG_LEVEL == "INFO":
        RichPrint(f"CRITICAL: {text}", "bold red", typeText="CRITICAL")

def RichPrintError(text):
    if DEBUG_LEVEL == "ERROR" or DEBUG_LEVEL == "ALL" or DEBUG_LEVEL == "INFO" or DEBUG_LEVEL == "WARNING":
        RichPrint(text, "bold red", typeText="ERROR")
def RichPrintInfo(text):
    if DEBUG_LEVEL == "INFO" or DEBUG_LEVEL == "ALL":
        RichPrint(text, "blue", typeText="INFO")
def RichPrintSuccess(text):
    if DEBUG_LEVEL == "INFO" or DEBUG_LEVEL == "WARNING" or DEBUG_LEVEL == "ERROR" or DEBUG_LEVEL == "ALL":
        RichPrint(text, "bold green", typeText="SUCCESS")
def RichPrintSuccessMinor(text):
    if DEBUG_LEVEL == "INFO" or DEBUG_LEVEL == "WARNING" or DEBUG_LEVEL == "ERROR" or DEBUG_LEVEL == "ALL":
        RichPrint(text, "dark_green", typeText="SUCCESS_MINOR")
def RichPrintWarning(text):
    if DEBUG_LEVEL == "WARNING" or DEBUG_LEVEL == "ALL" or DEBUG_LEVEL == "INFO":
        RichPrint(text, "bold yellow", typeText="WARNING")
def RichPrintSeparator():
    if DEBUG_LEVEL == "INFO" or DEBUG_LEVEL == "ALL":
        RichPrint("--------------------------------------------------", "bold white")

def print_me(sender, data, user_data):
    print("Hello World")
    print(sender, data, user_data)

def Settings_SaveCurrentSettings():
    WriteYaml(session["settingsPath"], settings)
    RichPrintSuccessMinor("Saved current settings to file")

# Fast print the ID and names of all teas and reviews in a tree
def printTeasAndReviews():
    RichPrintSeparator()
    RichPrintInfo("Teas and Reviews:")
    for i, tea in enumerate(TeaStash):
        RichPrintInfo(f"Tea {i}: {tea.name} ({tea.dateAdded})")
        for j, review in enumerate(tea.reviews):
            RichPrintInfo(f"\tReview {j}: {review.name} ({review.dateAdded})")
    RichPrintSeparator()

# Fast print of Categories and Review Categories
def printCategories():
    RichPrintSeparator()
    RichPrintInfo("Categories:")
    for i, cat in enumerate(TeaCategories):
        RichPrintInfo(f"Category {i}: {cat.name} ({cat.categoryType}) ({cat.categoryRole})")
    RichPrintSeparator()
    RichPrintInfo("Review Categories:")
    for i, cat in enumerate(TeaReviewCategories):
        RichPrintInfo(f"Category {i}: {cat.name} ({cat.categoryType}) ({cat.categoryRole})")
    RichPrintSeparator()

# Iterates through list of categories and returns first category id that matches the role
def getCategoryIDByrole(role):
    noneFoundValue = -1
    for i, cat in enumerate(TeaCategories):
        if cat.categoryRole == role:
            return i
        
    return noneFoundValue
def getCategoryByrole(role):
    catID = getCategoryIDByrole(role)
    if catID == -1:
        return None
    return TeaCategories[catID]

def getAlLCategoryEntriesByID(categoryID, review=False):
    # Get the values of all entries of a category by ID, returning the list of values
    returnList = []
    catName = ""
    catRole = ""

    
    if review == True:
        catName = TeaReviewCategories[categoryID].name
        catRole = TeaReviewCategories[categoryID].categoryRole
    else:
        catName = TeaCategories[categoryID].name
        catRole = TeaCategories[categoryID].categoryRole
    
    if review:
        for tea in TeaStash:
            for review in tea.reviews:
                if catName in review.attributes:
                    returnList.append(review.attributes[catName])
                elif catRole in review.attributes:
                    returnList.append(review.attributes[catRole])
    else:
        for tea in TeaStash:
            if catName in tea.attributes:
                returnList.append(tea.attributes[catName])
            elif catRole in tea.attributes:
                returnList.append(tea.attributes[catRole])


    return returnList

# Get all entries and uses function provided on the category to get the value
def aggregateCategoryEntriesByID(categoryID, review=False, func=None):
    if func is None:
        # Average by default
        func = lambda x: sum(x) / len(x)

    returnList = getAlLCategoryEntriesByID(categoryID, review=review)
    if len(returnList) == 0:
        RichPrintWarning(f"No entries found for category {categoryID} {TeaCategories[categoryID].name}, returning 0")

    returnValue = func(returnList)

    return returnValue

# Average category entries by ID
def averageCategoryEntriesByID(categoryID, review=False):
    # Average function, only if the category is a number
    def averageFunc(x):
        if len(x) == 0:
            return 0
        if isinstance(x[0], str):
            return -1
        elif isinstance(x[0], dt.datetime):
            return -1
        return round(sum(x) / len(x), 3)
    return aggregateCategoryEntriesByID(categoryID, review=review, func=averageFunc)

# Sum category entries by ID
def sumCategoryEntriesByID(categoryID, review=False):
    # Sum function, only if the category is a number
    def sumFunc(x):
        if len(x) == 0:
            return 0
        if isinstance(x[0], str):
            return -1
        elif isinstance(x[0], dt.datetime):
            return -1
        return round(sum(x), 3)
    return aggregateCategoryEntriesByID(categoryID, review=review, func=sumFunc)

# Count category entries by ID
def countCategoryEntriesByID(categoryID, review=False):
    # Count function
    def countFunc(x):
        return len(x)
    return aggregateCategoryEntriesByID(categoryID, review=review, func=countFunc)

# Unique category entries by ID
def uniqueCategoryEntriesByID(categoryID, review=False):
    # Unique function
    def uniqueFunc(x):
        return list(set(x))
    return aggregateCategoryEntriesByID(categoryID, review=review, func=uniqueFunc)

# UniqueEntries with count by ID
def uniqueEntriesWithCountByID(categoryID, review=False):
    # Unique function with count
    def uniqueFunc(x):
        return {i: x.count(i) for i in set(x)}
    return aggregateCategoryEntriesByID(categoryID, review=review, func=uniqueFunc)

def debugGetcategoryRole():
    allroleCategories = []
    for k, v in session["validroleCategory"].items():
        for i, cat in enumerate(v):
            allroleCategories.append(cat)

    # Dedup and remove UNUSED
    allroleCategories = list(set(allroleCategories))
    allroleCategories.remove("UNUSED")

    # Print a tea dict for debugging
    RichPrintInfo(f"TeaStash: {TeaStash[0].__dict__}")

    validCatgories = []
    for i, cat in enumerate(allroleCategories):
        if cat == "ID":
            continue

        hasCoorespondingCategory = getCategoryIDByrole(cat)
        if hasCoorespondingCategory == -1:
            RichPrintWarning(f"Category {cat} does not have a cooresponding category")
            continue
        else:
            # Get info on category
            numEntriesInCategory = 0
            for tea in TeaStash:
                if cat in tea.attributes:
                    numEntriesInCategory += 1

            # Get the values of all entries of a category by ID, then truncate to 10
            dataAverage = averageCategoryEntriesByID(hasCoorespondingCategory, review=False)
            dataUnique = uniqueCategoryEntriesByID(hasCoorespondingCategory, review=False)
            dataSum = sumCategoryEntriesByID(hasCoorespondingCategory, review=False)
            dataCount = countCategoryEntriesByID(hasCoorespondingCategory, review=False)
            dataUniqueCount = uniqueEntriesWithCountByID(hasCoorespondingCategory, review=False)


            RichPrintInfo(f"Category {cat} has a cooresponding category {hasCoorespondingCategory} of name {TeaCategories[hasCoorespondingCategory].name}")
            RichPrintInfo(f"Category {cat} has average {dataAverage}, unique {dataUnique}, sum {dataSum}, count {dataCount}, uniqueCount {dataUniqueCount}")

            if dataCount > 0:
                validCatgories.append(cat)
    RichPrintSuccess(f"Valid categories: {validCatgories}")

def getValidCategoryRolesList():
    # Get all valid category roles from the session
    allroleCategories = []
    for k, v in session["validroleCategory"].items():
        for i, cat in enumerate(v):
            allroleCategories.append(cat)

    # Dedup and remove UNUSED
    allroleCategories = list(set(allroleCategories))
    allroleCategories.remove("UNUSED")

    validCategoryRoles = []
    for i, cat in enumerate(allroleCategories):
        if cat == "ID":
            continue

        hasCoorespondingCategory = getCategoryIDByrole(cat)
        if hasCoorespondingCategory == -1:
            RichPrintWarning(f"Category {cat} does not have a cooresponding category")
            continue
        else:
            # Get info on category
            numEntriesInCategory = 0
            for tea in TeaStash:
                if cat in tea.attributes:
                    numEntriesInCategory += 1

            # Get the values of all entries of a category by ID, then truncate to 10
            #dataAverage = averageCategoryEntriesByID(hasCoorespondingCategory, review=False)
            #dataUnique = uniqueCategoryEntriesByID(hasCoorespondingCategory, review=False)
            #dataSum = sumCategoryEntriesByID(hasCoorespondingCategory, review=False)
            dataCount = countCategoryEntriesByID(hasCoorespondingCategory, review=False)

            if dataCount > 0:
                validCategoryRoles.append(cat)

    return validCategoryRoles, allroleCategories

def getValidReviewCategoryRolesList():
    # Get all valid category roles from the session
    allroleCategories = []
    for k, v in session["validroleReviewCategory"].items():
        for i, cat in enumerate(v):
            allroleCategories.append(cat)

    # Dedup and remove UNUSED
    allroleCategories = list(set(allroleCategories))
    allroleCategories.remove("UNUSED")

    validCategoryRoles = []
    for i, cat in enumerate(allroleCategories):
        if cat == "ID":
            continue

        hasCoorespondingCategory = getReviewCategoryIDByrole(cat)
        if hasCoorespondingCategory == -1:
            RichPrintWarning(f"Category {cat} does not have a cooresponding category")
            continue
        else:
            # Get info on category
            numEntriesInCategory = 0
            for tea in TeaStash:
                for review in tea.reviews:
                    if cat in review.attributes:
                        numEntriesInCategory += 1

            # Get the values of all entries of a category by ID, then truncate to 10
            #dataAverage = averageCategoryEntriesByID(hasCoorespondingCategory, review=True)
            #dataUnique = uniqueCategoryEntriesByID(hasCoorespondingCategory, review=True)
            #dataSum = sumCategoryEntriesByID(hasCoorespondingCategory, review=True)
            dataCount = countCategoryEntriesByID(hasCoorespondingCategory, review=True)

            if dataCount > 0:
                validCategoryRoles.append(cat)

    return validCategoryRoles, allroleCategories

def getStatsOnCategoryByRole(role, review=False):
    if review:
        # Get all review categories
        id = getReviewCategoryIDByrole(role)
        sum, avrg, count, unique = sumCategoryEntriesByID(id, review=True), averageCategoryEntriesByID(id, review=True), countCategoryEntriesByID(id, review=True), uniqueCategoryEntriesByID(id, review=True)
        uniqueCount = uniqueEntriesWithCountByID(id, review=True)
        return sum, avrg, count, unique, uniqueCount
    else:
        # Get all categories
        id = getCategoryIDByrole(role)
        sum, avrg, count, unique = sumCategoryEntriesByID(id, review=False), averageCategoryEntriesByID(id, review=False), countCategoryEntriesByID(id, review=False), uniqueCategoryEntriesByID(id, review=False)
        uniqueCount = uniqueEntriesWithCountByID(id, review=False)
        return sum, avrg, count, unique, uniqueCount
    

# Iterate through ReviewCategories and return the first category id that matches the role
def getReviewCategoryIDByrole(role):
    noneFoundValue = -1
    for i, cat in enumerate(TeaReviewCategories):
        if cat.categoryRole == role:
            return i
        
    return noneFoundValue

def debugGetReviewcategoryRole():
    allroleCategories = []
    for k, v in session["validroleReviewCategory"].items():
        for i, cat in enumerate(v):
            allroleCategories.append(cat)

    # Dedup and remove UNUSED
    allroleCategories = list(set(allroleCategories))
    allroleCategories.remove("UNUSED")

    # Print a tea dict for debugging
    RichPrintInfo(f"TeaStash: {TeaStash[1].__dict__}")
    
    validCatgories = []
    for i, cat in enumerate(allroleCategories):
        if cat == "ID":
            continue

        hasCoorespondingCategory = getReviewCategoryIDByrole(cat)
        if hasCoorespondingCategory == -1:
            RichPrintWarning(f"Category {cat} does not have a cooresponding category")
            continue
        else:
            # Get info on category
            numEntriesInCategory = 0
            for tea in TeaStash:
                for review in tea.reviews:
                    if cat in review.attributes:
                        numEntriesInCategory += 1

            # Get the values of all entries of a category by ID, then truncate to 10
            dataAverage = averageCategoryEntriesByID(hasCoorespondingCategory, review=True)
            dataUnique = uniqueCategoryEntriesByID(hasCoorespondingCategory, review=True)
            dataSum = sumCategoryEntriesByID(hasCoorespondingCategory, review=True)
            dataCount = countCategoryEntriesByID(hasCoorespondingCategory, review=True)
            
            
            RichPrintInfo(f"Category {cat} has a cooresponding category {hasCoorespondingCategory} of name {TeaReviewCategories[hasCoorespondingCategory].name}")
            RichPrintInfo(f"Category {cat} has average {dataAverage}, unique {dataUnique}, sum {dataSum}, count {dataCount}")
            if dataCount > 0:
                validCatgories.append(cat)

    RichPrintSuccess(f"Valid categories: {validCatgories}")

# Renumbers the IDs of all teas and reviews in the stash
def renumberTeasAndReviews(save=True):
    global TeaStash
    RichPrintInfo("Renumbering Teas and Reviews...")
    
    # Sort by date added, if available, otherwise by id
    if hasattr(TeaStash, 'sort') and callable(getattr(TeaStash, 'sort')):
        TeaStash.sort(key=lambda tea: (getattr(tea, 'date', dt.datetime.min), tea.id))
    else:
        RichPrintWarning("TeaStash does not support sorting or has no dateAdded attribute. Renumbering will proceed without sorting.")
        # Sort by id only if no dateAdded attribute is found
        TeaStash.sort(key=lambda tea: tea.id)  # Fallback to sorting by id if no dateAdded attribute exists

    # Renumber teas
    for i, tea in enumerate(TeaStash):
        tea.id = i

        # Renumber reviews
        for j, review in enumerate(tea.reviews):
            review.id = j
            review.parentID = tea.id  # Ensure parent ID is correct

    RichPrintSuccessMinor("Completed renumbering Teas and Reviews.")
    printTeasAndReviews()  # Print the updated teas and reviews for verification

    if save:
        # Save to file after renumbering
        saveTeasData(TeaStash, settings["TEA_REVIEWS_PATH"])
        RichPrintSuccess("Saved renumbered teas and reviews to file.")

# Grade letter functions

def getGradeList():
    return ["S+ (5.0)", "S (4.5)", "S- (4.25)", "A+ (4.0)", "A (3.5)", "A- (3.25)", "B+ (3.0)", "B (2.5)", "B- (2.25)", "C+ (2.0)", "C (1.5)", "C- (1.25)", "D+ (1.0)", "D (0.5)", "D- (0.25)", "F (0)"]

def getGradeValue(grade):
    # Get the value of a grade
    if grade is None or grade == "":
        RichPrintError("Grade is None or empty")
        return None
    gradingOptions = getGradeList()
    if grade in gradingOptions:
        return float(grade.split("(")[1].split(")")[0])
    else:
        RichPrintError(f"Grade {grade} not found in grading options")
        return None
    
def getGradeNumericalList():
    # Get a list of numerical values for the grades
    return [getGradeValue(grade) for grade in getGradeList() if getGradeValue(grade) is not None]

def getGradeLetter(value):
    # Get the letter grade for a value
    if value is None or value == "":
        return value
    gradingOptions = getGradeList()
    for grade in gradingOptions:
        if getGradeValue(grade) == value:
            return grade
    RichPrintError(f"Value {value} not found in grading options")
    return None

def getGradeLetterFuzzy(value):
    # Gets letter based on fuzzy range in the format
    # Letter (actual value)
    # Letters start at defined range and end right above the next range
    # IE S+ is from 4.51 to 5.0, S is from 4.26 to 4.5, etc.
    if value is None or value == "":
        return None
    gradingOptions = getGradeList()
    
    # If out of range
    if value < 0 or value > 5:
        return None
    
    # Round value to 3 decimal places
    value = round(value, 3)
    
    for grade in gradingOptions:
        gradeLettersOnly = grade.split(" (")[0]  # Get the letter part of the grade
        # If exact match, return grade
        if getGradeValue(grade) == value:
            return grade
        
        upperBound = getGradeValue(grade)
        lowerBound = upperBound - 0.5  # Assuming each grade has a range of 0.25
        if "+" not in grade:
            # If grade has a plus, it is the upper bound of the range
            lowerBound = upperBound - 0.25
        if grade == "F (0)":
            # F is a special case, it is always 0
            lowerBound = 0
            upperBound = 0.25

        if lowerBound < value <= upperBound:
            # If value is in range, return grade
            return f"{gradeLettersOnly} ({value})"  # Return grade with value in format "Grade (value)"

                
    # If no grade found, return None
    RichPrintError(f"Value {value} not found in grading options")
    return None

def getGradeDropdownValueByFloat(value):
    # Get the dropdown value for a float value
    gradingOptions = getGradeList()
    for grade in gradingOptions:
        if getGradeValue(grade) == value:
            return grade
    RichPrintError(f"Value {value} not found in grading options")
    return None


# Visualization stuff. 
# 1. Given a type of tea, return a list of average ratings for all reviews of that type of tea in list form
# 2. Given a vendor of tea, return a list of average ratings for all reviews of that vendor in list form
# 3. Given a year of tea, return a list of average ratings for all reviews of that year in list form
# 4. Given a list from 1-3, automatically find range, return a tuple of (x, y, size) points deduping similar points

def getAverageRatingRange(teaType=None, vendor=None, year=None, overlap_threshold=0.05):
    # If none are provided, it is considered "All"
    getAll = False
    if sum([teaType is None, vendor is None, year is None]) == 3:
        getAll = True
    # if more than 1 are provided, error for now
    elif sum([teaType is not None, vendor is not None, year is not None]) != 1:
        RichPrintError("Only one of teaType, vendor, or year must be provided")
        return None
    # Get the average ratings for the specified criteria
    if getAll:
        ratings = getAverageRatingsAll()
    elif teaType:
        ratings = getAverageRatingsByTeaType(teaType)
    elif vendor:
        ratings = getAverageRatingsByVendor(vendor)
    elif year:
        ratings = getAverageRatingsByYear(year)
    else:
        RichPrintError("No valid criteria provided")
        return None

    # If no ratings found, return None
    if not ratings:
        RichPrintError("No ratings found")
        return None

    # Sort ratings for easier clustering
    ratings = sorted(ratings)
    min_r, max_r = min(ratings), max(ratings)
    r_range = max_r - min_r if max_r != min_r else 1e-6  # avoid divide by zero

    # Define max distance considered "overlapping"
    threshold = overlap_threshold * r_range

    clusters = []
    current_cluster = [ratings[0]]

    # Group nearby points
    for r in ratings[1:]:
        if abs(r - current_cluster[-1]) <= threshold:
            current_cluster.append(r)
        else:
            clusters.append(current_cluster)
            current_cluster = [r]
    clusters.append(current_cluster)

    # Now convert clusters into (x, y, size) points
    points = []
    for cluster in clusters:
        x = np.mean(cluster)  # average rating in cluster
        # y should be static as the plot is very flat
        y = 1
        size = len(cluster)
        # Round y to 2 decimal places
        y = round(y, 2)
        points.append((x, y, size))

    return points
def getAverageRatingsAll():
    ratings = []
    for tea in TeaStash:
        for review in tea.reviews:
            if review.attributes.get("Final Score") is not None:
                ratings.append(review.attributes.get("Final Score"))
    return ratings

def getAverageRatingsByTeaType(teaType):
    ratings = []
    for tea in TeaStash:
        if teaType.lower() in tea.attributes.get("Type", "").lower():
            for review in tea.reviews:
                if review.attributes.get("Final Score") is not None:
                    ratings.append(review.attributes.get("Final Score"))
    return ratings

def getAverageRatingsByVendor(vendor):
    ratings = []
    for tea in TeaStash:
        if vendor.lower() in tea.attributes.get("Vendor", "").lower():
            for review in tea.reviews:
                if review.attributes.get("Final Score") is not None:
                    ratings.append(review.attributes.get("Final Score"))
    return ratings

def getAverageRatingsByYear(year):
    ratings = []
    for tea in TeaStash:
        if tea.attributes.get("Year") == year:
            for review in tea.reviews:
                if review.attributes.get("Final Score") is not None:
                    ratings.append(review.attributes.get("Final Score"))
    return ratings

def make_rating_bubble_image(points, width=300, height=125, highlight=None, name="", grade_labels=True):

    # Create figure
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    x, y, size = zip(*points)

    # Normalize size for bubbles
    # largest bubble shouldnt exceed 750 in size
    # smallest bubble shouldnt be smaller than 50
    # If any bubbles are greater than 750, scale all down proportionally
    bubble_sizes = [s * 100 for s in size]  # Scale sizes for better visibility
    if max(bubble_sizes) > 750:
        scale_factor = 750 / max(bubble_sizes)
        bubble_sizes = [s * scale_factor for s in bubble_sizes]
    elif min(bubble_sizes) < 50:
        scale_factor = 50 / min(bubble_sizes)
        bubble_sizes = [s * scale_factor for s in bubble_sizes]
    # Ensure at least 50 to most 750
    bubble_sizes = [max(50, min(s, 750)) for s in bubble_sizes]


    # Add a highlight for highlight if provided
    if highlight is not None:
        highlight = float(highlight)
        highlight_x = highlight
        highlight_y = 0.96

    if grade_labels == True:
        labels = {
        0: "F",
        0.5: "D",
        1.5: "C",
        2.5: "B",
        3.5: "A",
        4.5: "S",
        5: "S+"
        }
        # map 0-5 to the xlabels
        # Set tick positions and labels
        ax.set_xticks(list(labels.keys()))
        ax.set_xticklabels(list(labels.values()))

    ax.scatter(x, y, s=bubble_sizes, alpha=0.6, edgecolors='black', linewidths=0.5)
    if highlight is not None:
        ax.scatter([highlight_x], [highlight_y], s=85, color='red', edgecolors='black', linewidths=1.5, label='This Rating')
    ax.set_xlabel("")
    ax.set_ylabel("")  # y is just jitter
    ax.set_title(name if name else "Rating Distribution")
    ax.set_ylim(min(y) - 0.1, max(y) + 0.1)
    ax.set_xlim(-0.5, 5.5)
    ax.get_yaxis().set_visible(False)
    ax.grid(alpha=0.2)

    # Save figure to BytesIO buffer
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    buf.seek(0)

    # Load as Pillow image
    chart_img = Image.open(buf)
    return chart_img


# TODO: Fuzzy tea name matching under same vendor and type (ie sample vs cake or year differences)
def fuzzy_tea_name_matching(tea, strict_vendor=True, strict_type=True, strict_year=False):
    teaType = tea.attributes.get("Type", "").lower()
    vendor = tea.attributes.get("Vendor", "").lower()
    year = tea.attributes.get("Year", None)
    name = tea.name.lower().strip()
    allMatchedTeas = []
    allMatchedReviews = [] # return list of reviews as well for various display stuff
    # Implement fuzzy matching logic here
    for other_tea in TeaStash:
        if other_tea.id == tea.id:
            continue
        otherTea_vendor = other_tea.attributes.get("Vendor", "").lower().strip()
        otherTea_type = other_tea.attributes.get("Type", "").lower().strip()
        otherTea_year = other_tea.attributes.get("Year", None)
        otherTea_name = other_tea.name.lower().strip()
        if strict_vendor and otherTea_vendor != vendor:
            continue
        if strict_type and otherTea_type != teaType:
            continue
        if strict_year and otherTea_year != year:
            continue
        # If we reach here, we need to strip year and vendor from the name and do fuzzy matching
        # Remove year from name if it exists
        name_no_year = re.sub(r'\b(19|20)\d{2}\b', '', name).strip()
        other_name_no_year = re.sub(r'\b(19|20)\d{2}\b', '', otherTea_name).strip()
        # Remove vendor from name if it exists
        name_no_vendor = re.sub(r'\b' + re.escape(vendor) + r'\b', '', name_no_year).strip()
        other_name_no_vendor = re.sub(r'\b' + re.escape(otherTea_vendor) + r'\b', '', other_name_no_year).strip()
        # Perform fuzzy matching with package fuzzywuzzy
        lvratio = fuzz.partial_ratio(name_no_vendor, other_name_no_vendor)
        ratio = fuzz.ratio(name_no_vendor, other_name_no_vendor)
        print(f"Fuzzy matching {name_no_vendor} and {other_name_no_vendor}: LVRatio={lvratio}, Ratio={ratio}")
        # If either ratio is above 80, we consider it a match
        if lvratio >= 80 or ratio >= 70:
            allMatchedTeas.append(other_tea)
            allMatchedReviews.extend(other_tea.reviews)
    # add self tea and reviews to the list
    allMatchedTeas.append(tea)
    allMatchedReviews.extend(tea.reviews)
    return allMatchedTeas, allMatchedReviews


# Defines valid categories, and role as categories
# Also defines the types of role

def setValidTypes():
    session["validTypesCategory"] = ["string", "int", "float", "bool", "datetime"]
    session["validTypesReviewCategory"] = ["string", "int", "float", "bool", "datetime"]
    
    session["validroleCategory"] = {"string": ["UNUSED", "Notes (short)", "Notes (Long)", "Name", "Vendor", "Type"],
                                "int": ["UNUSED","Year"],
                                "float": ["UNUSED", "Total Score", "Amount", "Remaining", "Cost", "Cost per Gram"],
                                "bool": ["UNUSED", "bool"],
                                "date": ["UNUSED", "date"],
                                "datetime": ["UNUSED", "date"]}
    
    session["validroleReviewCategory"] = {"string": ["UNUSED", "Notes (short)", "Notes (Long)", "Name", "Method"],
                                "int": ["UNUSED", "Year", "Amount", "Steeps", "Vessel size"],
                                "float": ["UNUSED", "Score", "Final Score", "Amount"],
                                "bool": ["UNUSED", "bool"],
                                "date": ["UNUSED", "date"],
                                "datetime": ["UNUSED", "date"]}
    

def _table_sort_callback(sender, sortSpec):
    # If num rows is less than 2, return
    numRows = dpg.get_item_children(sender, 1)
    if numRows is None or len(numRows) < 2:
        RichPrintInfo("No rows to sort, skipping sort")
        return
    # sortSpec is a list of tuples: [(column_index, sort_direction), ...]
    # sort_direction: 1 = ascending, -1 = descending
    if not sortSpec or sortSpec[0] is None:
        RichPrintError("Sort spec is None or empty")
        return
    columnID, direction = sortSpec[0]
    # If column ID is None or cooresponds to (reivews or edit) column, ignore
    if columnID is None:
        RichPrintError("Sort spec is None or empty")
        return
    
    # Get column index from user data
    columnUserData = dpg.get_item_user_data(columnID)
    if columnUserData is None:
        RichPrintInfo("Column user data is None, Skipping sort")
        return
    
    # Convert user data to int
    try:
        column_index = int(columnUserData)
    except ValueError:
        RichPrintError(f"Column user data is not an int: {columnUserData}")
        return
    # Print column index for debugging
    
    # Determine if ascending or descending
    ascending = direction > 0
    # Get all the table rows
    rows = dpg.get_item_children(sender, 1)
    if not rows:
        RichPrintError("No rows to sort")
        return
    sortableItems = []
    for row in rows:
        if dpg.get_item_type(row) == dp.mvTableRow:
            rowData = dpg.get_item_children(row, 1)
            if rowData is not None and len(rowData) > 0:
                # Get the value from the column index
                cell = rowData[column_index]
                cellValue = dpg.get_value(cell)
                # If value is an number, convert it to float
                if isinstance(cellValue, str) and cellValue.replace('.', '', 1).isdigit():
                    cellValue = float(cellValue)
                sortableItems.append((row, cellValue))
    # Define sort key
    def sort_key(item):
        # If date string, try to parse it, if succeeds, use timestamp
        if isinstance(item[1], str):
            try:
                parsed_date = StringToTimeStamp(item[1], silent=True)
                if parsed_date:
                    return parsed_date
            except:
                # Fail silently as we know it isnt always a date
                return item[1]
        return item[1]
    
    unsortableItems = []
    cleanSortableItems = []
    RichPrintSuccessMinor(f"Found {len(sortableItems)} sortable items and {len(unsortableItems)} unsortable items")
    # Remove N/A from the list
    if len(sortableItems) > 1:
        for i, item in enumerate(sortableItems):
            if item[1] == "N/A":
                unsortableItems.append(item)
            else:
                cleanSortableItems.append(item)
    cleanSortableItems.sort(key=sort_key, reverse=not ascending)
    
    if len(cleanSortableItems) < 2:
        RichPrintError("Not enough sortable items to sort")
        return
    RichPrintSuccessMinor(f"Found {len(sortableItems)} sortable items and {len(unsortableItems)} unsortable items")
    # Re-add the unsortable items to the end of the list
    for item in unsortableItems:
        cleanSortableItems.append(item)
    sorted_rows = [item[0] for item in cleanSortableItems]
    # Reorder rows
    dpg.reorder_items(sender, 1, sorted_rows)
    RichPrintSuccess(f"Sorted table by column {column_index} in {'ascending' if ascending else 'descending'} order")


# We want to search our entire list of teas or reviews for a list of previous answers, then return the top X results by frequency
def searchPreviousAnswers(categoryName, data="Tea", topX=5):
    topX = int(topX)
    # data must be either "Tea" or "Review"
    if data not in ["Tea", "Review"]:
        RichPrintError("Data must be either Tea or Review")
        return []
    
    # If data less than top X return all data
    if len(TeaStash) < topX:
        topX = len(TeaStash)
    
    answersDict = {}
    if data == "Tea":
        for tea in TeaStash:
            if categoryName in tea.attributes:
                if tea.attributes[categoryName] in answersDict:
                    answersDict[tea.attributes[categoryName]] += 1
                else:
                    answersDict[tea.attributes[categoryName]] = 1

    elif data == "Review":
        for tea in TeaStash:
            for review in tea.reviews:
                if categoryName in review.attributes:
                    if review.attributes[categoryName] in answersDict:
                        answersDict[review.attributes[categoryName]] += 1
                    else:
                        answersDict[review.attributes[categoryName]] = 1

    # Get the top X results by frequency, then sort and return them
    sortedAnswers = sorted(answersDict.items(), key=lambda x: x[1], reverse=True)
    topAnswers = sortedAnswers[:topX]
    # Remove time from any datetime objects
    for i, answer in enumerate(topAnswers):
        if isinstance(answer[0], dt.datetime):
            topAnswers[i] = (answer[0].strftime(settings["DATE_FORMAT"]), answer[1])
    topAnswersList = [answer[0] for answer in topAnswers]
    RichPrintInfo(f"Top {topX} answers for {categoryName} in {data}: {topAnswers}")
    return topAnswers, topAnswersList


#endregion


#region DataObject Classes

# Defines one tea that has been purchased and may have reviews
class StashedTea:
    id = 0
    name = ""
    dateAdded = None  # Date when the tea was added to the stash
    attributes = {}
    reviews = []
    calculated = {}
    # Price and amount adjustments, if required, in lists of Adjustment dicts
    # Price adjustments = [{"price": 10, "amount": 100}, {"price": 5, "amount": 50}]
    adjustments = {}

    # Finished flag
    finished = False

    # Teas may be copies of other teas aquired in other methods. We would like to link them together somehow.
    # We can either link them with IDs or with names. For now, we will use names.
    # When we call a function with the keywork incLinkedTeas=True, it will include all linked teas in the calculation.
    linkedTeas = []  # List of tea IDs that are linked to this tea

    def __init__(self, id, name, dateAdded=None, attributes={}):
        self.id = id
        self.name = name
        if dateAdded is None:
            dateAdded = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        self.dateAdded = dateAdded
        self.attributes = attributes
        self.reviews = []
        self.calculated = {}

    def addReview(self, review):
        self.reviews.append(review)
    def removeReview(self, reviewID):
        # Remove review by ID
        self.reviews = [review for review in self.reviews if review.id != reviewID]
        # Recalculate the average rating after removing a review
        self.calculateAverageRating()

    def calculate(self):
        # call all the calculate functions
        self.calculateAverageRating()
    def calculateAverageRating(self):
        # calculate the average rating
        if len(self.reviews) > 0:
            totalRating = 0
            for review in self.reviews:
                totalRating += review.rating
            self.calculated["averageRating"] = totalRating / len(self.reviews)
        else:
            self.calculated["averageRating"] = 0

    def getLatestReview(self):
        # Get the latest review by date added
        if len(self.reviews) == 0:
            return None
        if "date" not in self.reviews[0].attributes:
            RichPrintError("No date attribute found in reviews, cannot get latest review. (DATEADDED)")
            return None
        latestReview = max(self.reviews, key=lambda r: r.attributes["date"])
        return latestReview
    
    def getEarliestReview(self):
        # Get the earliest review by date added
        if len(self.reviews) == 0:
            return None
        if "date" not in self.reviews[0].attributes:
            RichPrintError("No date attribute found in reviews, cannot get earliest review. (DATEADDED)")
            return None
        earliestReview = min(self.reviews, key=lambda r: r.attributes["date"])
        return earliestReview
    
    def getEstimatedConsumedByReviews(self):
        # Get the estimated consumed amount by reviews
        if len(self.reviews) == 0:
            return 0
        consumed = 0
        for review in self.reviews:
            if "Amount" in review.attributes:
                consumed += review.attributes["Amount"]

        consumed = round(consumed, 2)  # Round to 2 decimal places
        return consumed
    
    def getEstimatedRemaining(self):
        # Find self in cache
        global TeaCache
        if self in TeaCache:
            return TeaCache[self.id].get("remaining", None)
        
    def getCalcedValue(self, categoryRole="Cost per Gram"):
        # Get the category role
        cat = getCategoryByrole(categoryRole)
        
        # Check if flagged as autocalculated
        if cat is None:
            RichPrintError(f"Category role {categoryRole} not found")
            return None
        if not cat.isAutoCalculated:
            return self.attributes.get(categoryRole, None)

        # Get the calculated cost per gram from the cache
        global TeaCache
        if self in TeaCache:
            print(F"Getting {categoryRole} from cache")
            return TeaCache[self.id].get(categoryRole, None)
        # if not found, get calculated
        if categoryRole in self.calculated:
            print(F"Getting {categoryRole} from calculated")
            return self.calculated[categoryRole]
        # if not found, run autocalculate
        print(F"Calculating {categoryRole}")
        value, explanation = cat.autocalculate(self)
        self.calculated[categoryRole] = value
        return value
    
    def _getLinkedTeas(self):
        # Get the linked teas as StashedTea objects
        linkedTeas = [] # self is implicitly included
        global TeaCache
        for teaID in self.linkedTeas:
            tea = TeaCache.get(teaID, None)
            if tea is not None:
                linkedTeas.append(tea)
        return linkedTeas

# Defines a review for a tea
class Review:
    attempt = 0
    parentID = 0
    id = 0
    name = ""
    dateAdded = None
    attributes = {}
    calculated = {}

    # If is required, for when talking about tea, or for all, like teaware and shipping
    isRequiredForTea = False
    isRequiredForAll = False

    # Autocalculated, if it is, it would be hidden in entry window and would rely on a calc step after submission
    # based on its role, would be Not Required if so.
    isAutoCalculated = False

    # Show as dropdown?
    isDropdown = False
    def __init__(self, id, name, dateAdded, attributes, rating):
        self.id = id
        self.name = name
        if dateAdded is None:
            dateAdded = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        self.dateAdded = dateAdded
        self.attributes = attributes
        self.rating = rating
        self.calculated = {}

        self.isRequiredForTea = False
        self.isRequiredForAll = False
        self.isAutoCalculated = False
        self.isDropdown = False


    def calculate(self):
        # call all the calculate functions
        self.calculateFinalScore()




class TeaCategory:
    name = ""
    categoryType = ""
    color = ""
    defaultValue = None
    categoryRole = None

    # If is required, for when talking about tea, or for all, like teaware and shipping
    isRequiredForTea = False
    isRequiredForAll = False

    # Autocalculated, if it is, it would be hidden in entry window and would rely on a calc step after submission
    # based on its role, would be Not Required if so.
    isAutoCalculated = False

    # Show as dropdown?
    isDropdown = False

    # Prefix, rounding
    prefix = ""
    suffix = ""
    rounding = 2
    
    # Specific options
    dropdownMaxLength = 5
    gradingDisplayAsLetter = False  # If the category is a grading category, like "Score" or "Final Score", it will be a letter grade (A, B, C, D, F) instead of a number


    def __init__(self, name, categoryType):
        self.name = name
        self.categoryType = categoryType
        if categoryType == "string":
            self.defaultValue = ""
        elif categoryType == "int":
            self.defaultValue = 0
        elif categoryType == "float":
            self.defaultValue = 0.0
        elif categoryType == "bool":
            self.defaultValue = False
        elif categoryType == "date" or categoryType == "datetime":
            # Set the default value to the current date and time
            self.defaultValue = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        self.categoryRole = "UNUSED"

        self.isRequiredForTea = False
        self.isRequiredForAll = False
        self.isAutoCalculated = False
        self.isDropdown = False

    def autocalculate(self, data):
        
        # role - Remaining
        RichPrintInfo("Autocalculating...")
        if self.categoryRole == "Remaining":
            return data.calculated.get("remaining", None), data.calculated.get("remainingExplanation", None)
        elif self.categoryRole == "Cost per Gram":
            return data.calculated.get("costPerGram", None), data.calculated.get("costPerGramExplanation", None)
        elif self.categoryRole == "Total Score":
            # Pulls cached values from TeaCache and put into the calculated dict
            return data.calculated.get("averageScore", None), data.calculated.get("totalScoreExplanation", None)
        return None, None 
        
    # IsValidBase
    def isValidBase(self, value):
        # Checks based on data type
        if self.categoryType == "string":
            return isinstance(value, str)
        elif self.categoryType == "int":
            return isinstance(value, int)
        elif self.categoryType == "float":
            return isinstance(value, (int, float))
        elif self.categoryType == "bool":
            return isinstance(value, bool)
        elif self.categoryType == "date" or self.categoryType == "datetime":
            # Check if value is a valid datetime object or a timestamp
            if isinstance(value, dt.datetime):
                return True
            elif isinstance(value, (int, float)):
                # If it's a timestamp, check if it can be converted to a datetime object
                try:
                    dt.datetime.fromtimestamp(value, tz=dt.timezone.utc)
                    return True
                except (ValueError, OverflowError):
                    return False
        return False
    
    def isValid(self, value):
        # Checks base, and on autocalculated values
        if not self.isValidBase(value):
            RichPrintWarning(f"Value {value} is not valid for category {self.name} of type {self.categoryType}")
            return False
        # If autocalculated, check if it is None
        if self.isAutoCalculated:
            if value is None:
                RichPrintWarning(f"Value {value} is not valid for autocalculated category {self.name}")
                return False
            # If it is a string, check if it is empty
            if isinstance(value, str) and value.strip() == "":
                RichPrintWarning(f"Value {value} is not valid for autocalculated category {self.name}, it is empty")
                return False
        return True

# Themes for coloring
def create_cell_theme(color_rgba):
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvText):
            dpg.add_theme_color(dpg.mvThemeCol_Header, color_rgba, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 5, 5)
    return theme_id


class ReviewCategory:
    name = ""
    categoryType = ""
    defaultValue = ""
    categoryRole = None

    # If is required, for when talking about tea, or for all, like teaware and shipping
    isRequiredForTea = False
    isRequiredForAll = False
    
    # Autocalculated, if it is, it would be hidden in entry window and would rely on a calc step after submission
    # based on its role, would be Not Required if so.
    isAutoCalculated = False

    # Show as dropdown?
    isDropdown = False

    # Prefix, rounding
    prefix = ""
    suffix = ""
    rounding = 2

    # Special options
    dropdownMaxLength = 5
    gradingDisplayAsLetter = False

    def __init__(self, name, categoryType):
        self.name = name
        self.categoryType = categoryType
        self.categoryRole = self.categoryType
        self.ifisRequiredForTea = False
        self.ifisRequiredForAll = False
        
    # Define if is required depending on role
    def setRequired(self, isRequiredForTea, isRequiredForAll):
        self.isRequiredForTea = isRequiredForTea
        self.isRequiredForAll = isRequiredForAll

    def format_attribute(self, key, value):
        """Formats a review attribute based on its category metadata."""
        correctTeaReviewCat = TeaReviewCategories # This should be a list of ReviewCategory objects
        correct_cat = None
        for cat in correctTeaReviewCat:
            if cat.categoryRole == key:
                correct_cat = cat
                break

        if value is None:
            return "N/A"
            
        # Don't warn for vendor or cost per gram since they are injected from parent tea and may not have a category
        if not correct_cat and not key in ["Vendor", "Cost per Gram"]:
            RichPrintWarning(f"No category found for key: {key}. Returning raw value.")
            return str(value)
        
        # Special handling for injected attributes
        if key == "Vendor":
            return str(value)
        if key == "Cost per Gram":
            try:
                value = float(value)
            except ValueError:
                RichPrintWarning(f"Value {value} for key {key} is not a valid float for Cost per Gram.")
                return str(value)
            return f"${value:.2f}/g"

        # Handle datetime formatting
        if correct_cat.categoryType == "date" or correct_cat.categoryType == "datetime":
            return TimeStampToStringWithFallback(value, "Can't parse date")
        
        # Handle grading display by displaying both letter and number regardless of internal setting
        if correct_cat.categoryRole == "Score" or correct_cat.categoryRole == "Final Score":
            numerical_value = None
            try:
                numerical_value = float(value)
            except ValueError:
                RichPrintWarning(f"Value {value} for key {key} is not a valid float for grading.")
                return str(value)
            letter_grade = getGradeLetterFuzzy(numerical_value)
            # Will return either None, just the Letter if exact match, or Letter (value) if fuzzy match, we want it to always be letter (value/5)
            if letter_grade:
                return f"{letter_grade.split(' (')[0]} ({numerical_value:.{correct_cat.rounding}f}/5)"
            else:
                return f"{numerical_value:.{correct_cat.rounding}f}"
            
        
        # Handle numeric formatting
        if isinstance(value, (int, float)):
            formatted_value = f"{value:.{correct_cat.rounding}f}"
            # if int
            if correct_cat.categoryType == "int":
                formatted_value = str(int(float(formatted_value)))
            return f"{correct_cat.prefix}{formatted_value}{correct_cat.suffix}"
        
        

        return str(value)
    
    def generate_review_outputs(self, review: Review, font_size: int = 24):
        """
        Ingests a Review object and creates a text-only review, an HTML review, and a PNG image.

        Args:
            review: A Review object.
            review_categories: A dictionary mapping attribute names to ReviewCategory objects.
            font_size: The font size to use for the image generation.

        Returns:
            A tuple containing (text_review, html_review, image_path).
        """

        # Get the tea parent for the name of the tea, the vendor, and other info
        overrideDoNotGenerateImage = False
        overrideDoNotgenerateTeaLevelAttributes = False
        overrideDoNotDrawGraphs_relativeBubbles = False

        
        teaParent = None
        for tea in TeaStash:
            if tea.id == review.parentID:
                teaParent = tea
                break

        if teaParent is None:
            RichPrintError(f"Could not find parent tea for review {review.name} with parent ID {review.parentID}")
            return None, None, None
        RichPrintInfo(f"Generating review outputs for review: {review.name} of tea: {teaParent.name}")
        sessionNum = 1
        for r in teaParent.reviews:
            if r.id == review.id:
                break
            sessionNum += 1
        teaYear = teaParent.attributes.get("Year", "")

        reviewAttributes = review.attributes.items()
        # Tea level attributes, for multiple reviews across one tea.
        hasTeaLevelAttributes = False
        # Check if there are reviews dated before this one
        allReviewsIncludingThisOne = []
        thisReviewTimestamp = review.attributes.get("date", None)
        for r in teaParent.reviews:
            if "date" in r.attributes and thisReviewTimestamp is not None:
                if r.attributes["date"] <= thisReviewTimestamp:
                    allReviewsIncludingThisOne.append(r)
        if len(allReviewsIncludingThisOne) <= 1:
            hasTeaLevelAttributes = False  # Only this review, no tea-level attributes
        else:
            hasTeaLevelAttributes = True
        RichPrintInfo(f"Found {len(allReviewsIncludingThisOne)} reviews including this one for tea {teaParent.name}")

        # Attributes to derive tea-level: Average ratio, Average rating, earliest review date, latest review date (this review), average time between reviews, total amount drank
        teaLevelAttributes = dict()
        formattedTeaLevelAttributes = dict()
        numReviewsIncludingThisOne = len(allReviewsIncludingThisOne)
        if hasTeaLevelAttributes:
            # Average ratio
            totalRatio = 0
            countRatio = 0
            for r in allReviewsIncludingThisOne:
                if "Score" in r.attributes:
                    try:
                        totalRatio += float(r.attributes["Score"])
                        countRatio += 1
                    except ValueError:
                        RichPrintWarning(f"Score {r.attributes['Score']} is not a valid float for review {r.name}")
            if countRatio > 0:
                teaLevelAttributes["Average Score"] = round(totalRatio / countRatio, 2)
            else:
                teaLevelAttributes["Average Score"] = "N/A"

            # Average rating
            totalRating = 0
            countRating = 0
            for r in allReviewsIncludingThisOne:
                if r.rating is not None:
                    try:
                        totalRating += float(r.rating)
                        countRating += 1
                    except ValueError:
                        RichPrintWarning(f"Rating {r.rating} is not a valid float for review {r.name}")
            if countRating > 0:
                teaLevelAttributes["Average Rating"] = round(totalRating / countRating, 2)
            else:
                teaLevelAttributes["Average Rating"] = "N/A"

            # Stdev of rating
            if countRating > 1:
                ratings = [r.rating for r in allReviewsIncludingThisOne if r.rating is not None]
                if len(ratings) > 1:
                    teaLevelAttributes["Rating Std Dev"] = round(stdev(ratings), 2)
                else:
                    teaLevelAttributes["Rating Std Dev"] = "N/A"

            # Earliest review date
            earliestDate = None
            for r in allReviewsIncludingThisOne:
                if "date" in r.attributes:
                    try:
                        review_date = dt.datetime.fromtimestamp(r.attributes["date"], tz=dt.timezone.utc)
                        if earliestDate is None or review_date < earliestDate:
                            earliestDate = review_date
                    except (ValueError, OSError):
                        RichPrintWarning(f"Date {r.attributes['date']} is not a valid timestamp for review {r.name}")
            if earliestDate is not None:
                teaLevelAttributes["First Reviewed"] = earliestDate.strftime(settings["DATE_FORMAT"])
            else:
                teaLevelAttributes["First Reviewed"] = "N/A"

            # Latest review date (this review)
            if "date" in review.attributes:
                try:
                    latestDate = dt.datetime.fromtimestamp(review.attributes["date"], tz=dt.timezone.utc)
                    teaLevelAttributes["Last Reviewed"] = latestDate.strftime(settings["DATE_FORMAT"])
                except (ValueError, OSError):
                    RichPrintWarning(f"Date {review.attributes['date']} is not a valid timestamp for review {review.name}")
                    teaLevelAttributes["Last Reviewed"] = "N/A"
            else:
                teaLevelAttributes["Last Reviewed"] = "N/A"


            # Average time between reviews
            daysBetweenFirstAndLast = 0
            if earliestDate is not None and latestDate is not None:
                daysBetweenFirstAndLast = (latestDate - earliestDate).days
                teaLevelAttributes["Days Between First and Last Review"] = daysBetweenFirstAndLast
            if numReviewsIncludingThisOne > 1 and daysBetweenFirstAndLast > 0:
                teaLevelAttributes["Average Time Between Reviews"] = daysBetweenFirstAndLast / numReviewsIncludingThisOne
            else:
                teaLevelAttributes["Average Time Between Reviews"] = "N/A"

            # Total amount drank
            totalAmount = 0
            for r in allReviewsIncludingThisOne:
                if "Amount" in r.attributes:
                    try:
                        totalAmount += float(r.attributes["Amount"])
                    except ValueError:
                        RichPrintWarning(f"Amount {r.attributes['Amount']} is not a valid float for review {r.name}")
            teaLevelAttributes["Total Amount Drank"] = f"{totalAmount:.2f} g"
        else:
            teaLevelAttributes["Average Score"] = "N/A"
            teaLevelAttributes["Average Rating"] = "N/A"
            teaLevelAttributes["First Reviewed"] = "N/A"
            if "date" in review.attributes:
                try:
                    latestDate = dt.datetime.fromtimestamp(review.attributes["date"], tz=dt.timezone.utc)
                    teaLevelAttributes["Last Reviewed"] = latestDate.strftime(settings["DATE_FORMAT"])
                except (ValueError, OSError):
                    RichPrintWarning(f"Date {review.attributes['date']} is not a valid timestamp for review {review.name}")
                    teaLevelAttributes["Last Reviewed"] = "N/A"
            else:
                teaLevelAttributes["Last Reviewed"] = "N/A"
            teaLevelAttributes["Average Time Between Reviews"] = "N/A"
            if "Amount" in review.attributes:
                try:
                    totalAmount = float(review.attributes["Amount"])
                    teaLevelAttributes["Total Amount Drank"] = totalAmount
                except ValueError:
                    RichPrintWarning(f"Amount {review.attributes['Amount']} is not a valid float for review {review.name}")
                    teaLevelAttributes["Total Amount Drank"] = "N/A"
            else:
                teaLevelAttributes["Total Amount Drank"] = "N/A"


        # If first reviewed is n/a but last reviewed is not, set first reviewed to last reviewed
        if teaLevelAttributes["First Reviewed"] == "N/A" and teaLevelAttributes["Last Reviewed"] != "N/A":
            teaLevelAttributes["First Reviewed"] = teaLevelAttributes["Last Reviewed"]



        # Formatted tea level attributes
        # Grade/rating should be formatted
        

        if isinstance(teaLevelAttributes.get("Average Score", None), (int, float)):
            formattedTeaLevelAttributes["Average Score"] = self.format_attribute("Score", teaLevelAttributes["Average Score"])
        if isinstance(teaLevelAttributes.get("Average Rating", None), (int, float)):
            formattedTeaLevelAttributes["Average Rating"] = f"{self.format_attribute("Final Score", teaLevelAttributes["Average Rating"])} (Std Dev: {teaLevelAttributes.get('Rating Std Dev', 'N/A')})"

        # if average rating is n/a, set to current rating
        if teaLevelAttributes.get("Average Rating", "N/A") == "N/A" and review.attributes.get("Final Score", None) is not None:
            formatted_value = self.format_attribute("Final Score", review.attributes["Final Score"])
            formattedTeaLevelAttributes["Average Rating"] = f"{formatted_value} (only one review)"

        # First , last, average review time before should  be combined into 1 line
        reviewDateString = ""
        if teaLevelAttributes.get("First Reviewed", "N/A") != "N/A" and teaLevelAttributes.get("Last Reviewed", "N/A") != "N/A":
            reviewDateString += f"From {teaLevelAttributes['First Reviewed']} to {teaLevelAttributes['Last Reviewed']}"
        else:
            reviewDateString += "N/A"
        if teaLevelAttributes.get("Average Time Between Reviews", "N/A") != "N/A":
            if reviewDateString != "":
                reviewDateString += ", "
            reviewDateString += f"avg. {teaLevelAttributes['Average Time Between Reviews']:.1f} days between reviews"
            if numReviewsIncludingThisOne <= 1:
                reviewDateString += " (only one review)"
            formattedTeaLevelAttributes["Review Dates"] = reviewDateString
        else:
            if reviewDateString != "":
                reviewDateString += "."
            formattedTeaLevelAttributes["Review Dates"] = reviewDateString
        # Amount drank and number of reviews, should include both total and avrg
        reviewAmtString = ""
        if teaLevelAttributes.get("Total Amount Drank", "N/A") != "N/A":
            if reviewAmtString != "":
                reviewAmtString += " "
            reviewAmtString += f"Total amount drank: {teaLevelAttributes['Total Amount Drank']}g over {numReviewsIncludingThisOne} review(s)."
        else:
            reviewAmtString += "N/A"
        
        formattedTeaLevelAttributes["Amount Drank"] = reviewAmtString



        # inject attribute from parent: Cost per gram if exists, don't inject vendor because this is already covered in the graphs
        if "Cost" in teaParent.attributes and "Amount" in teaParent.attributes:
            # Calculate cost per gram if possible
            cpg = teaParent.getCalcedValue("Cost per Gram")
            if cpg is not None:
                reviewAttributes = list(reviewAttributes) + [("Cost per Gram", cpg)]

        # Sort attributes to have notes at the end, date and type near the beginning
        sortedAttributes = sorted(reviewAttributes, key=lambda x: (("note" in x[0].lower(), x[0] != "date", x[0] != "Type", x[0])))
        reviewAttributes = sortedAttributes


        # Graph data getting
        thisTeaAverageRating = teaLevelAttributes["Average Rating"] if isinstance(teaLevelAttributes["Average Rating"], (int, float)) else review.attributes.get("Final Score", None)
        typeDatapts = getAverageRatingRange(teaType=teaParent.attributes.get("Type", None))
        vendorDatapts = getAverageRatingRange(vendor=teaParent.attributes.get("Vendor", None))
        allDatrapts = getAverageRatingRange()
        sumTypeData = 0
        totalTypeData = 0
        sumvendorData = 0
        totalvendorData = 0
        sumAllData = 0
        totalAllData = 0
        for pt in typeDatapts:
            sumTypeData += pt[0] * pt[2]
            totalTypeData += pt[2]
        for pt in vendorDatapts:
            sumvendorData += pt[0] * pt[2]
            totalvendorData += pt[2]
        for pt in allDatrapts:
            sumAllData += pt[0] * pt[2]
            totalAllData += pt[2]
        typeAvrg = sumTypeData / totalTypeData if totalTypeData > 0 else 0
        vendorAvrg = sumvendorData / totalvendorData if totalvendorData > 0 else 0
        allAvrg = sumAllData / totalAllData if totalAllData > 0 else 0


        # --- Text & HTML Review Generation ---
        doIncludeTeaYear = teaYear != "" and teaYear is not None
        # Dont include if year is already in the name
        if doIncludeTeaYear and str(teaYear) in teaParent.name:
            doIncludeTeaYear = False

        if doIncludeTeaYear:
            teaYear = str(teaYear) + " "
        else:
            teaYear = ""
        text_review = f"Session {sessionNum}: {teaYear}{teaParent.name}\n"
        html_review = f"<h3>Session {sessionNum}: {teaYear}{teaParent.name}</h3>\n"
        image_title = f"Session {sessionNum}: {teaYear}{teaParent.name}"

        for key, value in reviewAttributes:
            if key in ["Name", "dateAdded"]:  # Filter out redundant or internal fields
                continue
            # If word "note" in key, lookup and use category description
            #if "note" in key.lower():
            
            formatted_value = self.format_attribute(key, value)
            for cat in TeaReviewCategories:
                if cat.categoryRole == key:
                    key = cat.name
                    break
            text_review += f"\n{key}: {formatted_value}"
            html_review += f"  <li><b>{key}:</b> {formatted_value.replace(chr(10), '<br>')}</li>\n"

        if hasTeaLevelAttributes:
            text_review += "\n\n--- Cross-Review Summary ---"
            html_review += "\n<h4>--- Cross-Review Summary ---</h4>\n<ul>"
            for key, value in formattedTeaLevelAttributes.items():
                if value == "N/A":
                    continue
                text_review += f"\n{key}: {value}"
                html_review += f"  <li><b>{key}:</b> {value}</li>\n"

            # Add type and vendor average ratings if available as a sub for graphs
            if typeAvrg > 0:
                text_review += f"\n Teas of this type ({teaParent.attributes.get('Type', 'N/A')}) average {typeAvrg:.2f} rating. (t={len(typeDatapts)} data points)"
                html_review += f"  <li>Teas of this type ({teaParent.attributes.get('Type', 'N/A')}) average {typeAvrg:.2f} rating. (t={len(typeDatapts)} data points)</li>\n"
            if vendorAvrg > 0:
                text_review += f"\n Teas from this vendor ({teaParent.attributes.get('Vendor', 'N/A')}) average {vendorAvrg:.2f} rating. (t={len(vendorDatapts)} data points)"
                html_review += f"  <li>Teas from this vendor ({teaParent.attributes.get('Vendor', 'N/A')}) average {vendorAvrg:.2f} rating. (t={len(vendorDatapts)} data points)</li>\n"

        html_review += "</ul>"

        # --- Image Review Generation ---
        padding = 50
        image_width = 1200
        line_spacing = 12
        try:
            title_font = ImageFont.truetype("arialbd.ttf", size=font_size + 8)
            body_font = ImageFont.truetype("arial.ttf", size=font_size)
        except IOError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()

        # --- Calculate Dynamic Image Height ---
        current_y = padding
        # Title height
        current_y += title_font.getbbox(teaParent.name)[3] - title_font.getbbox(teaParent.name)[1] + line_spacing * 2

        # Attributes height
        reviewAttributes = sortedAttributes
        for key, value in reviewAttributes:
            if key in ["Name", "dateAdded"]:
                continue
            
            # If word "note" in key, lookup and use category description
            if "note" in key.lower():
                for cat in TeaReviewCategories:
                    if cat.categoryRole == key:
                        key = cat.name
                        break
            
            formatted_value = self.format_attribute(key, value)
            for cat in TeaReviewCategories:
                if cat.categoryRole == key:
                    key = cat.name
                    break
            key_text = f"{key}: "

            # Calculate height for the key
            key_height = (body_font.getbbox(key_text)[3] - body_font.getbbox(key_text)[1]) + 3

            # Calculate height for the wrapped value
            wrapped_lines = textwrap.wrap(str(formatted_value), width=90)
            value_height = len(wrapped_lines) * (key_height + line_spacing)

            current_y += value_height + line_spacing

        # Add tea-level attributes height if applicable
        if hasTeaLevelAttributes:
            current_y += title_font.getbbox("--- Cross-Review Summary ---")[3] - title_font.getbbox("--- Cross-Review Summary ---")[1] + line_spacing * 2
            for key, value in formattedTeaLevelAttributes.items():
                if value == "N/A":
                    continue
                key_text = f"{key}: "

                # Calculate height for the key
                key_height = (body_font.getbbox(key_text)[3] - body_font.getbbox(key_text)[1]) + 3

                # Calculate height for the wrapped value
                wrapped_lines = textwrap.wrap(str(value), width=90)
                value_height = len(wrapped_lines) * (key_height + line_spacing)

                current_y += value_height + line_spacing

        # Add space for graphs if applicable
        if not overrideDoNotDrawGraphs_relativeBubbles:
            current_y += 100  # Arbitrary space for graphs

        image_height = current_y + padding

        # --- Create and Draw Image ---
        img = Image.new('RGB', (image_width, image_height), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)

        # Draw Title
        current_y = padding
        draw.text((padding, current_y), image_title, fill=(0, 0, 0), font=title_font)
        current_y += title_font.getbbox(image_title)[3] - title_font.getbbox(image_title)[1] + line_spacing * 2

        # Draw Attributes
        for key, value in reviewAttributes:
            if key in ["Name", "dateAdded"]:
                continue

            formatted_value = self.format_attribute(key, value)
            for cat in TeaReviewCategories:
                if cat.categoryRole == key:
                    key = cat.name
                    break
            key_text = f"{key}: "

            # Get line height from a sample character
            line_height = (body_font.getbbox('A')[3] - body_font.getbbox('A')[1] + line_spacing)

            draw.text((padding, current_y), key_text, fill=(80, 80, 80), font=body_font)
            key_width = draw.textlength(key_text, font=body_font)

            # Handle multi-line values
            lines = str(formatted_value).split('\n')
            for i, line in enumerate(lines):
                wrapped_sublines = textwrap.wrap(line, width=90) # Adjust width as needed
                if not wrapped_sublines: # Handle empty lines
                     current_y += line_height 
                for sub_line in wrapped_sublines:
                    # Indent subsequent lines of a wrapped value
                    text_x = padding + key_width if i == 0 else padding + key_width + 20
                    draw.text((text_x, current_y), sub_line, fill=(0, 0, 0), font=body_font)
                    current_y += line_height
            current_y += line_spacing # Extra space between attributes

        # Draw Tea-level attributes if applicable
        if hasTeaLevelAttributes:
            draw.text((padding, current_y), "--- Cross-Review Summary ---", fill=(0, 0, 0), font=title_font)
            current_y += title_font.getbbox("--- Cross-Review Summary ---")[3] - title_font.getbbox("--- Cross-Review Summary ---")[1] + line_spacing * 2
            for key, value in formattedTeaLevelAttributes.items():
                if value == "N/A":
                    continue
                key_text = f"{key}: "

                # Get line height from a sample character
                line_height = body_font.getbbox('A')[3] - body_font.getbbox('A')[1] + line_spacing

                draw.text((padding, current_y), key_text, fill=(80, 80, 80), font=body_font)
                key_width = draw.textlength(key_text, font=body_font)

                # Handle multi-line values
                lines = str(value).split('\n')
                for i, line in enumerate(lines):
                    wrapped_sublines = textwrap.wrap(line, width=90)

                    if not wrapped_sublines: # Handle empty lines
                        current_y += line_height
                    for sub_line in wrapped_sublines:
                        # Indent subsequent lines of a wrapped value
                        text_x = padding + key_width if i == 0 else padding + key_width + 20
                        draw.text((text_x, current_y), sub_line, fill=(0, 0, 0), font=body_font)
                        current_y += line_height
                current_y += line_spacing # Extra space between attributes

        # Image only graphing
        chart_img_all = make_rating_bubble_image(allDatrapts, highlight=thisTeaAverageRating, name="All" +f" (t={totalAllData})")
        chart_img_type = make_rating_bubble_image(typeDatapts, highlight=thisTeaAverageRating, name="Type: " + teaParent.attributes.get("Type", "Unknown") +f" (t={totalTypeData})")
        chart_img_vendor = make_rating_bubble_image(vendorDatapts, highlight=thisTeaAverageRating, name="Vendor: " + teaParent.attributes.get("Vendor", "Unknown") +f" (t={totalvendorData})")
        
        # Group the images horizontally with a title.
        if not overrideDoNotDrawGraphs_relativeBubbles:
            chart_title = "Relative Rating Comparison"
            draw.text((padding, current_y), chart_title, fill=(0, 0, 0), font=body_font)
            current_y += body_font.getbbox(chart_title)[3] - body_font.getbbox(chart_title)[1] + line_spacing
            if chart_img_all is not None:
                img.paste(chart_img_all, (padding, current_y))
            if chart_img_type is not None:
                img.paste(chart_img_type, (padding + (chart_img_all.width if chart_img_all is not None else 0) + 20, current_y))
            if chart_img_vendor is not None:
                img.paste(chart_img_vendor, (padding + (chart_img_all.width if chart_img_all is not None else 0) + (chart_img_type.width if chart_img_type is not None else 0) + 40, current_y))
        current_y += max(chart_img_type.height, chart_img_vendor.height) + 20
        # --- Save Image ---


        # Save image to unique path with timestamp, review, parent id, parent name abridged, using underscores
        image_path = f"review_{review.id}_{review.parentID}_{sessionNum}_{teaParent.name[:20].replace(' ', '_')}_{int(dt.datetime.now().timestamp())}.png"
        img.save(image_path)
        RichPrintSuccess(f"Generated review image at {image_path}")

        return text_review, html_review, image_path

#endregion

#region Window Classes
class WindowBase:
    tag = 0
    dpgWindow = None
    exclusive = False
    persist = False
    utitle = ""
    refreshing = False  # Flag to prevent multiple refreshes at the same time
    def __init__(self, title, width, height, exclusive=False):
        self.title = title
        self.width = width
        self.height = height
        self.exclusive = exclusive

        # if not exclusive, create a random number to add to the title
        self.utitle = title
        if not exclusive:
            rand = uuid.uuid4().hex[:6]
            self.utitle = f"{title} {rand}"
            while self.utitle in windowManager.windows:
                rand = uuid.uuid4().hex[:6]
                self.utitle = f"{title} {rand}"
        
        # add the window to the window manager, if exclusive, overwrite the title
        if exclusive and self.utitle in windowManager.windows:
            windowManager.deleteWindow(self.utitle)
        windowManager.windows[self.utitle] = self
            
        self.onCreateFirstTime()
        self.create()

    def onResizedWindow(self, sender, data):
        RichPrintInfo("[RESIZE] Window resized")
    
    def create(self):
        self.onCreate()
        self.dpgWindow = dp.Window(label=self.title, on_close=self.onDelete)
        self.dpgWindow.width = self.width
        self.dpgWindow.height = self.height
        self.tag = self.dpgWindow.tag
        # Bind resize callback
        self.windowDefintion(self.dpgWindow)

        RichPrintInfo(f"Created window: {self.title} with tag: {self.tag} and exclusive: {self.exclusive}")
        return self.dpgWindow
    def getTag(self):
        return self.tag
    def delete(self):
        self.onDelete()
        if self.dpgWindow is not None and self.dpgWindow.exists():
            dpg.delete_item(self.tag)
        
    def refresh(self):
        # refresh the window
        self.refreshing = True
        RichPrintInfo(f"[REFRESH] Refreshing window tag: {self.tag} title: {self.title}")
        self.onRefresh()
        dpg.delete_item(self.tag)
        self.create()
        self.refreshing = False

    def softRefresh(self):
        # soft refresh the window, does not delete the window, just refreshes the content
        RichPrintInfo(f"[SOFT REFRESH] Soft refreshing window tag: {self.tag} title: {self.title}")
        self.refreshing = True
        if self.dpgWindow is not None and self.dpgWindow.exists():
            dpg.delete_item(self.tag, children_only=True)  # Delete only the children of the window
            self.windowDefintion(self.dpgWindow)  # Recreate the window content
            self.onSoftRefresh()
            

    def onCreateFirstTime(self):
        # triggers when the window is created for the first time
        pass

    def onCreate(self):
        # triggers when the window is created
        pass
    def onRefresh(self):
        # triggers when the window is refreshed
        pass
    def onSoftRefresh(self):
        # triggers when the window is soft refreshed
        pass
    def onDelete(self):
        # triggers when the window is deleted
        
        # removes the window from the window manager
        print(f"[DELETE] Deleting window: {self.title} with tag: {self.tag}")
        windowManager.deleteWindow(self.utitle)

    def DummyCallback(self, sender, data):
        print(f"Sender: {sender}, Data: {data}")

    def exportYML(self):
        # export the window variables to array in string format to write to file
        pass
    def importYML(self, data):
        # import the window variables from array in string format
        pass

    def resizeToWH(self, width, height):
        self.width = width
        self.height = height
        if self.dpgWindow is not None and self.dpgWindow.exists():
            dpg.set_item_width(self.tag, width)
            dpg.set_item_height(self.tag, height)

def Menu_Timer(sender, app_data, user_data):
    w = 250 * settings["UI_SCALE"]
    h = 300 * settings["UI_SCALE"]
    timer = Window_Timer("Timer", w, h, exclusive=False)
    if user_data is not None:
        timer.importYML(user_data)

# Window for timer
class Window_Timer(WindowBase):
    timer = 0
    timerRunning = False
    startTime = 0
    threadTracking = None
    stopThreadFlag = False
    display = None
    rawDisplay = None
    childWindow = None
    previousTimes = []
    window = None
    titleText = ""
    titleTextObject = None
    buttonObject = None
    def onCreateFirstTime(self):
        # init new addresses for variables
        self.previousTimes = list()
    def onCreate(self):
        self.timer = 0
        self.persist = True
    def onRefresh(self):
        self.timer = 0
    def onDelete(self):
        self.timer = 0
        self.timerRunning = False

        # don't wait for the thread to finish
        if self.threadTracking is not None:
            self.stopThreadFlag = True
            self.threadTracking.join()
        RichPrintInfo("[THREAD] Stopped thread for timer tracking")

        return super().onDelete()

    def windowDefintion(self, window: dp.mvWindow):
        self.window = window
        # disable scrolling
        window.no_scrollbar = True
        with window:
            # Editable label for the timer
            if settings["TIMER_WINDOW_LABEL"]:
                with dp.Group(horizontal=True):
                    if self.titleText == "":
                        self.titleText = "Tea! "
                    dp.Text(label="Timer for... ", default_value="Timer for... ")
                    # increase font size
                    dpg.bind_item_font(dpg.last_item(), getFontName(2))
                    width = 125 * settings["UI_SCALE"]
                    self.titleTextObject = dp.InputText(default_value=self.titleText, width=width, multiline=False, callback=self.updateTitleText)
                    dpg.bind_item_font(dpg.last_item(), getFontName(2))

            self.display = dp.Text(label=f"{self.formatTimeDisplay(self.timer)}")
            dpg.bind_item_font(dpg.last_item(), getFontName(3))

            # in horizontal layout
            with dp.Group(horizontal=True):

                # Timer buttons
                # Toggle between start and stop
                self.buttonObject = dp.Button(label="Start", callback=self.startOrStopTimer)
                dpg.bind_item_font(dpg.last_item(), getFontName(3))
                dp.Button(label="Reset", callback=self.resetTimer)
                dpg.bind_item_font(dpg.last_item(), getFontName(3))

                dp.Checkbox(label="Persist", default_value=self.persist, callback=self.updatePersist)
                # Tooltip
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    tooltipText = RateaTexts.ListTextHelpMenu["menuStopwatchHelp"].wrap()
                    dp.Text(tooltipText)

            # Group that contains an input text raw and a button to copy to clipboard
            with dp.Group(horizontal=True):
                dp.Button(label="Copy", callback=self.copyRawTimeToClipboard)
                width = 125 * settings["UI_SCALE"]
                self.rawDisplay = dp.InputText(default_value="Raw Times", readonly=True, callback=self.updateDefaultValueDisplay, width=width)
                
            # Save and load buttons
            with dp.Group(horizontal=True):
                dp.Button(label="Import", callback=self.importPersistedData)
                dp.Button(label="Save", callback=self.savePersistedData)

        # child window logging up to 30 previous times
        self.updateChildWindow()
        
        self.threadTracking = threading.Thread(target=self.updateTimerLoop)
        RichPrintInfo(f"[THREAD] Starting thread for timer tracking on window: {self.title}")
        self.threadTracking.start()

    def updateTitleText(self, sender, data, user_data):
        self.titleText = data
    def updateDefaultValueDisplay(self):
        times = "["
        for i, time in enumerate(self.previousTimes):
            times += f"{time:.2f}"
            if i < len(self.previousTimes) - 1:
                times += ", "
        times += "]"
        self.rawDisplay.set_value(times)

    def copyRawTimeToClipboard(self):
        times = "["
        for i, time in enumerate(self.previousTimes):
            times += f"{time:.2f}"
            if i < len(self.previousTimes) - 1:
                times += ", "
        times += "]"
        # copy to clipboard with pyperclip
        pyperclip.copy(times)
        RichPrintSuccess(f"Copied Timer times: {times} to clipboard")

    def importPersistedData(self, sender, app_data, user_data):
        # Call window manager to get data, then call importYML to set the text input value
        data = windowManager.importOneWindow(sender, app_data, "Timer")
        if data is not None:
            self.importYML(data)
        else:
            RichPrintError("No persisted data found for Notepad.")
            return
        
    def savePersistedData(self, sender, app_data, user_data):
        # Call global export persisted data function to save the notepad text
        if self.persist and self.text != "":
            windowManager.exportOneWindow(sender, app_data, "Timer")
        

    def updateChildWindow(self):
        if self.childWindow is not None:
            print(type(self.childWindow), self.childWindow.tag)
            self.childWindow.delete()
        w = 225 * settings["UI_SCALE"]
        h = 200 * settings["UI_SCALE"]
        self.childWindow = dp.ChildWindow(label="Previous Times (max 30)", width=w, height=h, parent=self.window)
        with self.childWindow:
            # add it in reverse order sop latest is at the top
            reversedTimes = self.previousTimes[::-1]
            dp.Text(f"Previous Times ({len(reversedTimes)})")
            dpg.bind_item_font(dpg.last_item(), getFontName(2))
            for i, time in enumerate(reversedTimes):
                with dp.Group(horizontal=True):
                    dp.Button(label="Remove", callback=self.removeOneTime, user_data=i)
                    dp.Text(f"{len(reversedTimes) - i}: {self.formatTimeDisplay(time)}", color=(100, 255, 100, 255))
        
    def startOrStopTimer(self, sender, app_data):
        # Starts or stops the timer, changes the button label
        if self.timerRunning:
            self.stopTimer()
            self.buttonObject.label = "Start"
        else:
            self.startTimer()
            self.buttonObject.label = "Stop"

    def startTimer(self):
        self.timerRunning = True
        self.startTime = time.time()
    def stopTimer(self):
        self.timerRunning = False
        self.previousTimes.append(self.timer)
        if len(self.previousTimes) > 30:
            self.previousTimes.pop(0)
        self.updateChildWindow()
        self.updateDefaultValueDisplay()

        
    def resetTimer(self):
        self.timer = 0
        self.timerRunning = False
        self.display.set_value(self.formatTimeDisplay(self.timer))
        self.previousTimes = []
        self.buttonObject.label = "Start"
        self.updateChildWindow()
        self.updateDefaultValueDisplay()

    def removeOneTime(self, sender, app_data, user_data):
        self.previousTimes.pop(user_data)
        self.updateChildWindow()
        self.updateDefaultValueDisplay()

    def formatTimeDisplay(self, timeRaw):
        s, m, h = 0, 0, 0
        displayResult = f"{timeRaw:.2f}"
        if timeRaw > 60:
            s = timeRaw % 60
            m = timeRaw // 60
            # minute and hours are ints
            displayResult = f"{int(m):02d}:{s:05.2f} ({timeRaw:.2f}s)"
        if m > 60:
            m = timeRaw % 60
            h = timeRaw // 60
            displayResult = f"{int(h):02d}:{int(m):02d}:{s:05.2f} ({timeRaw:.2f}s)"
        return displayResult
    
    # Thread update 10x per second
    def updateTimerLoop(self):
        while not self.stopThreadFlag:
            if self.timerRunning:
                self.timer = time.time() - self.startTime
                self.display.set_value(self.formatTimeDisplay(self.timer))
            time.sleep(0.09)

    def updatePersist(self, sender, data):
        self.persist = data

    def exportYML(self):
        windowVars = {
            "timer": self.timer,
            "startTime": self.startTime,
            "previousTimes": self.previousTimes,
            "timerWindowLabel": self.titleText,
            "width": self.width,
            "height": self.height
        }
        return windowVars
    
    def importYML(self, data):
        self.timer = data["timer"]
        self.startTime = data["startTime"]
        self.previousTimes = data["previousTimes"]
        self.width = data["width"]
        self.height = data["height"]
        self.display.set_value(self.formatTimeDisplay(self.timer))
        self.titleText = data["timerWindowLabel"]
        self.titleTextObject.set_value(self.titleText)
        self.updateChildWindow()
        self.updateDefaultValueDisplay()

        # set the label to not run the timer
        if self.timerRunning:
            self.timerRunning = False
            self.buttonObject.label = "Start"
            RichPrintInfo("Imported timer data, stopped the timer.")


def Menu_Settings():
    w = 500 * settings["UI_SCALE"]
    h = 500 * settings["UI_SCALE"]
    settingsWindow = Window_Settings("Settings", w, h, exclusive=True)

class Window_Settings(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("Settings")
            dp.Text("Username")
            dp.InputText(label="Username", default_value=settings["USERNAME"], callback=self.UpdateSettings, user_data="USERNAME")
            dp.Text("Directory")
            dp.InputText(label="Directory", default_value=settings["DIRECTORY"], callback=self.UpdateSettings, user_data="DIRECTORY")
            dp.Button(label="Reset Settings", callback=self.ResetSettings)
            dp.Text("Date Format")
            # Dropdown for date format
            dateFormats = ["YYYY-MM-DD", "MM-DD-YYYY", "DD-MM-YYYY", "YYYY/MM/DD", "MM/DD/YYYY", "DD/MM/YYYY"]
            defaultDateTimeFormat = settings["DATE_FORMAT"].replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")
            dp.Combo(label="Date Format", items=dateFormats, default_value=defaultDateTimeFormat, callback=self.UpdateDateTimeFormat, user_data="DATE_FORMAT")
            dp.Text("Timezones (Not really used)")
            timezones = ["UTC"]
            defaultTimezone = settings["TIMEZONE"]
            dp.Combo(label="Timezone", items=timezones, default_value=defaultTimezone, callback=self.UpdateSettings, user_data="TIMEZONE")
            dp.Text("UI/UX")
            # Slider for UI scale
            dp.SliderFloat(label="UI Scale", default_value=settings["UI_SCALE"], min_value=0.5, max_value=2.0, callback=self.UpdateSettings, user_data="UI_SCALE")
            # Chevckbox for window label for timer
            dp.Checkbox(label="Timer Window Label", default_value=True, callback=self.UpdateSettings, user_data="TIMER_WINDOW_LABEL")
            dp.Separator()

            # Autosave
            dp.Text("Autosave")
            dp.Checkbox(label="Autosave", default_value=settings["AUTO_SAVE"], callback=self.UpdateSettings, user_data="AUTOSAVE")
            dp.Text("Autosave Interval (Minutes)")
            dp.InputInt(label="Autosave Interval", default_value=settings["AUTO_SAVE_INTERVAL"], callback=self.UpdateSettings, user_data="AUTO_SAVE_INTERVAL")

            # Fonts
            dp.Text("Font (Need to refresh program to apply)")
            # Dropdown
            validFonts = session["validFonts"]
            defaultFont = getFontName(1)  # Default font is the first one in the list
            dp.Combo(label="Font", items=validFonts, default_value=defaultFont, callback=self.UpdateSettings, user_data="DEFAULT_FONT")

    # Callback function for the input text to update the settings
    def UpdateSettings(self, sender, data, user_data):
        settings[user_data] = data
        Settings_SaveCurrentSettings()
        # ui scale
        if user_data == "UI_SCALE":
            uiscale = round(data, 2)
            settings["UI_SCALE"] = uiscale
            # Update the UI scale
            dpg.set_global_font_scale(uiscale)

        # Start/Stop Autosave
        if user_data == "AUTOSAVE":
            shouldStart = settings["AUTO_SAVE"]
            startStopBackupThread(shouldStart) # Starts or stops the autosave thread

        # Update font
        if user_data == "DEFAULT_FONT":
            # Set the font for all windows
            dpg.set_global_font_scale(settings["UI_SCALE"])
            dpg.bind_font(getFontName(1, fontName=data))  # Bind the font to the global context

    def UpdateDateTimeFormat(self, sender, data):
        rawDropdown = str(data)
        dropdown = rawDropdown.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
        settings["DATE_FORMAT"] = dropdown
        print(settings["DATE_FORMAT"])
        Settings_SaveCurrentSettings()
    
    
    def ResetSettings(self, sender, data):
        settings = default_settings
        Settings_SaveCurrentSettings()
        self.softRefresh()


def Menu_Stash_Reviews(sender, app_data, user_data):
    w = 600 * settings["UI_SCALE"]
    h = 960 * settings["UI_SCALE"]
    stashReviews = Window_Stash_Reviews("Stash Reviews", w, h, exclusive=True, parentWindow=user_data[0], tea=user_data[1])

class Window_Stash_Reviews(WindowBase):
    parentWindow = None
    tea = None
    addReviewList = list()
    reviewsWindow = None
    editReviewsWindow = None
    refreshIcon = None
    def ShowAddReview(self, sender, app_data, user_data):
        # Call Edit review with Add
        tea = user_data[0]
        operation = user_data[1]
        self.GenerateEditReviewWindow(sender, app_data, user_data=(None, operation, tea))  # Pass None for review to indicate new review
    def AddReview(self, sender, app_data, user_data):
        # Add a review to the tea
        timeStartAdd = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        allAttributes = {}
        teaID = user_data.id
        for k, v in self.addReviewList.items():
            if type(v) == dp.DatePicker:
                allAttributes[k] = DateDictToDT(v.get_value())
            else:
                val = v.get_value()
                # If float, round to 3 decimal places
                if type(val) == float:
                    val = round(val, 3)

                # If string, strip, and remove quotes
                if type(val) == str:
                    if k == "Notes (Long)":
                        val = RateaTexts.sanitizeInputMultiLineString(val)
                    elif "Score" in k:
                        # Stored as a float, but displayed as a letter grade
                        val = getGradeValue(val)
                    else:
                        val = RateaTexts.sanitizeInputLineString(val)
                allAttributes[k] = val

        if "dateAdded" not in allAttributes:
            allAttributes["dateAdded"] = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        if "Final Score" not in allAttributes:
            allAttributes["Final Score"] = 0

        newReview = Review(teaID, user_data.name, allAttributes["dateAdded"], allAttributes["attributes"], allAttributes["Final Score"])
        user_data.addReview(newReview)

        # Renumber and Save
        renumberTeasAndReviews(save=True)  # Renumber teas and reviews to keep IDs consistent
        
        # close the popup
        dpg.configure_item(self.reviewsWindow.tag, show=False)
        self.softRefresh()
        timeEndAdd = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        RichPrintSuccess(f"Added review for {user_data.name} in {timeEndAdd - timeStartAdd:.2f}s")

    def GenerateEditReviewWindow(self, sender, app_data, user_data):
        # Create a new window for editing the review
        w = 620 * settings["UI_SCALE"]
        h = 720 * settings["UI_SCALE"]

        itemType = "Review"
        
        editReviewWindowItems = dict()
        review = user_data[0]
        parentTea = user_data[2]
        operation = user_data[1]  # "edit" or "add"


        if operation != "edit":
            # Assume add, drop review data if provided
            review = None

        windowName = ""
        if operation == "edit":
            windowName = f"Edit | {itemType} | {review.id} - {parentTea.name}"
        elif operation == "add":
            windowName = f"Add | {itemType} | - {parentTea.name}"
        elif operation == "duplicate":
            # Get last review
            lastReview = parentTea.reviews[-1] if parentTea.reviews else None
            if lastReview is not None:
                review = Review(lastReview.id, lastReview.name, lastReview.dateAdded, lastReview.attributes.copy(), lastReview.rating)
                review.id = len(parentTea.reviews)  # New review ID is the length of existing reviews
                windowName = f"Duplicate | {itemType} | {review.id} - {parentTea.name}"
            # Duplicate the review, but don't save it yet
            else:
                # Change operation to add if no last review
                operation = "add"
                windowName = f"Add Review (No reviews to duplicate) - {parentTea.name}"
           
           
            # Set the ID to the length of the existing reviews
            review.id = len(parentTea.reviews)  # New review ID is the length of existing reviews


        self.editReviewWindow = dp.Window(label=windowName, width=w, height=h, modal=False, show=True)
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        windowManager.addSubWindow(self.editReviewWindow)

        nameReview = ""
        parentName = ""
        idReview = 0
        
        if review is not None:
            idReview = review.id
            nameReview = review.name
            if review.attributes == None or review.attributes == "":
                review.attributes = {}
            if review.name == None or review.name == "":
                # Get from name of parent
                for i, tea in enumerate(TeaStash):
                    if tea.id == review.parentID:
                        parentName = tea.name
                        idReview = i
                        break
        else:
            idReview = len(parentTea.reviews)  # New review ID is the length of existing reviews
            nameReview = parentTea.name
        


            
        with self.editReviewWindow:
            # Add a title
            if operation == "edit":
                dp.Text(f"Edit Review {idReview}:\n{nameReview}")
                dpg.bind_item_font(dpg.last_item(), getFontName(3, bold=True))
            elif operation == "duplicate":
                # Add a title for duplicating the review
                dp.Text(f"Duplicate Review {idReview}:\n{nameReview}")
                dpg.bind_item_font(dpg.last_item(), getFontName(3, bold=True))
            elif operation == "add":
                # Add a title for adding a new review
                dp.Text(f"Add New Review {idReview} - Parent Tea:\n{parentTea.name}")
                dpg.bind_item_font(dpg.last_item(), getFontName(3, bold=True))


            for cat in TeaReviewCategories:
                cat: ReviewCategory
                # Add it to the window
                catName = cat.name


                # Text indicators for required and auto calculated
                dp.Separator()
                with dp.Group(horizontal=True):
                    if cat.isRequiredForTea:
                        dp.Text("[required]", color=COLOR_REQUIRED_TEXT)
                    dp.Text(catName)

                    if cat.isAutoCalculated:
                        # If auto calculated, don't show the input
                        catItem = dp.Text(label=f"(Auto)", color=COLOR_AUTO_CALCULATED_TEXT)
                defaultValue = None

                try:
                    defaultValue = review.attributes[cat.categoryRole]
                except:
                    # also try to get from nameReview if review is None
                    defaultValue = f"{cat.defaultValue}"

                # Get the past answers for the category for dropdowns
                pastAnswers, pastAnswersList = searchPreviousAnswers(cat.categoryRole, data="Review", topX=cat.dropdownMaxLength)
                shouldShowDropdown = True if len(pastAnswers) > 0 and cat.isDropdown else False
                # If past answers are a timestamp, convert them to a readable format
                if cat.categoryType == "date" or cat.categoryType == "datetime":
                    # Convert to a readable format
                    pastAnswersTextList = [f"{x[1]} - {TimeStampToString(x[0])}" for x in pastAnswers]
                else:
                    # For other types, just use the string representation
                    pastAnswersTextList = [f"({x[1]}) - ({x[0]})" for x in pastAnswers]

                catItem = None
                
                # If the category is a string, int, float, or bool, add the appropriate input type
                if cat.categoryType == "string":
                    if cat.categoryRole == "Name":
                        # For the name, use a single line input text
                        catItem = dp.InputText(default_value=str(nameReview), width=480 * settings["UI_SCALE"])
    
                    elif cat.categoryRole == "Notes (Long)" or cat.categoryRole == "Notes":
                        # For notes, allow multiline input
                        height = 220 * settings["UI_SCALE"]
                        catItem = dp.InputText(default_value=str(defaultValue), multiline=True, height=height, width=480 * settings["UI_SCALE"])
                        
                    else:
                        # For other strings, single line input
                        catItem = dp.InputText(default_value=defaultValue, width=480 * settings["UI_SCALE"])
    
                        if shouldShowDropdown:
                            # Add a dropdown for the past answers
                            dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "string"))
        
                elif cat.categoryType == "int":
                    catItem = dp.InputInt(default_value=int(defaultValue), width=480 * settings["UI_SCALE"])

                    if shouldShowDropdown:
                        # Add a dropdown for the past answers
                        dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "int"))
    
                elif cat.categoryType == "float":
                    if ("Score" in cat.categoryRole) and cat.gradingDisplayAsLetter:
                        # For grading, use a predefined dropdown and then convert to float upon entry
                        gradingOptions = getGradeList()
                        defaultValue = getGradeDropdownValueByFloat(float(defaultValue))
                        catItem = dp.Combo(items=gradingOptions, default_value=defaultValue)
                    else:
                        catItem = dp.InputFloat(default_value=float(defaultValue), step=1.0, format="%.2f", width=480 * settings["UI_SCALE"])

                        if shouldShowDropdown:
                            # Add a dropdown for the past answers
                            dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "float"))
    
                elif cat.categoryType == "bool":
                    if defaultValue == "True" or defaultValue == True:
                        defaultValue = True
                    else:
                        defaultValue = False
                    catItem = dp.Checkbox(label=cat.name, default_value=bool(defaultValue))

                elif cat.categoryType == "date" or cat.categoryType == "datetime":
                    # Date picker widget
                    if defaultValue is None or defaultValue == "":
                        defaultValue = dt.datetime.now(tz=dt.timezone.utc).timestamp()
                        defaultValue = TimeStampToDateDict(defaultValue)
                    else:
                        defaultValue = TimeStampToDateDict(AnyDTFormatToTimeStamp(defaultValue))
                    # If supported, display as date
                    catItem =  dp.DatePicker(level=dpg.mvDatePickerLevel_Day, label=cat.name, default_value=defaultValue, width=480 * settings["UI_SCALE"])

                    if shouldShowDropdown:
                        # Add a dropdown for the past answers
                        dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "date"))
    
                else:
                    catItem = dp.InputText(default_value=f"Not Supported (Assume String): {cat.categoryType}, {cat.name}", width=480 * settings["UI_SCALE"])

                    if shouldShowDropdown:
                        # Add a dropdown for the past answers
                        dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "string"))
    

                if catItem is not None:
                    editReviewWindowItems[cat.categoryRole] = catItem
                    
            # Button to add the review
            dp.Separator()
            with dp.Group(horizontal=True):
                dpg.bind_item_font(dpg.last_item(), getFontName(3))
                buttonLabel = "Add Review"
                if operation == "edit":
                    buttonLabel = "Save Changes"
                elif operation == "duplicate":
                    buttonLabel = "Duplicate Review"
                dp.Button(label=buttonLabel, callback=self.validateAddEditReview, user_data=(review, editReviewWindowItems, self.editReviewWindow, operation))
                if operation == "edit":
                    dp.Button(label="Delete Review", callback=self.deleteReview, user_data=(review, parentTea))
                dp.Button(label="Cancel", callback=self.deleteEditReviewWindow)

    def deleteReview(self, sender, app_data, user_data):
        # Delete the review from the tea
        review = user_data[0]
        tea = user_data[1]
        if review is not None:
            tea: StashedTea
            tea.reviews = [r for r in tea.reviews if r.id != review.id]
            # Remove the review from the stash
            RichPrintSuccess(f"Deleted review {review.id} from tea {tea.name}")
            renumberTeasAndReviews(save=True)

        # Close the edit review window
        dpg.configure_item(self.editReviewWindow.tag, show=False)
        self.softRefresh()
            
    
    def validateAddEditReview(self, sender, app_data, user_data):
        review = user_data[0]
        editReviewWindowItems = user_data[1]

        isValid = True

        # Null check
        if review is None and editReviewWindowItems is None:
            RichPrintError("No review or editReviewWindowItems provided.")
            return False

        # Validate name
        parentTea = None
        if review is not None and review.parentID is not None:
            for i, tea in enumerate(TeaStash):
                if tea.id == review.parentID:
                    parentTea = tea
                    break
            else:
            # If review is None, we are adding a new review, so set the parent tea to the current tea
                parentTea = self.tea

        if review is not None:
            if review.name == "" or review.name is None:
                # Review name can be empty but it should instead be set to the tea name
                if parentTea is not None:
                    review.name = parentTea.name.strip()
                    RichPrintWarning("Review name is empty. Setting to tea name.")
                else:
                    RichPrintError("Review name cannot be empty.")
                    isValid = False

        # Strip and remove invalid quotes from name
        if "Name" in editReviewWindowItems:
            name = editReviewWindowItems["Name"].get_value()
            if name is None or name.strip() == "":
                RichPrintError("Review name cannot be empty.")
                isValid = False
            else:
                # Remove invalid quotes
                name = name.replace("\"", "").replace("'", "")
                editReviewWindowItems["Name"].set_value(name)
                if review is not None:
                    review.name = name
        
        # Check based on required fields
        for cat in TeaReviewCategories:
            cat: ReviewCategory
            if cat.categoryRole == "Name":
                # Name is handled above
                continue
            if cat.isRequiredForTea and cat.categoryRole not in editReviewWindowItems:
                RichPrintError(f"{cat.name} is required for tea.")
                isValid = False
            if cat.isRequiredForAll and cat.categoryRole not in editReviewWindowItems:
                RichPrintError(f"{cat.name} is required for all.")
                isValid = False

        # Act on the result
        if isValid:
            RichPrintSuccessMinor("Review edit/add passed validation.")
            self.EditAddReview(sender, app_data, user_data)
        else:
            RichPrintError("Review is not valid. Please check the fields.")
            return False
        

    def UpdateInputWithDropdownSelelction(self, sender, app_data, user_data):
        # Update the input with the new value
        typeOfValue = user_data[2]
        # Exclude default value "Past Answers"
        if app_data == "Past Answers":
            RichPrintWarning("Warning: \"Past Answers\" is not a valid selection.")
            return
        
        # Get the input item and the past answers
        if user_data[0]:
            splits = app_data.split(" - ")
            if len(splits) > 2:
                newSelectedValue = splits[1:]
                newSelectedValue = " - ".join(newSelectedValue).strip()
            else:
                newSelectedValue = splits[1].strip()
            # Remove parentheses if they exist
            if newSelectedValue.startswith("(") and newSelectedValue.endswith(")"):
                newSelectedValue = newnewSelectedValue = newSelectedValue[1:-1]


            # If typeOfValue is int or float, attempt to convert
            if typeOfValue == "int":
                try:
                    newSelectedValue = int(newSelectedValue)
                except ValueError:
                    RichPrintError(f"Error: {newSelectedValue} is not a valid integer.")
                    return
            elif typeOfValue == "float":
                try:
                    newSelectedValue = float(newSelectedValue)
                except ValueError:
                    RichPrintError(f"Error: {newSelectedValue} is not a valid float.")
                    return
            elif typeOfValue == "date" or typeOfValue == "datetime":
                # Convert string date to datetime object
                try:
                    newSelectedValue = TimeStampToDateDict(StringToTimeStamp(newSelectedValue))
                except TypeError:
                    # Convert date string to timestamp
                    try:
                        newSelectedValue = StringToTimeStamp(newSelectedValue)
                        newSelectedValue = TimeStampToDateDict(newSelectedValue)
                    except ValueError:
                        RichPrintError(f"Error: {newSelectedValue} is not a valid date.")
                        return
            # Set the value of the input item to the new value
            user_data[0].set_value(newSelectedValue)
        else:
            RichPrintError(f"Error: {user_data} not found in addTeaList.")


    def EditAddReview(self, sender, app_data, user_data):
        # Get the tea from the stash
        startAddEdit = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        review = user_data[0]
        teaId = review.parentID if review else None
        editReviewWindowItems = user_data[1]
        operation = user_data[3]  # Check if it's an edit or add operation
        if operation != "edit":
            review = None
            teaId = self.tea.id
            


        # All input texts and other input widgets are in the addTeaGroup
        # Revise the tea and save it to the stash, overwriting the old one
        allAttributes = {}
        for k in editReviewWindowItems:
            v = editReviewWindowItems[k]
            if type(v) == dp.DatePicker:
                allAttributes[k] = DateDictToDT(v.get_value())
            else:
                val = v.get_value()
                # If float, round to 3 decimal places
                if type(val) == float:
                    val = round(val, 3)

                # If string, strip, and remove quotes
                if type(val) == str:
                    if k == "Notes (Long)":
                        val = RateaTexts.sanitizeInputMultiLineString(val)
                    elif "Score" in k:
                        # Stored as a float, but displayed as a letter grade
                        val = getGradeValue(val)
                    else:
                        val = RateaTexts.sanitizeInputLineString(val)
                allAttributes[k] = val


        # Infer name from allAttributes if avaliable, review or parent else
        reviewName = ""
        if "Name" in allAttributes and allAttributes["Name"].strip() != "":
            reviewName = allAttributes["Name"].strip()
        elif review is not None and review.name.strip() != "":
            reviewName = review.name.strip()
        elif self.tea is not None:
            reviewName = self.tea.name.strip()
        else:
            RichPrintError("No review name provided and no parent tea found. Cannot save review.")
            return
        
        # Get dateAdded from allAttributes or use current time
        if "dateAdded" not in allAttributes:
            allAttributes["dateAdded"] = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        if "Final Score" not in allAttributes:
            allAttributes["Final Score"] = 0

        

        newReview = Review(teaId, reviewName, allAttributes["dateAdded"], allAttributes, allAttributes["Final Score"])
        hasModified = False
        if operation == "edit":
            # Transfer the reviews
            for i, tea in enumerate(TeaStash):
                if tea.id == teaId:
                    # Find the review and replace it
                    for j, rev in enumerate(tea.reviews):
                        if rev == review:
                            TeaStash[i].reviews[j] = newReview
                            hasModified = True
                            break
                    if hasModified:
                        break
            if not hasModified:
                RichPrintError(f"Review with ID {review.id} not found in tea {teaId}. Cannot edit review.")
                return
        else:
            # Append to the tea's reviews if it's a new review
            for i, tea in enumerate(TeaStash):
                if tea.id == teaId:
                    TeaStash[i].addReview(newReview)
                    break
        
        # Renumber and Save
        renumberTeasAndReviews(save=True)  # Renumber teas and reviews to keep IDs consistent
        

        # hide the popup
        dpg.configure_item(self.reviewsWindow.tag, show=False)
        self.deleteEditReviewWindow()
        # Refresh the window
        self.softRefresh()
        # Close the edit review window
        if self.editReviewWindow is not None:
            self.editReviewWindow.delete()
            self.editReviewWindow = None
        endAddEdit = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        RichPrintSuccess(f"Added/Edited review in {endAddEdit - startAddEdit:.2f}s for {newReview.name} with ID {newReview.id}")

    def __init__(self, title, width, height, exclusive=False, parentWindow=None, tea=None):
        self.parentWindow = parentWindow
        self.tea = tea
        super().__init__(title, width, height, exclusive)

    def softRefresh(self):
        # Refresh the stats window
        reCacheStats()
        super().softRefresh()
        
    def afterWindowDefinition(self):
        # After the window is defined, we can set the callback for the soft refresh
        # This will be called when the window is refreshed
        self.onSoftRefresh()
    
    def onSoftRefresh(self):
        if self.refreshIcon is not None and dpg.does_item_exist(self.refreshIcon):
            dpg.configure_item(self.refreshIcon, show=False)

    def windowDefintion(self, window):
        tea = self.tea
        tea: StashedTea
        timeLoadStart = dt.datetime.now(tz=dt.timezone.utc).timestamp()

        # Enable window resizing
        dpg.configure_item(window.tag, autosize=True)
        dpg.bind_item_font(window.tag, getFontName(1))
        # create a new window for the reviews
        with window:
            # Title
            dp.Text(f"Reviews for idx {tea.id}:  {tea.name}")
            dpg.bind_item_font(dpg.last_item(), getFontName(3, bold=True))
            dateString = f"Date Added: {TimeStampToString(tea.getLatestReview().attributes['date'])}" if tea.getLatestReview() else "No reviews yet"
            dp.Text(f"Total Reviews: {len(tea.reviews)}, Last Review date: {dateString}")
            # Populate stats cache if not already done
            global TeaCache
            if not TeaCache:
                TeaCache = populateStatsCache()
            # Get the estimated remaining tea
            val = tea.calculated["remaining"]
            exp = tea.calculated["remainingExplanation"]
            dp.Text(f"Estimated consumed by reviews: {tea.getEstimatedConsumedByReviews()}g")
            dp.Text(f"Estimated remaining: {val:.2f}g")
            with dp.Tooltip(dpg.last_item()):
                dp.Text(f"Estimated remaining: {val:.2f}g")
                if exp is not None:
                    dp.Text(f"{exp}")
            # Add a horizontal bar with buttons to add or duplicate reviews
            dp.Separator()
            hbarActionGroup = dp.Group(horizontal=True)
            dpg.bind_item_font(dpg.last_item(), getFontName(2))
            with hbarActionGroup:
                dp.Button(label="Add Review", callback=self.ShowAddReview, user_data=(tea, "add"))

                # Only show duplicate button if there are reviews
                if len(tea.reviews) > 0:
                    dp.Button(label="Duplicate Last Review", callback=self.ShowAddReview, user_data=(tea, "duplicate"))
                else:
                    dp.Button(label="No Reviews to Duplicate", enabled=False)

                # Reorder reviews button
                dp.Button(label="Reorder Reviews", callback=self.reorderReviews, user_data=(tea))

                # Tooltip
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    tooltipText = RateaTexts.ListTextHelpMenu["menuTeaReviews"].wrap()
                    dp.Text(tooltipText)

            with dp.Group(horizontal=True):
                dp.Button(label="Refresh", callback=self.softRefresh, width=100 * settings["UI_SCALE"], height=32 * settings["UI_SCALE"], user_data=self)
                # Show a refreshing emote icon
                self.refreshIcon = dpg.add_image("refresh_icon", width=32 * settings["UI_SCALE"], height=32 * settings["UI_SCALE"])
                
                
            # Add add review popup
            w = 900 * settings["UI_SCALE"]
            h = 500 * settings["UI_SCALE"]
            self.reviewsWindow = dp.Window(label="Reviews", width=w, height=h, show=False, modal=False)

            
            # --
            dp.Separator()
            # Add a table with reviews
            _filter_table_id = dpg.generate_uuid()
            filterAdvDropdown = None
            tableRows = list()
            w = 640 * settings["UI_SCALE"]
            dp.InputText(label="Filter Name (inc, -exc)", user_data=_filter_table_id, callback=lambda s, a, u: dpg.set_value(u, dpg.get_value(s)), width=w)
            with dp.CollapsingHeader(label="Advanced filtering/sorting", default_open=False, border=True):
                # Add a filter input text
                
                # Add a sort combo box
                filterOptions = ["Name"]
                for cat in TeaReviewCategories:
                    if cat.categoryRole not in filterOptions:
                        filterOptions.append(cat.categoryRole)
                filterAdvDropdown = dpg.add_combo(items=filterOptions, label="Filter By", default_value="Name", user_data=(None), callback=self._UpdateTableRowFilterKeys)
                dp.Separator()
            reviewsTable = dp.Table(header_row=True, no_host_extendX=True,
                                borders_innerH=True, borders_outerH=True, borders_innerV=True,
                                borders_outerV=True, row_background=True, hideable=True, reorderable=True,
                                resizable=True, sortable=True, policy=dpg.mvTable_SizingFixedFit,
                                scrollX=True, delay_search=True, scrollY=True, callback=_table_sort_callback, tag=_filter_table_id)
            with reviewsTable:
                # Add columns
                # Add ID
                dp.TableColumn(label="ID", no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True, user_data="0")
                for i, cat in enumerate(TeaReviewCategories):
                    dp.TableColumn(label=cat.name, no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True, user_data=f"{i+1}")
                # Add Action button
                dp.TableColumn(label="Action", no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True)
                # Add rows
                for i, review in enumerate(tea.reviews):
                    tableRow = dp.TableRow(filter_key=review.name)
                    tableRows.append((review, tableRow))  # Store the review and the row for later filtering
                    with tableRow:

                        # Add ID index based on position in list
                        # (parentID) - (reviewID)
                        idValue = f"{review.parentID}-{review.id}"
                        dp.Text(label=idValue, default_value=idValue)
                        # Add the review attributes

                        cat: TeaCategory
                        for j, cat in enumerate(TeaReviewCategories):
                            cellInvalidOrEmpty = False
                            # Convert attribbutes to json
                            displayValue = "N/A"
                            if cat.name == "Name":
                                displayValue = review.name
                            else:
                                if type(review.attributes) == str:
                                    try:
                                        attrJson = loadAttributesFromString(tea.attributes)
                                        if cat.categoryRole in attrJson:
                                            displayValue = attrJson[cat.categoryRole]
                                    except json.JSONDecodeError:
                                        # If there's an error in decoding, set to N/A
                                        displayValue = "Err (JSON Decode Error)"
                                        cellInvalidOrEmpty = True
                                    except KeyError:
                                        # If the key doesn't exist, set to N/A
                                        displayValue = "N/A"
                                        cellInvalidOrEmpty = True
                                    except Exception as e:
                                        RichPrintError(f"Error loading attributes: {e}")
                                        # If it fails, just set to N/A
                                        displayValue = f"Err (Exception {e})"
                                        cellInvalidOrEmpty = True
                                else:
                                    if cat.categoryRole in review.attributes:
                                        displayValue = review.attributes[cat.categoryRole]

                            # If the value is None or empty, set to N/A
                            if displayValue == None or displayValue == "" or displayValue == "N/A":
                                displayValue = "N/A"
                                cellInvalidOrEmpty = True

                            # If category is autocalculatable and the autocalculated value is not None, use that
                            usingAutocalculatedValue = False
                            exp = None
                            val = None
                            if cat.isAutoCalculated:
                                val, exp = cat.autocalculate(tea)
                                if val is not None and val != -1:
                                    displayValue = val
                                    if type(val) == float:
                                        displayValue = round(val, 3)
                                    usingAutocalculatedValue = True
                                    cellInvalidOrEmpty = False

                            if not cellInvalidOrEmpty and (cat.categoryType == "string"):
                                # Prefix, suffix
                                displayValue = cat.prefix + str(displayValue) + cat.suffix
                                dp.Text(default_value=RateaTexts.truncateString(displayValue, 70))
                                if cat.categoryRole == "Notes (Long)" or cat.categoryRole == "Notes (Short)":
                                    # Add a tooltip for long notes
                                    with dp.Tooltip(dpg.last_item()):
                                        # Wrap the text to a specified width
                                        wrappedText = RateaTexts.wrapLongLines(displayValue, breakwidth=70)
                                        dp.Text(wrappedText)
                            elif not cellInvalidOrEmpty and (cat.categoryType == "float" or cat.categoryType == "int"):
                                # Rounding
                                if type(displayValue) == float:
                                    displayValue = displayValue = f"{displayValue:.{cat.rounding}f}"
                                # Prefix, suffix
                                displayValue = cat.prefix + str(displayValue) + cat.suffix

                                if ("Score" in cat.categoryRole) and cat.gradingDisplayAsLetter:
                                    # If the category is a rating, display as letter grade
                                    if val != None and val == -1:
                                        displayValue = "---"
                                        cellInvalidOrEmpty = False
                                        exp = "No score available"
                                        usingAutocalculatedValue = False
                                    else:
                                        if usingAutocalculatedValue:
                                            displayValue = getGradeLetterFuzzy(val)
                                        else:
                                            displayValue = getGradeLetterFuzzy(float(displayValue))
                                        if usingAutocalculatedValue:
                                            exp += f"\n\nAutocalculated as letter grade: {displayValue}"

                                dp.Text(default_value=displayValue)    
                            elif cat.categoryType == "bool":
                                if displayValue == "True" or displayValue == True:
                                    displayValue = True
                                else:
                                    displayValue = False
                                dp.Checkbox(label=cat.name, default_value=bool(displayValue), enabled=False)
                            elif cat.categoryType == "date" or cat.categoryType == "datetime":
                                # Date Display widget
                                displayValue = TimeStampToString(displayValue)
                                if displayValue == "None":
                                    cellInvalidOrEmpty = True
                                # If supported, display as date
                                dp.Text(label=displayValue, default_value=displayValue)
                            else:
                                # If not supported, just display as string
                                displayValue = str(displayValue)
                                dp.Text(label=displayValue, default_value=displayValue)
                            
                            if cellInvalidOrEmpty:
                                # If the cell is invalid or empty, set the background color to red
                                dpg.highlight_table_cell(reviewsTable, i, j+1, COLOR_INVALID_EMPTY_TABLE_CELL)
                        

                        # button that opens a modal with reviews
                        with dp.Group(horizontal=True):
                            dp.Button(label="Edit", callback=self.GenerateEditReviewWindow, user_data=(review, "edit", self.tea))
                            # Button that generates review exports for copy-pasting elsewhere
                            dp.Button(label="Export", callback=self.exportReview, user_data=review)

            # Footer
            timeLoadEnd = dt.datetime.now(tz=dt.timezone.utc).timestamp()
            RichPrintSuccess(f"Window loaded in {timeLoadEnd - timeLoadStart:.2f} seconds.")
            dp.Text(parent=window, default_value=f"Loaded {len(TeaStash)} teas in {timeLoadEnd - timeLoadStart:.2f} seconds.")
        
        # disable autosize to prevent flickering or looping
        delay = 2 + statsNumTeas() // CONSTANT_DELAY_MULTIPLIER
        dpg.set_frame_callback(dpg.get_frame_count()+delay, self.afterWindowDefintion, user_data=window)

        dpg.set_item_user_data(filterAdvDropdown, tableRows)  # Set initial filter key to Name

        # End refreshing
        self.refreshing = False
        self.afterWindowDefinition()

    def _UpdateTableRowFilterKeys(self, sender, app_data, user_data, rowList):
        # Update the filter keys for the table rows
        rowList = user_data
        catAttr = app_data  # The category attribute to filter by
        for row in rowList:
            # Get the tea object from the row
            review = row[0]
            row = row[1]
            
            cat = None
            # Look up category by category role
            for c in TeaReviewCategories:
                c: ReviewCategory
                if c.categoryRole == catAttr:
                    cat = c
                    break

            row: dp.TableRow
            cat: ReviewCategory
            filterKey = review.name  # Default filter key is the tea name
            # Get the filter key from the category attribute

            # Run autocalculate if needed
            if cat.isAutoCalculated:
                val, exp = cat.autocalculate(review)
                if val is not None and val != -1:
                    filterKey = str(val)
                    if type(val) == float:
                        filterKey = f"{val:.{cat.rounding}f}"
                    if ("Score" in cat.categoryRole) and cat.gradingDisplayAsLetter:
                        filterKey = getGradeLetterFuzzy(val) + f" ({val})"
                elif val is not None:
                    filterKey = "0.0"  # If autocalculated value is None, set to 0.0
                else:
                    filterKey = review.name  # Default filter key is the review name
            else:
                # Get the filter key from the review attributes
                if cat.categoryRole in review.attributes:
                    filterKey = review.attributes[cat.categoryRole]
                else:
                    # If the attribute is not found, set to default
                    filterKey = review.name  # Default filter key is the review name
            
            # Set the filter key for the row
            row.filter_key = filterKey

    def afterWindowDefintion(self, sender, app_data, user_data):
        RichPrintInfo(f"Finished window definition for {user_data.tag}")
        window = user_data
        dpg.configure_item(window, autosize=False)
        minHeight = 480 * settings["UI_SCALE"]
        estHeight = statsNumReviews() * 30 * settings["UI_SCALE"]
        maxHeight = 930 * settings["UI_SCALE"]

        height = min(max(estHeight, minHeight), maxHeight)
        dpg.set_item_height(window.tag, height)

    def reorderReviews(self, sender, app_data, user_data):
        # Reviews should be reordered according to date purchased if available else date added
        # userdata is the tea object
        tea = user_data
        tea: StashedTea
        if tea is None:
            RichPrintError("No tea provided for reordering reviews.")
            return
        if len(tea.reviews) == 0 or tea.reviews is None:
            RichPrintError("No reviews to reorder.")
            return
        # sort by date purchased if available, else date added
        if "date" in tea.attributes:
            tea.reviews.sort(key=lambda r: r.attributes.get("date", r.attributes.get("dateAdded", 0)))
            RichPrintSuccessMinor(f"Reordered {len(tea.reviews)} reviews for tea {tea.name} by date purchased.")
        else:
            tea.reviews.sort(key=lambda r: r.attributes.get("dateAdded", 0))
            RichPrintWarning(f"No date purchased found for tea {tea.name}. Reordered reviews by date added instead.")
        # Renumber the reviews
        renumberTeasAndReviews(save=True)  # Renumber teas and reviews to keep IDs consistent
        RichPrintSuccess(f"Reordered {len(tea.reviews)} reviews for tea {tea.name} by date purchased or added.")

        # Refresh the window
        self.softRefresh()

    def deleteEditReviewWindow(self):
        # If window is open, close it first
        if self.editReviewWindow != None:
            self.editReviewWindow.delete()
            self.editReviewWindow = None
            self.addReviewList = list()
        else:
            print("No window to delete")

    def softRefresh(self):
        return super().softRefresh()
    
    def exportReview(self, sender, app_data, user_data):
        review = user_data
        review: Review
        if review is None:
            RichPrintError("No review provided for export.")
            return
        # Generate the export text
        textReview, htmlReview, imagePath = TeaReviewCategories[0].generate_review_outputs(review)
        # Copy the text review to clipboard
        try:
            pyperclip.copy(textReview)
            RichPrintSuccess(f"Copied text review for {review.name} to clipboard.")
        except pyperclip.PyperclipException as e:
            RichPrintError(f"Failed to copy text review to clipboard: {e}")
        
        # Show a popup with the html review and image path
        exportWindow = dp.Window(label="Export Review", width=800 * settings["UI_SCALE"], height=600 * settings["UI_SCALE"], modal=True, show=True)
        with exportWindow:
            dp.Text(f"Text Review (copied to clipboard):")
            dp.InputText(default_value=textReview, multiline=True, readonly=True, width=760 * settings["UI_SCALE"], height=200 * settings["UI_SCALE"])
            dp.Separator()
            dp.Text(f"HTML Review:")
            dp.InputText(default_value=htmlReview, multiline=True, readonly=True, width=760 * settings["UI_SCALE"], height=200 * settings["UI_SCALE"])
            dp.Separator()
            if imagePath is not None:
                dp.Text(f"Image Path (screenshot of review): {imagePath}")
                # Add image to registry
                addImageToRegistryFromFile(imagePath, f"{imagePath[:-4]}")
                dp.Image(f"{imagePath[:-4]}", width=400 * settings["UI_SCALE"], height=300 * settings["UI_SCALE"])
            else:
                dp.Text("No image generated.")
            dp.Separator()
            dp.Button(label="Close", callback=lambda s, a, u: exportWindow.delete())

        # End of exportReview

def Menu_Stash():
    w = 500 * settings["UI_SCALE"]
    h = 940 * settings["UI_SCALE"]
    stash = Window_Stash("Stash", w, h, exclusive=True)

class Window_Stash(WindowBase):
    addTeaList = dict()
    teasWindow = None
    adjustmentsWindow = None
    adjustmentsDict = dict()
    refreshIcon = None
    hideInvalid = False
    hideFinished = False

    def onDelete(self):
        # Close all popups
        if self.teasWindow != None and type(self.teasWindow) == dp.Window and self.teasWindow.exists():
            self.teasWindow.delete()
        elif self.teasWindow is not None:
            RichPrintInfo("Warning: Attempted to delete a non-existent teas window.")
            self.teasWindow = None

        # Close adjustments window
        if self.adjustmentsWindow != None and type(self.adjustmentsWindow) == dp.Window and self.adjustmentsWindow.exists():
            self.adjustmentsWindow.delete()
        elif self.adjustmentsWindow is not None:
            RichPrintInfo("Warning: Attempted to delete a non-existent adjustments window.")
            self.adjustmentsWindow = None
        # Invoke base class delete
        super().onDelete()

    def softRefresh(self):
        # Refresh the stats window
        reCacheStats()
        super().softRefresh()
        
    def afterWindowDefinition(self):
        # After the window is defined, we can set the callback for the soft refresh
        # This will be called when the window is refreshed
        self.onSoftRefresh()
    
    def onSoftRefresh(self):
        if self.refreshIcon is not None and dpg.does_item_exist(self.refreshIcon):
            dpg.configure_item(self.refreshIcon, show=False)

    def hideInvalidFlag(self, sender, app_data, user_data):
        # Flag to hide invalid teas
        self.hideInvalid = app_data
        if self.hideInvalid:
            RichPrintSuccessMinor("Hiding invalid teas.")
        else:
            RichPrintSuccessMinor("Showing all teas, including invalid ones.")
        
        # Refresh the table to apply the filter
        self.softRefresh()
    
    def hideFinishedFlag(self, sender, app_data, user_data):
        # Flag to hide finished teas
        self.hideFinished = app_data
        if self.hideFinished:
            RichPrintSuccessMinor("Hiding finished teas.")
        else:
            RichPrintSuccessMinor("Showing all teas, including finished ones.")

        # Refresh the table to apply the filter
        self.softRefresh()

    def windowDefintion(self, window):
        self.addTeaList = dict()
        self.addReviewList = dict()
        dpg.configure_item(window.tag, autosize=True)
        dpg.bind_item_font(window.tag, getFontName(1))
        timeLoadStart = dt.datetime.now(tz=dt.timezone.utc).timestamp()

        # Call the pop of the TeaCache if not already populated
        global TeaCache
        if TeaCache is None or (len(TeaCache) == 0 and len(TeaStash) > 0):
            TeaCache = populateStatsCache()
            RichPrintSuccessMinor("TeaCache populated from TeaStash")

        numTeasDisplay = None

                
        with window:
            dp.Separator()
            hgroupButtons = dp.Group(horizontal=True)
            dpg.bind_item_font(dpg.last_item(), getFontName(2))
            with hgroupButtons:
                dp.Button(label="Add Tea", callback=self.ShowAddTea)
                if len(TeaStash) > 0:
                    dp.Button(label="Duplicate Last Tea", callback=self.ShowAddTea, user_data="duplicate")
                else:
                    dp.Button(label="No Teas to Duplicate", enabled=False)
                dp.Button(label="Import Tea", callback=self.importOneTeaFromClipboard)
                dp.Button(label="Import All (TODO)", callback=self.DummyCallback)
                dp.Button(label="Export One (TODO)", callback=self.DummyCallback)
                dp.Button(label="Export All (TODO)", callback=self.DummyCallback)
                
                

                # Tooltip for the buttons
                dp.Button(label="?")
                with dp.Tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextHelpMenu["menuTeaStash"].wrap()
                    dp.Text(toolTipText)

            with dp.Group(horizontal=True):
                dp.Button(label="Refresh", callback=self.softRefresh, width=100 * settings["UI_SCALE"], height=32 * settings["UI_SCALE"], user_data=self)
                # Show a refreshing emote icon
                self.refreshIcon = dpg.add_image("refresh_icon", width=32 * settings["UI_SCALE"], height=32 * settings["UI_SCALE"])
            dp.Separator()

            _filter_table_id = dpg.generate_uuid()
            filterAdvDropdown = None
            tableRows = list()
            w = 640 * settings["UI_SCALE"]
            dp.InputText(label="Filter Name (inc, -exc)", user_data=_filter_table_id, callback=lambda s, a, u: dpg.set_value(u, dpg.get_value(s)), width=w)
            dpg.bind_item_font(dpg.last_item(), getFontName(2))
            with dp.CollapsingHeader(label="Advanced filtering/sorting", default_open=False, border=True):
                # Add a filter input text
                
                # Add a sort combo box
                filterOptions = ["Name"]
                for cat in TeaCategories:
                    if cat.categoryRole not in filterOptions:
                        filterOptions.append(cat.categoryRole)
                filterAdvDropdown = dpg.add_combo(items=filterOptions, label="Filter By", default_value="Name", user_data=(None), callback=self._UpdateTableRowFilterKeys)

                # Add two checkboxes for hide invalid, and hide finished
                dp.Checkbox(label="Hide Invalid", default_value=self.hideInvalid, user_data=(None), callback=self.hideInvalidFlag)
                dp.Checkbox(label="Hide Finished", default_value=self.hideFinished, user_data=(None), callback=self.hideFinishedFlag)
                numTeasDisplay = dpg.add_text(default_value=f"Total Teas: {len(TeaStash)}", user_data=(None), tag="numTeasDisplay")

                dp.Separator()
            # Operations on the stash
            with dp.CollapsingHeader(label="Operations", default_open=False, border=True):
                # Operations that cover the stash as a whole

                # Mark all teas zeroed or negative as finished, zero all negative
                dp.Button(label="Mark All Teas Finished (TODO)", callback=self.DummyCallback, user_data=None)

                # Renumber all teas and reviews
                dp.Button(label="Renumber All Teas and Reviews", callback=lambda s, a, u: renumberTeasAndReviews(save=True), user_data=None)

            # Table with collapsable rows for reviews
            teasTable = dp.Table(header_row=True, no_host_extendX=True,
                                borders_innerH=True, borders_outerH=True, borders_innerV=True,
                                borders_outerV=True, row_background=True, hideable=True, reorderable=True,
                                resizable=True, sortable=True, policy=dpg.mvTable_SizingFixedFit,
                                scrollX=True, delay_search=True, scrollY=True, callback=_table_sort_callback, tag=_filter_table_id)
            with teasTable:
                # Add columns from teaCategories
                # Add ID
                dpg.add_table_column(label="ID", no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True, user_data="0")
                # Add the categories
                for i, cat in enumerate(TeaCategories):
                    dp.TableColumn(label=cat.name, no_resize=False, no_clip=True, user_data=f"{i+1}")
                dp.TableColumn(label="Reviews", no_resize=False, no_clip=True, width=300, no_hide=True)
                dp.TableColumn(label="Actions", no_resize=False, no_clip=True, width=50, no_hide=True)


                # Abridged TeaStash that factors in the hideInvalid and hideFinished flags
                AbridgedTeaStash = list()
                remainingCategory = None

                if self.hideInvalid or self.hideFinished:
                    RichPrintInfo("Filtering teas based on hideInvalid and hideFinished flags.")
                    for cat in TeaCategories:
                        if cat.categoryRole == "Remaining":
                            remainingCategory = cat
                            break
                    for tea in TeaStash:
                        # If hideInvalid is set, filter out invalid teas
                        if self.hideInvalid:
                            # We check if the tea has invalid attributes by looking at the 
                            # attributes and checking if they are valid
                            # Check if any of the attributes are invalid
                            invalidAttributes = False
                            for cat in TeaCategories:
                                if cat.categoryRole in tea.attributes:
                                    if not cat.isValid(tea.attributes[cat.categoryRole]):
                                        invalidAttributes = True
                                        break
                            if invalidAttributes:
                                RichPrintInfo(f"Tea {tea.name} has invalid attributes, skipping.")
                                continue
                            
                        # If hideFinished is set, filter out finished teas
                        if self.hideFinished:
                            remainingCategory.autocalculate(tea)
                            if tea.finished or (remainingCategory and remainingCategory.autocalculate(tea)[0] <= 0):
                                RichPrintInfo(f"Tea {tea.name} is finished, skipping.")
                                continue

                        # If the tea passes the filters, add it to the abridged stash
                        AbridgedTeaStash.append(tea)

                    # If no teas are left after filtering, show a message
                    if len(AbridgedTeaStash) == 0:
                        dp.Text("No teas found after filtering. Please adjust your filters.")
                        return

                    # Update the number of teas display
                    if numTeasDisplay is not None and dpg.does_item_exist(numTeasDisplay):
                        dpg.set_value(numTeasDisplay, f"Total Teas: {len(AbridgedTeaStash)}")
                    else:
                        RichPrintError("numTeasDisplay text item does not exist. Cannot update number of teas display.")
                else:
                    # If no filtering is applied, use the full TeaStash
                    AbridgedTeaStash = TeaStash

                # If no teas are left after filtering, show a message
                if len(AbridgedTeaStash) == 0:
                    dp.Text("No teas found. Please add some teas to the stash.")
                    return

                

                # Add rows
                for i, tea in enumerate(AbridgedTeaStash):
                    tableRow = dp.TableRow(filter_key=tea.name)
                    tableRows.append((tea, tableRow))
                    with tableRow:
                        # Add ID index based on position in list
                        dp.Text(label=f"{i}", default_value=f"{i}")
                        # Add the tea attributes

                        cat: TeaCategory
                        for j, cat in enumerate(TeaCategories):
                            cellInvalidOrEmpty = False
                            # Convert attributes to json
                            displayValue = "N/A"
                            if cat.name == "Name":
                                displayValue = tea.name
                            else:
                                if type(tea.attributes) == str:
                                    pass  # Add appropriate logic here or remove this placeholder
                                    try:
                                        attrJson = loadAttributesFromString(tea.attributes)
                                        if cat.categoryRole in attrJson:
                                            displayValue = attrJson[cat.categoryRole]
                                    except json.JSONDecodeError:
                                        # If there's an error in decoding, set to N/A
                                        displayValue = "Err (JSON Decode Error)"
                                        cellInvalidOrEmpty = True
                                    except KeyError:
                                        # If the key doesn't exist, set to N/A
                                        displayValue = "N/A"
                                        cellInvalidOrEmpty = True
                                    except Exception as e:
                                        RichPrintError(f"Error loading attributes: {e}")
                                        # If it fails, just set to N/A
                                        displayValue = "Err (Exception)"
                                        cellInvalidOrEmpty = True
                                else:
                                    if cat.categoryRole in tea.attributes:
                                        displayValue = tea.attributes[cat.categoryRole]
                                    else:
                                        displayValue = "N/A"
                                        cellInvalidOrEmpty = True
                            if displayValue == None or displayValue == "" or displayValue == "N/A":
                                displayValue = "N/A"
                                cellInvalidOrEmpty = True
                            # If category is autocalculatable and the autocalculated value is not None, use that
                            usingAutocalculatedValue = False
                            autocalculatingAlternateColor = False
                            exp = None
                            if cat.isAutoCalculated:
                                val, exp = cat.autocalculate(tea)
                                if val is not None and val != -1:
                                    displayValue = val
                                    if type(val) == float:
                                        displayValue = round(val, 3)
                                    usingAutocalculatedValue = True
                                    cellInvalidOrEmpty = False

                                    # if cat is Remaining, check if finished, if so, use alternate color
                                    if ("Remaining" in cat.categoryRole) and (tea.finished or val <= 0):
                                        autocalculatingAlternateColor = True
                                        val = 0
                                        displayValue = 0

                            if not cellInvalidOrEmpty and (cat.categoryType == "string"):
                                # Prefix, suffix
                                displayValue = cat.prefix + str(displayValue) + cat.suffix
                                dp.Text(default_value=RateaTexts.truncateString(displayValue, 70))
                                if cat.categoryRole == "Notes (Long)":
                                    # Add a tooltip for long notes
                                    with dp.Tooltip(dpg.last_item()):
                                        # Wrap the text to a specified width
                                        wrappedText = RateaTexts.wrapLongLines(displayValue, breakwidth=70)
                                        dp.Text(wrappedText)
                            elif not cellInvalidOrEmpty and (cat.categoryType == "float" or cat.categoryType == "int"):
                                # Rounding
                                if type(displayValue) == float:
                                    displayValue = f"{displayValue:.{cat.rounding}f}"
                                # Prefix, suffix
                                displayValue = cat.prefix + str(displayValue) + cat.suffix

                                if ("Score" in cat.categoryRole) and cat.gradingDisplayAsLetter:
                                    if val != None and val == -1:
                                        displayValue = "---"
                                        cellInvalidOrEmpty = False
                                        exp = "No score available"
                                        usingAutocalculatedValue = False
                                    else:
                                        # If the category is a rating, display as letter grade
                                        if usingAutocalculatedValue:
                                            displayValue = getGradeLetterFuzzy(val)
                                        else:
                                            displayValue = getGradeLetterFuzzy(float(displayValue))
                                        if usingAutocalculatedValue:
                                            exp += f"\n\nAutocalculated as letter grade: {displayValue}"
                                dp.Text(default_value=displayValue)
                                if usingAutocalculatedValue:
                                    # Give tooltip for autocalculated value
                                    with dp.Tooltip(dpg.last_item()):
                                        dp.Text(f"Autocalc Formula:\n{exp}")
                            elif cat.categoryType == "bool":
                                if displayValue == "True" or displayValue == True:
                                    displayValue = True
                                else:
                                    displayValue = False
                                dp.Checkbox(label=cat.name, default_value=bool(displayValue), enabled=False)
                            elif cat.categoryType == "date" or cat.categoryType == "datetime":
                                # Date picker widget
                                displayValue = TimeStampToStringWithFallback(displayValue, "None")
                                if displayValue == "None":
                                    cellInvalidOrEmpty = True
                                # If supported, display as date
                                dp.Text(label=displayValue, default_value=displayValue)
                            else:
                                # If not supported, just display as string
                                displayValue = str(displayValue)
                                dp.Text(label=displayValue, default_value=displayValue)

                            if usingAutocalculatedValue and autocalculatingAlternateColor:
                                dpg.highlight_table_cell(teasTable, i, j+1, color=COLOR_AUTOCALCULATED_2)
                            elif usingAutocalculatedValue:
                                dpg.highlight_table_cell(teasTable, i, j+1, color=COLOR_AUTOCALCULATED_TABLE_CELL)
                            if cellInvalidOrEmpty:
                                dpg.highlight_table_cell(teasTable, i, j+1, color=COLOR_INVALID_EMPTY_TABLE_CELL)

                        # button that opens a modal with reviews
                        numReviews = len(tea.reviews)
                        dp.Button(label=f"{numReviews} Reviews", callback=self.generateReviewListWindow, user_data=tea)
                        with dp.Group(horizontal=True):
                            dp.Button(label="Edit", callback=self.ShowEditTea, user_data=tea)
                            dp.Button(label="Adjust", callback=self.showAdjustTeaWindow, user_data=tea)

            # Add seperator and import/export buttons
            dp.Separator()
        # Footer
        timeLoadEnd = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        RichPrintSuccess(f"Window loaded in {timeLoadEnd - timeLoadStart:.2f} seconds.")
        dp.Text(parent=window, default_value=f"Loaded {len(TeaStash)} teas in {timeLoadEnd - timeLoadStart:.2f} seconds.")
        # disable autosize to prevent flickering or looping
        delay = 2 + statsNumTeas() // CONSTANT_DELAY_MULTIPLIER
        dpg.set_frame_callback(dpg.get_frame_count()+delay, self.afterWindowDefintion, user_data=window)

        dpg.set_item_user_data(filterAdvDropdown, tableRows)  # Set initial filter key to Name

        # End refreshing
        self.refreshing = False
        
        self.afterWindowDefinition()

    def _UpdateTableRowFilterKeys(self, sender, app_data, user_data, rowList):
        # Update the filter keys for the table rows
        rowList = user_data
        catAttr = app_data  # The category attribute to filter by
        for row in rowList:
            # Get the tea object from the row
            tea = row[0]
            row = row[1]
            
            cat = None
            # Look up category by category role
            for c in TeaCategories:
                if c.categoryRole == catAttr:
                    cat = c
                    break

            row: dp.TableRow
            cat: TeaCategory
            filterKey = tea.name  # Default filter key is the tea name
            # Get the filter key from the category attribute

            # Run autocalculate if needed
            if cat.isAutoCalculated:
                val, exp = cat.autocalculate(tea)
                if val is not None and val != -1:
                    filterKey = str(val)
                    if type(val) == float:
                        filterKey = f"{val:.{cat.rounding}f}"
                    if ("Score" in cat.categoryRole) and cat.gradingDisplayAsLetter:
                        filterKey = getGradeLetterFuzzy(val) + f" ({val})"
                elif val is not None:
                    filterKey = "0.0"  # If autocalculated value is None, set to 0.0
                else:
                    filterKey = tea.name  # Default filter key is the tea name
            else:
                # Get the filter key from the tea attributes
                if cat.categoryRole in tea.attributes:
                    filterKey = tea.attributes[cat.categoryRole]
                else:
                    # If the attribute is not found, set to default
                    filterKey = tea.name  # Default filter key is the tea name
            
            # Set the filter key for the row
            row.filter_key = filterKey


    def afterWindowDefintion(self, sender, app_data, user_data):
        RichPrintInfo(f"Finished window definition for {user_data.tag}")
        window = user_data
        dpg.configure_item(window, autosize=False)
        minHeight = 480 * settings["UI_SCALE"]
        estHeight = statsNumTeas() * 30 * settings["UI_SCALE"]
        maxHeight = 930 * settings["UI_SCALE"]

        height = min(max(estHeight, minHeight), maxHeight)
        dpg.set_item_height(window.tag, height)



    def importOneTeaFromClipboard(self, sender, app_data, user_data):
        # Import a tea from the clipboard
        # Ex: {"Name": "reviews", "Year": 2000, "Type": "Hong", "Remaining": 123123.0, "Vendor": "N/A", "bool": true, "datetime": "2025-05-07"}
        # Get the data from the clipboard
        clipboardData = pyperclip.paste()
        allAttributes = None
        try:
            allAttributes = json.loads(clipboardData)
            RichPrintInfo(f"Clipboard data: {clipboardData}")
            # Create a new tea object and add it to the stash
            newId = len(TeaStash)
            newTea = StashedTea(newId, allAttributes["Name"], allAttributes["dateAdded"], allAttributes)

            # Add reviews to the tea object
            newTea.reviews = []  # No reviews for now, just an empty list
            clipboardReviews = allAttributes.get("reviews", [])
            for review in clipboardReviews:
                newTea.addReview(loadReviewFromDictNewID(review, len(newTea.reviews), newId))

            # Add adjustments and finished flag
            newTea.adjustments = allAttributes.get("adjustments", [])
            newTea.finished = allAttributes.get("finished", False)

            TeaStash.append(newTea)
            RichPrintSuccess(f"Imported tea from clipboard: {newTea.name}")

            # Save the tea stash to file
            saveTeasData(TeaStash, settings["TEA_REVIEWS_PATH"])

            # Refresh the window
            self.softRefresh()
        except json.JSONDecodeError:
            RichPrintError("Error: Clipboard data is not valid JSON.")
        except Exception as e:
            RichPrintError(f"Error importing tea from clipboard: {e}")
            return
        
        if allAttributes is None:
            RichPrintError("No valid attributes found in clipboard data.")
            return
        
            

    def generateReviewListWindow(self, sender, app_data, user_data):
        Menu_Stash_Reviews(sender, app_data, (self, user_data))

    def generateTeasWindow(self, sender, app_data, user_data):
        # If window is open, close it first
        if self.teasWindow != None and type(self.teasWindow) == dp.Window:
            self.deleteTeasWindow()

        teasData = None
        duplicateTea = False
        operation = user_data[1]
        self.addTeaList = dict()
        itemType = "Tea"
        if operation == "add":
            teasData = None
        elif operation == "edit" or operation == "duplicate":
            teasData = user_data[0]

        # Fill in field from user_data but add as a new tea
        if operation == "duplicate":
            # Get the last tea in the stash
            if len(TeaStash) > 0:
                duplicateTea = True
            else:
                RichPrintError("Error: No teas in stash to duplicate.")
                return
            
        idTea = 0
        if teasData is not None:
            # If editing, get the ID of the tea
            idTea = teasData.id
        else:
            # If adding, get the next ID
            idTea = len(TeaStash)

        # Create a new window
        w = 580 * settings["UI_SCALE"]
        h = 540 * settings["UI_SCALE"]
        windowName = f"{operation.capitalize()} | {itemType} | {idTea}"
        self.teasWindow = dp.Window(label=windowName, width=w, height=h, show=True)
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        windowManager.addSubWindow(self.teasWindow)
        with self.teasWindow:
            if operation == "add":
                dp.Text(f"Add | {itemType} | {idTea}")
            elif operation == "edit":
                dp.Text(f"Edit | {itemType} | {idTea}:\n{teasData.name if teasData else 'Unknown name'}")
            elif operation == "duplicate":
                if duplicateTea:
                    dp.Text(f"Duplicate | {itemType} | {idTea}:\n{teasData.name if teasData else 'Unknown name'}")
                else:
                    RichPrintError("Error: No teas in stash to duplicate.")
                    return
            dpg.bind_item_font(dpg.last_item(), getFontName(3, bold=True))



            for cat in TeaCategories:
                cat: TeaCategory
                # Add it to the window
                catName = cat.name
                dp.Separator()

                # Text indicators for required and auto calculated
                with dp.Group(horizontal=True):
                    if cat.isRequiredForTea:
                        dp.Text("[required]", color=COLOR_REQUIRED_TEXT)
                    dp.Text(catName)
                    if cat.isAutoCalculated:
                        # If auto calculated, don't show the input
                        dp.Text("(Auto)", color=COLOR_AUTO_CALCULATED_TEXT)
                defaultValue = None
                

                try:
                    defaultValue = teasData.attributes[cat.categoryRole]
                except:
                    defaultValue = f"{cat.defaultValue}"

                # If the category is a string, int, float, or bool, add the appropriate input type
                catItem = None
                # Get past values for dropdown
                pastAnswers, pastAnswersList = searchPreviousAnswers(cat.categoryRole, "Tea", cat.dropdownMaxLength)
                shouldShowDropdown = True if len(pastAnswers) > 0 and cat.isDropdown else False
                # If past answers are a timestamp, convert them to a readable format
                if cat.categoryType == "date" or cat.categoryType == "datetime":
                    # Convert to a readable format
                    pastAnswersTextList = [f"{x[1]} - {TimeStampToString(x[0])}" for x in pastAnswers]
                else:
                    # For other types, just use the string representation
                    pastAnswersTextList = [f"({x[1]}) - ({x[0]})" for x in pastAnswers]

                if cat.categoryType == "string":
                    # For notes, allow multiline input if it's a note
                    if cat.categoryRole == "Notes (short)" or cat.categoryRole == "Notes (Long)":
                        height = 220 * settings["UI_SCALE"]
                        catItem = dp.InputText(default_value=str(defaultValue), multiline=True, height=height, width=480 * settings["UI_SCALE"])
                    else:
                        
                        catItem = dp.InputText(default_value=str(defaultValue), multiline=False, width=480 * settings["UI_SCALE"])
                        if shouldShowDropdown:
                            # Create a dropdown with the past answers
                            dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "string"))
                elif cat.categoryType == "int":
                    catItem = dp.InputInt(default_value=int(defaultValue), width=480 * settings["UI_SCALE"])
                    if shouldShowDropdown:
                        # Create a dropdown with the past answers
                        dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "int"))
                elif cat.categoryType == "float":
                    if ("Score" in cat.categoryRole) and cat.gradingDisplayAsLetter:
                        # For grading, use a predefined dropdown and then convert to float upon entry
                        gradingOptions = getGradeList()
                        defaultValue = getGradeDropdownValueByFloat(float(defaultValue))
                        catItem = dp.Combo(items=gradingOptions, default_value=defaultValue)
                    else:
                        catItem = dp.InputFloat(default_value=float(defaultValue), step=1.0, format="%.2f", width=480 * settings["UI_SCALE"])
                        if shouldShowDropdown:
                            # Add a dropdown for the past answers
                            dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "float"))
                elif cat.categoryType == "bool":
                    if defaultValue == "True" or defaultValue == True:
                        defaultValue = True
                    else:
                        defaultValue = False
                    catItem = dp.Checkbox(default_value=bool(defaultValue), width=480 * settings["UI_SCALE"])
                elif cat.categoryType == "date" or cat.categoryType == "datetime":
                    if teasData is None:
                        # Add, so default to now if no date is set
                        defaultValue = dt.datetime.now(tz=dt.timezone.utc).timestamp()
                        defaultValue = TimeStampToDateDict(defaultValue)
                    else:                    # Date picker widget
                        defaultValue = TimeStampToDateDict(AnyDTFormatToTimeStamp(defaultValue))
                    # If supported, display as date
                    catItem = dp.DatePicker(level=dpg.mvDatePickerLevel_Day, default_value=defaultValue, width=480 * settings["UI_SCALE"])
                    if shouldShowDropdown:
                        # Create a dropdown with the past answers
                        dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "date"))
                else:
                    catItem = dp.InputText(default_value=f"Not Supported (Assume String): {cat.categoryType}, {cat.name}", width=480 * settings["UI_SCALE"])
                    if shouldShowDropdown:
                        # Create a dropdown with the past answers
                        dp.Combo(items=pastAnswersTextList, default_value="Past Answers", callback=self.UpdateInputWithDropdownSelelction, user_data=(catItem, pastAnswersList, "string"))

                # Add it to the list
                if catItem != None:
                    self.addTeaList[cat.categoryRole] = catItem
                else:
                    RichPrintError(f"Error: {cat.categoryRole} not supported")

            dp.Separator()

            # Add buttons
            with dp.Group(horizontal=True):
                if operation == "add":
                    dp.Button(label="Add New Tea", callback=self.validateAddEditTea, user_data=(teasData, "ADD"))
                elif operation == "edit":
                    dp.Button(label="Confirm Edit", callback=self.validateAddEditTea, user_data=(teasData, "EDIT"))
                elif operation == "duplicate":
                    dp.Button(label="Confirm Duplicate", callback=self.validateAddEditTea, user_data=(teasData, "DUPLICATE"))
                # Copy Values to string (json) for the edit window, use function
                if operation == "edit":
                    dp.Button(label="Copy/Export Tea", callback=self.copyTeaValues, user_data=teasData)
                dp.Button( label="Paste Values", callback= self.pasteTeaValues, user_data=teasData)
                if operation == "edit":
                    dp.Button(label="Delete Tea", callback=self.DeleteTea, user_data=teasData)
                dp.Button(label="Cancel", callback=self.deleteTeasWindow)
    
    def validateAddEditTea(self, sender, app_data, user_data):
        # Function to validate the input values
        isValid = True
        isTea = True # Placeholder for later 
        teasData = user_data[0]
        isAdd = False
        if user_data[1] == "ADD" or user_data[1] == "DUPLICATE":
            isAdd = True
        # Name must always be present
        if "Name" not in self.addTeaList or self.addTeaList["Name"].get_value() == "":
            RichPrintError("Error: Name is required.")
            isValid = False


        # Some fields are marked required for tea or for all, check them here
        
        # Iterate through categories and validate
        for cat in TeaCategories:
            cat: TeaCategory
            if cat.categoryRole in self.addTeaList:
                # Check if the category is required and validate accordingly
                if cat.isRequiredForTea and self.addTeaList[cat.categoryRole].get_value() == "":
                    RichPrintError(f"Error: {cat.name} is required for a Tea entry.")
                    isValid = False
                
                if cat.isRequiredForAll and self.addTeaList[cat.categoryRole].get_value() == "":
                    RichPrintError(f"Error: {cat.name} is required for all entries.")
                    isValid = False
        
        if isValid:
            RichPrintInfo("Validation passed. Proceeding to add/edit tea.")
            if isAdd:
                # If validation passes, proceed to add the tea
                self.AddTea(sender, app_data, teasData)
            else:
                # If validation passes, proceed to edit the tea
                self.EditTea(sender, app_data, teasData)
        else:
            # If validation fails, show an error message and do not proceed
            RichPrintError("Error: Validation failed. Please check the input values.")
            return
        
    def UpdateInputWithDropdownSelelction(self, sender, app_data, user_data):
        # Update the input with the new value
        typeOfValue = user_data[2]
        # Exclude default value "Past Answers"
        if app_data == "Past Answers":
            RichPrintWarning("Warning: \"Past Answers\" is not a valid selection.")
            return
        
        # Get the input item and the past answers
        if user_data[0]:
            splits = app_data.split(" - ")
            if len(splits) > 2:
                newSelectedValue = splits[1:]
                newSelectedValue = " - ".join(newSelectedValue).strip()
            else:
                newSelectedValue = splits[1].strip()
            # Remove parentheses if they exist
            if newSelectedValue.startswith("(") and newSelectedValue.endswith(")"):
                newSelectedValue = newSelectedValue[1:-1]

            # If typeOfValue is int or float, attempt to convert
            if typeOfValue == "int":
                try:
                    newSelectedValue = int(newSelectedValue)
                except ValueError:
                    RichPrintError(f"Error: {newSelectedValue} is not a valid integer.")
                    return
            elif typeOfValue == "float":
                try:
                    newSelectedValue = float(newSelectedValue)
                except ValueError:
                    RichPrintError(f"Error: {newSelectedValue} is not a valid float.")
                    return
            elif typeOfValue == "date" or typeOfValue == "datetime":
                # Convert string date to datetime object
                try:
                    newSelectedValue = TimeStampToDateDict(newSelectedValue)
                except TypeError as e:
                    # Convert date string to timestamp
                    try:
                        newSelectedValue = StringToTimeStamp(newSelectedValue)
                        newSelectedValue = TimeStampToDateDict(newSelectedValue)
                    except ValueError:
                        RichPrintError(f"Error: {newSelectedValue} is not a valid date.")
                        return
            # Set the value of the input item to the new value
            user_data[0].set_value(newSelectedValue)
        else:
            RichPrintError(f"Error: {user_data} not found in addTeaList.")


    def copyTeaValues(self, sender, app_data, user_data):
        # Call the dumpReviewToString function to get the string representation of the review
        # and copy it to the clipboard
        if self.teasWindow is None:
            RichPrintError("No teas window to copy values from.")
            return
        
        allAttributes = {}
        for k, v in self.addTeaList.items():
            if type(v) == dp.DatePicker:
                allAttributes[k] = parseDTToString(DateDictToDT(v.get_value()))
            else:
                val = v.get_value()
                # If float, round to 3 decimal places
                if type(val) == float:
                    val = round(val, 3)
                allAttributes[k] = val

        # Add in recursive attributes field
        allAttributes["attributes"] = {}
        for k, v in allAttributes.items():
            if k != "attributes":
                allAttributes["attributes"][k] = v

        # Add in blank reviews and calculated field
        allAttributes["reviews"] = []
        allAttributes["calculated"] = {}

        # Add in reviews from the tea object
        if user_data is not None and hasattr(user_data, 'reviews'):
            # Reviews is a list of Review objects, convert to dicts first
            reviews = []
            for review in user_data.reviews:
                reviews.append(dumpReviewToDict(review))
            allAttributes["reviews"] = reviews

        # Convert to JSON string
        jsonString = json.dumps(allAttributes)
        pyperclip.copy(jsonString)
        RichPrintSuccess(f"Copied Tea Values: {jsonString}")


    def pasteTeaValues(self, sender, app_data, user_data):
        # (DEBUG) Print instead of actually setting, compare to original to see if it works
        if self.teasWindow is None:
            RichPrintError("No teas window to paste values into.")
            return
        
        clipboardData = pyperclip.paste()
        allAttributes = None
        try:
            allAttributes = json.loads(clipboardData)
            for k, v in self.addTeaList.items():
                if k in allAttributes:
                    if type(v) == dp.DatePicker:
                        # Convert string date to datetime object
                        dt_value = TimeStampToDateDict(StringToTimeStamp(allAttributes[k]))
                        v.set_value(dt_value)
                    else:
                        v.set_value(allAttributes[k])
            RichPrintSuccess("Pasted Tea Values Successfully.")
        except json.JSONDecodeError:
            RichPrintError("Error: Clipboard data is not valid JSON.")
        except Exception as e:
            RichPrintError(f"Error pasting values: {e}")
            return
        
        if allAttributes is None:
            RichPrintError("No valid attributes found in clipboard data.")
            return
        
        # If we reach here, it means we successfully pasted the values
        RichPrintInfo(f"Pasted Tea Values: {allAttributes}")

        # Update the window to reflect the new values
        for k, v in self.addTeaList.items():
            if k in allAttributes:
                if type(v) == dp.DatePicker:
                    dt_value = StringToTimeStamp(allAttributes[k])
                    dt_value = TimeStampToDateDict(dt_value)
                    v.set_value(dt_value)
                else:
                    v.set_value(allAttributes[k])




    def deleteTeasWindow(self):
        # If window is open, close it first
        if self.teasWindow != None:
            self.teasWindow.delete()
            self.teasWindow = None
            self.addTeaList = dict()
        else:
            print("No window to delete")

    def deleteAdjustmentsWindow(self):
        # If window is open, close it first
        if self.adjustmentsWindow != None:
            self.adjustmentsWindow.delete()
            self.adjustmentsWindow = None
            self.addTeaList = dict()
        else:
            print("No window to delete")
            




    def ShowAddTea(self, sender, app_data, user_data):
        if self.teasWindow != None and type(self.teasWindow) == dp.Window:
            self.deleteTeasWindow()
        if user_data == "duplicate":
            # Duplicate the last tea
            if len(TeaStash) > 0:
                lastTea = TeaStash[-1]
                self.generateTeasWindow(sender, app_data, user_data=(lastTea, "duplicate"))
                return
            else:
                RichPrintError("No teas to duplicate.")
                return
        self.generateTeasWindow(sender, app_data, user_data=(None,"add"))
    def ShowEditTea(self, sender, app_data, user_data):
        if self.teasWindow != None and type(self.teasWindow) == dp.Window:
            self.deleteTeasWindow()
        self.generateTeasWindow(sender, app_data, user_data=(user_data,"edit"))
        return
    
    def showAdjustTeaWindow(self, sender, app_data, user_data):
        # Show the adjust tea window
        if self.adjustmentsWindow != None and type(self.adjustmentsWindow) == dp.Window:
            self.deleteAdjustmentsWindow()
        if not isinstance(user_data, StashedTea):
            RichPrintError("Error: user_data is not a StashedTea object, is: ", user_data)
        else:
            self.generateAdjustmentsWindow(sender, app_data, user_data=user_data)
        return
    

    # The adjustments window allows the user to adjust the amount of tea remaining, and mark it as finished
    def generateAdjustmentsWindow(self, sender, app_data, user_data):
        # If window is open, close it first
        if self.adjustmentsWindow != None and type(self.adjustmentsWindow) == dp.Window:
            self.deleteAdjustmentsWindow()

        # Create a new window
        w = 500 * settings["UI_SCALE"]
        h = 500 * settings["UI_SCALE"]
        self.adjustmentsWindow = dp.Window(label="Adjustments", width=w, height=h, show=True)
        dpg.bind_item_font(dpg.last_item(), getFontName(2))

        windowManager.addSubWindow(self.adjustmentsWindow)
        teaCurrent = user_data
        teaCurrent: StashedTea
        with self.adjustmentsWindow:
            dp.Text("Adjustments")
            dpg.bind_item_font(dpg.last_item(), getFontName(3))

            # Check if all required categories are present,
            # Needs Amount Purchased, amount remaining
            if "Amount" in teaCurrent.attributes or "Remaining" in teaCurrent.attributes:
                # Get Amount and Remaining categories
                remainingCategory = None
                for cat in TeaCategories:
                    if cat.categoryRole == "Remaining":
                        remainingCategory = cat
                        break

                # Display the current tea name and amount
                dp.Text(f"Tea Name: {teaCurrent.name}")
                dp.Separator()
                # Display the amount purchased and current remaining
                currentRemaining, exp = remainingCategory.autocalculate(teaCurrent)
                if currentRemaining is None:
                    currentRemaining = 0.0
                totalPurchased = teaCurrent.attributes.get("Amount", None)
                dp.Text(f"Total Purchased: {totalPurchased:.3f}g")
                dp.Text(f"Current Amount: {currentRemaining:.3f}g")
                with dp.Tooltip(dpg.last_item()):
                    dp.Text(f"Autocalc Formula:\n{exp}")


                # Current Adjustment in the tea dict
                currentAdjustmentAmt = 0
                currentAdjustmentDict = teaCurrent.adjustments
                if currentAdjustmentDict is not None:
                    # Try to get standard adjustment
                    currentAdjustmentAmt = currentAdjustmentDict.get("Standard", None)
                    if currentAdjustmentAmt is None:
                        currentAdjustmentAmt = 0.0
                dp.Text(f"Adjustments to the remaining total amount:")
                dpg.bind_item_font(dpg.last_item(), getFontName(2, bold=True))
                dp.Text(f"Current Adjustment: {currentAdjustmentAmt:.3f}g")
                # Current Gift Adjustment in the tea dict
                currentGiftAdjustmentAmt = 0
                currentGiftAdjustmentDict = teaCurrent.adjustments
                if currentGiftAdjustmentDict is not None:
                    # Try to get gift adjustment
                    currentGiftAdjustmentAmt = currentGiftAdjustmentDict.get("Gift", None)
                    if currentGiftAdjustmentAmt is None:
                        currentGiftAdjustmentAmt = 0.0
                dp.Text(f"Current Gift Adjustment: {currentGiftAdjustmentAmt:.3f}g")
                currentSaleAdjustmentAmt = 0
                currentSaleAdjustmentDict = teaCurrent.adjustments
                if currentSaleAdjustmentDict is not None:
                    # Try to get sale adjustment
                    currentSaleAdjustmentAmt = currentSaleAdjustmentDict.get("Sale", None)
                    if currentSaleAdjustmentAmt is None:
                        currentSaleAdjustmentAmt = 0.0
                dp.Text(f"Current Sale Adjustment: {currentSaleAdjustmentAmt:.3f}g")
                # Add a checkbox to mark the tea as finished
                dp.Separator()
                finished = teaCurrent.finished
                finsihedCheckbox = dp.Checkbox(label="Finished", default_value=finished, callback=self.greyOutAdjustmentInput)     


                # Add a text input for the adjustment
                dp.Text("Adjustment:")
                adjustmentInput = dp.InputFloat(default_value=currentAdjustmentAmt, enabled=not finished, step=1.0, format="%.2f")

                # Button to set the above adjustmentInput to the current remaining amount
                def _setAdjustmentToCurrentRemaining(sender, app_data, user_data):
                    # Set the adjustment input to the current remaining amount
                    adjustmentInput = user_data[0]
                    currentRemaining = user_data[1]
                    if adjustmentInput is not None:
                        adjustmentInput.set_value(currentRemaining)
                    else:
                        RichPrintError("Error: Adjustment input is None.")
                dp.Button(label="Set Adjustment to Current Remaining", callback=_setAdjustmentToCurrentRemaining, user_data=(adjustmentInput, currentRemaining))

                self.addTeaList["Adjustment"] = adjustmentInput

                # Add userdata for the adjustment input to grey out
                finsihedCheckbox.user_data = (finished, teaCurrent, adjustmentInput, currentRemaining)

                # Add a button to confirm the adjustment
                dp.Separator()
                dp.Button(label="Confirm Adjustment/Finished", callback=self.UpdateAdjustmentAmt, user_data=(teaCurrent, adjustmentInput, finsihedCheckbox, "Standard"))

                # Adjust gift amount, adjustment that doesnt count towards consumption
                dp.Text("Gift Adjustment (Does not count towards consumption):")
                giftAdjustmentInput = dp.InputFloat(default_value=currentGiftAdjustmentAmt, step=1.0, format="%.2f")
                self.addTeaList["Gift Adjustment"] = giftAdjustmentInput
                # Add a button to confirm the gift adjustment
                dp.Button(label="Confirm Gift Adjustment", callback=self.UpdateAdjustmentAmt, user_data=(teaCurrent, giftAdjustmentInput, finsihedCheckbox, "Gift"))

                # Adjust Sale amount
                dp.Text("Sale Adjustment")
                dp.Text("(Does not count towards consumption, proceeds counted separately)")
                saleAdjustmentInput = dp.InputFloat(default_value=currentSaleAdjustmentAmt, step=1.0, format="%.2f")
                self.addTeaList["Sale Adjustment"] = saleAdjustmentInput
                # Add a button to confirm the sale adjustment
                dp.Button(label="Confirm Sale Adjustment", callback=self.UpdateAdjustmentAmt, user_data=(teaCurrent, saleAdjustmentInput, finsihedCheckbox, "Sale"))
            else:
                # If the tea does not have the required attributes, show an error message
                dp.Text("Error: Tea does not have the required attributes for adjustments.")
                dp.Text("Required attributes: Amount, Remaining")

            # Add a separator
            dp.Separator()

            # Move index of tea placeholder
            dp.Text("Operations on Tea Stash")
            dpg.bind_item_font(dpg.last_item(), getFontName(2, bold=True))
            dp.Text(f"Tea Index: {teaCurrent.id} (0-based index) out of {len(TeaStash)} teas in stash")
            dpg.bind_item_font(dpg.last_item(), getFontName(1, bold=False))
            # Add a text input for the new index
            moveInput = dp.InputInt(label="New Index, (Adds below current index)", default_value=teaCurrent.id, min_value=0, max_value=len(TeaStash)-1, width=200 * settings["UI_SCALE"])
            # Add a button to move the tea index
            dp.Button(label="Move Tea Index", callback=self.moveTeaIndex, user_data=(moveInput, teaCurrent))

            # Add buttons to move the tea index to the end or top of the stash
            dp.Button(label="Move Tea to End", callback=self.moveTeaIndexToEnd, user_data=(moveInput, teaCurrent))
            dp.Button(label="Move Tea to Top", callback=self.moveTeaIndexToTop, user_data=(moveInput, teaCurrent))

            # Add a separator
            dp.Separator()
            dp.Text(f"TODO: Move to end, Move to Top, Move down 1, Move up 1")
            dp.Text(f"Migrate reviews to new tea index, TODO: Implement moving reviews in stash)")
            dp.Text(f"TODO: Merge teas of two indexes into one, combining reviews as well, delete the other tea")
            dpg.bind_item_font(dpg.last_item(), getFontName(1, bold=False))

            # Add a button to cancel the adjustment
            dp.Button(label="Cancel", callback=self.deleteAdjustmentsWindow)

    def moveTeaIndexToEnd(self, sender, app_data, user_data):
        # Wrapper around moveTeaIndex to move the tea to the end of the stash
        # user_data[0] is the moveinput object, overwrite this with the integer length of the stash
        # user_data[1] is the tea object
        moveInput = len(TeaStash) - 1  # Move to the end of the stash
        tea = user_data[1]
        self.moveTeaIndex(sender, app_data, user_data=(moveInput, tea))

    def moveTeaIndexToTop(self, sender, app_data, user_data):
        # Wrapper around moveTeaIndex to move the tea to the top of the stash
        # user_data[0] is the moveinput object, overwrite this with 0
        # user_data[1] is the tea object
        moveInput = 0  # Move to the top of the stash
        tea = user_data[1]
        self.moveTeaIndex(sender, app_data, user_data=(moveInput, tea))

    def moveTeaIndex(self, sender, app_data, user_data):
        # Move tea index to the index below the specified index
        # user_data[0] is the moveInput, user_data[1] is the tea object
        # Factor in renumbering and saving the tea stash
        newIndex = user_data[0].get_value()

        if newIndex is None:
            RichPrintError("Error: New index is None, cannot move tea.")
            return

        tea = user_data[1]
        currentIndex = tea.id

        global TeaStash
        RichPrintInfo(f"Moving tea {tea.name} to index {newIndex} from current index {currentIndex}")
        

        # Check if the new index is valid
        if newIndex < 0 or newIndex >= len(TeaStash):
            RichPrintError(f"Error: Invalid index {newIndex}. Must be between 0 and {len(TeaStash)-1}.")
            return
        # Check if the tea is already at the new index
        if tea.id == newIndex:
            RichPrintWarning(f"Warning: Tea {tea.name} is already at index {newIndex}. No changes made.")
            return
        # Remove the tea from the stash
        teaStashObj = None
        for i, teaStash in enumerate(TeaStash):
            if teaStash.id == tea.id:
                teaStashObj = teaStash
                break
        if teaStashObj is None:
            RichPrintError("Error: Tea not found in stash.")
            return
        # Remove the tea from the stash
        TeaStash.remove(teaStashObj)
        # Insert the tea at the new index
        TeaStash = TeaStash[:newIndex] + [teaStashObj] + TeaStash[newIndex:]
        # Renumber the tea ids
        for i, teaStash in enumerate(TeaStash):
            teaStash.id = i
        # Save the tea stash to file
        saveTeasData(TeaStash, settings["TEA_REVIEWS_PATH"])
        RichPrintSuccess(f"Moved tea {tea.name} to index {newIndex} from current index {currentIndex}, renumbered stash.")
        # Refresh the window
        self.deleteAdjustmentsWindow()
        self.softRefresh()

    def greyOutAdjustmentInput(self, sender, app_data, user_data):
        # If the tea is finished, grey out the adjustment input

        finished = app_data
        teaCurrent = user_data[1]
        adjustmentInput = user_data[2]
        currentAmount = user_data[3]
        if finished:
            # If the tea is finished, grey out the adjustment input
            adjustmentInput.enabled = False
            adjustmentInput.set_value(0.0)
            RichPrintInfo(f"Tea {teaCurrent.name} is finished. Adjustment input is disabled.")
        else:
            # If the tea is not finished, enable the adjustment input
            adjustmentInput.enabled = True
            adjustmentInput.set_value(0.0)
            RichPrintInfo(f"Tea {teaCurrent.name} is not finished. Adjustment input is enabled.")


    
    def UpdateAdjustmentAmt(self, sender, app_data, user_data):
        # Updates the adjustment amount, user_data[0] is the tea object
        tea = user_data[0]
        adjustmentInput = user_data[1]
        adjustment = adjustmentInput.get_value()
        finishedCheckbox = user_data[2]
        finished = finishedCheckbox.get_value()
        typeOfAdjustment = user_data[3]
        # Check if the adjustment is a valid number
        # Discard Nonetype values, which occur from a bug
        if adjustment is None:
            RichPrintError("Error: Nonetype found, discarding (results from a library bug, may crash.).")
            return
        try:
            adjustment = float(adjustment)
        except ValueError:
            RichPrintError("Error: Adjustment is not a valid number. Found: ", adjustment)
            return
        # Modify tea object
                
        # Update the adjustment amount
        tea.adjustments[typeOfAdjustment] = round(adjustment, 2)
        tea.finished = finished
        # Save the tea stash to file
        saveTeasData(TeaStash, settings["TEA_REVIEWS_PATH"])
        RichPrintSuccess(f"Updated {typeOfAdjustment} adjustment amount for tea {tea.name} to {adjustment:.3f}g")

        # Delete the adjustments window
        self.deleteAdjustmentsWindow()


    def AddTea(self, sender, app_data, user_data):
        # All input texts and other input widgets are in the addTeaGroup
        # create a new tea and add it to the stash
        allAttributes = {}
        for k, v in self.addTeaList.items():
            if type(v) == dp.DatePicker:
                allAttributes[k] = DateDictToDT(v.get_value())
            else:
                val = v.get_value()
                # If float, round to 3 decimal places
                if type(val) == float:
                    val = round(val, 3)

                # If string, strip, and remove quotes
                if type(val) == str:
                    if k == "Notes (Long)":
                        val = RateaTexts.sanitizeInputMultiLineString(val)
                    elif "Score" in k:
                        # Stored as a float, but displayed as a letter grade
                        val = getGradeValue(val)
                    else:
                        val = RateaTexts.sanitizeInputLineString(val)
                allAttributes[k] = val

        RichPrintInfo(f"Adding tea: {allAttributes}")

        # Check if the dateAdded attribute is present, if not, set it to the current time
        if "dateAdded" not in allAttributes:
            allAttributes["dateAdded"] = dt.datetime.now(tz=dt.timezone.utc).timestamp()

        # Create a new tea and add it to the stash
        newTea = StashedTea(len(TeaStash) + 1, allAttributes["Name"], allAttributes["dateAdded"], allAttributes)
        dateAdded = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        newTea.dateAdded = dateAdded
        TeaStash.append(newTea)

        # Save to file
        saveTeasData(TeaStash, settings["TEA_REVIEWS_PATH"])
        
        # hide the popup
        dpg.configure_item(self.teasWindow.tag, show=False)
        self.softRefresh()


    def EditTea(self, sender, app_data, user_data):
        # Get the tea from the stash
        tea = user_data

        # All input texts and other input widgets are in the addTeaGroup
        # Revise the tea and save it to the stash, overwriting the old one
        allAttributes = {}
        for k in self.addTeaList:
            v = self.addTeaList[k]
            if type(v) == dp.DatePicker:
                allAttributes[k] = DateDictToDT(v.get_value())
            else:
                val = v.get_value()
                # If float, round to 3 decimal places
                if type(val) == float:
                    val = round(val, 3)

                # If string, strip, and remove quotes
                if type(val) == str:
                    if k == "Notes (Long)":
                        val = RateaTexts.sanitizeInputMultiLineString(val)
                    elif "Score" in k:
                        # Stored as a float, but displayed as a letter grade
                        val = getGradeValue(val)
                    else:
                        val = RateaTexts.sanitizeInputLineString(val)
                allAttributes[k] = val


        
        dateAdded = None
        if hasattr(tea, 'dateAdded') and tea.dateAdded is not None:
            dateAdded = tea.dateAdded
        # Transfer the dateAdded if it exists, otherwise use the current time
        if dateAdded is None:
            dateAdded = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        newTea = StashedTea(tea.id, allAttributes["Name"], dateAdded, allAttributes)

        # Transfer the reviews
        newTea.reviews = tea.reviews
        # Transfer the calculated values
        newTea.calculated = tea.calculated
        # Transfer the adjustments
        newTea.adjustments = tea.adjustments
        # Transfer the finished flag
        newTea.finished = tea.finished

        for i, tea in enumerate(TeaStash):
            if tea.id == user_data.id:
                TeaStash[i] = newTea
                break

        # Save to file
        saveTeasData(TeaStash, settings["TEA_REVIEWS_PATH"])

        # hide the popup
        dpg.configure_item(self.teasWindow.tag, show=False)
        self.deleteTeasWindow()
        self.softRefresh()

    def DeleteTea(self, sender, app_data, user_data):
        # Remove tea from the stash (DUMMY, JUST PRINT)
        # User data is the tea object to be deleted, which we need to get the tag and grab from the TeaStash list
        if self.teasWindow is None:
            RichPrintError("No teas window to delete from.")
            return
        
        selectedTea = None
        try:
            selectedTea = user_data  # This should be the tea object to delete
            if selectedTea is None:
                RichPrintError("No tea selected for deletion.")
                return
        except Exception as e:
            RichPrintError(f"Error getting selected tea: {e}")
            return
        
        # Tag
        for i, tea in enumerate(TeaStash):
            if tea.id == selectedTea.id:
                RichPrintInfo(f"Deleting tea: {tea.name} (ID: {tea.id})")
                TeaStash.pop(i)
                break

        # Renumber the IDs of the remaining teas
        renumberTeasAndReviews(save=False)

        # Save to file
        saveTeasData(TeaStash, settings["TEA_REVIEWS_PATH"])

        # Refresh the window to reflect the deletion
        self.softRefresh()
        # Close the teas window if it's open (This is the edit reviews window)
        if self.teasWindow is not None:
            self.teasWindow.delete()
            self.teasWindow = None

        


def Menu_Notepad(sender, app_data, user_data):
    w = 520 * settings["UI_SCALE"]
    h = 560 * settings["UI_SCALE"]
    notepad = Window_Notepad("Notepad", w, h, exclusive=False)
    if user_data is not None:
        notepad.importYML(user_data)

class Window_Notepad(WindowBase):
    text = ""
    textInput = None
    def onCreate(self):
        self.persist = True
        return super().onCreate()
    def _enableSaveReminder(self):
        # Enables the save reminder for the notepad window
        if self.persist and self.text != "":
            # If persist is enabled, set the save reminder to True
            self.dpgWindow.unsaved_document = True
        else:
            # If persist is disabled, set the save reminder to False
            self.dpgWindow.unsaved_document = False

    def _disableSaveReminder(self):
        # Disables the save reminder for the notepad window
        self.dpgWindow.unsaved_document = False
    def savePersistedData(self, sender, app_data, user_data):
        # Call global export persisted data function to save the notepad text
        if self.persist and self.text != "":
            windowManager.exportOneWindow(sender, app_data, "Notepad")
        self._disableSaveReminder()
    def windowDefintion(self, window):
        with window:
            dp.Text("Notepad")
            # Toolbar with clear
            hgroupToolbar = dp.Group(horizontal=True)
            with hgroupToolbar:
                dp.Button(label="Clear", callback=self.clearNotepad)
                dp.Button(label="Copy", callback=self.copyNotepad)
                dp.Button(label="Template", callback=self.setTemplate)
                dp.Button(label="Format/Wrap", callback=self.wrapText)
                dp.Checkbox(label="Persist", default_value=self.persist, callback=self.updatePersist)
                dp.Button(label="Save", callback=self.savePersistedData, user_data=self)
                dp.Button(label="Load", callback=self.importPersistedData, user_data=self)
                #tooltip
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    tooltipText = '''Notepad for writing down notes tea steeps.
                    \nTemplate button will generate a template for notes based on defined categories. (WIP)
                    \nPersist will save the timer between sessions (WIP)'''
                    dp.Text(tooltipText)

            # Text input
            defaultText = "Some space for your notes!"
            scaledWidth = 440 * settings["UI_SCALE"]
            scaledHeight = 440 * settings["UI_SCALE"]
            self.textInput = dp.InputText(default_value=defaultText, multiline=True, width=scaledWidth, height=scaledHeight, callback=self.updateText, user_data=self)
            
            dp.Separator()

    def clearNotepad(self, sender, data):
        self.textInput.set_value("")
        self.text = ""
        self._disableSaveReminder()
    def copyNotepad(self, sender, data):
        pyperclip.copy(self.text)
    def updatePersist(self, sender, data):
        self.persist = data
        if not self.persist:
            self._disableSaveReminder()
    def importPersistedData(self, sender, app_data, user_data):
        # Call window manager to get data, then call importYML to set the text input value
        data = windowManager.importOneWindow(sender, app_data, "Notepad")
        self._disableSaveReminder()
        if data is not None:
            self.importYML(data)
        else:
            RichPrintError("No persisted data found for Notepad.")
            return
    def wrapLongLines(self, text, breakwidth=70):
        # Wraps long lines of text to a specified width
        lines = text.split("\n")
        wrappedLines = []
        for line in lines:
            if len(line) > breakwidth-20:
                wrappedLines.extend(textwrap.wrap(line, width=breakwidth, replace_whitespace=False, break_on_hyphens=False))
            else:
                wrappedLines.append(line)
        return "\n".join(wrappedLines)

    def wrapText(self, sender, app_data, user_data):
        # Calls the textwrap package to wrap the text and sets the value of the text input to the wrapped text
        wrappedText = self.wrapLongLines(self.text, breakwidth=100)
        self.textInput.set_value(wrappedText)
        self.text = wrappedText
    def setTemplate(self, sender, app_data, user_data):
        # Sets the value to a simple template for notes
        template = '''
Template for notes
---
Name: 
Producer: 
Type: 
Amount: 
Pot/Temperature: 100C/212F
Date: DATE


Times Steeped:
Grade/Rating: 
Notes: 




Reference Scale:
+ / / -
S -- (5.0, 4.5, 4.25)
A -- (4.0, 3.5, 3.25)
B -- (3.0, 2.5, 2.25)
C -- (2.0, 1.5, 1.25)
D -- (1.0, 0.5, 0.25)
F -- (0.0, 0.0, 0.0)


---
'''
        # Replace the date with the current date
        currentDate = dt.datetime.now(tz=dt.timezone.utc)
        template = template.replace("DATE", currentDate.strftime(settings["DATE_FORMAT"]))
        self.textInput.set_value(template)
        self.text = template
    def updateText(self, sender, app_data, user_data):
        self.text = app_data
        self._enableSaveReminder()

    def exportYML(self):
        windowVars = {
            "text": self.text,
            "width": self.width,
            "height": self.height
        }
        return windowVars
    
    def importYML(self, data):
        text = data.get("text", "")
        text = text.replace("\r", "")  # Remove carriage returns
        text = text.replace("\\n", "\n")  # Replace escaped newlines with actual newlines
        text.replace("\n", '''
''')  # Replace newlines with double newlines for better formatting
        self.text = text
        self.width = data["width"]
        self.height = data["height"]
        self.textInput.set_value(self.text)

        # Update size
        self.dpgWindow.width = self.width
        self.dpgWindow.height = self.height



# Stats functions

# Get Start day will use the start day from the settings, or default the earliest date it can find

def reCacheStats():
    # Recalculate all stats and cache them
    global statsCache
    statsCache = populateStatsCache()
    RichPrintSuccessMinor(f"Stats cache updated")
    return statsCache

def populateStatsCache():
    # Run all calcs in parallel and cache them for other cals. return the cache
    cache = {}
    timeCacheStart = dt.datetime.now(tz=dt.timezone.utc).timestamp()
    AllTypesCategoryRoleValid, AllTypesCategoryRole = getValidCategoryRolesList()
    allTypesCategoryRoleReviewsValid, allTypesCategoryRoleReviews = getValidReviewCategoryRolesList()

    remainingCategory = None
    for cat in TeaCategories:
        if cat.categoryRole == "Remaining":
            remainingCategory = cat
            break


    # Num teas
    cache["numTeas"] = statsNumTeas()
    # Num reviews
    cache["numReviews"] = statsNumReviews()
    # Start day
    cache["startDay"] = statsgetStartDayTimestamp()
    totalDays = dt.datetime.now(tz=dt.timezone.utc).timestamp() - cache["startDay"]
    cache["totalDays"] = totalDays / (24 * 60 * 60)  # Convert to days

    # Num teas by type
    cache["numTeasByType"] = dict()
    for tea in TeaStash:
        if "Type" in tea.attributes:
            teaType = tea.attributes["Type"]
            if teaType in cache["numTeasByType"]:
                cache["numTeasByType"][teaType] += 1
            else:
                cache["numTeasByType"][teaType] = 1

    # Calc total volume, average volume and all the other stash stats in one loop to prevent multiple loops
    ctrTotalVolume = 0
    ctrTotalCost = 0
    ctrTotalConsumedByReviews = 0
    ctrTotalConsumedByStdAdjustments = 0
    ctrTotalConsumedByFinishedTeas = 0
    ctrTotalConsumedByGiftedTeas = 0
    ctrTotalConsumedBySaleAdjustments = 0
    ctrTotalReturnedBySales = 0
    ctrTotalRemaining = 0
    ctrTotalTeasTried = 0
    dictCtrTeasTried = {}
    ctrTeasFinished = 0
    dictCtrTeasFinished = {}
    ctrTotalScored = 0
    dictCtrScoresByType = {}
    dictSteepsByType = {}
    dictNumReviewsByType = {}
    listTopTenTeasSoldByValue = []
    ctrTotalTeasSold= 0

    # Set to 1990-01-01 00:00:00 UTC as the default for latest purchase
    ctrLatestPurchase = dt.datetime(1990, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc).timestamp()
    remainingCategory = None
    for cat in TeaCategories:
        if cat.categoryRole == "Remaining":
            remainingCategory = cat
            break
    cache["remainingCategory"] = remainingCategory
    
    for tea in TeaStash:
        ctrTeaRemaining = 0
        ctrTeaDrankReviews = 0
        ctrTeaTotalAdjustments = 0
        ctrTeaGiftAdjustments = 0
        ctrTeaStandardAdjustments = 0
        ctrTeaFinishedAmt = 0
        autocalcTotalScore = 0
        autocalcAveragedScore = 0
        autocalcCostPerGram = 0
        teaType = None
        if "Type" in AllTypesCategoryRoleValid:
            teaType = tea.attributes["Type"]

        if "Cost" in AllTypesCategoryRoleValid and "Amount" in AllTypesCategoryRoleValid:
            if "Cost" in tea.attributes and "Amount" in tea.attributes:
                autocalcCostPerGram = tea.attributes["Cost"] / tea.attributes["Amount"]
        if "Amount" in AllTypesCategoryRoleValid:
            if "Amount" in tea.attributes:
                ctrTotalVolume += tea.attributes["Amount"]
        if "Cost" in AllTypesCategoryRoleValid:
            if "Cost" in tea.attributes:
                ctrTotalCost += tea.attributes["Cost"]

        # If the tea has a date, check if it's the latest purchase
        if "date" in tea.attributes:
            if tea.attributes["date"] > ctrLatestPurchase:
                ctrLatestPurchase = tea.attributes["date"]

        if "Standard" in tea.adjustments:
            ctrTeaStandardAdjustments = tea.adjustments["Standard"]
            ctrTotalConsumedByStdAdjustments += ctrTeaStandardAdjustments
            ctrTeaTotalAdjustments += ctrTeaStandardAdjustments

        # Gifted teas
        if "Amount" in tea.attributes:
            if "Gift" in tea.adjustments:
                ctrTeaGiftAdjustments = tea.adjustments["Gift"]
                ctrTotalConsumedByGiftedTeas += ctrTeaGiftAdjustments
                ctrTeaTotalAdjustments += ctrTeaGiftAdjustments

        # Sale adjustments
        ctrTeaSaleAdjustments = 0
        if "Sale" in tea.adjustments:
            ctrTeaSaleAdjustments = tea.adjustments["Sale"]
            if ctrTeaSaleAdjustments > 0:
            # If there is a sale adjustment, add it to the list of top ten teas sold by value
                ctrTotalTeasSold += 1
                ctrTotalConsumedBySaleAdjustments += ctrTeaSaleAdjustments
                ctrTeaTotalAdjustments += ctrTeaSaleAdjustments
                # Given cost and amount of sale, calculate total returned
                if "Cost" in tea.attributes and "Amount" in tea.attributes:
                    ctrTotalReturnedBySales += autocalcCostPerGram * ctrTeaSaleAdjustments
                    listTopTenTeasSoldByValue.append((tea, ctrTeaSaleAdjustments, autocalcCostPerGram))

        # Teas tried
        if len(tea.reviews) > 0 or tea.finished or ctrTeaStandardAdjustments > 0:
            # If the tea has reviews or is finished, count it as tried
            ctrTotalTeasTried += 1
            if "Type" in AllTypesCategoryRoleValid:
                if tea.attributes["Type"] not in dictCtrTeasTried:
                    dictCtrTeasTried[tea.attributes["Type"]] = 1
                else:
                    dictCtrTeasTried[tea.attributes["Type"]] += 1

        

        # Review loop
        for review in tea.reviews:
            if "Amount" in allTypesCategoryRoleReviewsValid:
                if "Amount" in review.attributes:
                    ctrTeaDrankReviews += review.attributes["Amount"]

            # Total up score raw value
            if "Final Score" in allTypesCategoryRoleReviewsValid and "Total Score" in AllTypesCategoryRoleValid:
                ctrTotalScored += review.attributes["Final Score"]
                autocalcTotalScore += review.attributes["Final Score"]
                if "Type" in allTypesCategoryRoleReviewsValid:
                    if review.attributes["Type"] not in dictCtrScoresByType:
                        dictCtrScoresByType[review.attributes["Type"]] = 0
                    dictCtrScoresByType[review.attributes["Type"]] += review.attributes["Final Score"]

            # Steeps by type
            if "Steeps" in allTypesCategoryRoleReviewsValid and teaType is not None:
                if teaType not in dictSteepsByType:
                    dictSteepsByType[teaType] = 0
                dictSteepsByType[teaType] += review.attributes["Steeps"]

            # Num reviews by type
            if teaType is not None:
                if teaType not in dictNumReviewsByType:
                    dictNumReviewsByType[teaType] = 0
                dictNumReviewsByType[teaType] += 1


        ctrTotalConsumedByReviews += ctrTeaDrankReviews
        # Calculate remaining
        ctrTeaRemaining = tea.attributes["Amount"] - ctrTeaDrankReviews - tea.adjustments.get("Standard", 0) - tea.adjustments.get("Gift", 0) - tea.adjustments.get("Sale", 0)

        # If finished, the remaining is set to 0 and added to the total consumed by finished teas
        if ctrTeaRemaining <= 0:
            ctrTeaRemaining = 0
            # If the tea is finished, set the finished flag
            tea.finished = True
        if tea.finished:
            ctrTotalConsumedByFinishedTeas += ctrTeaRemaining
            ctrTeaFinishedAmt = ctrTeaRemaining
            ctrTeaRemaining = 0
            ctrRemainingExcludingStandard = tea.attributes["Amount"] - ctrTeaDrankReviews - tea.adjustments.get("Gift", 0) - tea.adjustments.get("Sale", 0)

            if ctrRemainingExcludingStandard > 0:
                RichPrintInfo(f"Tea {tea.name} is finished, adjusting standard amount to {ctrRemainingExcludingStandard:.2f}g and remaining amount to 0g.")
                # back-adjust the tea's standard adjustment to reflect the remaining amount
                tea.adjustments["Standard"] = ctrRemainingExcludingStandard
                # back-adjust the tea's remaining amount to 0 to reflect the finished state, only if it is autocalculated
                if "Remaining" in AllTypesCategoryRoleValid and remainingCategory.isAutoCalculated:
                    tea.attributes["Remaining"] = 0

        ctrTotalRemaining += ctrTeaRemaining


        # Derive explanation for remaining
        remainingExplanation = ""
        stdPlusFinished = tea.adjustments.get("Standard", 0) + ctrTeaFinishedAmt
        explanation = f"{tea.attributes['Amount']:.2f}g Purchased\n- {ctrTeaDrankReviews:.2f}g Sum of all review Amounts\n- {stdPlusFinished:.2f}g Standard Adjustments (inc Finished)\n- {ctrTeaGiftAdjustments:.2f}g Gift Adjustments\n- {ctrTeaSaleAdjustments:.2f}g Sale Adjustments\n= {ctrTeaRemaining:.2f}g Remaining"
        if ctrTeaRemaining < 0:
            remainingExplanation = explanation + " (Overdrawn)"
        elif ctrTeaRemaining == 0:
            remainingExplanation = explanation + " (Finished)"
        else:
            remainingExplanation = explanation + " (Not Finished)"

        # Calc average score
        if autocalcTotalScore > 0:
            autocalcAveragedScore = autocalcTotalScore / len(tea.reviews)

        totalScoreExplanation = f"{autocalcTotalScore:.2f} Total Score\n/ {len(tea.reviews)} Number of reviews\n= {autocalcAveragedScore:.2f} Average Score"

        # if no reviews, set autocalcAveragedScore to -1
        if len(tea.reviews) == 0:
            autocalcAveragedScore = -1
            totalScoreExplanation = "No reviews, no score"

        # Finished teas
        if tea.finished or ctrTeaRemaining <= 0:
            ctrTeasFinished += 1
            if "Type" in AllTypesCategoryRoleValid:
                if tea.attributes["Type"] not in dictCtrTeasFinished:
                    dictCtrTeasFinished[tea.attributes["Type"]] = 1
                else:
                    dictCtrTeasFinished[tea.attributes["Type"]] += 1
            
        # Autocalc explanation for cost per gram
        costPerGramExplanation = f"${tea.attributes['Cost']:.2f} Cost\n/ {tea.attributes['Amount']:.2f} Amount\n= ${autocalcCostPerGram:.2f} Price per gram"
        # Add to tea.cache
        tea.calculated["remaining"] = ctrTeaRemaining
        tea.calculated["remainingExplanation"] = remainingExplanation
        tea.calculated["averageScore"] = autocalcAveragedScore
        tea.calculated["totalScoreExplanation"] = totalScoreExplanation
        tea.calculated["costPerGramExplanation"] = costPerGramExplanation
        tea.calculated["costPerGram"] = autocalcCostPerGram

    if cache["numTeas"] > 0:
        cache["averageVolume"] = ctrTotalVolume / cache["numTeas"]
    else:
        cache["averageVolume"] = 0

    cache["totalVolume"] = ctrTotalVolume
    if cache["numTeas"] > 0:
        cache["averageCost"] = ctrTotalCost / cache["numTeas"]
    else:
        cache["averageCost"] = 0
    cache["totalCost"] = ctrTotalCost
    # Weighted average cost
    if "Cost" in AllTypesCategoryRoleValid and "Amount" in AllTypesCategoryRoleValid:
        if ctrTotalVolume > 0:
            cache["weightedAverageCost"] = ctrTotalCost / ctrTotalVolume
        else:
            cache["weightedAverageCost"] = 0
    else:
        cache["weightedAverageCost"] = 0

    # Total consumed by reviews
    if "Amount" in allTypesCategoryRoleReviewsValid and cache["numReviews"] > 0 and cache["numTeas"] > 0:
        cache["totalConsumedByReviewsSum"] = ctrTotalConsumedByReviews
        cache["averageConsumedByReviews"] = ctrTotalConsumedByReviews / cache["numTeas"]
    else:
        cache["totalConsumedByReviewsSum"] = 0
        cache["averageConsumedByReviews"] = 0

    # Total consumed by standard adjustments
    if "Remaining" in AllTypesCategoryRoleValid and cache["numTeas"] > 0:
        cache["totalConsumedByStdAdjustmentsOnlySum"] = ctrTotalConsumedByStdAdjustments
        cache["averageConsumedByStdAdjustmentsOnly"] = ctrTotalConsumedByStdAdjustments / cache["numTeas"]
    else:
        cache["totalConsumedByStdAdjustmentsOnlySum"] = 0
        cache["averageConsumedByStdAdjustmentsOnly"] = 0

    # Total consumed by finished teas
    if "Amount" in AllTypesCategoryRoleValid and cache["numTeas"] > 0:
        cache["totalConsumedByFinishedTeasSum"] = ctrTotalConsumedByFinishedTeas
        cache["averageConsumedByFinishedTeas"] = ctrTotalConsumedByFinishedTeas / cache["numTeas"]
    else:
        cache["totalConsumedByFinishedTeasSum"] = 0
        cache["averageConsumedByFinishedTeas"] = 0

    # Total personally consumed (finished + reviews + standard adjustments)
    if "Amount" in AllTypesCategoryRoleValid and cache["numTeas"] > 0:
        cache["totalConsumedByPersonalSum"] = ctrTotalConsumedByReviews + ctrTotalConsumedByStdAdjustments + ctrTotalConsumedByFinishedTeas
        cache["averageConsumedByPersonal"] = (ctrTotalConsumedByReviews + ctrTotalConsumedByStdAdjustments + ctrTotalConsumedByFinishedTeas) / cache["numTeas"]
    else:
        cache["totalConsumedByPersonalSum"] = 0
        cache["averageConsumedByPersonal"] = 0

    # Total consumed by gifted teas
    if "Amount" in AllTypesCategoryRoleValid and cache["numTeas"] > 0:
        cache["totalConsumedByGiftedTeasSum"] = ctrTotalConsumedByGiftedTeas
        cache["averageConsumedByGiftedTeas"] = ctrTotalConsumedByGiftedTeas / cache["numTeas"]
    else:
        cache["totalConsumedByGiftedTeasSum"] = 0
        cache["averageConsumedByGiftedTeas"] = 0

    # Total consumed by sale adjustments
    if "Amount" in AllTypesCategoryRoleValid and cache["numTeas"] > 0:
        cache["totalConsumedBySaleAdjustmentsSum"] = ctrTotalConsumedBySaleAdjustments
        cache["averageConsumedBySaleAdjustments"] = ctrTotalConsumedBySaleAdjustments / cache["numTeas"]
    else:
        cache["totalConsumedBySaleAdjustmentsSum"] = 0
        cache["averageConsumedBySaleAdjustments"] = 0

    # Total returned by sales
    if "Amount" in AllTypesCategoryRoleValid and cache["numTeas"] > 0:
        cache["totalReturnedBySales"] = ctrTotalReturnedBySales
        cache["averageReturnedBySales"] = ctrTotalReturnedBySales / cache["numTeas"]
    else:
        cache["totalReturnedBySales"] = 0
        cache["averageReturnedBySales"] = 0

    # Top ten teas sold by value
    listTopTenTeasSoldByValue.sort(key=lambda x: x[1], reverse=True)
    cache["topTenTeasSoldByValue"] = listTopTenTeasSoldByValue[:10]  # Limit to top 10
    cache["totalTeasSold"] = ctrTotalTeasSold

    # Steeps by type
    cache["steepsByType"] = dictSteepsByType
    # Num reviews by type
    cache["numReviewsByType"] = dictNumReviewsByType

    # Total consumed by all methods
    totalConsumed = ctrTotalConsumedByReviews + ctrTotalConsumedByStdAdjustments + ctrTotalConsumedByFinishedTeas + ctrTotalConsumedByGiftedTeas + ctrTotalConsumedBySaleAdjustments
    cache["totalConsumed"] = totalConsumed
    cache["averageConsumed"] = totalConsumed / cache["numTeas"] if cache["numTeas"] > 0 else 0

    # Total consumed excluding gift adjustments
    totalConsumedExcludingGiftAdj = ctrTotalConsumedByReviews + ctrTotalConsumedByStdAdjustments + ctrTotalConsumedByFinishedTeas
    cache["totalConsumedExcludingGiftAdj"] = totalConsumedExcludingGiftAdj
    cache["averageConsumedExcludingGiftAdj"] = totalConsumedExcludingGiftAdj / cache["numTeas"] if cache["numTeas"] > 0 else 0

    # Total Consumed Standard Adjustments is finished plus standard
    totalConsumedStandardAdj = ctrTotalConsumedByStdAdjustments
    cache["totalConsumedStandardAdj"] = totalConsumedStandardAdj
    cache["averageConsumedStandardAdj"] = totalConsumedStandardAdj / cache["numTeas"] if cache["numTeas"] > 0 else 0

    # Total Consumed Gift Adjustments is just the gift adjustments
    totalConsumedGiftAdj = ctrTotalConsumedByGiftedTeas
    cache["totalConsumedGiftAdj"] = totalConsumedGiftAdj
    cache["averageConsumedGiftAdj"] = totalConsumedGiftAdj / cache["numTeas"] if cache["numTeas"] > 0 else 0

    # Total consumed by sale and gift adjustments
    totalConsumedSaleAdj = ctrTotalConsumedBySaleAdjustments
    cache["totalConsumedSaleGiftAdj"] = totalConsumedSaleAdj
    cache["averageConsumedSaleGiftAdj"] = totalConsumedSaleAdj / cache["numTeas"] if cache["numTeas"] > 0 else 0

    # Total Remaining
    cache["totalRemaining"] = ctrTotalRemaining
    if cache["numTeas"] > 0:
        cache["averageRemaining"] = ctrTotalRemaining / cache["numTeas"]
    else:
        cache["averageRemaining"] = 0

    # Teas tried
    cache["totalTeasTried"] = ctrTotalTeasTried
    cache["averageTeasTried"] = ctrTotalTeasTried / cache["numTeas"] if cache["numTeas"] > 0 else 0
    cache["teasTriedByType"] = dictCtrTeasTried
    
    # Teas not tried
    cache["totalTeasNotTried"] = cache["numTeas"] - ctrTotalTeasTried
    cache["averageTeasNotTried"] = (cache["numTeas"] - ctrTotalTeasTried) / cache["numTeas"] if cache["numTeas"] > 0 else 0
    cache["teasNotTriedByType"] = {k: cache["numTeasByType"].get(k, 0) - dictCtrTeasTried.get(k, 0) for k in cache["numTeasByType"]}

    # Teas finished
    cache["totalTeasFinished"] = ctrTeasFinished
    cache["averageTeasFinished"] = ctrTeasFinished / cache["numTeas"] if cache["numTeas"] > 0 else 0
    cache["teasFinishedByType"] = dictCtrTeasFinished

    # Total and average score by type
    cache["totalScore"] = ctrTotalScored
    cache["averageScore"] = ctrTotalScored / len(tea.reviews) if len(tea.reviews) > 0 else 0
    cache["scoreByType"] = dictCtrScoresByType

    # Average purchase per month
    monthsSinceStart = cache["totalDays"] / 30.44  # Average days per month
    if monthsSinceStart > 0:
        cache["averagePurchasePerMonth"] = cache["totalCost"] / monthsSinceStart
    else:
        cache["averagePurchasePerMonth"] = 0
    # Latest purchase date
    cache["latestPurchase"] = ctrLatestPurchase
    
    # Days since last purchase
    if ctrLatestPurchase > 0:
        daysSinceLastPurchase = (dt.datetime.now(tz=dt.timezone.utc).timestamp() - ctrLatestPurchase) / (24 * 60 * 60)
        cache["daysSinceLastPurchase"] = daysSinceLastPurchase
    else:
        cache["daysSinceLastPurchase"] = 0

    # Purchases by month
    purchasesByMonth = {}
    for tea in TeaStash:
        if "date" in tea.attributes and tea.attributes["date"] is not None:
            purchaseDate = dt.datetime.fromtimestamp(tea.attributes["date"], tz=dt.timezone.utc)
            monthYear = purchaseDate.strftime("%Y-%m")
            if monthYear not in purchasesByMonth:
                purchasesByMonth[monthYear] = 0
            purchasesByMonth[monthYear] += tea.attributes.get("Cost", 0)
    cache["purchasesByMonth"] = purchasesByMonth

    timeCacheEnd = dt.datetime.now(tz=dt.timezone.utc).timestamp()
    timeCacheDuration = timeCacheEnd - timeCacheStart
    RichPrintSuccessMinor(f"Stats cache duration: {timeCacheDuration:.2f} seconds")

    return cache

def statsgetStartDayTimestamp():
    startDay = None
    if "START_DAY" in settings and settings["START_DAY"] is not None and settings["START_DAY"] != "":
        startDay = settings["START_DAY"]
        return AnyDTFormatToTimeStamp(startDay)
    # If no start day is set, find the earliest date in the stash
    earliestDate = None
    for tea in TeaStash:
        if tea.dateAdded is not None:
            dateAddedTimestamp = AnyDTFormatToTimeStamp(tea.dateAdded)
            if earliestDate is None or dateAddedTimestamp < earliestDate:
                earliestDate = dateAddedTimestamp
        # Also check date purchased if it exists
        if "date" in tea.attributes and tea.attributes["date"] is not None:
            datePurchasedTimestamp = AnyDTFormatToTimeStamp(tea.attributes["date"])
            if earliestDate is None or datePurchasedTimestamp < earliestDate:
                earliestDate = datePurchasedTimestamp
    if earliestDate is not None:
        return earliestDate
    # If no teas are in the stash, return the current time
    RichPrintWarning("No start day set and no teas in the stash. Defaulting to current time.")
    return dt.datetime.now(tz=dt.timezone.utc).timestamp()

def statsNumTeas():
    # Get the number of teas in the stash
    numTeas = len(TeaStash)
    return numTeas
def statsNumReviews():
    # Get the number of reviews in the stash
    numReviews = 0
    for tea in TeaStash:
        numReviews += len(tea.reviews)
    return numReviews

def statsWaterConsumed():
    # For each review, multiply the number of steeps by vessel size
    # and sum them up
    totalWaterConsumed = 0
    for tea in TeaStash:
        tea: StashedTea
        for review in tea.reviews:
            if "Steeps" in review.attributes and "Vessel size" in review.attributes:
                steeps = review.attributes["Steeps"]
                vesselSize = review.attributes["Vessel size"]
                totalWaterConsumed += steeps * vesselSize
    # Calculate the average water consumed
    sum, avrg, count, unique, _ = getStatsOnCategoryByRole("Steeps", True)
    if sum > 0:
        averageWaterConsumed = totalWaterConsumed / sum
    else:
        averageWaterConsumed = 0
    return totalWaterConsumed, averageWaterConsumed


def Menu_Stats():
    w = 1280 * settings["UI_SCALE"]
    h = 920 * settings["UI_SCALE"]
    stats = Window_Stats("Stats", w, h, exclusive=True)

class Window_Stats(WindowBase):
    win = None
    refreshIcon = None
    cache = None

    def softRefresh(self):
        # Refresh the stats window
        self.cache = reCacheStats()
        super().softRefresh()

    def afterWindowDefinition(self):
        # After the window is defined, we can set the callback for the soft refresh
        # This will be called when the window is refreshed
        self.onSoftRefresh()
    
    def onSoftRefresh(self):
        if self.refreshIcon is not None and dpg.does_item_exist(self.refreshIcon):
            dpg.configure_item(self.refreshIcon, show=False)


    # Categories and types
    def window_subwindow_0_0_categories(self, sender=None, app_data=None, user_data=None):
        # All types is userdata0, all types reviews is userdata1
        
        AllTypesCategoryRole = user_data[0] if user_data and len(user_data) > 0 else []
        AllTypesCategoryRoleValid = user_data[1] if user_data and len(user_data) > 1 else []

        allTypesCategoryRoleReviews = user_data[2] if user_data and len(user_data) > 2 else []
        allTypesCategoryRoleReviewsValid = user_data[3] if user_data and len(user_data) > 3 else []

        dp.Text("Categories and Types")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))

        # Create a text box
        with dp.CollapsingHeader(label="Enabled Categories", default_open=True):
            with dp.CollapsingHeader(label="Tea Categories", default_open=False, indent=20 * settings["UI_SCALE"]):
                for cat in AllTypesCategoryRole:
                    if cat in AllTypesCategoryRoleValid:
                        dp.Text(f"{cat}", color=COLOR_GREEN_TEXT)
                    else:
                        dp.Text(f"{cat} - Not Enabled", color=COLOR_RED_TEXT)
            dp.Separator()
            # Review categories
            with dp.CollapsingHeader(label="Enabled Review Categories", default_open=False, indent=20 * settings["UI_SCALE"]):
                for cat in allTypesCategoryRoleReviews:
                    if cat in allTypesCategoryRoleReviewsValid:
                        dp.Text(f"{cat}", color=COLOR_GREEN_TEXT)
                    else:
                        dp.Text(f"{cat} - Not Enabled", color=COLOR_RED_TEXT)
                dp.Separator()

        with dp.CollapsingHeader(label="Tea Types", default_open=True):
            teaTypeStats = {}
            with dp.CollapsingHeader(label="Tea Type Stats", default_open=False, indent=20 * settings["UI_SCALE"]):
                if "Type" in AllTypesCategoryRoleValid:                
                    for tea in TeaStash:
                        if "Type" in tea.attributes:
                            teaType = tea.attributes["Type"]
                            if teaType not in teaTypeStats:
                                teaTypeStats[teaType] = 0
                            teaTypeStats[teaType] += 1
                    for teaType, count in teaTypeStats.items():
                        dp.Text(f"{teaType}: {count}")
                else:
                    dp.Text("Required Category role 'Type' for Tea is not enabled.")
            dp.Separator()
            with dp.CollapsingHeader(label="Review Type Stats", default_open=False, indent=20 * settings["UI_SCALE"]):
                if "Type" in allTypesCategoryRoleReviewsValid:
                    # Tea Type Stats
                    teaTypeStats = {}
                    for tea in TeaStash:
                        if "Type" in tea.attributes:
                            teaType = tea.attributes["Type"]
                            if teaType not in teaTypeStats:
                                teaTypeStats[teaType] = 0
                            teaTypeStats[teaType] += 1
                    for teaType, count in teaTypeStats.items():
                        dp.Text(f"{teaType}: {count}")
                else:
                    dp.Text("Required Category role 'Type' for Review is not enabled.")
                dp.Separator()

    # Topline Stats
    def window_subwindow_0_1_categories(self, sender=None, app_data=None, user_data=None):
        allTypesCategoryRoleReviewsValid = user_data[1] if user_data and len(user_data) > 0 else []
        dp.Text("Topline")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        dp.Separator()

        # Topline stats
        # Total purchased, total remaining, cost, consumption per day, days since start
        # No collapsing header, just a list of stats
        totalPurchased = self.cache["totalVolume"]
        totalRemaining = self.cache["totalRemaining"]
        totalCost = self.cache["totalCost"]
        totalConsumed = self.cache["totalConsumed"]
        startDay = self.cache["startDay"]
        totalDays = self.cache["totalDays"]

        # Days
        dp.Text(f"-- Days --")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        dp.Text(f"Start day was: {dt.datetime.fromtimestamp(startDay, tz=dt.timezone.utc).strftime(settings['DATE_FORMAT'])}, which is {totalDays:.2f} days ago")
        dp.Text(f"Total purchased: {totalPurchased:.2f}g, Total remaining: {totalRemaining:.2f}g")
        
        dp.Separator()

        # Total teas. reviews, tried, finished
        dp.Text(f"-- Teas and Reviews --")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        totalTeas = self.cache["numTeas"]
        totalReviews = self.cache["numReviews"]
        totalTeasTried = self.cache["totalTeasTried"]
        totalTeasFinished = self.cache["totalTeasFinished"]
        dp.Text(f"Total teas: {totalTeas}, Total reviews: {totalReviews}")
        dp.Text(f"Total teas tried: {totalTeasTried}, Total teas finished: {totalTeasFinished}")
        dp.Separator()

        # Purchasing stats
        dp.Text(f"-- Purchasing Stats --")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        averagePurchasePerMonth = self.cache["averagePurchasePerMonth"]
        daysSinceLastPurchase = self.cache["daysSinceLastPurchase"]
        totalCost = self.cache["totalCost"]
        dp.Text(f"Total cost: ${totalCost:.2f}")
        dp.Text(f"Average purchase per month: ${averagePurchasePerMonth:.2f}")
        dp.Text(f"Days since last purchase: {daysSinceLastPurchase:.2f} days")
        if totalPurchased > 0:
            averageCostPerGram = totalCost / totalPurchased
            dp.Text(f"Average cost per gram: ${averageCostPerGram:.2f}")
        else:
            dp.Text(f"Average cost per gram: N/A (no purchased teas)")
        dp.Separator()

        # Water consumption
        dp.Text(f"-- Water Consumption --")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        totalWaterConsumed, averageWaterConsumed = statsWaterConsumed()
        liters = totalWaterConsumed / 1000  # Convert to liters
        litersPerDay = liters / totalDays if totalDays > 0 else 0
        dp.Text(f"Total water consumed: {totalWaterConsumed:.2f}ml ({liters:.2f}L, {litersPerDay:.2f}L/day)")
        dp.Separator()

        # Consumption of just personally consumed teas (finished + reviews + standard adjustments)
        dp.Text(f"-- Personally Consumed --")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        totalConsumedByPersonal = self.cache["totalConsumedByPersonalSum"]
        averagePerDay = totalConsumedByPersonal / totalDays if totalDays > 0 else 0
        dp.Text(f"Total personally consumed: {totalConsumedByPersonal:.2f}g")
        dp.Text(f"Average personally consumed per day: {averagePerDay:.2f}g/day")
        # Years remaining
        if totalPurchased > 0:
            yearsRemaining = totalRemaining / (averagePerDay * 365) if averagePerDay > 0 else float('inf')
            dp.Text(f"Years remaining based on current consumption: {yearsRemaining:.2f} years")
        dp.Separator()

        # Consumption from all sources
        dp.Text(f"-- Total Consumption --")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        totalConsumed = self.cache["totalConsumed"]
        averageConsumed = self.cache["averageConsumed"]
        dp.Text(f"Total consumed (all sources): {totalConsumed:.2f}g")
        dp.Text(f"Average consumed per tea (all sources): {averageConsumed:.2f}g")
        # Years remaining based on all consumption
        if totalPurchased > 0:
            yearsRemainingAll = totalRemaining / (averageConsumed * 365) if averageConsumed > 0 else float('inf')
            dp.Text(f"Years remaining based on all consumption: {yearsRemainingAll:.2f} years")
        dp.Separator()
        

    # Dates, spending, purchasing
    def window_subwindow_0_2_categories(self, sender=None, app_data=None, user_data=None):
        dp.Text("Dates, spending, purchasing")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        dp.Separator()
        with dp.CollapsingHeader(label="Purchasing", default_open=True):
            with dp.CollapsingHeader(label="Start Date", default_open=False, indent=20 * settings["UI_SCALE"]):
                # Start day
                dp.Text("Start Day")
                startDay = self.cache["startDay"]
                dp.Text(f"Start Day: {dt.datetime.fromtimestamp(startDay, tz=dt.timezone.utc).strftime(settings['DATE_FORMAT'])}")
                dp.Separator()
                # Total days since start day
                totalDays = self.cache["totalDays"]
                dp.Text(f"Total Days Since Start Day: {totalDays:.2f} days")
                dp.Separator()
            with dp.CollapsingHeader(label="Purchases", default_open=False, indent=20 * settings["UI_SCALE"]):
            # Total spent
                dp.Text(f"Total Spent: ${self.cache['totalCost']:.2f}")

                # Total spent by month
                dp.Text(f"Average Purchase per Month: ${self.cache['averagePurchasePerMonth']:.2f}")
                dp.Text(f"Days Since Last Purchase: {self.cache['daysSinceLastPurchase']:.2f} days")
                dp.Text(f"Latest Purchase: {dt.datetime.fromtimestamp(self.cache['latestPurchase'], tz=dt.timezone.utc).strftime(settings['DATE_FORMAT']) if self.cache['latestPurchase'] > 0 else 'N/A'}")
                dp.Separator()
                with dp.CollapsingHeader(label="Purchasing by Month", default_open=False, indent=20 * settings["UI_SCALE"]):
                    # Purchasing by month
                    dp.Text("Purchasing by Month")
                    # Table of months and total spent
                    purchasesByMonth = self.cache["purchasesByMonth"]
                    i = 0
                    if purchasesByMonth:
                        # Make a table to display the months and total spent
                        spendingTable = dp.Table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True)
                        with spendingTable:
                            dp.TableColumn(label="Month", width_fixed=True, init_width_or_weight=100 * settings["UI_SCALE"])
                            dp.TableColumn(label="Total Spent", width_fixed=True, init_width_or_weight=100 * settings["UI_SCALE"])
                            for month, total in purchasesByMonth.items():
                                with dp.TableRow():
                                    dp.Text(month)
                                    # if month is latest, highlight cell light blue
                                    if month == dt.datetime.fromtimestamp(self.cache["latestPurchase"], tz=dt.timezone.utc).strftime("%Y-%m"):
                                        dpg.highlight_table_cell(spendingTable, i, 0, color=COLOR_LIGHT_BLUE_TEXT)  # Light blue
                                    dp.Text(f"${total:.2f}")
                                    # Highlight light red/dark red/light green/dark green if above +- 25/50% of average
                                    col = None
                                    if total > self.cache["averagePurchasePerMonth"] * 1.5:
                                        col = COLOR_RED_TEXT
                                    elif total > self.cache["averagePurchasePerMonth"] * 1.25:
                                        col = COLOR_LIGHT_RED_TEXT
                                    elif total < self.cache["averagePurchasePerMonth"] * 0.5:
                                        col = COLOR_GREEN_TEXT
                                    elif total < self.cache["averagePurchasePerMonth"] * 0.75:
                                        col = COLOR_LIGHT_GREEN_TEXT

                                    if col is not None:
                                        col = col[0:3] + (col[3] * 0.5,)
                                        dpg.highlight_table_cell(spendingTable, i, 1, color=col)

                                i += 1
                    else:
                        dp.Text("No purchases found.")

                    dp.Separator()
        with dp.CollapsingHeader(label="Resale", default_open=False, indent=20 * settings["UI_SCALE"]):
            # Get sale amount and returned value from cache
            totalSoldAmt = self.cache["totalConsumedBySaleAdjustmentsSum"]
            totalReturnedAmt = self.cache["totalReturnedBySales"]
            dp.Text(f"Total Sold Amount: {totalSoldAmt:.2f}g")
            dp.Text(f"Total Returned value: ${totalReturnedAmt:.2f}")
            pricepergram = 0
            if totalSoldAmt > 0:
                pricepergram = totalReturnedAmt / totalSoldAmt
            dp.Text(f"Price per gram: ${pricepergram:.2f}")
            # Top 10 sold teas by price
            with dp.CollapsingHeader(label="Top 10 Sold Teas by Price", default_open=False, indent=20 * settings["UI_SCALE"]):
                for topTeaTuple in TeaCache["topTenTeasSoldByValue"]:
                    tea = topTeaTuple[0]
                    amt = topTeaTuple[1]
                    ppg = topTeaTuple[2]
                    value = amt * ppg
                    if "Cost" in tea.attributes and "Amount" in tea.attributes:
                        dp.Text(f"{tea.name} - {amt:.2f}g, ${ppg:.2f}/g, Value: ${value:.2f}")
            dp.Separator()

    # Consumption and remaining stats
    def window_subwindow_1_0_categories(self, sender=None, app_data=None, user_data=None):
        AllTypesCategoryRoleValid = user_data[0] if user_data and len(user_data) > 0 else []
        allTypesCategoryRoleReviewsValid = user_data[1] if user_data and len(user_data) > 1 else []
        dp.Text("Consumption and Remaining Stats")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        dp.Separator()
        # Total volume Purchased, total cost, and weighted average cost
        with dp.CollapsingHeader(label="Volume, costs, adjustments", default_open=True):
            with dp.CollapsingHeader(label="Total Volume and Cost", default_open=False, indent=20 * settings["UI_SCALE"]):
                # Total volume Purchased, total cost, and weighted average cost
                if "Cost" in AllTypesCategoryRoleValid and "Amount" in AllTypesCategoryRoleValid:
                    dp.Text("Total Volume and Cost")
                    totalVolume = self.cache["totalVolume"]
                    averageVolume = self.cache["averageVolume"]
                    dp.Text(f"Total Volume: {totalVolume:.2f}g, Average Volume: {averageVolume:.2f}g")
                    totalCost = self.cache["totalCost"]
                    averageCost = self.cache["averageCost"]
                    dp.Text(f"Total Cost: ${totalCost:.2f}, Average Cost: ${averageCost:.2f}")
                    weightedAverageCost = self.cache["weightedAverageCost"]
                    dp.Text(f"Weighted Average Cost: ${weightedAverageCost:.2f}")
                else:
                    dp.Text("Required Category role 'Cost' or 'Amount' for Tea is not enabled.")
                dp.Separator()

            with dp.CollapsingHeader(label="Total Consumed and Remaining", default_open=False, indent=20 * settings["UI_SCALE"]):
                # Total consumed by summing all reviews, adjustments, and finished teas
                dp.Text("Consumed - (All)")
                if "Amount" in AllTypesCategoryRoleValid:
                    totalConsumed = self.cache["totalConsumed"]
                    averageConsumed = self.cache["averageConsumed"]
                    dp.Text(f"Total: {totalConsumed:.2f}g, Average per Tea: {averageConsumed:.2f}g")
                else:
                    dp.Text("Required Category role 'Amount' for Tea is not enabled.")
                dp.Separator()
                # Total consumed excluding Gift adjustments
                dp.Text("Consumed - (Review, Standard, Finished Teas)")
                if "Amount" in AllTypesCategoryRoleValid:
                    totalConsumedExclAdj = self.cache["totalConsumedExcludingGiftAdj"]
                    averageConsumedExclAdj = self.cache["averageConsumedExcludingGiftAdj"]
                    dp.Text(f"Total: {totalConsumedExclAdj:.2f}g, Average per Tea: {averageConsumedExclAdj:.2f}g")
                else:
                    dp.Text("Required Category role 'Amount' for Tea is not enabled.")
                dp.Separator()
                # Total consumed excluding all adjustments
                dp.Text("Consumed - (Review Only)")
                if "Amount" in AllTypesCategoryRoleValid:
                    totalConsumedReviews = self.cache["totalConsumedByReviewsSum"]
                    averageConsumedReviews = self.cache["averageConsumedByReviews"]
                    dp.Text(f"Total: {totalConsumedReviews:.2f}g, Average per Tea: {averageConsumedReviews:.2f}g")
                else:
                    dp.Text("Required Category role 'Amount' for Tea is not enabled.")
                dp.Separator()
                # Total standard adjustments, Total gift adjustments
                dp.Text("Standard Adjustments - (Standard)")
                totalStandardAdjustments = self.cache["totalConsumedStandardAdj"]
                averageStandardAdjustments = self.cache["averageConsumedStandardAdj"]
                dp.Text(f"Total: {totalStandardAdjustments:.2f}g, Average per tea: {averageStandardAdjustments:.2f}g")
                dp.Separator()
                # Total Gift Adjustments
                if "Amount" in AllTypesCategoryRoleValid:
                    dp.Text("Gift Adjustments - (Gift)")
                    totalGiftAdjustments = self.cache["totalConsumedByGiftedTeasSum"]
                    averageGiftAdjustments = self.cache["averageConsumedByGiftedTeas"]
                    dp.Text(f"Total: {totalGiftAdjustments:.2f}g, Average per tea: {averageGiftAdjustments:.2f}g")
                else:
                    dp.Text("Required Category role 'Amount' for Tea is not enabled.")
                dp.Separator()

                # Total finished specifically
                dp.Text("Finished Teas - (Finished)")
                totalFinishedTeas = self.cache["totalConsumedByFinishedTeasSum"]
                averageFinishedTeas = self.cache["averageConsumedByFinishedTeas"]
                dp.Text(f"Total: {totalFinishedTeas:.2f}g, Average per tea: {averageFinishedTeas:.2f}g")
                dp.Separator()

                # Total sale adjustments
                dp.Text("Sale Adjustments - (Sale)")
                totalSaleAdjustments = self.cache["totalConsumedBySaleAdjustmentsSum"]
                averageSaleAdjustments = self.cache["averageConsumedBySaleAdjustments"]
                dp.Text(f"Total Sales: {totalSaleAdjustments:.2f}g, Average Sale per tea: {averageSaleAdjustments:.2f}g")
                totalReturnedBySales = self.cache["totalReturnedBySales"]
                averageReturnedBySales = self.cache["averageReturnedBySales"]
                pricePerGram = 0
                if totalSaleAdjustments > 0:
                    pricePerGram = totalReturnedBySales / totalSaleAdjustments
                dp.Text(f"Total Returned by Sales: ${totalReturnedBySales:.2f}, Average $ per tea: ${averageReturnedBySales:.2f}")
                dp.Text(f"Price per gram: ${pricePerGram:.2f}")
                
                dp.Separator()
                # Total remaining by summing all remaining amounts after applying autocalculations
                dp.Text("Total Remaining")
                if "Remaining" in AllTypesCategoryRoleValid:
                    totalRemaining = self.cache["totalRemaining"]
                    averageRemaining = self.cache["averageRemaining"]
                    dp.Text(f"Total Remaining: {totalRemaining:.2f}g, Average Remaining per tea: {averageRemaining:.2f}g")
                else:
                    dp.Text("Required Category role 'Remaining' for Tea is not enabled.")
                dp.Separator()
            startDay = self.cache["startDay"]
            today = dt.datetime.now(tz=dt.timezone.utc).timestamp()
            numDays = (today - startDay) / (24 * 60 * 60)

        # Stash amounts
        with dp.CollapsingHeader(label="Stash Amounts", default_open=False):
            # Total volume of all teas in the stash
            dp.Text("Total Volume of All Teas in Stash")
            totalVolume = self.cache["totalVolume"]
            averageVolume = self.cache["averageVolume"]
            dp.Text(f"Total Volume: {totalVolume:.2f}g, Average Volume: {averageVolume:.2f}g")
            dp.Separator()
            # Total cost of all teas in the stash
            dp.Text("Total Cost of All Teas in Stash")
            totalCost = self.cache["totalCost"]
            averageCost = self.cache["averageCost"]
            dp.Text(f"Total Cost: ${totalCost:.2f}, Average Cost: ${averageCost:.2f}")
            weightedAverageCost = self.cache["weightedAverageCost"]
            dp.Text(f"Weighted Average Cost: ${weightedAverageCost:.2f}")
            dp.Separator()
        # Consumed amounts
        with dp.CollapsingHeader(label="Consumed Amounts", default_open=False):
        # Total consumed by summing all reviews, adjustments, and finished teas
            # Total volume of consumed tea (Review-remaining-stats)
            dp.Text("Tea Consumed")
            days = self.cache["totalDays"]
            totalPurchased = self.cache["totalVolume"]
            if "Amount" in allTypesCategoryRoleReviewsValid:
                totalConsumedByPersonal = self.cache["totalConsumedByPersonalSum"]
                averagePerDay = totalConsumedByPersonal / days if days > 0 else 0
                dp.Text(f"Total personally consumed: {totalConsumedByPersonal:.2f}g")
                dp.Text(f"Average personally consumed per day: {averagePerDay:.2f}g/day")
                # Years remaining
                if totalPurchased > 0:
                    yearsRemaining = totalRemaining / (averagePerDay * 365) if averagePerDay > 0 else float('inf')
                    dp.Text(f"Years remaining based on current consumption: {yearsRemaining:.2f} years")
                dp.Separator()
            else:
                dp.Text("Required Category role 'Amount' for Review is not enabled.")
            dp.Separator()
            dp.Text("Tea Consumed by all Methods")
            if "Amount" in AllTypesCategoryRoleValid:
                averageConsumed = self.cache["averageConsumed"]
                dp.Text(f"Total consumed (all sources): {totalConsumed:.2f}g")
                averagePerDay = totalConsumed / days if days > 0 else 0
                dp.Text(f"Average consumed per day (all sources): {averagePerDay:.2f}g/day")
                # Years remaining based on all consumption
                if totalPurchased > 0:
                    yearsRemainingAll = totalRemaining / (averageConsumed * 365) if averageConsumed > 0 else float('inf')
                    dp.Text(f"Years remaining based on all consumption: {yearsRemainingAll:.2f} years")
            else:
                dp.Text("Required Category role 'Amount' for Tea is not enabled.")
            dp.Separator()
            


    # Steeps and water consumption stats
    def window_subwindow_1_1_categories(self, sender=None, app_data=None, user_data=None):
        allTypesCategoryRoleValid = user_data[0] if user_data and len(user_data) > 0 else []
        allTypesCategoryRoleReviewsValid = user_data[1] if user_data and len(user_data) > 1 else []
        dp.Text("Steeps and Water Consumption Stats")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        dp.Separator()
        # Steeps and water consumption
        with dp.CollapsingHeader(label="Steeps and Water Consumption", default_open=True):
            with dp.CollapsingHeader(label="Steeps", default_open=False, indent=20 * settings["UI_SCALE"]):
                # Total steeps (Review-steep-count-stats)
                dp.Text("Total Steeps")
                if "Steeps" in allTypesCategoryRoleReviewsValid:
                    sum, avrg, count, unique, _ = getStatsOnCategoryByRole("Steeps", True)
                    dp.Text(f"Sum: {sum} steeps, Average: {avrg} steeps, Count: {count}")
                else:
                    dp.Text("Required Category role 'Steeps' for Review is not enabled.")
                dp.Separator()
            # Total water consumed by summing all reviews (Review-Vessel Size-stats)
            with dp.CollapsingHeader(label="Water Consumption", default_open=False, indent=20 * settings["UI_SCALE"]):
                if "Vessel size" in allTypesCategoryRoleReviewsValid and "Steeps" in allTypesCategoryRoleReviewsValid:
                    totalWaterConsumed, averageWaterConsumed = statsWaterConsumed()
                    dp.Text(f"Total Water Consumed: {totalWaterConsumed:.2f}ml")
                    dp.Text(f"Average Water Consumed per steep: {averageWaterConsumed:.2f}ml")
                    dp.Separator()
                    liters = totalWaterConsumed / 1000
                    gallons = liters / 3.78541
                    dp.Text(f"{liters:.2f}L ({gallons:.2f} gallons) over {self.cache['totalDays']:.2f} days")
                    dp.Text(f"That's approximately {liters / self.cache['totalDays']:.2f}L per day")
                else:
                    dp.Text("Required Category role 'Vessel size' and 'Steeps' for Review is not enabled.")

            # Average Steeps per Tea type
            with dp.CollapsingHeader(label="Average Steeps per Tea Type", default_open=False, indent=20 * settings["UI_SCALE"]):
                steepsByType = self.cache["steepsByType"]
                numReviewsByType = self.cache["numReviewsByType"]
                for teaType, steeps in steepsByType.items():
                    numReviews = numReviewsByType.get(teaType, 0)
                    if numReviews > 0:
                        averageSteeps = steeps / numReviews
                        with dp.Group(horizontal=True):
                            dp.Text(f"{teaType}: {averageSteeps:.2f} steeps average")
                            dpg.bind_item_font(dpg.last_item(), getFontName(2))
                            dp.Text(f" ({steeps} steeps, {numReviews} reviews)", color=COLOR_LIGHT_BLUE_TEXT)
                    else:
                        dp.Text(f"{teaType}: No reviews found", color=COLOR_RED_TEXT)
                dp.Separator()
            
            with dp.CollapsingHeader(label="Teaware Size", default_open=False, indent=20 * settings["UI_SCALE"]):
                if "Vessel size" in allTypesCategoryRoleReviewsValid:
                    sum, avrg, count, unique, uniqueDict = getStatsOnCategoryByRole("Vessel size", True)
                    dp.Text(f"Sum: {sum}ml, Average: {avrg}ml, Count: {count}")
                    dp.Text("Unique Sizes by Review:")
                    for size, count in uniqueDict.items():
                        dp.Text(f"{size}: {count}")
                else:
                    dp.Text("Required Category role 'Vessel size' for Review is not enabled.")
                dp.Separator()


    # Ratings and Grades
    def window_subwindow_1_2_categories(self, sender=None, app_data=None, user_data=None):
        dp.Text("Ratings and Grades Stats")
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        dp.Separator()
        # Ratings and Grades
        with dp.CollapsingHeader(label="Ratings and Grades", default_open=True):
            with dp.CollapsingHeader(label="Ratings and Grades", default_open=False, indent=20 * settings["UI_SCALE"]):
                # Teas tried total
                dp.Text("Teas Tried Total")
                teasTriedPerType = self.cache["teasTriedByType"]
                teasNotTriedPerType = self.cache["teasNotTriedByType"]
                teasFinishedPerType = self.cache["teasFinishedByType"]
                totalFinished = self.cache["totalTeasFinished"]
                numTeasTried = self.cache["totalTeasTried"]
                totalTeas = self.cache["numTeas"]
                dp.Text(f"Number of Teas Tried: {numTeasTried} out of {totalTeas} total teas, {numTeasTried / totalTeas * 100:.2f}%")
                dp.Text(f"Number of Teas Finished: {totalFinished} out of {totalTeas} total teas, {totalFinished / totalTeas * 100:.2f}%")
            # Teas tried per type
            with dp.CollapsingHeader(label="Teas Tried per Type", default_open=False, indent=20 * settings["UI_SCALE"]):
                # iterate both dictionaries
                dp.Text(f"Number of types: {len(teasTriedPerType)}")
                for teaType, count in teasTriedPerType.items():
                    numNotTried = teasNotTriedPerType.get(teaType, 0)
                    numTried = teasTriedPerType.get(teaType, 0)
                    numTotal = numTried + numNotTried
                    rightpartstr = f"{count}/{numTotal},  {(count / numTotal) * 100:.2f}%"
                    numFinished = teasFinishedPerType.get(teaType, 0)
                    teaType = teaType.ljust(25)
                    if len(teaType) > 25:
                        teaType = teaType[:22] + "..."
                    
                    if count > 0:
                        with dp.Group(horizontal=True):
                            dp.Text(f"{teaType}")
                            dpg.bind_item_font(dpg.last_item(), getFontName(2))
                            dp.Text(f"{rightpartstr}", color=COLOR_GREEN_TEXT)
                            if numNotTried > 0:
                                dp.Text(f"({numNotTried} not tried)", color=COLOR_RED_TEXT)
                            if numFinished > 0:
                                dp.Text(f"({numFinished} finished)", color=COLOR_LIGHT_BLUE_TEXT)
                dp.Separator()
    


        
    def windowDefintion(self, window):
        self.win = window
        window = self.win
        with window:
            # Divider
            dp.Separator()
            # Tea Stats
            dp.Text("Tea Stats")
            numTeas = statsNumTeas()
            numReviews = statsNumReviews()
            dp.Text(f"Teas: {numTeas}, Reviews: {numReviews}")
            dp.Separator()

            # Refresh button
            with dp.Group(horizontal=True):
                dp.Button(label="Refresh", callback=self.softRefresh, width=100 * settings["UI_SCALE"], height=32 * settings["UI_SCALE"], user_data=self)
                # Show a refreshing emote icon
                self.refreshIcon = dpg.add_image("refresh_icon", width=32 * settings["UI_SCALE"], height=32 * settings["UI_SCALE"])
            dp.Separator()

            timeLoadStart = dt.datetime.now(tz=dt.timezone.utc).timestamp()

            # All stats should only be displayed if the coorsponding category is enabled
            AllTypesCategoryRoleValid, AllTypesCategoryRole = getValidCategoryRolesList()
            allTypesCategoryRoleReviewsValid, allTypesCategoryRoleReviews = getValidReviewCategoryRolesList()

            # Init cache so we dont have to recalculate every time
            if self.cache is None:
                # Check global cache
                global TeaCache
                lenGlobalCache = len(TeaCache)
                
                if TeaCache is not None and lenGlobalCache > 0:
                    self.cache = TeaCache
                else:
                    self.cache = populateStatsCache()
                    # Populate global cache
                    TeaCache = self.cache
                    RichPrintSuccessMinor("Stats cache populated.")

            windowWidth = window.width
            windowHeight = window.height
            childWidth = (windowWidth - 20 * settings["UI_SCALE"]) / 3
            childHeight = (windowHeight - 20 * settings["UI_SCALE"]) / 2

            for row in range(2):
                with dpg.group(horizontal=True):
                    for col in range(3):
                        with dpg.child_window(width=childWidth, height=childHeight, border=True):
                            
                            if row == 0 and col == 0:
                                self.window_subwindow_0_0_categories(user_data=[AllTypesCategoryRole, AllTypesCategoryRoleValid, allTypesCategoryRoleReviews, allTypesCategoryRoleReviewsValid])
                            elif row == 0 and col == 1:
                                self.window_subwindow_0_1_categories(user_data=[AllTypesCategoryRoleValid, allTypesCategoryRoleReviewsValid])
                            elif row == 0 and col == 2:
                                self.window_subwindow_0_2_categories()
                            elif row == 1 and col == 0:
                                self.window_subwindow_1_0_categories(user_data=[AllTypesCategoryRoleValid, allTypesCategoryRoleReviewsValid])
                            elif row == 1 and col == 1:
                                self.window_subwindow_1_1_categories(user_data=[AllTypesCategoryRoleValid, allTypesCategoryRoleReviewsValid])
                            elif row == 1 and col == 2:
                                self.window_subwindow_1_2_categories(user_data=[allTypesCategoryRoleReviewsValid])
                            else:
                                dpg.add_text(f"Placeholder {row * 3 + col + 1}")
            dp.Separator()


            

            

            

            
        # End refreshing
        self.refreshing = False
        timeLoadEnd = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        RichPrintSuccess(f"Stats window loaded in {timeLoadEnd - timeLoadStart:.2f} seconds.")
        self.afterWindowDefinition()
        



        
def Menu_EditCategories():
    w = 800 * settings["UI_SCALE"]
    h = 600 * settings["UI_SCALE"]
    editCategories = Window_EditCategories("Edit Categories", w, h, exclusive=True)

class Window_EditCategories(WindowBase):
    teaCategoryGroup = None
    teaReviewGroup = None
    reviewCategories = []
    hideUsedCategoriesBool = True
    editCatWindow = None
    def windowDefintion(self, window):
        dpg.bind_item_font(window.tag, getFontName(1))
        with window:
            # vertical half half split, one for tea, one for review
            with dp.Group(horizontal=True):
                # Tea Categories
                scaledWidth = 400 * settings["UI_SCALE"]

                with dp.Group(horizontal=False):
                    dp.Text("Tea Categories")
                    dpg.bind_item_font(dpg.last_item(), getFontName(3))
                    dp.Button(label="Add Stash Category", callback=self.showAddCategory)
                    dpg.bind_item_font(dpg.last_item(), getFontName(2))
                    scaledHeight = 480 * settings["UI_SCALE"]
                    with dpg.child_window(label="Tea Categories", width=scaledWidth, height=scaledHeight):
                        self.teaCategoryGroup = dp.Group(horizontal=False)
                        dp.Separator()
                        self.generateTeaCategoriesList(self.teaCategoryGroup)

                # Vertical split for review
                # Review
                with dp.Group(horizontal=False):
                    dp.Text("Review Categories")
                    dpg.bind_item_font(dpg.last_item(), getFontName(3))
                    dp.Button(label="Add Review Category", callback=self.showAddReviewCategory)
                    dpg.bind_item_font(dpg.last_item(), getFontName(2))
                    scaledHeight = 480 * settings["UI_SCALE"]
                    with dpg.child_window(label="Review Categories", width=scaledWidth, height=scaledHeight):
                        dp.Separator()
                        self.teaReviewGroup = dp.Group(horizontal=False)
                        self.generateReviewCategoriesList()
    
    def hideUsedCategories(self, sender, app_data, user_data):
        # switch variable and refresh the window
        self.hideUsedCategoriesBool = app_data
        win = user_data[1]
        print(f"Hide used categories: {self.hideUsedCategoriesBool}")
        if user_data[0] == "EDIT_CATEGORY":
            print("Edit Category")
        elif user_data[0] == "ADD_CATEGORY":
            print("Add Category")
        elif user_data[0] == "EDIT_REVIEW_CATEGORY":
            print("Edit Review Category")
        elif user_data[0] == "ADD_REVIEW_CATEGORY":
            print("Add Review Category")
        win.delete()


    def generateTeaCategoriesList(self, window):
        with self.teaCategoryGroup:
            for i, category in enumerate(TeaCategories):
                with dp.Group(horizontal=True):
                    scaledWidth = 320 * settings["UI_SCALE"]
                    scaledHeight = 150 * settings["UI_SCALE"]
                    with dp.ChildWindow(width=scaledWidth, height=scaledHeight):
                        dp.Text(f"{i+1}: {category.name} -- ({category.categoryRole})")
                        dpg.bind_item_font(dpg.last_item(), getFontName(2))
                        dp.Separator()
                        dp.Text(f"Default Value: {category.defaultValue}")
                        dp.Text(f"Category Type: {category.categoryType}")
                        dp.Text(f"Dropdown?: {category.isDropdown}, Autocalculated?: {category.isAutoCalculated}")
                        suffix = category.suffix if category.suffix is not None and category.suffix != "" else "<None>"
                        prefix = category.prefix if category.prefix is not None and category.prefix != "" else "<None>"
                        dp.Text(f"Prefix: {prefix}, Suffix: {suffix}")
                        dp.Text(f"Rounding Amount: {category.rounding}, dropdown items: {category.dropdownMaxLength}")

                    scaledWidth = 75 * settings["UI_SCALE"]
                    with dp.ChildWindow(width=scaledWidth, height=scaledHeight):
                        if i != 0:
                            dp.Button(label="Up", callback=self.moveItemUpCategory, user_data=i)
                        else:
                            dp.Text("[---]")
                        if i != len(TeaCategories) - 1:
                            dp.Button(label="Down", callback=self.moveItemDownCategory, user_data=i)
                        else:
                            dp.Text("[---]")

                        with dp.Group(horizontal=False):
                            dp.Button(label="Edit", callback=self.showEditCategory, user_data=i)
                            dp.Button(label="Delete", callback=self.deleteCategory, user_data=i)
            dp.Separator()

    def generateReviewCategoriesList(self):
        with self.teaReviewGroup:
            for i, category in enumerate(TeaReviewCategories):
                with dp.Group(horizontal=True):
                    scaledWidth = 250 * settings["UI_SCALE"]
                    scaledHeight = 150 * settings["UI_SCALE"]
                    with dp.ChildWindow(width=scaledWidth, height=scaledHeight):
                        dp.Text(f"{i+1}: {category.name} -- ({category.categoryRole})")
                        dpg.bind_item_font(dpg.last_item(), getFontName(2))
                        dp.Separator()
                        dp.Text(f"Default Value: {category.defaultValue}")
                        dp.Text(f"Category Type: {category.categoryType}")
                        dp.Text(f"Dropdown?: {category.isDropdown}, Autocalculated?: {category.isAutoCalculated}")
                        suffix = category.suffix if category.suffix is not None and category.suffix != "" else "<None>"
                        prefix = category.prefix if category.prefix is not None and category.prefix != "" else "<None>"
                        dp.Text(f"Prefix: {prefix}, Suffix: {suffix}")
                        dp.Text(f"Rounding Amount: {category.rounding}, dropdown items: {category.dropdownMaxLength}")

                    scaledWidth = 75 * settings["UI_SCALE"]
                    with dp.ChildWindow(width=scaledWidth, height=scaledHeight):
                        if i != 0:
                            dp.Button(label="Up", callback=self.moveItemUpReviewCategory, user_data=i)
                        else:
                            dp.Text("[---]")
                        if i != len(TeaReviewCategories) - 1:
                            dp.Button(label="Down", callback=self.moveItemDownReviewCategory, user_data=i)
                        else:
                            dp.Text("[---]")

                        with dp.Group(horizontal=False):
                            dp.Button(label="Edit", callback=self.showEditReviewCategory, user_data=i)
                            dp.Button(label="Delete", callback=self.deleteReviewCategory, user_data=i)
            dp.Separator()



    def moveItemUpCategory(self, sender, app_data, user_data):
        TeaCategories[user_data], TeaCategories[user_data - 1] = TeaCategories[user_data - 1], TeaCategories[user_data]
        # Refresh the window
        self.softRefresh()
        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
    def moveItemDownCategory(self, sender, app_data, user_data):
        TeaCategories[user_data], TeaCategories[user_data + 1] = TeaCategories[user_data + 1], TeaCategories[user_data]
        # Refresh the window
        self.softRefresh()
        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])

    def moveItemUpReviewCategory(self, sender, app_data, user_data):
        TeaReviewCategories[user_data], TeaReviewCategories[user_data - 1] = TeaReviewCategories[user_data - 1], TeaReviewCategories[user_data]
        # Refresh the window
        self.softRefresh()
        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
    def moveItemDownReviewCategory(self, sender, app_data, user_data):
        TeaReviewCategories[user_data], TeaReviewCategories[user_data + 1] = TeaReviewCategories[user_data + 1], TeaReviewCategories[user_data]
        # Refresh the window
        self.softRefresh()
        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])

    def showAddCategory(self, sender, app_data, user_data):
        # Create a popup window to add a new the category
        w = 500 * settings["UI_SCALE"]
        h = 500 * settings["UI_SCALE"]
        addCategoryWindow = dp.Window(label="Add Category", width=w, height=h, modal=True, show=True)
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        windowManager.addSubWindow(addCategoryWindow)
        addCategoryWindowItems = dict()

        with addCategoryWindow:
            dp.Text("Add Category")
            dpg.bind_item_font(dpg.last_item(), getFontName(3))
            dp.Separator()
            category: TeaCategory
            # Declare category name, width, type
            dp.Text("Category Name")
            nameItem = dp.InputText(default_value="")
            dp.Separator()
            addCategoryWindowItems["Name"] = nameItem

            dp.Text("Default Value")
            defaultValueItem = dp.InputText(default_value="")
            addCategoryWindowItems["DefaultValue"] = defaultValueItem
            dp.Separator()
            
            validTypes = session["validTypesCategory"]
            with dp.Group(horizontal=True):
                dp.Text("Category Type")

                dp.Button(label="?")

                with dpg.tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextCategory["CategoryType"].wrap()
                    dp.Text(toolTipText)

            catItem = dp.Listbox(items=validTypes, default_value="string", num_items=5, callback=self.updateTypeDuringEdit)
            addCategoryWindowItems["Type"] = catItem
            dp.Separator()


            # Category role dropdown
            with dp.Group(horizontal=True):
                dp.Text("Category Role")

                # Explanation tooltip
                dp.Separator()
                dp.Button(label="?")

                with dpg.tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextCategory["CategoryRole"].wrap()
                    dp.Text(toolTipText)

            # Add hide used categories option
            with dp.Group(horizontal=True):
                dp.Text("Hide Used Categories")

                hideUsedItem = dp.Checkbox(default_value=self.hideUsedCategoriesBool, callback=self.hideUsedCategories, user_data=("ADD_CATEGORY", addCategoryWindow))
            typeCategory = f"{catItem.get_value()}"
            items = session["validroleCategory"][typeCategory]
            alreadyUsedItems = []
            for cat in TeaCategories:
                if cat.categoryType == typeCategory:
                    alreadyUsedItems.append(cat.categoryRole)
            if self.hideUsedCategoriesBool:
                items = [item for item in items if item not in alreadyUsedItems]

            roleItem = dp.Listbox(items=items, default_value="UNUSED", num_items=5)
            addCategoryWindowItems["role"] = roleItem
            dp.Separator()

            # Additional flags: isRequired, isrequiredForAll, isAutoCalculated, isDropdown
            dp.Text("Additional Flags")
            isRequiredItem = dp.Checkbox(label="Is Required (inc Teaware, fees)", default_value=False)
            addCategoryWindowItems["isRequiredForAll"] = isRequiredItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isRequiredForAll"].wrap()
                dp.Text(toolTipTxt)

            isRequiredForTeaItem = dp.Checkbox(label="Is Required for Tea only", default_value=False)
            addCategoryWindowItems["isRequiredForTea"] = isRequiredForTeaItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isRequiredForTea"].wrap()
                dp.Text(toolTipTxt)

            isDropdownItem = dp.Checkbox(label="Is Dropdown", default_value=False)
            addCategoryWindowItems["isDropdown"] = isDropdownItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isDropdown"].wrap()
                dp.Text(toolTipTxt)

            isAutoCalculatedItem = dp.Checkbox(label="Is Autocalculated", default_value=False)
            addCategoryWindowItems["isAutoCalculated"] = isAutoCalculatedItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isAutoCalculated"].wrap()
                dp.Text(toolTipTxt)

            

            dp.Separator()

            # Prefix, rounding, etc
            dp.Text("Additional Options")
            dp.Text("Rounding")
            roundingAmtSliderInt = dp.SliderInt(default_value=2, min_value=0, max_value=5, format="%d")
            addCategoryWindowItems["rounding"] = roundingAmtSliderInt
            dp.Text("Prefix")
            prefixItem = dp.InputText(default_value="")
            addCategoryWindowItems["prefix"] = prefixItem
            dp.Text("Suffix")
            suffixItem = dp.InputText(default_value="")
            addCategoryWindowItems["suffix"] = suffixItem
            dp.Text("Dropdown - Max Items")
            maxItemsItem = dp.SliderInt(default_value=5, min_value=3, max_value=30, format="%d")
            addCategoryWindowItems["maxItems"] = maxItemsItem

            gradingAsLetterItem = dp.Checkbox(label="Grading as Letter", default_value=False)
            addCategoryWindowItems["gradingAsLetter"] = gradingAsLetterItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["gradingAsLetter"].wrap()
                dp.Text(toolTipTxt)


                
            
            dp.Separator()

            addCategoryWindowItems["Type"].user_data = (addCategoryWindowItems["Type"], roleItem)
                    

            dp.Button(label="Add", callback=self.AddCategory, user_data=(addCategoryWindowItems, addCategoryWindow))
            dp.Button(label="Cancel", callback=addCategoryWindow.delete)
            # Help question mark
            dp.Button(label="?")
            # Hover tooltip
            with dpg.tooltip(dpg.last_item()):
                dp.Text("Add a new category to the stash")

    def showAddReviewCategory(self, sender, app_data, user_data):
        # Create a popup window to add a new the review category
        w = 500 * settings["UI_SCALE"]
        h = 500 * settings["UI_SCALE"]
        # Create a new window
        addReviewCategoryWindow = dp.Window(label="Add Review Category", width=w, height=h, modal=True, show=True)
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        windowManager.addSubWindow(addReviewCategoryWindow)
        addReviewCategoryWindowItems = dict()

        with addReviewCategoryWindow:
            dp.Text("Add Review Category")
            dp.Separator()
            category: ReviewCategory
            # Declare category name, width, type
            dp.Text("Category Name")
            nameItem = dp.InputText(default_value="")
            addReviewCategoryWindowItems["Name"] = nameItem
            dp.Separator()
            
            dp.Text("Default Value")
            defaultValueItem = dp.InputText(default_value="")
            addReviewCategoryWindowItems["DefaultValue"] = defaultValueItem
            dp.Separator()

            
            validTypes = session["validTypesReviewCategory"]
            with dp.Group(horizontal=True):
                dp.Text("Category Type")
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextCategory["CategoryType"].wrap()
                    dp.Text(toolTipText)

            catItem = dp.Listbox(items=validTypes, default_value="string", num_items=5, callback=self.updateTypeDuringEditReview)
            addReviewCategoryWindowItems["Type"] = catItem
            dp.Separator()

            # Category role dropdown
            with dp.Group(horizontal=True):
                dp.Text("Category Role")
                # Explanation tooltip
                dp.Separator()
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextCategory["CategoryRole"].wrap()
                    dp.Text(toolTipText)

            # Add hide used categories option
            with dp.Group(horizontal=True):
                dp.Text("Hide Used Categories")
                hideUsedItem = dp.Checkbox(default_value=self.hideUsedCategoriesBool, callback=self.hideUsedCategories, user_data=("ADD_REVIEW_CATEGORY", addReviewCategoryWindow))


            typeCategory = f"{catItem.get_value()}"
            items = session["validroleReviewCategory"][typeCategory]
            alreadyUsedItems = []
            for cat in TeaReviewCategories:
                if cat.categoryType == typeCategory:
                    alreadyUsedItems.append(cat.categoryRole)
            if self.hideUsedCategoriesBool:
                items = [item for item in items if item not in alreadyUsedItems]
            roleItem = dp.Listbox(items=items, default_value="UNUSED", num_items=5)
            addReviewCategoryWindowItems["role"] = roleItem

            # Additional flags: isRequired, isrequiredForAll, isAutoCalculated, isDropdown
            dp.Separator()
            dp.Text("Additional Flags")
            dp.Separator()
            isRequiredItem = dp.Checkbox(label="Is Required (inc Teaware, fees)", default_value=False)
            addReviewCategoryWindowItems["isRequiredForAll"] = isRequiredItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isRequiredForAll"].wrap()
                dp.Text(toolTipTxt)

            isRequiredForTeaItem = dp.Checkbox(label="Is Required for Tea only", default_value=False)
            addReviewCategoryWindowItems["isRequiredForTea"] = isRequiredForTeaItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isRequiredForTea"].wrap()
                dp.Text(toolTipTxt)

            isDropdownItem = dp.Checkbox(label="Is Dropdown", default_value=False)
            addReviewCategoryWindowItems["isDropdown"] = isDropdownItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isDropdown"].wrap()
                dp.Text(toolTipTxt)

            isAutoCalculatedItem = dp.Checkbox(label="Is Autocalculated", default_value=False)
            addReviewCategoryWindowItems["isAutoCalculated"] = isAutoCalculatedItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isAutoCalculated"].wrap()
                dp.Text(toolTipTxt)
                
            dp.Separator()

            # Prefix, rounding, etc
            dp.Text("Additional Options")
            dp.Separator()
            dp.Text("Rounding")
            roundingAmtSliderInt = dp.SliderInt(default_value=2, min_value=0, max_value=5, format="%d")
            addReviewCategoryWindowItems["rounding"] = roundingAmtSliderInt
            dp.Text("Prefix")
            prefixItem = dp.InputText(default_value="")
            addReviewCategoryWindowItems["prefix"] = prefixItem
            dp.Text("Suffix")
            suffixItem = dp.InputText(default_value="")
            addReviewCategoryWindowItems["suffix"] = suffixItem
            dp.Text("Dropdown - Max Items")
            maxItemsItem = dp.SliderInt(default_value=5, min_value=3, max_value=30, format="%d")
            addReviewCategoryWindowItems["maxItems"] = maxItemsItem

            # Grading as letter
            gradingAsLetterItem = dp.Checkbox(label="Grading as Letter", default_value=False)
            addReviewCategoryWindowItems["gradingAsLetter"] = gradingAsLetterItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["gradingAsLetter"].wrap()
                dp.Text(toolTipTxt)
            
            dp.Separator()


            addReviewCategoryWindowItems["Type"].user_data = (addReviewCategoryWindowItems["Type"], roleItem)
                    

            dp.Button(label="Add", callback=self.AddReviewCategory, user_data=(addReviewCategoryWindowItems, addReviewCategoryWindow))
            dp.Button(label="Cancel", callback=addReviewCategoryWindow.delete)
            # Help question mark
            dp.Button(label="?")
            # Hover tooltip
            with dpg.tooltip(dpg.last_item()):
                dp.Text("Add a new review category to the stash")

    def AddReviewCategory(self, sender, app_data, user_data):
        allObjects = user_data[0]
        allAttributes = dict()
        for item in allObjects:
            allAttributes[item] = allObjects[item].get_value()

        # Check if the category already exists
        if allAttributes["Name"] in [cat.name for cat in TeaReviewCategories]:
            RichPrintWarning(f"Category {allAttributes['Name']} already exists")
            return
        # Check if the category type is valid
        if allAttributes["Type"] not in session["validTypesReviewCategory"]:
            RichPrintWarning(f"Category type {allAttributes['Type']} is not valid, defaulting to string")
            allAttributes["Type"] = "string"

        # Create a new category
        name = allAttributes["Name"]
        if name == None or name == "":
            RichPrintWarning("Category name is empty")
            name = allAttributes["role"]

        
        newCategory = ReviewCategory(name, allAttributes["Type"])
        defaultValue = allAttributes["DefaultValue"]
        if defaultValue != None and defaultValue != "":
            newCategory.defaultValue = defaultValue

        # Add role
        newCategory.categoryRole = allAttributes["role"]
        if newCategory.categoryRole not in session["validroleReviewCategory"][newCategory.categoryType]:
            newCategory.categoryRole = "UNUSED"

        ## Add flags
        newCategory.isRequiredForAll = allAttributes["isRequiredForAll"]
        newCategory.isRequiredForTea = allAttributes["isRequiredForTea"]
        newCategory.isDropdown = allAttributes["isDropdown"]
        newCategory.isAutoCalculated = allAttributes["isAutoCalculated"]

        # Add additional options
        newCategory.rounding = int(allAttributes["rounding"])
        newCategory.prefix = allAttributes["prefix"]
        newCategory.suffix = allAttributes["suffix"]
        newCategory.dropdownMaxLength = int(allAttributes["maxItems"])
        newCategory.gradingDisplayAsLetter = allAttributes["gradingAsLetter"]

        
        TeaReviewCategories.append(newCategory)

        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
        
        # close the popup
        self.softRefresh()
        dpg.delete_item(user_data[1])

    def showEditCategory(self, sender, app_data, user_data):
        # Create a popup window to edit the category
        w = 500 * settings["UI_SCALE"]
        h = 500 * settings["UI_SCALE"]
        # Create a new window
        editCategoryWindow = dp.Window(label="Edit Category", width=w, height=h, modal=True, show=True)
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        self.editCatWindow = editCategoryWindow
        editCategoryWindowItems = dict()
        category = TeaCategories[user_data]
        category: TeaCategory

        with editCategoryWindow:
            dp.Text("Edit Category")
            dpg.bind_item_font(dpg.last_item(), getFontName(3))
            dp.Text(f"{category.name}")
            dp.Separator()
            
            dp.Text(f"Default Value")
            editCategoryWindowItems["DefaultValue"] = dp.InputText(default_value=category.defaultValue)
            dp.Separator()

            validTypes = session["validTypesCategory"]
            with dp.Group(horizontal=True):
                dp.Text("Category Type")
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextCategory["CategoryType"].wrap()
                    dp.Text(toolTipText)

            catItem = dp.Listbox(items=validTypes, default_value=category.categoryType, callback=self.updateTypeDuringEdit, num_items=5)
            if category.categoryType not in validTypes:
                catItem.set_value("ERR: Assume String")

            editCategoryWindowItems["Type"] = catItem

            # Dropdown for category role
            with dp.Group(horizontal=True):
                dp.Text("Category Role")
                dp.Text(f"")
                # Explanation tooltip
                dp.Separator()
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextCategory["CategoryRole"].wrap()
                    dp.Text(toolTipText)

            # Add hide used categories option
            with dp.Group(horizontal=True):
                dp.Text("Hide Used Categories")
                hideUsedItem = dp.Checkbox(default_value=self.hideUsedCategoriesBool, callback=self.hideUsedCategories, user_data=("EDIT_CATEGORY", editCategoryWindow))

            typeCategory = f"{category.categoryType}"
            items = session["validroleCategory"][typeCategory]
            alreadyUsedItems = []
            for cat in TeaCategories:
                if cat.categoryType == typeCategory and cat.categoryRole != category.categoryRole:
                    alreadyUsedItems.append(cat.categoryRole)
            if self.hideUsedCategoriesBool:
                items = [item for item in items if item not in alreadyUsedItems]
            if category.categoryRole not in items:
                items.append(category.categoryRole)

            roleItem = dp.Listbox(items=items, default_value=category.categoryRole, num_items=5)
            if category.categoryRole not in items:
                roleItem.set_value("ERR: Assume Unused")
            
            editCategoryWindowItems["role"] = roleItem

            # Additional flags: isRequired, isrequiredForAll, isAutoCalculated, isDropdown
            dp.Separator()
            dp.Text("Additional Flags")
            isRequiredItem = dp.Checkbox(label="Is Required (inc Teaware, fees)", default_value=category.isRequiredForAll)
            editCategoryWindowItems["isRequiredForAll"] = isRequiredItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isRequiredForAll"].wrap()
                dp.Text(toolTipTxt)

            isRequiredForTeaItem = dp.Checkbox(label="Is Required for Tea only", default_value=category.isRequiredForTea)
            editCategoryWindowItems["isRequiredForTea"] = isRequiredForTeaItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isRequiredForTea"].wrap()
                dp.Text(toolTipTxt)

            isDropdownItem = dp.Checkbox(label="Is Dropdown", default_value=category.isDropdown)
            editCategoryWindowItems["isDropdown"] = isDropdownItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isDropdown"].wrap()
                dp.Text(toolTipTxt)

            isAutoCalculatedItem = dp.Checkbox(label="Is Autocalculated", default_value=category.isAutoCalculated)
            editCategoryWindowItems["isAutoCalculated"] = isAutoCalculatedItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isAutoCalculated"].wrap()
                dp.Text(toolTipTxt)

            dp.Separator()

            # Prefix, rounding, etc
            dp.Text("Additional Options")
            dp.Text("Rounding")
            roundingAmtSliderInt = dp.SliderInt(label="Rounding Amount", default_value=int(category.rounding), min_value=0, max_value=5, format="%d")
            roundingAmtSliderInt.set_value(int(category.rounding))
            editCategoryWindowItems["rounding"] = roundingAmtSliderInt
            dp.Text("Prefix")
            prefixItem = dp.InputText(label="Prefix", default_value=category.prefix)
            editCategoryWindowItems["prefix"] = prefixItem
            dp.Text("Suffix")
            suffixItem = dp.InputText(label="Suffix", default_value=category.suffix)
            editCategoryWindowItems["suffix"] = suffixItem
            dp.Text("Dropdown - Max Items")
            maxItemsItem = dp.SliderInt(label="Max Items", default_value=int(category.dropdownMaxLength), min_value=3, max_value=30, format="%d")
            editCategoryWindowItems["maxItems"] = maxItemsItem
            # Grading as letter
            dp.Text("Grading as Letter")
            gradingAsLetterItem = dp.Checkbox(label="Grading as Letter", default_value=category.gradingDisplayAsLetter)
            editCategoryWindowItems["gradingAsLetter"] = gradingAsLetterItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["gradingAsLetter"].wrap()
                dp.Text(toolTipTxt)


            dp.Separator()

            editCategoryWindowItems["Type"].user_data = (editCategoryWindowItems["Type"], roleItem)
            
            

            with dp.Group(horizontal=True):
                dp.Button(label="Save", callback=self.EditCategory, user_data=(category, editCategoryWindowItems, editCategoryWindow))
                dp.Button(label="Cancel", callback=editCategoryWindow.delete)
                # Help question mark
                dp.Button(label="?")
                # Hover tooltip
                with dpg.tooltip(dpg.last_item()):
                    dp.Text("Edit the category name, type, and width in pixels")
        print("Edit Category")

    def updateTypeDuringEdit(self, sender, app_data, user_data):
        # We need to update type during edit to show correct role
        RichPrintInfo(F"[INFO] Updated Type: {user_data[0].get_value()}")
        valueToSet = user_data[0].get_value()
        roleItem = user_data[1]
        validTypes = session["validroleCategory"][valueToSet]
        # Account for already used categories
        alreadyUsedItems = []
        if self.hideUsedCategoriesBool:
            for cat in TeaCategories:
                if cat.categoryType == valueToSet and cat.categoryRole != roleItem.get_value():
                    alreadyUsedItems.append(cat.categoryRole)
            print(f"Already used items: {alreadyUsedItems}")
            validTypes = [item for item in validTypes if item not in alreadyUsedItems]
            # Add in the current category role if it is not already in the list
            if roleItem.get_value() not in validTypes:
                validTypes.append(roleItem.get_value())
        dpg.configure_item(roleItem.tag, items=validTypes)
        roleItem.set_value(validTypes[0])

    def updateTypeDuringEditReview(self, sender, app_data, user_data):
        # We need to update type during edit to show correct role
        RichPrintInfo(F"[INFO] Updated Type: {user_data[0].get_value()}")
        valueToSet = user_data[0].get_value()
        roleItem = user_data[1]
        validTypes = session["validroleReviewCategory"][valueToSet]
        # Account for already used categories
        alreadyUsedItems = []
        if self.hideUsedCategoriesBool:
            for cat in TeaReviewCategories:
                if cat.categoryType == valueToSet and cat.categoryRole != roleItem.get_value():
                    alreadyUsedItems.append(cat.categoryRole)
            validTypes = [item for item in validTypes if item not in alreadyUsedItems]
            # Add in the current category role if it is not already in the list
            if roleItem.get_value() not in validTypes:
                validTypes.append(roleItem.get_value())
        dpg.configure_item(roleItem.tag, items=validTypes)
        roleItem.set_value(validTypes[0])

    def EditCategory(self, sender, app_data, user_data):
        category = user_data[0]
        allAttributes = user_data[1]
        category.categoryType = allAttributes["Type"].get_value()
        if category.categoryType not in session["validTypesCategory"]:
            category.categoryType = "UNUSED"
        category.defaultValue = allAttributes["DefaultValue"].get_value()

        category.categoryRole = allAttributes["role"].get_value()
        if category.categoryRole not in session["validroleCategory"][allAttributes["Type"].get_value()]:
            category.categoryRole = "UNUSED"

        # Flags
        category.isRequiredForAll = allAttributes["isRequiredForAll"].get_value()
        category.isRequiredForTea = allAttributes["isRequiredForTea"].get_value()
        category.isDropdown = allAttributes["isDropdown"].get_value()
        isAutoCalculated = allAttributes["isAutoCalculated"].get_value()
        category.isAutoCalculated = isAutoCalculated

        # Additional options
        category.rounding = int(allAttributes["rounding"].get_value())
        category.prefix = allAttributes["prefix"].get_value()
        category.suffix = allAttributes["suffix"].get_value()
        category.dropdownMaxLength = int(allAttributes["maxItems"].get_value())
        category.gradingDisplayAsLetter = allAttributes["gradingAsLetter"].get_value()
        print(f"{category.__dict__}")

        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
        # close the popup
        self.softRefresh()
        dpg.delete_item(user_data[2])

    def showEditReviewCategory(self, sender, app_data, user_data):
        # Create a popup window to edit the review category
        w = 500 * settings["UI_SCALE"]
        h = 500 * settings["UI_SCALE"]
        # Create a new window
        editReviewCategoryWindow = dp.Window(label="Edit Review Category", width=w, height=h, modal=True, show=True)
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        windowManager.addSubWindow(editReviewCategoryWindow)
        editReviewCategoryWindowItems = dict()
        category = TeaReviewCategories[user_data]

        with editReviewCategoryWindow:
            dp.Text("Edit Review Category")
            dpg.bind_item_font(dpg.last_item(), getFontName(3))
            dp.Text(f"{category.name}")
            dp.Separator()

            dp.Text(f"Default Value: {category.defaultValue}")
            editReviewCategoryWindowItems["DefaultValue"] = dp.InputText(default_value=category.defaultValue)
            dp.Separator()
            # Declare category name, width, type
            validTypes = session["validTypesReviewCategory"]
            with dp.Group(horizontal=True):
                dp.Text("Category Type")
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextCategory["CategoryType"].wrap()
                    dp.Text(toolTipText)

            catItem = dp.Listbox(items=validTypes, default_value=category.categoryType, num_items=5, callback=self.updateTypeDuringEditReview)
            if category.categoryType not in validTypes:
                catItem.set_value("ERR: Assume String")

            editReviewCategoryWindowItems["Type"] = catItem
            dp.Separator()

            with dp.Group(horizontal=True):
                dp.Text("Category Role")

                # Explanation tooltip
                dp.Button(label="?")

                with dpg.tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextCategory["CategoryRole"].wrap()
                    dp.Text(toolTipText)
            # Add hide used categories option
            with dp.Group(horizontal=True):
                dp.Text("Hide Used Categories")

                hideUsedItem = dp.Checkbox(default_value=self.hideUsedCategoriesBool, callback=self.hideUsedCategories, user_data=("EDIT_REVIEW_CATEGORY", editReviewCategoryWindow))

            # Dropdown for category role
            items = session["validroleReviewCategory"][category.categoryType]
            alreadyUsedItems = []
            for cat in TeaReviewCategories:
                if cat.categoryType == category.categoryType and cat.categoryRole != category.categoryRole:
                    alreadyUsedItems.append(cat.categoryRole)
            if self.hideUsedCategoriesBool:
                items = [item for item in items if item not in alreadyUsedItems]
            # Add in the current category role
            if category.categoryRole not in items:
                items.append(category.categoryRole)

            roleItem = dp.Listbox(items=items, default_value=category.categoryRole)
            editReviewCategoryWindowItems["role"] = roleItem
            if category.categoryRole not in items:
                roleItem.set_value("ERR: Assume Unused")
            dp.Separator()

            # Additional flags: isRequired, isrequiredForAll, isAutoCalculated, isDropdown
            dp.Separator()
            dp.Text("Additional Flags")

            isRequiredItem = dp.Checkbox(label="Is Required (inc Teaware, fees)", default_value=category.isRequiredForAll)
            editReviewCategoryWindowItems["isRequiredForAll"] = isRequiredItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isRequiredForAll"].wrap()
                dp.Text(toolTipTxt)

            isRequiredForTeaItem = dp.Checkbox(label="Is Required for Tea only", default_value=category.isRequiredForTea)
            editReviewCategoryWindowItems["isRequiredForTea"] = isRequiredForTeaItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isRequiredForTea"].wrap()
                dp.Text(toolTipTxt)

            isDropdownItem = dp.Checkbox(label="Is Dropdown", default_value=category.isDropdown)
            editReviewCategoryWindowItems["isDropdown"] = isDropdownItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isDropdown"].wrap()
                dp.Text(toolTipTxt)

            isAutoCalculatedItem = dp.Checkbox(label="Is Autocalculated", default_value=category.isAutoCalculated)
            editReviewCategoryWindowItems["isAutoCalculated"] = isAutoCalculatedItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["isAutoCalculated"].wrap()
                dp.Text(toolTipTxt)

            dp.Separator()

            # Prefix, rounding, etc
            dp.Text("Additional Options")
            dp.Text("Rounding")
            roundingAmtSliderInt = dp.SliderInt(default_value=int(category.rounding), min_value=0, max_value=5, format="%d")
            roundingAmtSliderInt.set_value(int(category.rounding))
            editReviewCategoryWindowItems["rounding"] = roundingAmtSliderInt
            dp.Text("Prefix")
            prefixItem = dp.InputText(default_value=category.prefix)
            editReviewCategoryWindowItems["prefix"] = prefixItem
            dp.Text("Suffix")
            suffixItem = dp.InputText(default_value=category.suffix)
            editReviewCategoryWindowItems["suffix"] = suffixItem
            dp.Text("Dropdown - Max Items")
            maxItemsItem = dp.SliderInt(default_value=int(category.dropdownMaxLength), min_value=3, max_value=30, format="%d")
            editReviewCategoryWindowItems["maxItems"] = maxItemsItem

            # Grading as letter
            dp.Text("Grading as Letter")
            gradingAsLetterItem = dp.Checkbox(label="Grading as Letter", default_value=category.gradingDisplayAsLetter)
            editReviewCategoryWindowItems["gradingAsLetter"] = gradingAsLetterItem
            with dpg.tooltip(dpg.last_item()):
                toolTipTxt = RateaTexts.ListTextCategory["gradingAsLetter"].wrap()
                dp.Text(toolTipTxt)

            dp.Separator()

            editReviewCategoryWindowItems["Type"].user_data = (editReviewCategoryWindowItems["Type"], roleItem)

            with dp.Group(horizontal=True):
                dp.Button(label="Save", callback=self.EditReviewCategory, user_data=(category, editReviewCategoryWindowItems, editReviewCategoryWindow))

                dp.Button(label="Cancel", callback=editReviewCategoryWindow.delete)

                # Help question mark
                dp.Button(label="?")

                # Hover tooltip
                with dpg.tooltip(dpg.last_item()):
                    dp.Text("Edit the review category name, type, and width in pixels")

    def updateTypeDuringEditReview(self, sender, app_data, user_data):
        # We need to update type during edit to show correct role
        RichPrintInfo(F"[INFO] Updated Type: {user_data[0].get_value()}")
        valueToSet = user_data[0].get_value()
        roleItem = user_data[1]
        validTypes = session["validroleReviewCategory"][valueToSet]
        dpg.configure_item(roleItem.tag, items=validTypes)
        roleItem.set_value(validTypes[0])

    def EditReviewCategory(self, sender, app_data, user_data):
        category = user_data[0]
        allAttributes = user_data[1]
        category.categoryType = allAttributes["Type"].get_value()
        if category.categoryType not in session["validTypesReviewCategory"]:
            category.categoryType = "string"
        category.defaultValue = allAttributes["DefaultValue"].get_value()

        category.categoryRole = allAttributes["role"].get_value()
        if category.categoryRole not in session["validroleReviewCategory"][allAttributes["Type"].get_value()]:
            category.categoryRole = "UNUSED"

        # Flags
        category.isRequiredForAll = allAttributes["isRequiredForAll"].get_value()
        category.isRequiredForTea = allAttributes["isRequiredForTea"].get_value()
        category.isDropdown = allAttributes["isDropdown"].get_value()
        category.isAutoCalculated = allAttributes["isAutoCalculated"].get_value()

        # Additional options
        category.rounding = int(allAttributes["rounding"].get_value())
        category.prefix = allAttributes["prefix"].get_value()
        category.suffix = allAttributes["suffix"].get_value()
        category.dropdownMaxLength = int(allAttributes["maxItems"].get_value())
        category.gradingDisplayAsLetter = allAttributes["gradingAsLetter"].get_value()


        RichPrintInfo(f"Editing review category: {category.name} ({category.categoryType}, Flags: {category.isRequiredForAll}, {category.isRequiredForTea}, {category.isAutoCalculated}, {category.isDropdown})")
        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
        # close the popup
        self.softRefresh()
        dpg.delete_item(user_data[2])


        
    def deleteCategory(self, sender, app_data, user_data):
        print(f"Delete Category - {user_data}")
        # Delete the category
        TeaCategories.pop(user_data)
        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
        
        # Refresh the window
        self.softRefresh()

    def deleteReviewCategory(self, sender, app_data, user_data):
        nameOfCategory = TeaReviewCategories[user_data].name
        # Delete the category
        TeaReviewCategories.pop(user_data)
        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])

        RichPrintSuccess(f"Deleted {nameOfCategory} category")
        
        # Refresh the window
        self.softRefresh()

    def AddCategory(self, sender, app_data, user_data):
        allObjects = user_data[0]
        allAttributes = dict()
        for item in allObjects:
            allAttributes[item] = allObjects[item].get_value()

        # Check if the category already exists
        if allAttributes["Name"] in [cat.name for cat in TeaCategories]:
            RichPrintWarning(f"Category {allAttributes['Name']} already exists")
            return
        # Check if the category type is valid
        if allAttributes["Type"] not in session["validTypesCategory"]:
            RichPrintWarning(f"Category type {allAttributes['Type']} is not valid, defaulting to string")
            allAttributes["Type"] = "string"

        defaultValue = allAttributes["DefaultValue"]
        if defaultValue == None or defaultValue == "":
            defaultValue = ""

        # Create a new category
        name = allAttributes["Name"]
        if name == None or name == "":
            RichPrintWarning(f"Category name is empty, defaulting to role")
            name = allAttributes["role"]

        newCategory = TeaCategory(name, allAttributes["Type"])
        newCategory.defaultValue = defaultValue

        # Add in role
        newCategory.categoryRole = allAttributes["role"]
        if newCategory.categoryRole not in session["validroleCategory"][allAttributes["Type"]]:
            newCategory.categoryRole = "UNUSED"

        # Add in flags
        newCategory.isRequiredForAll = allAttributes["isRequiredForAll"]
        newCategory.isRequiredForTea = allAttributes["isRequiredForTea"]
        newCategory.isAutoCalculated = allAttributes["isAutoCalculated"]
        newCategory.isDropdown = allAttributes["isDropdown"]

        # Additional options
        newCategory.rounding = int(allAttributes["rounding"])
        newCategory.prefix = allAttributes["prefix"]
        newCategory.suffix = allAttributes["suffix"]
        newCategory.dropdownMaxLength = int(allAttributes["maxItems"])
        newCategory.gradingDisplayAsLetter = allAttributes["gradingAsLetter"]

        # Log
        RichPrintInfo(f"Adding category: {newCategory.name} ({newCategory.categoryType}, Flags: {newCategory.isRequiredForAll}, {newCategory.isRequiredForTea}, {newCategory.isAutoCalculated}, {newCategory.isDropdown})")

        # Add the new category to the list
        TeaCategories.append(newCategory)
        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
       
        # close the popup
        self.softRefresh()
        dpg.delete_item(user_data[1])

def Menu_ReviewsTable():
    w = 480 * settings["UI_SCALE"]
    h = 600 * settings["UI_SCALE"]
    reviewsTable = Window_ReviewsTable("Reviews Table", w, h, exclusive=True)

class Window_ReviewsTable(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("Reviews Table")
            dp.Text("Reviews Table go here")

def Menu_Summary():
    w = 480 * settings["UI_SCALE"]
    h = 600 * settings["UI_SCALE"]
    summary = Window_Summary("Summary", w, h, exclusive=True)
class Window_Summary(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("Summary (TODO)")
            dp.Separator()
            # Mockup stats for now

            # Topline stats
            with dp.Group(horizontal=False):
                dp.Text(f"Num Teas: 2")
                dp.Text(f"Num Reviews: 5")
                dp.Text(f"Average Rating: X")
                dp.Text(f"Average drank per day: X")
                dp.Text(f"Amount in stash: X")
            # Stash stats
            dp.Text("Stash Stats")
            dp.Separator()
            with dp.Group(horizontal=False):
                dp.Text(f"Last Tea Added: Tea 2 at {parseDTToString(dt.datetime.now(tz=dt.timezone.utc))}")
                dp.Text(f"Grams in Stash: X")
                dp.Text(f"Total Spent: X")
                dp.Text(f"Average Price: X")
                dp.Text(f"Average Price per Gram: X")
                dp.Text(f"Average spent per month: X")
            

            # Reviews stats
            dp.Text("Reviews Stats")
            dp.Separator()
            with dp.Group(horizontal=False):
                dp.Text(f"Last Review Added: Tea 2 at {parseDTToString(dt.datetime.now(tz=dt.timezone.utc))}")
                dp.Text(f"Average Rating: X")
                dp.Text(f"Favorite Type: X")
                dp.Text(f"Favorite Year: X")

            # Table of tea types to grams, price, etc
            dp.Text("Tea Types")
            dp.Separator()
            # Table with tea types
            teasTable = dp.Table(header=["Type", "Grams", "Price", "Price per Gram"], header_row=True, no_host_extendX=True,
                                borders_innerH=True, borders_outerH=True, borders_innerV=True,
                                borders_outerV=True, row_background=True, hideable=True, reorderable=True,
                                resizable=True, sortable=True, policy=dpg.mvTable_SizingFixedFit,
                                scrollX=True, delay_search=True, scrollY=True, callback=_table_sort_callback)
            with teasTable:
                # Add columns
                dp.TableColumn(label="Type" , no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True, user_data="0")
                dp.TableColumn(label="Grams", no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True, user_data="1")
                dp.TableColumn(label="Price", no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True, user_data="2")
                dp.TableColumn(label="Price per Gram", no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True, user_data="3")
                # Add rows
                for i, tea in enumerate(TeaStash):
                    tableRow = dp.TableRow()
                    with tableRow:
                        dp.Text(label="Type", default_value="TODO")
                        dp.Text(label="Grams", default_value="TODO")
                        dp.Text(label="Price", default_value="TODO")
                        dp.Text(label="Price per Gram", default_value="TODO")


def Menu_Welcome(sender, app_data, user_data):
    w = 640 * settings["UI_SCALE"]
    h = 200 * settings["UI_SCALE"]
    welcome = Window_Welcome("Welcome", w, h, exclusive=True)
class Window_Welcome(WindowBase):
    def windowDefintion(self, window):
        # Get screen dimensions using Dear PyPixl
        screenWidth, screenHeight = screeninfo.get_monitors()[0].width, screeninfo.get_monitors()[0].height
        cw = screenWidth / 4
        ch = screenHeight / 4

        # Place in central location of screen
        self.x = int(cw - (self.width / 2))
        self.y = int(ch - (self.height / 2))
        dpg.set_item_pos(window.tag, [self.x, self.y])

        with window:
            todayDate = dt.datetime.now(tz=dt.timezone.utc)
            dp.Text(f"Welcome {settings['USERNAME']}! Today is {parseDTToString(todayDate)}")
            dpg.bind_item_font(dpg.last_item(), getFontName(3))
            numTeas = statsNumTeas()
            numReviews = statsNumReviews()
            
            
            
            dp.Text(f"You have {numTeas} teas and {numReviews} reviews in your stash.")
            dpg.bind_item_font(dpg.last_item(), getFontName(2))
            dp.Separator()
            dp.Text("Welcome to Ratea!")
            dp.Text(f"This is a simple tea stash manager (V{settings['APP_VERSION']}) to keep track of your teas and reviews.")
            dp.Text("This is a In-Progress demo, so expect bugs and missing features. - Rex")
            dp.Text("Head over to the settings then to the categories window to get started, "
            "\nOnce you have added some teas, you can add reviews to them and view your stats!")
            dp.Separator()
            
            dp.Button(label="OK", callback=window.delete)

# Userguide window
def Menu_UserGuide():
    w = 640 * settings["UI_SCALE"]
    h = 480 * settings["UI_SCALE"]
    userGuide = Window_UserGuide("User Guide", w, h, exclusive=True)

class Window_UserGuide(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("User Guide")
            dpg.bind_item_font(dpg.last_item(), getFontName(3))
            dp.Separator()
            # Collapsing header for each section
            with dp.CollapsingHeader(label="Introduction", default_open=True):
                text = RateaTexts.ListTextUserGuide["introduction"].wrap().strip()
                dp.Text(text)
                dp.Separator()
            with dp.CollapsingHeader(label="Windows", default_open=False):
                text = RateaTexts.ListTextUserGuide["windows"].wrap().strip()
                dp.Text(text)
                dp.Separator()
            with dp.CollapsingHeader(label="Stash Basics", default_open=False):
                text = RateaTexts.ListTextUserGuide["stashBasics"].wrap().strip()
                dp.Text(text)
                dp.Separator()
            with dp.CollapsingHeader(label="Stash Functions", default_open=False):
                text = RateaTexts.ListTextUserGuide["stashFunctions"].wrap().strip()
                dp.Text(text)
                dp.Separator()
            with dp.CollapsingHeader(label="Stash Reviews", default_open=False):
                text = RateaTexts.ListTextUserGuide["stashReviews"].wrap().strip()
                dp.Text(text)
                dp.Separator()
            with dp.CollapsingHeader(label="Misc Functions", default_open=False):
                text = RateaTexts.ListTextUserGuide["userGuide"].wrap().strip()
                dp.Text(text)
                dp.Separator()

# About window
def Menu_About():
    w = 640 * settings["UI_SCALE"]
    h = 480 * settings["UI_SCALE"]
    about = Window_About("About", w, h, exclusive=True)

class Window_About(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("About Ratea")
            dpg.bind_item_font(dpg.last_item(), getFontName(3))
            dp.Text(f"Ratea - Tea Stash Manager (V{settings['APP_VERSION']})")
            text = RateaTexts.ListTextUserGuide["About"].wrap()
            dp.Text(text)

            # Changelog section with collapsing header
            with dp.CollapsingHeader(label="Changelog", default_open=False):
                changelogText = RateaTexts.ListTextUserGuide["changelog"].wrap()
                dp.Text(changelogText)

# Terminal window
def Menu_Terminal():
    w = 880 * settings["UI_SCALE"]
    h = 720 * settings["UI_SCALE"]
    terminal = Window_Terminal("Terminal", w, h, exclusive=True)

class Window_Terminal(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("Terminal")
            # Add a text input box
            defaultLogs = self.getTerminalConsoleLogs()
            textInput = dp.InputText(default_value=defaultLogs, multiline=True, width=800 * settings["UI_SCALE"], height=600 * settings["UI_SCALE"], readonly=True)
            # Add a button to clear the terminal
            dp.Button(label="Clear", callback=self.clearTerminal, user_data=textInput)
            dp.Button(label="Copy to Clipboard", callback=self.copyTerminalToClipboard, user_data=textInput)
            dp.Separator()
        RichPrintSuccess("Opened Terminal window")

    def clearTerminal(self, sender, app_data, user_data):
        print("Clearing terminal")
        dpg.set_value(user_data, "")
        terminalConsoleLogs.clear()
        RichPrintSuccess("Cleared terminal logs")
    def getTerminalConsoleLogs(self):
        # Get the console logs
        global terminalConsoleLogs
        consoleLogs = '\n'.join(terminalConsoleLogs)
        return consoleLogs
    def copyTerminalToClipboard(self, sender, app_data, user_data):
        # Copy the console logs to clipboard
        global terminalConsoleLogs
        consoleLogs = '\n'.join(terminalConsoleLogs)
        dpg.set_clipboard_text(consoleLogs)
        RichPrintSuccess("Copied terminal logs to clipboard")


class Manager_Windows:
    windows = {}
    subWindows = [] 
    # Sub windows are windows that shouldnt be sorted, ie popups and just are
    # Tracked for deletion
    def __init__(self):
        self.windows = {}
    def addWindow(self, window):
        self.windows[window.title] = window
    def removeWindow(self, window: WindowBase):
        # Trigger the delete function
        del self.windows[window.utitle]
        window.delete()
    def addSubWindow(self, window):
        self.subWindows.append(window)
    def clearSubWindows(self):
        for window in self.subWindows:
            if window != None and type(window) == dp.Window and window.exists():
                window.delete()
            else:
                continue
        self.subWindows = []
        
            
        
    def deleteWindow(self, title):
        print(f"Deleting window: {title} (utitle={title})")
        if title in self.windows:
            self.removeWindow(self.windows[title])
    def sortWindows(self):
        # Callback function to sort and re-layout windows

        # Get screen dimensions using Dear PyPixl
        screen_width, screen_height = screeninfo.get_monitors()[0].width, screeninfo.get_monitors()[0].height

        # Padding between viewport
        padding_viewport = 20

        # Padding between windows
        padding_x, padding_y = 15, 15

        # Current x and y positions for window placement
        current_x, current_y = padding_x + padding_viewport, padding_y + padding_viewport

        # Maximum height in the current row (to properly stack rows)
        max_row_height = 0

        # Sort windows alphabetically by their title (utitle)
        sorted_windows = sorted(self.windows.items(), key=lambda x: x[0])

        for utitle, window_obj in sorted_windows:
            dpg_window = window_obj.dpgWindow

            # Get window size
            width = dpg.get_item_width(dpg_window)
            height = dpg.get_item_height(dpg_window)

            # If the window overflows horizontally, move to the next row
            if current_x + width + padding_x > screen_width:
                current_x = padding_x + padding_viewport
                current_y += max_row_height + padding_y
                max_row_height = 0

            # Move and position the window
            dpg.set_item_pos(dpg_window, [current_x, current_y])

            # Update positions for the next window
            current_x += width + padding_x
            max_row_height = max(max_row_height, height)

        # Ensure all windows fit within the screen height
        if current_y + max_row_height > screen_height:
            print("Warning: Some windows may exceed the screen height.")
    def printWindows(self):
        for key, value in self.windows.items():
            print(f"Window: {key}, {value}")

    def exportPersistantWindowWrapper(self, sender, app_data, user_data):
        # default to path defined in settings, error otherwise
        filePath = settings["PERSISTANT_WINDOWS_PATH"]
        if not os.path.exists(filePath):
            RichPrintWarning(f"Path {filePath} does not exist, please create it")
            os.makedirs(filePath, exist_ok=True)
            RichPrintSuccessMinor(f"Path {filePath} created")
        if not os.path.isfile(filePath):
            RichPrintWarning(f"Path {filePath} is not a file, please create it")
            return
        
        self.exportPersistantWindows(filePath)
        RichPrintSuccess(f"Exported all windows to {filePath}")

    def exportPersistantWindows(self, filePath):
        # Export all windows to a file
        allData = []
        for key, value in self.windows.items():
            title = value.title
            if value.persist:
                yml = value.exportYML()
                allData.append({title: yml})

        WriteYaml(filePath, allData)
        return allData
    
    def exportOneWindow(self, sender, app_data, user_data):
        # Export one window to a file
        # Get the window title from user_data
        title = user_data
        window = None
        for key, value in self.windows.items():
            if title in key:
                window = value
                break
        if window is None:
            RichPrintError(f"Window {title} not found")
            return
        
        filePath = f"{settings['PERSISTANT_WINDOWS_PATH']}"
        # First get the rest of the data
        allData = ReadYaml(filePath)
        # Check if the window already exists in the file
        for windowData in allData:
            title = list(windowData.keys())[0]
            if title == window.title:
                RichPrintInfo(f"Window {title} already exists in {filePath}, overwriting")
                allData.remove(windowData)
        
        # Now add the window data
        windowyml = window.exportYML()
        allData.append({window.title: windowyml})
        # Write the data to the file
        WriteYaml(filePath, allData)
        RichPrintSuccess(f"Exported window {window.title} to {filePath}")

    def importOneWindow(self, sender, app_data, user_data):
        # Import one window from a file
        # Get the window title from user_data
        title = user_data
        filePath = f"{settings['PERSISTANT_WINDOWS_PATH']}"
        if not os.path.exists(filePath):
            RichPrintError(f"Path {filePath} does not exist, please create it")
            return
        if not os.path.isfile(filePath):
            RichPrintError(f"Path {filePath} is not a file, please create it")
            return
        
        allData = ReadYaml(filePath)
        winDat = None
        for windowData in allData:
            if title in windowData:
                winDat = windowData[title]
                break
        if winDat is None:
            RichPrintError(f"Window {title} not found in {filePath}")
            return
        
        # Return yaml
        return winDat
    
    def importPersistantWindowWrapper(self, sender, app_data, user_data):
        # default to path defined in settings, error otherwise
        filePath = settings["PERSISTANT_WINDOWS_PATH"]
        if not os.path.exists(filePath):
            RichPrintError(f"Path {filePath} does not exist, please create it")
            return
        if not os.path.isfile(filePath):
            RichPrintError(f"Path {filePath} is not a file, please create it")
            return
        
        self.importPersistantWindows(filePath)
        RichPrintSuccess(f"Imported all windows from {filePath}")
    
    def importPersistantWindows(self, filePath):
        # Import all windows from a file
        allData = ReadYaml(filePath)
        for windowData in allData:
            title = list(windowData.keys())[0]
            data = windowData[title]
            # Create a new window
            if title == "Timer":
                Menu_Timer(None, None, data)
            elif title == "Notepad":
                Menu_Notepad(None, None, data)
        windowManager.sortWindows()

#endregion


#region Save and Load

def generateBackup():
    # Use the alternate backup path and generate a folder containing all backed up files, add datetime to path
    backupPath = f"{settings['BACKUP_PATH']}/{parseDTToStringWithHoursMinutes(dt.datetime.now(tz=dt.timezone.utc))}"
    os.makedirs(backupPath, exist_ok=True)
    SaveAll(backupPath, saveCSV=True)
    RichPrintSuccess(f"Backup generated at {backupPath}")

def saveTeasData(stash, path):
    # Save as one file in yml format
    allData = []
    nowString = parseDTToString(dt.datetime.now(tz=dt.timezone.utc))  # Get current time as string for default dateAdded
    for tea in stash:
        teaAttributesModified = tea.attributes
        # Convert all datetimes to unix timestamps
        for key, value in teaAttributesModified.items():
            if isinstance(value, dt.datetime):
                teaAttributesModified[key] = value.timestamp()

        timestamp = tea.dateAdded
        if type(timestamp) == dt.datetime:
            timestamp = tea.dateAdded.timestamp()
        # Clone adjustments
        adjustments = tea.adjustments.copy() if tea.adjustments else {}
        teaData = {
            "_index": tea.id,
            "Name": tea.name,
            "dateAddedTimeStamp": timestamp,  # Save dateAdded as timestamp for easier parsing
            "attributes": teaAttributesModified,
            "attributesJson": dumpAttributesToString(tea.attributes),  # Save attributes as JSON string for easier parsing
            "reviews": [],
            "adjustments": adjustments,
            "finished": tea.finished,
        }
        for review in tea.reviews:
            reviewAttributesModified = review.attributes
            # Convert all datetimes to unix timestamps
            for key, value in reviewAttributesModified.items():
                if isinstance(value, dt.datetime):
                    reviewAttributesModified[key] = value.timestamp()

            timestamp = review.dateAdded
            if type(timestamp) == dt.datetime:
                timestamp = review.dateAdded.timestamp()
            reviewData = {
                "_reviewindex": review.id,
                "parentIDX": tea.id,
                "Name": review.name,
                "dateAddedTimeStamp": timestamp,  # Save dateAdded as timestamp for easier parsing
                "attributes": reviewAttributesModified,
                "attributesJson": dumpAttributesToString(review.attributes),  # Save review attributes as JSON string for easier parsing
                "rating": review.rating,
            }
            teaData["reviews"].append(reviewData)
        allData.append(teaData)

    # If stash is not empty and data is not empty, write to file
    if len(allData) > 0 and allData is not None:
        RichPrintInfo(f"Saving {len(allData)} teas to {path}")
        WriteYaml(path, allData)
    else:
        RichPrintWarning(f"No teas to save, skipping save to {path}")
        return

    

def loadTeasReviews(path):
    # If not exists, create the directory, return false
    if not os.path.exists(path):
        RichPrintInfo(f"Directory {path} created")
        return []
    
    # Load from one file in yml format
    allData = ReadYaml(path)
    TeaStash = []
    i = 0
    j = 0
    for teaData in allData:
        idx = i
        if "_index" in teaData:
            idx = teaData["_index"]

        # Name could be under name or Name
        name = teaData.get("name", None)
        if name is None:
            name = teaData.get("Name", None)

        dateAdded = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        if "dateAddedTimeStamp" in teaData:
            dateAdded = dt.datetime.fromtimestamp(teaData["dateAddedTimeStamp"], tz=dt.timezone.utc)

        tea = StashedTea(idx, name, dateAdded=dateAdded, attributes=teaData["attributes"])
        
        if "attributesJson" in teaData and teaData["attributesJson"]:
            # If attributesJson is present, load it
            try:
                tea.attributes = loadAttributesFromString(teaData["attributesJson"])
            except Exception as e:
                # Fall back on loading from the old attributes format if JSON loading fails
                if "attributes" in teaData:
                    tea.attributes = teaData["attributes"]
                else:
                    RichPrintError(f"Failed to load attributes from JSON: {e}. Falling back to old attributes format.")
                    tea.attributes = {}  # Fallback to empty attributes if both fail

        # Add adjustments and finished flags
        if "adjustments" in teaData:
            tea.adjustments = teaData["adjustments"]
        if "finished" in teaData:
            tea.finished = teaData["finished"]
        
        for reviewData in teaData["reviews"]:
            idx2 = j
            if "_reviewindex" in reviewData:
                idx2 = reviewData["_reviewindex"]
            # Rating could be stored under 'rating' or 'Final Score', check both
            rating = reviewData.get("rating", None)
            if rating is None:
                rating = reviewData.get("Final Score", None)

            # Name could be under name or Name
            name = reviewData.get("name", None)
            if name is None:
                name = reviewData.get("Name", None)


            # dateadded Timestamp could be under dateAddedTimeStamp or Date Added TimeStamp
            dateAddedTimeStamp = reviewData.get("dateAddedTimeStamp", None)
            if dateAddedTimeStamp is None:
                dateAddedTimeStamp = reviewData.get("Date Added TimeStamp", None)

            
            review = Review(idx2, name, dateAddedTimeStamp, reviewData["attributes"], rating)
            review.parentID = tea.id
            tea.addReview(review)
            j += 1
        TeaStash.append(tea)
        i += 1
        j = 0
    return TeaStash

def saveTeaCategories(categories, path):
    # Save as one file in yml format
    allData = []
    for category in categories:
        category: TeaCategory
        categoryData = {
            "Name": category.name,
            "categoryType": category.categoryType,
            "defaultValue": category.defaultValue,
            "categoryRole": category.categoryRole,
            "isAutoCalculated": category.isAutoCalculated,
            "isRequiredForTea": category.isRequiredForTea,
            "isRequiredForAll": category.isRequiredForAll,
            "isDropdown": category.isDropdown,
            "rounding": int(category.rounding),
            "prefix": category.prefix,
            "suffix": category.suffix,
            "maxItems": int(category.dropdownMaxLength),
            "gradingDisplayAsLetter": category.gradingDisplayAsLetter,
        }
        allData.append(categoryData)

    WriteYaml(path, allData)

def loadTeaCategories(path):
    # If not exists, create the directory, return false
    if not os.path.exists(path):
        RichPrintInfo(f"Directory {path} created")
        return []
    
    # Load from one file in yml format
    allData = ReadYaml(path)
    TeaCategories = []
    for categoryData in allData:
        category = TeaCategory(categoryData["Name"], categoryData["categoryType"])
        category.defaultValue = ""
        if "defaultValue" in categoryData:
            category.defaultValue = categoryData["defaultValue"]
        # Check if the category type is valid
        if category.categoryType not in session["validTypesCategory"]:
            category.categoryType = "string"

        # Add role
        if "categoryRole" in categoryData:
            category.categoryRole = categoryData["categoryRole"]
        else:
            category.categoryRole = category.categoryType
        TeaCategories.append(category)

        # Add flags
        if "isRequiredForAll" in categoryData:
            category.isRequiredForAll = categoryData["isRequiredForAll"]
        else:
            category.isRequiredForAll = False

        if "isRequiredForTea" in categoryData:
            category.isRequiredForTea = categoryData["isRequiredForTea"]

        if "isDropdown" in categoryData:
            category.isDropdown = categoryData["isDropdown"]

        if "isAutoCalculated" in categoryData:
            category.isAutoCalculated = categoryData["isAutoCalculated"]

        # Additional options
        if "rounding" in categoryData:
            category.rounding = int(categoryData["rounding"])
        else:
            category.rounding = 2

        if "prefix" in categoryData:
            category.prefix = categoryData["prefix"]

        if "suffix" in categoryData:
            category.suffix = categoryData["suffix"]

        if "maxItems" in categoryData:
            category.dropdownMaxLength = int(categoryData["maxItems"])
        else:
            category.dropdownMaxLength = 5

        if "gradingDisplayAsLetter" in categoryData:
            category.gradingDisplayAsLetter = categoryData["gradingDisplayAsLetter"]
        else:
            category.gradingDisplayAsLetter = False

    return TeaCategories

def loadTeaReviewCategories(path):
    # If not exists, create the directory, return false
    if not os.path.exists(path):
        RichPrintInfo(f"Directory {path} created")
        return []
    
    # Load from one file in yml format
    allData = ReadYaml(path)
    TeaReviewCategories = []
    for categoryData in allData:
        category = ReviewCategory(categoryData["Name"], categoryData["categoryType"])
        category.defaultValue = ""
        if "defaultValue" in categoryData:
            category.defaultValue = categoryData["defaultValue"]
        # Check if the category type is valid
        if category.categoryType not in session["validTypesReviewCategory"]:
            category.categoryType = "string"
        TeaReviewCategories.append(category)

        # Add role
        if "categoryRole" in categoryData:
            category.categoryRole = categoryData["categoryRole"]
        else:
            category.categoryRole = category.categoryType

        # Add flags
        if "isRequiredForAll" in categoryData:
            category.isRequiredForAll = categoryData["isRequiredForAll"]
        else:
            category.isRequiredForAll = False

        if "isRequiredForTea" in categoryData:
            category.isRequiredForTea = categoryData["isRequiredForTea"]

        if "isDropdown" in categoryData:
            category.isDropdown = categoryData["isDropdown"]

        if "isAutoCalculated" in categoryData:
            category.isAutoCalculated = categoryData["isAutoCalculated"]

        if "rounding" in categoryData:
            category.rounding = int(categoryData["rounding"])

        if "prefix" in categoryData:
            category.prefix = categoryData["prefix"]

        if "suffix" in categoryData:
            category.suffix = categoryData["suffix"]

        if "maxItems" in categoryData:
            category.dropdownMaxLength = int(categoryData["maxItems"])

        if "gradingDisplayAsLetter" in categoryData:
            category.gradingDisplayAsLetter = categoryData["gradingDisplayAsLetter"]
        else:
            category.gradingDisplayAsLetter = False


    return TeaReviewCategories

def verifyCategoriesReviewCategories():
    # For each category, double check all values are valid
    for category in TeaCategories:
        if category.categoryType not in session["validTypesCategory"]:
            category.categoryType = "string"
        if category.categoryRole not in session["validroleCategory"]:
            category.categoryRole = "UNUSED"
    for category in TeaReviewCategories:
        if category.categoryType not in session["validTypesReviewCategory"]:
            category.categoryType = "string"
        if category.categoryRole not in session["validroleReviewCategory"]:
            category.categoryRole = "UNUSED"

    RichPrintInfo(f"Number of Tea Categories: {len(TeaCategories)}")
    RichPrintInfo(f"Number of Review Categories: {len(TeaReviewCategories)}")

    # Save the categories again
    SaveAll(saveCSV=False)

def saveTeaReviewCategories(categories, path):
    # Save as one file in yml format
    allData = []
    for category in categories:
        category: ReviewCategory
        categoryData = {
            "Name": category.name,
            "categoryType": category.categoryType,
            "defaultValue": category.defaultValue,
            "categoryRole": category.categoryRole,
            "isAutoCalculated": category.isAutoCalculated,
            "isRequiredForTea": category.isRequiredForTea,
            "isRequiredForAll": category.isRequiredForAll,
            "isDropdown": category.isDropdown,
            "rounding": int(category.rounding),
            "prefix": category.prefix,
            "suffix": category.suffix,
            "maxItems": category.dropdownMaxLength,
            "gradingDisplayAsLetter": category.gradingDisplayAsLetter,
        }
        allData.append(categoryData)

    WriteYaml(path, allData)

def SaveAll(altPath=None, saveCSV=True):
    # ignore sender and app_data
    if type(altPath) != str and altPath is not None:
        altPath = None
    # Save all data
    if altPath is not None:
        # This is a backup path, so save to the backup path
        newBaseDirectory = altPath
        saveTeasData(TeaStash, f"{newBaseDirectory}/tea_reviews.yml")
        saveTeaCategories(TeaCategories, f"{newBaseDirectory}/tea_categories.yml")
        saveTeaReviewCategories(TeaReviewCategories, f"{newBaseDirectory}/tea_review_categories.yml")
        WriteYaml(f"{newBaseDirectory}/user_settings.yml", settings)
        windowManager.exportPersistantWindows(f"{newBaseDirectory}/persistant_windows.yml")
        RichPrintSuccess(f"All data saved to {newBaseDirectory}")

        # CSVs
        if saveCSV:
            teaStashToCSV(f"{newBaseDirectory}/tea.csv", f"{newBaseDirectory}/review.csv")
            RichPrintSuccess(f"CSV files saved to {newBaseDirectory}")
        return
    saveTeasData(TeaStash, settings["TEA_REVIEWS_PATH"])
    saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
    saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
    WriteYaml(session["settingsPath"], settings)
    windowManager.exportPersistantWindows(settings["PERSISTANT_WINDOWS_PATH"])

    # CSVs
    if saveCSV:
        # CSVs are slow to save due to file serialization, so only save if specified
        teaStashToCSV(settings["CSV_OUTPUT_TEA_PATH"], settings["CSV_OUTPUT_REVIEW_PATH"])
        RichPrintSuccess(f"CSV files saved to {settings['CSV_OUTPUT_TEA_PATH']} and {settings['CSV_OUTPUT_REVIEW_PATH']}")


# Start Backup Thread
def checkboxBackupThread(sender, app_data, user_data):
    print(f"Checkbox Backup Thread: {app_data}")
    startStopBackupThread(app_data)
def startStopBackupThread(shouldStart=False):
    # If ShouldStart and not started, start, else end
    global backupThread
    global backupStopEvent
    
    if shouldStart == True and backupThread == False:
        backupStopEvent.clear()
        RichPrintInfo("Starting backup thread")
        backupThread = threading.Thread(target=backupThreadFunc, daemon=True)
        backupThread.start()
        RichPrintSuccess("Backup thread started")
    elif shouldStart == False and backupThread != False:
        RichPrintInfo("Stopping backup thread")
        backupStopEvent.set()
        backupThread.join(timeout=2)
        backupThread = False
        RichPrintSuccess("Backup thread stopped")
    else:
        RichPrintInfo("Backup thread already started or stopped, doing nothing")



def backupThreadFunc():
    # Start a loop to poll the time since start and save if needed
    while not backupStopEvent.is_set():
        # Check if the backup thread is running
        pollAndAutosaveIfNeeded()
        #time.sleep(60)  # Poll every 5s
        backupStopEvent.wait(timeout=60)  # Wait for 60 seconds or until the event is set

def pollAndAutosaveIfNeeded():
    timeLastSave = pollTimeSinceStartMinutes()
    autosaveInterval = settings["AUTO_SAVE_INTERVAL"]
    if timeLastSave >= autosaveInterval and settings["AUTO_SAVE"] and timeLastSave >= 5:
        print(f"Autosaving after {timeLastSave} minutes")
        # Save To Backup
        autoBackupPath = settings["AUTO_SAVE_PATH"] + f"/{parseDTToStringWithHoursMinutes(dt.datetime.now(tz=dt.timezone.utc))}"
        if autoBackupPath != None and autoBackupPath != "":
            if not os.path.exists(autoBackupPath):
                os.makedirs(autoBackupPath, exist_ok=True)
            SaveAll(autoBackupPath, saveCSV=True)
            global globalTimeLastSave
            globalTimeLastSave = dt.datetime.now(tz=dt.timezone.utc)
            timeLastSave = pollTimeSinceStartMinutes()
        else:
            RichPrintError("Auto backup path not set, skipping auto backup")
        

    RichPrintInfo(f"Autosave interval is {autosaveInterval} minutes, last save was {timeLastSave} minutes ago")

def LoadSettings(path=None):
    global settings
    if path is None:
        path = session["settingsPath"]
    if not os.path.exists(path):
        RichPrintError(f"Settings file {path} does not exist. Using default settings.")
        return False
    settings = ReadYaml(path)
    if settings is None:
        RichPrintError("Failed to load settings from YAML.")
        return False
    session["settingsPath"] = path
    RichPrintSuccess(f"Loaded settings from {path}")
    return settings

def hasLoadableFiles():
    # Checks if the DIRECTORY exists and if the files exist
    # else, checks if backup or autobackup path exists
    mainFilesExist = os.path.exists(settings["TEA_REVIEWS_PATH"]) and os.path.exists(settings["TEA_CATEGORIES_PATH"]) and os.path.exists(settings["TEA_REVIEW_CATEGORIES_PATH"])
    backupFilesExist = os.path.exists(settings["AUTO_SAVE_PATH"]) and os.path.exists(settings["BACKUP_PATH"])
    return mainFilesExist, backupFilesExist

def LoadAll(baseDir=None):
    if baseDir is None:
        baseDir = os.path.dirname(os.path.abspath(__file__))
    # Load all data
    global settings
    #baseDir = os.path.dirname(os.path.abspath(__file__))
    settingsPath = f"{baseDir}/{default_settings['SETTINGS_FILENAME']}"
    session["settingsPath"] = settingsPath
    settings = LoadSettings(session["settingsPath"])
    # Update version
    categoriesPath = f"{baseDir}/{settings['TEA_CATEGORIES_PATH']}"
    teaReviewCategoriesPath = f"{baseDir}/{settings['TEA_REVIEW_CATEGORIES_PATH']}"
    session["categoriesPath"] = categoriesPath
    session["reviewCategoriesPath"] = teaReviewCategoriesPath
    settings["APP_VERSION"] = default_settings["APP_VERSION"]
    global TeaStash
    TeaStash = loadTeasReviews(settings["TEA_REVIEWS_PATH"])
    global TeaCategories
    TeaCategories = loadTeaCategories(session["categoriesPath"])
    global TeaReviewCategories
    TeaReviewCategories = loadTeaReviewCategories(session["reviewCategoriesPath"])
    # Renumber the teas and reviews if needed
    renumberTeasAndReviews()  # Ensure all teas and reviews have unique IDs after loading

    RichPrintInfo(f"Loaded settings from {session['settingsPath']}")
    
    RichPrintSuccess(f"Loaded {len(TeaStash)} teas and {len(TeaCategories)} categories")

# Attributes to string, json, with special datetime handling
def dumpAttributesToString(attributes):
    returnDict = dumpAttributesToDict(attributes)
    # Convert dict to JSON string
    returnString = json.dumps(returnDict)  # Convert datetime objects to string
    
    # Replace escaped double quotes with double quotes
    returnString = returnString.replace('\\"', '"')
    return returnString
    

def dumpAttributesToDict(attributes):
    returnDict = {}
    parseDict = json.loads(json.dumps(attributes, default=str))  # Convert datetime objects to string
    # for strings, remove the HH:MM:SS part
    if isinstance(parseDict, str):
        parseDict = parseDict.replace("00:00:00", "")  # Remove HH:MM:SS part
    if not isinstance(parseDict, dict):
        try:
            parseDict = json.loads(parseDict)  # Try to parse it again if it's not a dict
        except json.JSONDecodeError:
            RichPrintError("Failed to parse attributes to dict")
            return {}
    if not isinstance(parseDict, dict):
        RichPrintError("Attributes must be a dictionary")
        return {}
    
    # Ensure all datetime objects are converted to strings
    for key, value in parseDict.items():
        if isinstance(value, dt.datetime):
            #atetimeString = parseDTToString(value)
            #dateString = datetimeString.split(" ")[0]
            #timeString = datetimeString.split(" ")[1]
            # Timestamp
            dateString = TimeStampToString(value.timestamp())
            returnDict[key] = dateString
        else:
            keyvalue = value
            if isinstance(value, str):
                keyvalue = keyvalue.replace("00:00:00", "")  # Remove HH:MM:SS part
            returnDict[key] = keyvalue
    return returnDict

# Return Attributes dict from a JSON string, handling datetime parsing
def loadAttributesFromString(json_string):
    if not json_string or json_string.strip() == "":
        return {}
    try:
        attributes = json.loads(json_string)
        # Convert datetime strings back to datetime objects if needed
        for key, value in attributes.items():
            if isinstance(value, str):
                try:
                    # Attempt to parse as datetime
                    parsed_date = parseStringToDT(value, silent=True)
                    if parsed_date is None or parsed_date == "" or parsed_date == False:
                        raise ValueError("Invalid datetime string")
                    if type(parsed_date) is dt.datetime:
                        attributes[key] = parsed_date
                    else:
                        attributes[key] = value
                except (ValueError, TypeError):
                    # If parsing fails, keep the original string value
                    attributes[key] = value
                except ValueError:
                    pass  # Not a datetime string, keep it as is
        return attributes
    except json.JSONDecodeError:
        print (f"Error decoding JSON string: {json_string}")
        RichPrintError("Failed to decode JSON string for attributes")
        return {}
    
def dumpReviewToDict(review):
    returnDict = {}
    # Declare an empty dict then handle each attribute seperately, datetime needs to be converted to string
    for key, value in review.__dict__.items():
        if isinstance(value, dt.datetime):
            datetimeString = parseDTToString(value)
            dateString = datetimeString.split(" ")[0]
            #timeString = datetimeString.split(" ")[1]
            returnDict[key] = dateString
        elif isinstance(value, dict):
            # Recursive handling
            returnDict[key] = dumpAttributesToDict(value)
        else:
            returnDict[key] = value
    return returnDict

def dumpTeaToDict(tea):
    returnDict = {}
    # Declare an empty dict then handle each attribute seperately, datetime needs to be converted to string
    for key, value in tea.__dict__.items():
        if isinstance(value, dt.datetime):
            datetimeString = parseDTToString(value)
            dateString = datetimeString.split(" ")[0]
            #timeString = datetimeString.split(" ")[1]
            returnDict[key] = dateString
    
        elif isinstance(value, dict):
            # Recursive handling
            returnDict[key] = dumpAttributesToDict
        else:
            returnDict[key] = value
    
    returnDict["attributes"] = dumpAttributesToDict(tea.attributes)  # Save attributes as JSON string for easier parsing
    
    returnDict["calculated"] = tea.calculated  # Save calculated values
    returnDict["reviews"] = []  # Add empty list for reviews

    # Add in reviews from the tea object
    # Reviews is a list of Review objects, convert to dicts first
    reviews = []
    for review in tea.reviews:
        reviews.append(dumpReviewToDict(review))
    returnDict["reviews"] = reviews


    return returnDict

def loadReviewFromDictNewID(reviewData, id, parentId):
    # Create a new review object from the dict generated by the above function
    review = Review(id, reviewData["Name"], reviewData["dateAdded"], reviewData["attributes"], reviewData["Final Score"])
    review.parentID = parentId  # Set the parent ID to the tea ID
    if type(reviewData["attributes"]) is str:
        review.attributes = loadAttributesFromString(reviewData["attributes"])
    else:
        review.attributes = reviewData["attributes"]

    # Convert datetime strings back to datetime objects if needed
    for key, value in review.__dict__.items():
        if isinstance(value, str):
            try:
                # Attempt to parse as datetime
                parsed_date = parseStringToDT(value, silent=True)
                if type(parsed_date) is dt.datetime:
                    review.__dict__[key] = parsed_date
                else:
                    review.__dict__[key] = value
            except (ValueError, TypeError):
                # If parsing fails, keep the original string value
                review.__dict__[key] = value
            except ValueError:
                pass

    # If calculated is not in the review, add blank
    if "calculated" not in review.__dict__:
        review.calculated = {}

    return review

def teaStashToCSV(csvPath=None, csvPathReviews=None):
    # If no path is given, use the default path
    if csvPath is None:
        csvPath = settings["CSV_OUTPUT_TEA_PATH"]
    if csvPathReviews is None:
        csvPathReviews = settings["CSV_OUTPUT_REVIEW_PATH"]
    # Piggyback on exisitng json support to convert to CSV
    # For exporting every tea in TeaStash to a CSV file
    RichPrintInfo("Exporting TeaStash to CSV")
    rawData = TeaStash
    # For each tea, convert to dict
    allData = []
    for tea in rawData:
        teaData = dumpTeaToDict(tea)
        allData.append(teaData)
        
    # Seperate reviews from the tea data
    allReviews = []
    for tea in allData:
        if len(tea["reviews"]) > 0:
            for review in tea["reviews"]:
                allReviews.append(review)
    
    # Flatten attributes and calculated values
    for tea in allData:
        for key, value in tea["attributes"].items():
            if key not in tea:
                tea[key] = value
        for key, value in tea["calculated"].items():
            if key not in tea:
                tea[key] = value

    for review in allReviews:
        for key, value in review["attributes"].items():
            if key not in review:
                review[key] = value
        for key, value in review["calculated"].items():
            if key not in review:
                review[key] = value

    # Remove reviews from the tea data
    for tea in allData:
        tea.pop("reviews", None)
        tea.pop("calculated", None)
        tea.pop("attributes", None)
    
    # Remove attributes from the review data
    for review in allReviews:
        review.pop("attributes", None)
        review.pop("calculated", None)
    

    # Swap datetime to string for all datetime objects
    for tea in allData:
        for key, value in tea.items():
            if isinstance(value, dt.datetime):
                datetimeString = parseDTToString(value)
                dateString = datetimeString.split(" ")[0]
                #timeString = datetimeString.split(" ")[1]
                tea[key] = dateString
    
    for review in allReviews:
        for key, value in review.items():
            if isinstance(value, dt.datetime):
                datetimeString = parseDTToString(value)
                dateString = datetimeString.split(" ")[0]
                #timeString = datetimeString.split(" ")[1]
                review[key] = dateString

    # Add headers for both by iterating over all keys in both lists
    headers = []
    for tea in allData:
        for key in tea.keys():
            if key not in headers:
                headers.append(key)
    headersReviews = []
    for review in allReviews:
        for key in review.keys():
            if key not in headersReviews:
                headersReviews.append(key)



    # Create two CSV files, one for teas and one for reviews
    with open(csvPath, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for tea in allData:
            writer.writerow(tea)
        RichPrintSuccess(f"Exported {len(allData)} teas to {csvPath}")

    with open(csvPathReviews, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headersReviews)
        writer.writeheader()
        for review in allReviews:
            writer.writerow(review)
        RichPrintSuccess(f"Exported {len(allReviews)} reviews to {csvPathReviews}")
    return allData, allReviews


#endregion

def UI_CreateViewPort_MenuBar():
    # UI is constructed before backup thread is started, so check if it is enabled
    shouldBackupThread = settings["AUTO_SAVE"]

    with dp.ViewportMenuBar() as menuBar:
        with dp.Menu(label="File"):
            dp.Button(label="Save", callback=SaveAll)
            dp.Button(label="Load", callback=LoadAll)
            with dp.Menu(label="Backup"):
                dp.Button(label="Backup", callback=generateBackup)
                dp.Checkbox(label="Auto Backup", callback=checkboxBackupThread, default_value=shouldBackupThread)
            with dp.Menu(label="Export"):
                dp.Button(label="Export to CSV", callback=teaStashToCSV)
        with dp.Menu(label="Stash"):
            dp.MenuItem(label="Log", callback=Menu_Stash)
            dp.MenuItem(label="Edit Categories", callback=Menu_EditCategories)
        with dp.Menu(label="Stats"):
            dp.MenuItem(label="Reviews(TODO)", callback=Menu_ReviewsTable)
            dp.MenuItem(label="Stats", callback=Menu_Stats)
            dp.MenuItem(label="Summary(WIP)", callback=Menu_Summary)
            with dp.Menu(label="Graphs(TODO)"):
                dp.MenuItem(label="Graph 1(TODO)", callback=print_me)
                dp.MenuItem(label="Graph 2(TODO)", callback=print_me)
        with dp.Menu(label="Tools"):
            dp.MenuItem(label="Timer", callback=Menu_Timer)
            dp.MenuItem(label="Notepad", callback=Menu_Notepad)
            dp.MenuItem(label="Terminal", callback=Menu_Terminal)
            dp.Button(label="Settings", callback=Menu_Settings)
        with dp.Menu(label="Windows"):
            dp.Button(label="Sort Windows", callback=windowManager.sortWindows)
            dp.Button(label="Import Persistant Windows", callback=windowManager.importPersistantWindowWrapper)
            dp.Button(label="Export Persistant Windows", callback=windowManager.exportPersistantWindowWrapper)
        with dp.Menu(label="Help"):
            dp.Button(label="User Guide", callback=Menu_UserGuide)
            dp.Button(label="About", callback=Menu_About)
            with dp.Menu(label="Library(TODO)"):
                dp.Button(label="Press Me", callback=print_me)
        with dp.Menu(label="Debug"):
            dp.Button(label="Demo", callback=demo.show_demo)
            with dp.Menu(label="Ops"):
                dp.Button(label="Terminal", callback=Menu_Terminal)
                dp.Button(label="Renumber data", callback=renumberTeasAndReviews)
                dp.Button(label="Check Categories", callback=verifyCategoriesReviewCategories)
                dp.Button(label="Stop Backup Thread", callback=startStopBackupThread)
            with dp.Menu(label="Print"):
                dp.Button(label="Poll Time", callback=debugPrintPolledTime)
                dp.Button(label="printTeasAndReviews", callback=printTeasAndReviews)
                dp.Button(label="Print Categories/Reviews", callback=printCategories)
                dp.Button(label="Print role Cat", callback=debugGetcategoryRole)
                dp.Button(label="Print role Rev Cat", callback=debugGetReviewcategoryRole)
                dp.Button(label="Settings", callback=printSettings)
                dp.Button(label="Threads", callback=printThreads)
                dp.Button(label="Windows", callback=windowManager.printWindows)
                
    

def bindLoadFonts():
    # Load fonts
    with dpg.font_registry():
        dpg.add_font("assets/fonts/Roboto-Regular.ttf", 16, tag="RobotoRegular")
        dpg.add_font("assets/fonts/Roboto-Regular.ttf", 20, tag="RobotoRegular2")
        dpg.add_font("assets/fonts/Roboto-Regular.ttf", 26, tag="RobotoRegular3")

        dpg.add_font("assets/fonts/Roboto-Bold.ttf", 16, tag="RobotoBold")
        dpg.add_font("assets/fonts/Roboto-Bold.ttf", 20, tag="RobotoBold2")
        dpg.add_font("assets/fonts/Roboto-Bold.ttf", 26, tag="RobotoBold3")
        # Merriweather 24pt regular
        dpg.add_font("assets/fonts/Merriweather_24pt-Regular.ttf", 16, tag="MerriweatherRegular")
        dpg.add_font("assets/fonts/Merriweather_24pt-Regular.ttf", 20, tag="MerriweatherRegular2")
        dpg.add_font("assets/fonts/Merriweather_24pt-Regular.ttf", 26, tag="MerriweatherRegular3")
        # Merriweather 24pt bold
        dpg.add_font("assets/fonts/Merriweather_24pt-Bold.ttf", 16, tag="MerriweatherBold")
        dpg.add_font("assets/fonts/Merriweather_24pt-Bold.ttf", 20, tag="MerriweatherBold2")
        dpg.add_font("assets/fonts/Merriweather_24pt-Bold.ttf", 26, tag="MerriweatherBold3")
        # Montserrat-regular
        dpg.add_font("assets/fonts/Montserrat-Regular.ttf", 16, tag="MontserratRegular")
        dpg.add_font("assets/fonts/Montserrat-Regular.ttf", 20, tag="MontserratRegular2")
        dpg.add_font("assets/fonts/Montserrat-Regular.ttf", 26, tag="MontserratRegular3")
        # Montserrat-bold
        dpg.add_font("assets/fonts/Montserrat-Bold.ttf", 16, tag="MontserratBold")
        dpg.add_font("assets/fonts/Montserrat-Bold.ttf", 20, tag="MontserratBold2")
        dpg.add_font("assets/fonts/Montserrat-Bold.ttf", 26, tag="MontserratBold3")
        # Opensans regular
        dpg.add_font("assets/fonts/OpenSans-Regular.ttf", 18, tag="OpenSansRegular")
        dpg.add_font("assets/fonts/OpenSans-Regular.ttf", 20, tag="OpenSansRegular2")
        dpg.add_font("assets/fonts/OpenSans-Regular.ttf", 26, tag="OpenSansRegular3")
        # Opensans bold
        dpg.add_font("assets/fonts/OpenSans-Bold.ttf", 18, tag="OpenSansBold")
        dpg.add_font("assets/fonts/OpenSans-Bold.ttf", 20, tag="OpenSansBold2")
        dpg.add_font("assets/fonts/OpenSans-Bold.ttf", 26, tag="OpenSansBold3")

        # Set the default font to specified in settings
        if settings["DEFAULT_FONT"] is not None and settings["DEFAULT_FONT"] in session["validFonts"]:
            dpg.bind_font(f"{settings['DEFAULT_FONT']}Regular")
        else:
            RichPrintError(f"Default font {settings['DEFAULT_FONT']} not found, using OpenSansRegular")
            dpg.bind_font("OpenSansRegular")
    
def bind_image_registry():
    # Bind the image registry for the application
    with dpg.texture_registry(show=False):
        # Load images from assets folder
        texture_data = []
        for i in range(0, 100 * 100):
            texture_data.append(255/255)
            texture_data.append(0)
            texture_data.append(0)
            texture_data.append(255/255)
        
        dpg.add_static_texture(width=100, height=100, default_value=texture_data, tag="test")
        width, height, channels, data = dpg.load_image("assets/images/icons8-refresh-64.png")
        dpg.add_static_texture(width=width, height=height, default_value=data, tag="refresh_icon")

def addImageToRegistryFromFile(path, tag):
    if not os.path.exists(path):
        RichPrintError(f"Image {path} does not exist, cannot add to registry")
        return False
    
    # check if alias tag already exists, if does, delete old one
    if dpg.does_item_exist(tag):
        dpg.delete_item(tag)
        RichPrintInfo(f"Deleted old texture for {tag}")
    width, height, channels, data = dpg.load_image(path)
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=width, height=height, default_value=data, tag=tag)
    return True

def printSettings():
    for key, value in settings.items():
        print(f"Setting {key} is {value}")
def printThreads():
    print(threading.enumerate())

def pollTimeSinceStartMinutes():
    # Get the current time
    currentTime = dt.datetime.now(tz=dt.timezone.utc)
    # Calculate the difference
    timeDiff = currentTime - globalTimeLastSave
    # Convert to minutes
    timeDiffMinutes = timeDiff.total_seconds() / 60.0
    
    # Round to 0.1
    timeDiffMinutes = round(timeDiffMinutes, 1)
    return timeDiffMinutes

def debugPrintPolledTime():
    polledTime = pollTimeSinceStartMinutes()
    RichPrintInfo(f"Polled time since start: {polledTime} minutes")

def main():
    RichPrintInfo("Starting Tea Tracker")
    print("RaTea - Tea Tracker")
    timestartLoad = dt.datetime.now(tz=dt.timezone.utc)
    global globalTimeLastSave
    globalTimeLastSave = dt.datetime.now(tz=dt.timezone.utc)
    # get monitor resolution
    monitors = screeninfo.get_monitors()
    monitor = monitors[0] if len(monitors) == 1 else None
    if monitor is None:
        # Find based on primary monitor
        for m in monitors:
            if m.is_primary:
                monitor = m
                break
    Monitor_Scale = 1
    if monitor.width >= 3840:
        Monitor_Scale = 2.0
    elif monitor.width < 2560:
        Monitor_Scale = 1.5
    elif monitor.width < 1920:
        Monitor_Scale = 1.25
    elif monitor.width < 1600:
        Monitor_Scale = 1.0
    elif monitor.width < 1280:
        Monitor_Scale = 0.75
    print(f"Monitor scale set to {Monitor_Scale} based on resolution {monitor.width}x{monitor.height}")
    baseDir = os.path.dirname(os.path.abspath(__file__))
    

    DEBUG_ALWAYSNEWJSON = False

    global windowManager
    windowManager = Manager_Windows()
    windowManager.sortWindows()

    global backupThread
    backupThread = False

    global default_settings
    default_settings = {
        "UI_SCALE": Monitor_Scale,
        "SETTINGS_FILENAME": "ratea-data/user_settings.yml", # do not change
        "TEA_CATEGORIES_PATH": f"ratea-data/tea_categories.yml",
        "TEA_REVIEW_CATEGORIES_PATH": f"ratea-data/tea_review_categories.yml",
        "CSV_OUTPUT_TEA_PATH": f"ratea-data/tea_stash.csv",
        "CSV_OUTPUT_REVIEW_PATH": f"ratea-data/tea_review.csv",
        "FALLBACK_DEFAULT_PATH": f"defaults",
        "USERNAME": "John Puerh",
        "DIRECTORY": "ratea-data",
        "DATE_FORMAT": "%Y-%m-%d",
        "TIMEZONE": "UTC", # default to UTC, doesn't really matter since time is not used
        "TIMER_WINDOW_LABEL": True,
        "TIMER_PERSIST_LAST_WINDOW": True, # TODO
        "TEA_REVIEWS_PATH": f"ratea-data/tea_reviews.yml",
        "BACKUP_PATH": f"ratea-data/backup",
        "PERSISTANT_WINDOWS_PATH": f"ratea-data/persistant_windows.yml",
        "APP_VERSION": "0.21.0", # Updates to most recently loaded
        "AUTO_SAVE": True,
        "AUTO_SAVE_INTERVAL": 15, # Minutes
        "AUTO_SAVE_PATH": f"ratea-data/auto_backup",
        "DEFAULT_FONT": "OpenSans",
        "START_DAY": "" # If none, will find the earliest tea date, else will use the date set here
    }
    global settings
    settings = default_settings
    global session
    session = {}
    # Get a list of all valid types for Categories
    setValidTypes()
    session["validFonts"] = ["OpenSans", "Roboto", "Merriweather", "Montserrat"]
    
    global TeaStash
    global TeaCache
    TeaStash = {}
    TeaCache = {}
    
    global TeaCategories
    TeaCategories = []


    global TeaReviewCategories
    TeaReviewCategories = []



    mainfilesExist, backupFilesExist = hasLoadableFiles()
    if mainfilesExist and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess("Main files found, loading main files")
        LoadAll()  # Load all data including settings, teas, categories, reviews, etc
    elif backupFilesExist and not DEBUG_ALWAYSNEWJSON:
        RichPrintError("Main files not found, loading backup files")
        LoadAll(settings["BACKUP_PATH"])  # Load all data including settings, teas, categories, reviews, etc
    else:
        RichPrintError("No files found. Please copy the files to the correct directory. Exiting.")
        exit(1)




    dataPath = f"{baseDir}/{settings['DIRECTORY']}"
    session["dataPath"] = dataPath
    hasDataDirectory = os.path.exists(dataPath)
    if hasDataDirectory and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found {settings['DIRECTORY']} at full path {os.path.abspath(settings['DIRECTORY'])}")
    else:
        RichPrintError(f"Could not find {settings['DIRECTORY']} at full path {os.path.abspath(settings['DIRECTORY'])}")
        MakeFilePath(dataPath)
        RichPrintInfo(f"Made {settings['DIRECTORY']} at full path {os.path.abspath(settings['DIRECTORY'])}")

    if len(TeaStash) == 0:
        RichPrintError("No teas found in stash! Potentially issue with loading teas. ")
    
    # Menu MUST be loaded before any font based calls, don't ask me why. Will Ref error if not
    UI_CreateViewPort_MenuBar()
    bindLoadFonts()
    bind_image_registry()  # Bind the image registry for the application


    Settings_SaveCurrentSettings()
    # Set the DearPyGui theme
        
        
    dpg.set_global_font_scale(settings["UI_SCALE"])

    # Start first welcome window
    Menu_Welcome(None, None, None)

    
    startStopBackupThread(settings["AUTO_SAVE"])
    # Start the backup thread
    dp.Viewport.title = "RaTea"
    dp.Viewport.width = monitor.width
    dp.Viewport.height = monitor.height
    # Move the viewport to the to top left corner
    dp.Viewport.x_pos = 0
    dp.Viewport.y_pos = 0

    timeEndLoad = dt.datetime.now(tz=dt.timezone.utc)
    timeDiff = timeEndLoad - timestartLoad
    timeDiffSeconds = timeDiff.total_seconds()
    RichPrintSuccess(f"Loaded RaTea in {timeDiffSeconds:.2f} seconds")
    print(f"Loaded RaTea in {timeDiffSeconds:.2f} seconds")

    dpg.set_exit_callback(on_exit_callback)

    dp.Runtime.start()


def on_exit_callback():
    print("Exiting...")
    # Strange errors with image pil and tkiner to surpress
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    startStopBackupThread(False)  # Stop the backup thread if running
    dp.Runtime.stop()

if __name__ == "__main__":
    main()