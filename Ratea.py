import csv
import datetime as dt
import json
import time
import pandas as pd
import uuid
import dearpypixl as dp
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import os
import re
from rich.console import Console as RichConsole
import screeninfo
import yaml
import threading
import pyperclip
import textwrap

# From local files
import RateaTexts

# Reminders
'''
Need for basic functionality: 
TODO: Features: Add in functionality for flags: isRequiredForTea, isRequiredForAll
TODO: Validation: Validate that name and other important fields are not empty
TODO: Features: Fill out or remove review tabs
TODO: Menus: Update settings menu with new settings
TODO: Files: Persistant windows in settings
TODO: fix monitor ui sizing
TODO: Export to google sheets readable format
TODO: Button to re-order reviews and teas based on current view
TODO: save table sort state
TODO: Sold: Support adjustment
TODO: Optional refresh on add tea/ review
TODO: Section off autocalculate functions, account for remaining=0 or naegative values
TODO: renumber review button
TODO: review window

Nice To Have:
TODO: Documentation: Add ? tooltips to everything
TODO: Customization: Add color themes
TODO: Feature: Some form of category migration
TODO: Code: Centralize tooltips and other large texts
TODO: Tables: Non-tea items, like teaware, shipping, etc.
TODO: Category: Write in description for each category role
TODO: Slider for textbox size for notepad, wrap too
TODO: Confirmation window for deleting tea/review
TODO: Terminal window to print out debug info
TODO: Grades support for scores
TODO: operation: Link reviews
TODO: Optional non-refreshing table updates, limit number of items on first load



Looking Forward:
TODO: Visualization: Single-review reports
TODO: Visualization: Single-tea reports
TODO: Documentation: Write in blog window
TODO: Documentation: Add Image Support to blog window.
TODO: Visualizeation: Pie chart for consumption of amount and types of tea, split over all, over years
TODO: Visualization: Solid fill line graph for consumption of types of tea over years
TODO: Summary: User preference visualization for types of tea, amount of tea, etc.
TODO: File: Import from CSV: Add in functionality to import from CSV
TODO: 2d array of stats by divisor (vendor, type, etc.)
TODO: Optional Override of autocalculated fields
TODO: Adjustments of quantities including sells and purchases and 'Done' status
TODO: Highlight when '0' flags are set
TODO: Highlight color customization
TODO: Make a clean default page for new users
TODO: Alternate calculation methods and a flag for that
TODO: Visualization: Network graph, word cloud, tier list


---Done---
Feat(0.5.8): Duplicate reviews button
Feat(0.5.8): Gift adjustment
Feat(0.5.8): Adjustment move tea index
Feat(0.5.8): Overhaul ui a bit with bigger fonts, refresh button
Feat(0.5.8): Calculate Start day and consumed/day
Feat(0.5.8): Added adjustments window for teas
Feat(0.5.7): Table filters by name search
Feat(0.5.7): Stopwatch, combine stop/start button
Feat(0.5.7): Stats: Volume, cost, weighted avrg stat
Feat(0.5.7): Auto-Resize tea and review table with frame callbacks
Feat(0.5.7): Put notes in tooltips when hovered
Feat(0.5.7): Resize monitor on creation
Feat(0.5.7): Rounding, dropdown size, prefix, postfix
Feat(0.5.7): Added price/gram and total score autocalcs
Feat(0.5.7): Notepad: Wrap text in notepad, add template for notepad
Feat(0.5.6): Validation: Add in a proper default folder for settings and data
Feat(0.5.6): Validation: Restrict categories to only if not already in use
Feat(0.5.6): Add some metrics relating to steeps and amount of tea
Feat(0.5.6): Code: Centralize tooltips and other large texts
Feat(0.5.6): Stats: Basic stats for tea and reviews, like average rating, total amount of tea, etc.
Feat(0.5.6): Files: Export To CSV
Feat(0.5.6): Fix bug with edit category, add some toolltips
Feat(0.5.6): Make dropdown widgets based on past inputs
Feat(0.5.6): Tables: Dynamic Sizing of columns based on content
Feat(0.5.6): Tables: Dynamic Sorting of columns based on content
'''


# ALL - All messages
# INFO - Informational messages that are not errors
# WARNING - Warning messages that may indicate a problem or alteration
# ERROR - Error messages that indicate a problem
# CRITICAL - Critical error messages that indicate a serious problem that may cause the program to crash
DEBUG_LEVEL = "ERROR"  # ALL, INFO, WARNING, ERROR, CRITICAL

#region Constants

# light green
COLOR_AUTOCALCULATED_TABLE_CELL = (0, 100, 0, 60)
# light red
COLOR_INVALID_EMPTY_TABLE_CELL = (100, 0, 0, 100)
# Red
COLOR_REQUIRED_TEXT = (255, 0, 0, 200)
# green
COLOR_AUTO_CALCULATED_TEXT = (0, 255, 0, 200)

CONSTANT_DELAY_MULTIPLIER = 125 # +1frame per X items for the table
#endregion

#region Global Variables
backupThread = False
backupStopEvent = threading.Event()
# Global variables


#region Helpers

richPrintConsole = RichConsole()

def MakeFilePath(path):
    # Make sure the folder exists
    if not os.path.exists(path):
        os.makedirs(path)
        RichPrintSuccess(f"Made {path} folder")
    else:
        RichPrintWarning(f"{path} folder already exists")
        
def WriteFile(path, content):
    with open(path, "w") as file:
        file.write(content)
    RichPrintSuccess(f"Written {path} to file")
    
def ReadFile(path):
    with open(path, "r") as file:
        RichPrintSuccess(f"Read {path} from file")
        return file.read()

def ListFiles(path):
    return os.listdir(path)

def WriteYaml(path, data):
    with open(path, "w") as file:
        yaml.dump(data, file)
    RichPrintSuccess(f"Written {path} to file")

def ReadYaml(path):
    with open(path, "r") as file:
        RichPrintSuccess(f"Read {path} from file")
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
        



def parseDTToStringWithFallback(stringOrDT, fallbackString):
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
        if not silent:
            RichPrintError(f"Failed to parse date string: {string}. No valid date found and no default provided.")
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
    return parseDTToStringWithFallback(datetime, fallbackString=fallbackString)
def AnyDTFormatToTimeStamp(unknownDT):
    # Convert any datetime format to timestamp
    if type(unknownDT) is dt.datetime:
        return DateTimeToTimeStamp(unknownDT)
    elif isinstance(unknownDT, str):
        return DateDictToTimeStamp(parseStringToDT(unknownDT))
    elif isinstance(unknownDT, dict):
        return DateDictToTimeStamp(DateDictToDT(unknownDT))
    elif isinstance(unknownDT, int) or isinstance(unknownDT, float):
        # If it's a timestamp, return it directly
        return int(unknownDT)
    else:
        raise ValueError("Invalid datetime format")
def StringToTimeStamp(string):
    # Convert string to timestamp
    dt = parseStringToDT(string)
    return DateTimeToTimeStamp(dt)




def RichPrint(text, color):
    richPrintConsole.print(text, style=color)

def RichPrintCritical(text):
    if DEBUG_LEVEL == "CRITICAL" or DEBUG_LEVEL == "WARNING" or DEBUG_LEVEL == "ERROR" or DEBUG_LEVEL == "CRITICAL" or DEBUG_LEVEL == "ALL" or DEBUG_LEVEL == "INFO":
        RichPrint(f"CRITICAL: {text}", "bold red")

def RichPrintError(text):
    if DEBUG_LEVEL == "ERROR" or DEBUG_LEVEL == "ALL" or DEBUG_LEVEL == "INFO" or DEBUG_LEVEL == "WARNING":
        RichPrint(text, "bold red")
def RichPrintInfo(text):
    if DEBUG_LEVEL == "INFO" or DEBUG_LEVEL == "ALL":
        RichPrint(text, "bold blue")
def RichPrintSuccess(text):
    if DEBUG_LEVEL == "INFO" or DEBUG_LEVEL == "ALL":
        RichPrint(text, "bold green")
def RichPrintWarning(text):
    if DEBUG_LEVEL == "WARNING" or DEBUG_LEVEL == "ALL" or DEBUG_LEVEL == "INFO":
        RichPrint(text, "bold yellow")
def RichPrintSeparator():
    if DEBUG_LEVEL == "INFO" or DEBUG_LEVEL == "ALL":
        RichPrint("--------------------------------------------------", "bold white")

def print_me(sender, data, user_data):
    print("Hello World")
    print(sender, data, user_data)

def Settings_SaveCurrentSettings():
    RichPrintSuccess("Saving settings")
    WriteYaml(session["settingsPath"], settings)

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
    #RichPrintInfo(f"Getting all entries of category {catName} by ID: {categoryID}, review={review}")
    
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


    #RichPrintSuccess(f"Found {len(returnList)} entries for category {catName} by ID: {categoryID}, name={catName}, role={catRole}, review={review}")
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

    RichPrintSuccess("Renumbering complete.")
    printTeasAndReviews()  # Print the updated teas and reviews for verification

    if save:
        # Save to file after renumbering
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])
        RichPrintSuccess("Saved renumbered teas and reviews to file.")

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
                parsed_date = StringToTimeStamp(item[1])
                if parsed_date:
                    return parsed_date.timestamp()
            except:
                # Fail silently as we know it isnt always a date
                return item[1]
        return item[1]
    
    unsortableItems = []
    cleanSortableItems = []
    # Remove N/A from the list
    if len(sortableItems) > 1:
        for i, item in enumerate(sortableItems):
            if item[1] == "N/A":
                unsortableItems.append(item)
            else:
                cleanSortableItems.append(item)
    cleanSortableItems.sort(key=sort_key, reverse=not ascending)
    RichPrintInfo(f"Found {len(cleanSortableItems)} sortable items and {len(unsortableItems)} unsortable items")
    if len(cleanSortableItems) < 2:
        RichPrintError("Not enough sortable items to sort")
        return
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
    RichPrintSuccess(f"Top {topX} answers for {categoryName} in {data}: {topAnswers}")
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
    dropdownMaxLength = 5


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
            # Requires: Amount to be set, Amount in reviews to be set
            validReviewsCategories, _ = getValidReviewCategoryRolesList()
            validCategories, _ = getValidCategoryRolesList()
            if "Amount" in validCategories and "Amount" in validReviewsCategories and "Amount" in data.attributes:
                RichPrintInfo("Calculating remaining")
                # Sum of all review Amounts in the tea (data)
                reviewAmount = 0
                for review in data.reviews:
                    if "Amount" in review.attributes:
                        reviewAmount += review.attributes["Amount"]

                # Get adjustments amount
                adjustmentsAmountTotal, adjustmentsGift, adjustmentsStandard = 0, 0, 0
                try:
                    adjustmentsStandard += data.adjustments["Standard"]
                    adjustmentsGift += data.adjustments["Gift"]
                except:
                    RichPrintWarning("No adjustments found, skipping")

                originalAmount = data.attributes["Amount"]
                # Remaining = Original Amount - Sum of all review Amounts
                remaining = originalAmount - reviewAmount - adjustmentsStandard - adjustmentsGift
                adjustmentsAmount = adjustmentsStandard + adjustmentsGift

                # Also check if finished
                finished = data.finished

                # Explanation
                if not finished:
                    explanation = f"{originalAmount:.2f}g Purchased\n- {reviewAmount:.2f}g Sum of all review Amounts\n- {adjustmentsStandard:.2f}g Standard Adjustments\n- {adjustmentsGift:.2f}g Gift Adjustments\n= {remaining:.2f}g Remaining"
                    if remaining < 0:
                        explanation += " (Overdrawn)"
                    elif remaining == 0:
                        explanation += " (Finished)"
                    else:
                        explanation += " (Not Finished)"
                    return remaining, explanation
                else:
                    explanation = f"{originalAmount:.2f}g Purchased\n- {reviewAmount:.2f}g Sum of all review Amounts\n- {adjustmentsStandard:.2f}g Standard Adjustments\n- {adjustmentsGift:.2f}g Gift Adjustments\n= {remaining:.2f}g Remaining (Finished)"
                    return remaining, explanation
                    return 0, explanation
            else:
                RichPrintError("Amount not found in categories, cannot calculate remaining")
                return None, None
        elif self.categoryRole == "Cost per Gram":
            # Requires: Cost to be set, Amount to be set
            validCategories, _ = getValidCategoryRolesList()
            if "Cost" in validCategories and "Amount" in data.attributes:
                RichPrintInfo("Calculating price per gram")
                # Price per gram = Cost / Amount
                cost = data.attributes["Cost"]
                amount = data.attributes["Amount"]
                pricePerGram = cost / amount
                # Explanation
                explanation = f"${cost:.2f} Cost\n/ {amount:.2f} Amount\n= ${pricePerGram:.2f} Price per gram"
                return pricePerGram, explanation
            else:
                RichPrintError("Cost or Amount not found in categories, cannot calculate price per gram")
                return None, None
        elif self.categoryRole == "Total Score":
            # Average of all review scores
            validReviewsCategories, _ = getValidReviewCategoryRolesList()
            if "Final Score" in validReviewsCategories:
                RichPrintInfo("Calculating total score")
                # Total score = Average of all review scores
                totalScore = 0
                for review in data.reviews:
                    if "Final Score" in review.attributes:
                        totalScore += review.attributes["Final Score"]
                # Divide by the number of reviews
                if len(data.reviews) == 0:
                    RichPrintWarning("No reviews found, cannot calculate total score")
                    return None, None
                

                avrgScore = totalScore / len(data.reviews)

                # Explanation
                explanation = f"{totalScore:.2f} Total Score\n/ {len(data.reviews)} Number of reviews\n= {avrgScore:.2f} Average Score"
                return avrgScore, explanation
            else:
                RichPrintError("Score not found in review categories, cannot calculate total score")
                return None, None
                    

# Themes for coloring
def create_cell_theme(color_rgba):
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvText):
            dpg.add_theme_color(dpg.mvThemeCol_Header, color_rgba, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 5, 5)
    return theme_id


#green_theme = create_cell_theme((100, 255, 100, 255))
#yellow_theme = create_cell_theme((255, 255, 100, 255))


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
    dropdownMaxLength = 5

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

#endregion

#region Window Classes
class WindowBase:
    tag = 0
    dpgWindow = None
    exclusive = False
    persist = False
    utitle = ""
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
        #dpg.add_item_resize_handler(callback=self.onResizedWindow, user_data=self.tag, parent=self.tag)
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
        RichPrintInfo(f"[REFRESH] Refreshing window tag: {self.tag} title: {self.title}")
        self.onRefresh()
        dpg.delete_item(self.tag)
        self.create()

    def onCreateFirstTime(self):
        # triggers when the window is created for the first time
        pass

    def onCreate(self):
        # triggers when the window is created
        pass
    def onRefresh(self):
        # triggers when the window is refreshed
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
                    #tooltipText = '''Timer for timing tea steeps. Copy times to clipboard with the clipboard button.
                    #\nPersist will save the timer between sessions (WIP)'''
                    dp.Text(tooltipText)

            # Group that contains an input text raw and a button to copy to clipboard
            with dp.Group(horizontal=True):
                dp.Button(label="Copy", callback=self.copyRawTimeToClipboard)
                width = 125 * settings["UI_SCALE"]
                self.rawDisplay = dp.InputText(default_value="Raw Times", readonly=True, callback=self.updateDefaultValueDisplay, width=width)
                

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
        #self.refresh()


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
        self.refresh()


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
    def ShowAddReview(self, sender, app_data, user_data):
        # Call Edit review with Add
        tea = user_data[0]
        operation = user_data[1]
        self.GenerateEditReviewWindow(sender, app_data, user_data=(None, operation, tea))  # Pass None for review to indicate new review
    def AddReview(self, sender, app_data, user_data):
        # Add a review to the tea
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
        self.refresh()

    def GenerateEditReviewWindow(self, sender, app_data, user_data):
        # Create a new window for editing the review
        w = 620 * settings["UI_SCALE"]
        h = 720 * settings["UI_SCALE"]
        
        editReviewWindowItems = dict()
        review = user_data[0]
        parentTea = user_data[2]
        operation = user_data[1]  # "edit" or "add"


        if operation != "edit":
            # Assume add, drop review data if provided
            review = None

        windowName = ""
        if operation == "edit":
            windowName = f"Edit Review {review.id} - {parentTea.name}"
        elif operation == "add":
            windowName = f"Add Review - {parentTea.name}"
        elif operation == "duplicate":
            # Get last review
            lastReview = parentTea.reviews[-1] if parentTea.reviews else None
            if lastReview is not None:
                review = Review(lastReview.id, lastReview.name, lastReview.dateAdded, lastReview.attributes.copy(), lastReview.rating)
                review.id = len(parentTea.reviews)  # New review ID is the length of existing reviews
                windowName = f"Duplicate Review {review.id} - {parentTea.name}"
            # Duplicate the review, but don't save it yet
            else:
                # Change operation to add if no last review
                operation = "add"
                windowName = f"Add Review (No reviews to duplicate) - {parentTea.name}"
           
           
            # Set the ID to the length of the existing reviews
            review.id = len(parentTea.reviews)  # New review ID is the length of existing reviews


        self.editReviewWindow = dp.Window(label=windowName, width=w, height=h, modal=True, show=True)
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
                        height = 180 * settings["UI_SCALE"]
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
        self.refresh()
            
    
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
                    print("Found parent tea")
                    print(parentTea.name)
                    break
            else:
            # If review is None, we are adding a new review, so set the parent tea to the current tea
                print("Parent tea not found, setting to current tea")
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
            RichPrintSuccess("Review edit/add passed validation.")
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
                    RichPrintSuccess(f"Teastash I is now {TeaStash[i]}, added new review: {newReview.name} with ID {newReview.id} to tea {teaId}")
                    break
        
        # Renumber and Save
        RichPrintSuccess(f"Added new review: {newReview.name} with ID {newReview.id} to tea {teaId}")

        # Save to file
        renumberTeasAndReviews(save=True)  # Renumber teas and reviews to keep IDs consistent
        #saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])

        # hide the popup
        dpg.configure_item(self.reviewsWindow.tag, show=False)
        self.deleteEditReviewWindow()
        # Refresh the window
        self.refresh()
        #self.parentWindow.refresh()
        # Close the edit review window
        if self.editReviewWindow is not None:
            self.editReviewWindow.delete()
            self.editReviewWindow = None

    def __init__(self, title, width, height, exclusive=False, parentWindow=None, tea=None):
        self.parentWindow = parentWindow
        self.tea = tea
        super().__init__(title, width, height, exclusive)

    def windowDefintion(self, window):
        tea = self.tea

        # Enable window resizing
        dpg.configure_item(window.tag, autosize=True)
        dpg.bind_item_font(window.tag, getFontName(1))
        # create a new window for the reviews
        with window:
            hbarActionGroup = dp.Group(horizontal=True)
            with hbarActionGroup:
                dp.Button(label="Add Review", callback=self.ShowAddReview, user_data=(tea, "add"))
                dp.Button(label="Duplicate Last Review", callback=self.ShowAddReview, user_data=(tea, "duplicate"))
                
                # Tooltip
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    tooltipText = RateaTexts.ListTextHelpMenu["menuTeaReviews"].wrap()
                    dp.Text(tooltipText)
                # Add a button to open the reviews window
                # Add review popup
                w = 900 * settings["UI_SCALE"]
                h = 500 * settings["UI_SCALE"]
                self.reviewsWindow = dp.Window(label="Reviews", width=w, height=h, show=False, modal=False)
                with self.reviewsWindow:
                    addReviewGroup = dp.Group(horizontal=False)
                    with addReviewGroup:
                        dp.Text("Add Review")
                        dp.Text("Attributes")
                        AttributesItem = dp.InputText(label="Attributes", default_value="{'Type': 'Raw Puerh', 'Region': 'Yunnan'}")
                        self.addReviewList.append(AttributesItem)
                        dp.Text("Rating")
                        RatingItem = dp.InputText(label="Rating", default_value="90")
                        self.addReviewList.append(RatingItem)
                        dp.Text("Notes")
                        notesItem = dp.InputText(label="Notes", default_value="Good tea")
                        self.addReviewList.append(notesItem)
                    # Add buttons
                    dp.Button(label="Add Review", callback=self.ShowAddReview, user_data=(tea, "add"))
                    dp.Button(label="Duplicate Last Review", callback=self.ShowAddReview, user_data=(tea, "duplicate"))
            dp.Separator()
            # Add a table with reviews
            _filter_table_id = dpg.generate_uuid()
            dpg.add_input_text(label="Filter Name (inc, -exc)", user_data=_filter_table_id, callback=lambda s, a, u: dpg.set_value(u, dpg.get_value(s)))
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
                # Add Edit button
                dp.TableColumn(label="Edit", no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True)
                # Add rows
                for i, review in enumerate(tea.reviews):
                    tableRow = dp.TableRow(filter_key=review.name)
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
                                    displayValue = displayValue = f"{displayValue:.{cat.rounding}f}"
                                # Prefix, suffix
                                displayValue = cat.prefix + str(displayValue) + cat.suffix
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
                        dp.Button(label="Edit", callback=self.GenerateEditReviewWindow, user_data=(review, "edit", self.tea))
        
        # disable autosize to prevent flickering or looping
        delay = 2 + statsNumTeas() // CONSTANT_DELAY_MULTIPLIER
        dpg.set_frame_callback(dpg.get_frame_count()+delay, self.afterWindowDefintion, user_data=window)

    def afterWindowDefintion(self, sender, app_data, user_data):
        RichPrintInfo(f"Finished window definition for {user_data.tag}")
        window = user_data
        dpg.configure_item(window, autosize=False)
        minHeight = 480 * settings["UI_SCALE"]
        estHeight = statsNumReviews() * 30 * settings["UI_SCALE"]
        maxHeight = 930 * settings["UI_SCALE"]

        height = min(max(estHeight, minHeight), maxHeight)
        dpg.set_item_height(window.tag, height)

    def deleteEditReviewWindow(self):
        # If window is open, close it first
        if self.editReviewWindow != None:
            self.editReviewWindow.delete()
            self.editReviewWindow = None
            self.addReviewList = list()
        else:
            print("No window to delete")

def Menu_Stash():
    w = 500 * settings["UI_SCALE"]
    h = 940 * settings["UI_SCALE"]
    stash = Window_Stash("Stash", w, h, exclusive=True)

class Window_Stash(WindowBase):
    addTeaList = dict()
    teasWindow = None
    adjustmentsWindow = None
    adjustmentsDict = dict()

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

    def windowDefintion(self, window):
        self.addTeaList = dict()
        self.addReviewList = dict()
        dpg.configure_item(window.tag, autosize=True)
        dpg.bind_item_font(window.tag, getFontName(1))
        with window:
            dp.Separator()
            hgroupButtons = dp.Group(horizontal=True)
            dpg.bind_item_font(dpg.last_item(), getFontName(2))
            with hgroupButtons:
                dp.Button(label="Add Tea", callback=self.ShowAddTea)
                dp.Button(label="Duplicate Last Tea", callback=self.ShowAddTea, user_data="duplicate")
                dp.Button(label="Import Tea", callback=self.importOneTeaFromClipboard)
                dp.Button(label="Import All (TODO)", callback=self.DummyCallback)
                dp.Button(label="Export One (TODO)", callback=self.DummyCallback)
                dp.Button(label="Export All (TODO)", callback=self.DummyCallback)
                dp.Button(label="Refresh", callback=self.refresh)
                

                # Tooltip for the buttons
                dp.Button(label="?")
                with dp.Tooltip(dpg.last_item()):
                    toolTipText = RateaTexts.ListTextHelpMenu["menuTeaStash"].wrap()
                    dp.Text(toolTipText)

            dp.Separator()

            # Table with collapsable rows for reviews
            _filter_table_id = dpg.generate_uuid()
            dpg.add_input_text(label="Filter Name (inc, -exc)", user_data=_filter_table_id, callback=lambda s, a, u: dpg.set_value(u, dpg.get_value(s)))
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
                

                # Add rows
                for i, tea in enumerate(TeaStash):
                    tableRow = dp.TableRow(filter_key=tea.name)
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
                            exp = None
                            if cat.isAutoCalculated:
                                val, exp = cat.autocalculate(tea)
                                if val is not None:
                                    displayValue = val
                                    if type(val) == float:
                                        displayValue = round(val, 3)
                                    usingAutocalculatedValue = True
                                    cellInvalidOrEmpty = False

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

                            if usingAutocalculatedValue:
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
        
        # disable autosize to prevent flickering or looping
        delay = 2 + statsNumTeas() // CONSTANT_DELAY_MULTIPLIER
        dpg.set_frame_callback(dpg.get_frame_count()+delay, self.afterWindowDefintion, user_data=window)


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
            saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])

            # Refresh the window
            self.refresh()
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
        self.teasWindow = dp.Window(label="Teas", width=w, height=h, show=True)
        dpg.bind_item_font(dpg.last_item(), getFontName(2))
        windowManager.addSubWindow(self.teasWindow)
        with self.teasWindow:
            if operation == "add":
                dp.Text(f"Add New Tea {idTea}")
            elif operation == "edit":
                dp.Text(f"Edit Tea {idTea}:\n{teasData.name if teasData else 'Unknown name'}")
            elif operation == "duplicate":
                if duplicateTea:
                    dp.Text(f"Duplicate Tea {idTea}:\n{teasData.name if teasData else 'Unknown name'}")
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
                        height = 150 * settings["UI_SCALE"]
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
                    catItem = dp.InputFloat(default_value=float(defaultValue), width=480 * settings["UI_SCALE"], step=1.0, format="%.2f")
                    if shouldShowDropdown:
                        # Create a dropdown with the past answers
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
            AllTypesCategoryRoleValid, AllTypesCategoryRole = getValidCategoryRolesList()
            allTypesCategoryRoleReviewsValid, allTypesCategoryRoleReviews = getValidReviewCategoryRolesList()
            if "Amount" in teaCurrent.attributes or "Remaining" in teaCurrent.attributes:

                # Get Amount and Remaining categories
                amountCategory = None
                for cat in TeaCategories:
                    if cat.categoryRole == "Amount":
                        amountCategory = cat
                        break
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
                # Add a checkbox to mark the tea as finished
                dp.Separator()
                finished = teaCurrent.finished
                finsihedCheckbox = dp.Checkbox(label="Finished", default_value=finished, callback=self.greyOutAdjustmentInput)                


                # Add a text input for the adjustment
                dp.Text("Adjustment:")
                adjustmentInput = dp.InputFloat(default_value=currentAdjustmentAmt, enabled=not finished, step=1.0, format="%.2f")

                self.addTeaList["Adjustment"] = adjustmentInput

                # Add userdata for the adjustment input to grey out
                finsihedCheckbox.user_data = (finished, teaCurrent, adjustmentInput, currentRemaining)

                # Add a button to confirm the adjustment
                dp.Separator()
                dp.Button(label="Confirm Adjustment", callback=self.UpdateAdjustmentAmt, user_data=(teaCurrent, adjustmentInput, finsihedCheckbox, "Standard"))

                # Adjust gift amount, adjustment that doesnt count towards consumption
                dp.Text("Gift Adjustment (Does not count towards consumption):")
                giftAdjustmentInput = dp.InputFloat(default_value=currentGiftAdjustmentAmt, step=1.0, format="%.2f")
                self.addTeaList["Gift Adjustment"] = giftAdjustmentInput
                # Add a button to confirm the gift adjustment
                dp.Button(label="Confirm Gift Adjustment", callback=self.UpdateAdjustmentAmt, user_data=(teaCurrent, giftAdjustmentInput, finsihedCheckbox, "Gift"))
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

            # Add a separator
            dp.Separator()
            dp.Text(f"TODO: Move to end, Move to Top, Move down 1, Move up 1")
            dp.Text(f"Migrate reviews to new tea index, TODO: Implement moving reviews in stash)")
            dp.Text(f"TODO: Merge teas of two indexes into one, combining reviews as well, delete the other tea")
            dpg.bind_item_font(dpg.last_item(), getFontName(1, bold=False))

            # Add a button to cancel the adjustment
            dp.Button(label="Cancel", callback=self.deleteAdjustmentsWindow)

    def moveTeaIndex(self, sender, app_data, user_data):
        # Move tea index to the index below the specified index
        # user_data[0] is the moveInput, user_data[1] is the tea object
        # Factor in renumbering and saving the tea stash
        moveInput = user_data[0]
        tea = user_data[1]
        newIndex = moveInput.get_value()
        currentIndex = tea.id


        # DEBUG print
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
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])
        RichPrintSuccess(f"Moved tea {tea.name} to index {newIndex} from current index {currentIndex}, renumbered stash.")
        # Refresh the window
        self.deleteAdjustmentsWindow()
        self.refresh()

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
        try:
            adjustment = float(adjustment)
        except ValueError:
            RichPrintError("Error: Adjustment is not a valid number.")
            return
        # Modify the TeaStash object
        teaStashObj = None
        for i, teaStash in enumerate(TeaStash):
            if teaStash.id == tea.id:
                teaStashObj = teaStash
                break
        if teaStashObj is None:
            RichPrintError("Error: Tea not found in stash.")
            return
                
        # Update the adjustment amount
        teaStashObj.adjustments[typeOfAdjustment] = round(adjustment, 2)
        teaStashObj.finished = finished
        # Save the tea stash to file
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])

        # Refresh the window
        self.deleteAdjustmentsWindow()
        self.refresh()
                   
                    


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
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])
        
        # hide the popup
        dpg.configure_item(self.teasWindow.tag, show=False)
        self.refresh()


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
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])

        # hide the popup
        dpg.configure_item(self.teasWindow.tag, show=False)
        self.deleteTeasWindow()
        self.refresh()

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
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])

        # Refresh the window to reflect the deletion
        self.refresh()
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
    def copyNotepad(self, sender, data):
        pyperclip.copy(self.text)
    def updatePersist(self, sender, data):
        self.persist = data
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

    def exportYML(self):
        windowVars = {
            "text": self.text,
            "width": self.width,
            "height": self.height
        }
        return windowVars
    
    def importYML(self, data):
        self.text = data["text"]
        self.width = data["width"]
        self.height = data["height"]
        self.textInput.set_value(self.text)

        # Update size
        self.dpgWindow.width = self.width
        self.dpgWindow.height = self.height



# Stats functions

# Get Start day will use the start day from the settings, or default the earliest date it can find
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

# Get total Purchase volume of all teas in the stash
def statsTotalVolume():
    # Guard if no attributes are present
    validCategories, _  = getValidCategoryRolesList()
    if "Amount" not in validCategories:
        RichPrintError("Error: No 'Amount' attribute found in Tea Categories.")
        return 0, 0
    numTeas = statsNumTeas()
    totalVolume = 0
    for tea in TeaStash:
        if "Amount" in tea.attributes:
            totalVolume += tea.attributes["Amount"]
    if numTeas > 0:
        averageVolume = totalVolume / numTeas
    else:
        averageVolume = 0
    
    return totalVolume, averageVolume

# Get the total cost of all teas in the stash
def statsTotalAverageCost():
    # Guard if no attributes are present
    validCategories, _  = getValidCategoryRolesList()
    if "Cost" not in validCategories:
        RichPrintError("Error: No 'Cost' attribute found in Tea Categories.")
        return 0, 0
    numTeas = statsNumTeas()
    totalCost = 0
    for tea in TeaStash:
        if "Cost" in tea.attributes:
            totalCost += tea.attributes["Cost"]
    if numTeas > 0:
        averageCost = totalCost / numTeas
    
    return totalCost, averageCost

# Get the weighted average cost of all teas in the stash
def statsWeightedAverageCost():
    # Guard if no attributes are present
    validCategories, _ = getValidCategoryRolesList()
    if "Cost" not in validCategories or "Amount" not in validCategories:
        RichPrintError("Error: No 'Cost' or 'Amount' attribute found in Tea Categories.")
        return 0, 0
    
    totalVol, _ = statsTotalVolume()
    totalCost = statsTotalAverageCost()[0]
    if totalVol > 0:
        weightedAverageCost = totalCost / totalVol
    else:
        weightedAverageCost = 0
    return weightedAverageCost

# Get total consumed by summing all reviews, adjustments, and finished teas
def statsTotalConsumed():
    # Guard if no attributes are present
    validCategories, _ = getValidCategoryRolesList()
    if "Remaining" not in validCategories:
        RichPrintError("Error: No 'Amount' attribute found in Tea Categories.")
        return 0, 0
    
    numTeas = statsNumTeas()
    totalConsumed = 0
    for tea in TeaStash:
        if not tea.finished:
            # If the tea is not finished, add the amount from the reviews
            for review in tea.reviews:
                if "Amount" in review.attributes:
                    totalConsumed += review.attributes["Amount"]
            # Add the adjustments
            if "Standard" in tea.adjustments:
                totalConsumed += tea.adjustments["Standard"]
        else:
            # Directly add total purchase volume
            if "Amount" in tea.attributes:
                totalConsumed += tea.attributes["Amount"]
    if numTeas > 0:
        averageConsumed = totalConsumed / numTeas
    else:
        averageConsumed = 0
    
    return totalConsumed, averageConsumed

# Get total consumed, excluding adjustments
def statsTotalConsumedExcludingGiftAdj():
    # Guard if no attributes are present
    validCategories, _ = getValidCategoryRolesList()
    if "Remaining" not in validCategories:
        RichPrintError("Error: No 'Amount' attribute found in Tea Categories.")
        return 0, 0
    
    numTeas = statsNumTeas()
    totalConsumed = 0
    for tea in TeaStash:
        if not tea.finished:
            # If the tea is not finished, add the amount from the reviews
            for review in tea.reviews:
                if "Amount" in review.attributes:
                    totalConsumed += review.attributes["Amount"]
        else:
            # Directly add total purchase volume
            if "Amount" in tea.attributes:
                totalConsumed += tea.attributes["Amount"]

        # Add the adjustments, but only the standard ones
        if "Standard" in tea.adjustments:
            totalConsumed += tea.adjustments["Standard"]

        # Less Gift adjustments, assuming they are not part of the consumed amount
        if "Gift" in tea.adjustments:
            totalConsumed -= tea.adjustments["Gift"]
    if numTeas > 0:
        averageConsumed = totalConsumed / numTeas
    else:
        averageConsumed = 0
    
    return totalConsumed, averageConsumed

# Get total consumed by summing all reviews, adjustments, and finished teas
def statsTotalConsumedExcludingAdj():
    # Guard if no attributes are present
    validCategories, _ = getValidCategoryRolesList()
    if "Remaining" not in validCategories:
        RichPrintError("Error: No 'Amount' attribute found in Tea Categories.")
        return 0, 0
    
    numTeas = statsNumTeas()
    totalConsumed = 0
    for tea in TeaStash:
        if not tea.finished:
            # If the tea is not finished, add the amount from the reviews
            for review in tea.reviews:
                if "Amount" in review.attributes:
                    totalConsumed += review.attributes["Amount"]
        else:
            # Directly add total purchase volume
            if "Amount" in tea.attributes:
                totalConsumed += tea.attributes["Amount"]
    if numTeas > 0:
        averageConsumed = totalConsumed / numTeas
    else:
        averageConsumed = 0
    
    return totalConsumed, averageConsumed

def statsAllStandardAdjustmentsSum():
    # Guard if no attributes are present
    validCategories, _ = getValidCategoryRolesList()
    if "Remaining" not in validCategories:
        RichPrintError("Error: No 'Amount' attribute found in Tea Categories.")
        return 0, 0
    
    numTeas = statsNumTeas()
    totalStandardAdjustments = 0
    for tea in TeaStash:
        if "Standard" in tea.adjustments:
            totalStandardAdjustments += tea.adjustments["Standard"]
    
    if numTeas > 0:
        averageStandardAdjustments = totalStandardAdjustments / numTeas
    else:
        averageStandardAdjustments = 0
    
    return totalStandardAdjustments, averageStandardAdjustments

def statsAllGiftAdjustmentsSum():
    # Guard if no attributes are present
    validCategories, _ = getValidCategoryRolesList()
    if "Remaining" not in validCategories:
        RichPrintError("Error: No 'Amount' attribute found in Tea Categories.")
        return 0, 0
    
    numTeas = statsNumTeas()
    totalGiftAdjustments = 0
    for tea in TeaStash:
        if "Gift" in tea.adjustments:
            totalGiftAdjustments += tea.adjustments["Gift"]
    
    if numTeas > 0:
        averageGiftAdjustments = totalGiftAdjustments / numTeas
    else:
        averageGiftAdjustments = 0
    
    return totalGiftAdjustments, averageGiftAdjustments

# Get total remaining by summing all remaining amounts after applying autocalculations
def statsTotalRemaining():
    # Guard if no attributes are present
    validCategories, _ = getValidCategoryRolesList()
    if "Remaining" not in validCategories:
        RichPrintError("Error: No 'Remaining' attribute found in Tea Categories.")
        return 0, 0
    
    numTeas = statsNumTeas()
    totalRemaining = 0

    remainingCategory = None
    for cat in TeaCategories:
        cat: TeaCategory
        if cat.categoryRole == "Remaining":
            remainingCategory = cat
            break
    
    for tea in TeaStash:
        tea: StashedTea
        currentRemaining, exp = remainingCategory.autocalculate(tea)
        if currentRemaining is None:
            currentRemaining = 0.0
        totalRemaining += currentRemaining

    # Calculate the average remaining
    if numTeas > 0:
        averageRemaining = totalRemaining / numTeas
    else:
        averageRemaining = 0
    
    return totalRemaining, averageRemaining


def Menu_Stats():
    w = 540 * settings["UI_SCALE"]
    h = 720 * settings["UI_SCALE"]
    stats = Window_Stats("Stats", w, h, exclusive=True)

class Window_Stats(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("Stats")

            # Divider
            dp.Separator()
            # Tea Stats
            dp.Text("Tea Stats")
            numTeas = statsNumTeas()
            dp.Text(f"Number of Teas: {numTeas}")
            numReviews = statsNumReviews()
            dp.Text(f"Number of Reviews: {numReviews}")
            dp.Separator()

            # All stats should only be displayed if the coorsponding category is enabled
            AllTypesCategoryRoleValid, AllTypesCategoryRole = getValidCategoryRolesList()
            allTypesCategoryRoleReviewsValid, allTypesCategoryRoleReviews = getValidReviewCategoryRolesList()


            # Display enabled categories
            dp.Text("Tea Categories:")
            # Foldable tab
            with dp.CollapsingHeader(label="Enabled Categories", default_open=False):
                for cat in AllTypesCategoryRole:
                    if cat in AllTypesCategoryRoleValid:
                        dp.Text(f"{cat}")
                    else:
                        dp.Text(f"{cat} - Not Enabled")

            dp.Separator()
            dp.Text("Review Categories:")
            with dp.CollapsingHeader(label="Enabled Review Categories", default_open=False):
                for cat in allTypesCategoryRoleReviews:
                    if cat in allTypesCategoryRoleReviewsValid:
                        dp.Text(f"{cat}")
                    else:
                        dp.Text(f"{cat} - Not Enabled")

                dp.Separator()

            

            if "Type" in AllTypesCategoryRoleValid:
                # Tea Type Stats
                dp.Text("Tea Type Stats")
                teaTypeStats = {}
                with dp.CollapsingHeader(label="Tea Type Stats", default_open=False):
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

            dp.Text("Review Type Stats")
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

            # Total volume of consumed tea (Review-remaining-stats)
            dp.Text("Total Volume of Consumed Tea")
            if "Amount" in allTypesCategoryRoleReviewsValid:
                sum, avrg, count, unique, _ = getStatsOnCategoryByRole("Amount", True)
                dp.Text(f"Sum: {sum}g, Average: {avrg}g, Count: {count} Count")
            else:
                dp.Text("Required Category role 'Amount' for Review is not enabled.")
            dp.Separator()

            # Total steeps (Review-steep-count-stats)
            dp.Text("Total Steeps")
            if "Steeps" in allTypesCategoryRoleReviewsValid:
                sum, avrg, count, unique, _ = getStatsOnCategoryByRole("Steeps", True)
                dp.Text(f"Sum: {sum} steeps, Average: {avrg} steeps, Count: {count}")
            else:
                dp.Text("Required Category role 'Steeps' for Review is not enabled.")
            dp.Separator()

            # Teaware size (Reviews-Vessel Size-stats)
            dp.Text("Teaware Size by Review")
            if "Vessel size" in allTypesCategoryRoleReviewsValid:
                sum, avrg, count, unique, uniqueDict = getStatsOnCategoryByRole("Vessel size", True)
                dp.Text(f"Sum: {sum}ml, Average: {avrg}ml, Count: {count}")

                dp.Text("Unique Sizes by Review:")
                for size, count in uniqueDict.items():
                    dp.Text(f"{size}: {count}")

            else:
                dp.Text("Required Category role 'Vessel size' for Review is not enabled.")
            dp.Separator()

            # Total volume Purchased, total cost, and weighted average cost
            if "Cost" in AllTypesCategoryRoleValid and "Amount" in AllTypesCategoryRoleValid:
                dp.Text("Total Volume and Cost")
                totalVolume, averageVolume = statsTotalVolume()
                dp.Text(f"Total Volume: {totalVolume:.2f}g, Average Volume: {averageVolume:.2f}g")
                totalCost, averageCost = statsTotalAverageCost()
                dp.Text(f"Total Cost: ${totalCost:.2f}, Average Cost: ${averageCost:.2f}")
                weightedAverageCost = statsWeightedAverageCost()
                dp.Text(f"Weighted Average Cost: ${weightedAverageCost:.2f}")
            else:
                dp.Text("Required Category role 'Cost' or 'Amount' for Tea is not enabled.")

            dp.Separator()
            # Total consumed by summing all reviews, adjustments, and finished teas
            dp.Text("Total Consumed Including Adjustments")
            if "Amount" in AllTypesCategoryRoleValid:
                totalConsumed, averageConsumed = statsTotalConsumed()
                dp.Text(f"Total Consumed: {totalConsumed:.2f}g, Average Consumed per tea: {averageConsumed:.2f}g")
            else:
                dp.Text("Required Category role 'Amount' for Tea is not enabled.")
            dp.Separator()

            # Total consumed excluding Gift adjustments
            dp.Text("Total Consumed Excluding Gift Adjustments")
            if "Amount" in AllTypesCategoryRoleValid:
                totalConsumedExclAdj, averageConsumedExclAdj = statsTotalConsumedExcludingGiftAdj()
                dp.Text(f"Total Consumed Excluding Gift Adjustments: {totalConsumedExclAdj:.2f}g, Average Consumed per tea: {averageConsumedExclAdj:.2f}g")
            else:
                dp.Text("Required Category role 'Amount' for Tea is not enabled.")
            dp.Separator()

            # Total consumed excluding all adjustments
            dp.Text("Total Consumed Excluding All Adjustments")
            if "Amount" in AllTypesCategoryRoleValid:
                totalConsumedExclAdj, averageConsumedExclAdj = statsTotalConsumedExcludingAdj()
                dp.Text(f"Total Consumed Excluding All Adjustments: {totalConsumedExclAdj:.2f}g, Average Consumed per tea: {averageConsumedExclAdj:.2f}g")
            else:
                dp.Text("Required Category role 'Amount' for Tea is not enabled.")
            dp.Separator()

            # Total standard adjustments, Total gift adjustments
            dp.Text("Total Standard Adjustments")
            totalStandardAdjustments, averageStandardAdjustments = statsAllStandardAdjustmentsSum()
            dp.Text(f"Total Standard Adjustments: {totalStandardAdjustments:.2f}g, Average Standard Adjustments per tea: {averageStandardAdjustments:.2f}g")

            dp.Separator()
            dp.Text("Total Gift Adjustments")
            totalGiftAdjustments, averageGiftAdjustments = statsAllGiftAdjustmentsSum()
            dp.Text(f"Total Gift Adjustments: {totalGiftAdjustments:.2f}g, Average Gift Adjustments per tea: {averageGiftAdjustments:.2f}g")

            dp.Separator()

            # Total remaining by summing all remaining amounts after applying autocalculations
            dp.Text("Total Remaining")
            if "Remaining" in AllTypesCategoryRoleValid:
                totalRemaining, averageRemaining = statsTotalRemaining()
                dp.Text(f"Total Remaining: {totalRemaining:.2f}g, Average Remaining per tea: {averageRemaining:.2f}g")
            else:
                dp.Text("Required Category role 'Remaining' for Tea is not enabled.")



            dp.Separator()
            # Start day
            dp.Text("Start Day")
            startDay = statsgetStartDayTimestamp()
            dp.Text(f"Start Day (First recorded date): {dt.datetime.fromtimestamp(startDay, tz=dt.timezone.utc).strftime(settings['DATE_FORMAT'])}")
            today = dt.datetime.now(tz=dt.timezone.utc).timestamp()
            numDays = (today - startDay) / (24 * 60 * 60)
            dp.Text(f"Number of Days since Start Day: {numDays:.2f} days")
            dp.Separator()

            # Grams of tea consumed per day
            dp.Text("Grams of Tea Consumed per Day")
            if "Amount" in AllTypesCategoryRoleValid:
                totalConsumed, averageConsumed = statsTotalConsumed()
                if numDays > 0:
                    gramsPerDay = totalConsumed / numDays
                    dp.Text(f"Total Consumed: {totalConsumed:.2f}g, Average Consumed per day: {gramsPerDay:.2f}g")
                else:
                    dp.Text("No valid start day or no teas consumed.")
            else:
                dp.Text("Required Category role 'Amount' for Tea is not enabled.")



        
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
        self.refresh()
        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
    def moveItemDownCategory(self, sender, app_data, user_data):
        TeaCategories[user_data], TeaCategories[user_data + 1] = TeaCategories[user_data + 1], TeaCategories[user_data]
        # Refresh the window
        self.refresh()
        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])

    def moveItemUpReviewCategory(self, sender, app_data, user_data):
        TeaReviewCategories[user_data], TeaReviewCategories[user_data - 1] = TeaReviewCategories[user_data - 1], TeaReviewCategories[user_data]
        # Refresh the window
        self.refresh()
        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
    def moveItemDownReviewCategory(self, sender, app_data, user_data):
        TeaReviewCategories[user_data], TeaReviewCategories[user_data + 1] = TeaReviewCategories[user_data + 1], TeaReviewCategories[user_data]
        # Refresh the window
        self.refresh()
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
            maxItemsItem = dp.SliderInt(default_value=5, min_value=3, max_value=20, format="%d")
            addCategoryWindowItems["maxItems"] = maxItemsItem


                
            
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
            maxItemsItem = dp.SliderInt(default_value=5, min_value=3, max_value=20, format="%d")
            addReviewCategoryWindowItems["maxItems"] = maxItemsItem
            
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

        
        TeaReviewCategories.append(newCategory)

        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
        
        # close the popup
        self.refresh()
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
            maxItemsItem = dp.SliderInt(label="Max Items", default_value=int(category.dropdownMaxLength), min_value=3, max_value=20, format="%d")
            editCategoryWindowItems["maxItems"] = maxItemsItem


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
        print(f"{category.__dict__}")

        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
        # close the popup
        self.refresh()
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
            maxItemsItem = dp.SliderInt(default_value=int(category.dropdownMaxLength), min_value=3, max_value=20, format="%d")
            editReviewCategoryWindowItems["maxItems"] = maxItemsItem

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


        RichPrintInfo(f"Editing review category: {category.name} ({category.categoryType}, Flags: {category.isRequiredForAll}, {category.isRequiredForTea}, {category.isAutoCalculated}, {category.isDropdown})")
        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
        # close the popup
        self.refresh()
        dpg.delete_item(user_data[2])


        
    def deleteCategory(self, sender, app_data, user_data):
        print(f"Delete Category - {user_data}")
        # Delete the category
        TeaCategories.pop(user_data)
        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
        
        # Refresh the window
        self.refresh()

    def deleteReviewCategory(self, sender, app_data, user_data):
        nameOfCategory = TeaReviewCategories[user_data].name
        # Delete the category
        TeaReviewCategories.pop(user_data)
        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])

        RichPrintSuccess(f"Deleted {nameOfCategory} category")
        
        # Refresh the window
        self.refresh()

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

        # Log
        RichPrintInfo(f"Adding category: {newCategory.name} ({newCategory.categoryType}, Flags: {newCategory.isRequiredForAll}, {newCategory.isRequiredForTea}, {newCategory.isAutoCalculated}, {newCategory.isDropdown})")

        # Add the new category to the list
        TeaCategories.append(newCategory)
        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
       
        # close the popup
        self.refresh()
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
            dp.Text(f"This is a simple tea stash manager (V{settings["APP_VERSION"]}) to keep track of your teas and reviews.")
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
            dp.Text("This is a simple user guide for Ratea.")
            dp.Text("You can find more information on the GitHub page:")

# Terminal window
def Menu_Terminal():
    w = 640 * settings["UI_SCALE"]
    h = 480 * settings["UI_SCALE"]
    terminal = Window_Terminal("Terminal", w, h, exclusive=True)

class Window_Terminal(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("Terminal")
            dp.Text("Terminal goes here")
            # Add a text input box
            textInput = dp.InputText(label="Input", default_value="", multiline=True, width=600 * settings["UI_SCALE"], height=400 * settings["UI_SCALE"])
            # Add a button to clear the terminal
            dp.Button(label="Clear", callback=self.clearTerminal)

    def clearTerminal(self, sender, app_data):
        print("Clearing terminal")
        pass


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
            RichPrintSuccess(f"Path {filePath} created")
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
    SaveAll(backupPath)
    RichPrintSuccess(f"Backup generated at {backupPath}")

def saveTeasReviews(stash, path):
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

    WriteYaml(path, allData)

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
            "maxItems": int(category.dropdownMaxLength)
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
    SaveAll()

def saveTeaReviewCategories(categories, path):
    # Save as one file in yml format
    allData = []
    for category in categories:
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
            "maxItems": int(category.dropdownMaxLength)
        }
        allData.append(categoryData)

    WriteYaml(path, allData)

def SaveAll(altPath=None):
    # ignore sender and app_data
    if type(altPath) != str and altPath is not None:
        altPath = None
    # Save all data
    if altPath is not None:
        # This is a backup path, so save to the backup path
        newBaseDirectory = altPath
        saveTeasReviews(TeaStash, f"{newBaseDirectory}/tea_reviews.yml")
        saveTeaCategories(TeaCategories, f"{newBaseDirectory}/tea_categories.yml")
        saveTeaReviewCategories(TeaReviewCategories, f"{newBaseDirectory}/tea_review_categories.yml")
        WriteYaml(f"{newBaseDirectory}/user_settings.yml", settings)
        windowManager.exportPersistantWindows(f"{newBaseDirectory}/persistant_windows.yml")
        RichPrintSuccess(f"All data saved to {newBaseDirectory}")

        # CSVs
        teaStashToCSV(f"{newBaseDirectory}/tea.csv", f"{newBaseDirectory}/review.csv")
        return
    saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])
    saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
    saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
    WriteYaml(session["settingsPath"], settings)
    windowManager.exportPersistantWindows(settings["PERSISTANT_WINDOWS_PATH"])

    # CSVs
    teaStashToCSV(settings["CSV_OUTPUT_TEA_PATH"], settings["CSV_OUTPUT_REVIEW_PATH"])


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
            SaveAll(autoBackupPath)
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
    categoriesPath = f"{baseDir}/{settings["TEA_CATEGORIES_PATH"]}"
    teaReviewCategoriesPath = f"{baseDir}/{settings["TEA_REVIEW_CATEGORIES_PATH"]}"
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
                parsed_date = parseStringToDT(value)
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
            dp.MenuItem(label="Stats(WIP)", callback=Menu_Stats)
            dp.MenuItem(label="Summary(WIP)", callback=Menu_Summary)
            with dp.Menu(label="Graphs(TODO)"):
                dp.MenuItem(label="Graph 1(TODO)", callback=print_me)
                dp.MenuItem(label="Graph 2(TODO)", callback=print_me)
        with dp.Menu(label="Tools"):
            dp.MenuItem(label="Timer", callback=Menu_Timer)
            dp.MenuItem(label="Notepad", callback=Menu_Notepad)
            dp.Button(label="Settings", callback=Menu_Settings)
        with dp.Menu(label="Windows"):
            dp.Button(label="Sort Windows", callback=windowManager.sortWindows)
            dp.Button(label="Import Persistant Windows", callback=windowManager.importPersistantWindowWrapper)
            dp.Button(label="Export Persistant Windows", callback=windowManager.exportPersistantWindowWrapper)
        with dp.Menu(label="Help(TODO)", callback=print_me):
            dp.Button(label="User Guide", callback=Menu_UserGuide)
            dp.Button(label="About", callback=print_me)
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
        "APP_VERSION": "0.5.8", # Updates to most recently loaded
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




    dataPath = f"{baseDir}/{settings["DIRECTORY"]}"
    session["dataPath"] = dataPath
    hasDataDirectory = os.path.exists(dataPath)
    if hasDataDirectory and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
    else:
        RichPrintError(f"Could not find {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
        MakeFilePath(dataPath)
        RichPrintInfo(f"Made {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")

    if len(TeaStash) == 0:
        RichPrintError("No teas found in stash! Potentially issue with loading teas. ")
    
    # Menu MUST be loaded before any font based calls, don't ask me why. Will Ref error if not
    UI_CreateViewPort_MenuBar()
    bindLoadFonts()


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

    dp.Runtime.start()




if __name__ == "__main__":
    main()
