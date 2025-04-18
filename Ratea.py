import datetime as dt
import json
import time
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

# Reminders
'''
Need for basic functionality: 
TODO: Features: Make dropdown widgets based on past inputs
TODO: Stats: Add basic stats and metrics based on remaining tea and reviews
TODO: Features: Add in functionality for flags: isAutoCalculated, isRequiredForTea, isRequiredForAll, isDropdown
TODO: Features: Calculated fields for teas and reviews
TODO: Validation: Validate that name and other important fields are not empty
TODO: Features: Fill out or remove review tabs
TODO: Menus: Update settings menu with new settings
TODO: Category: Correction for amount of tea, and amount of tea consumed/marker for finished tea
TODO: Feature: Import/Export To CSV


Nice To Have:
TODO: Validation: Restrict categories to only if not already in use
TODO: Documentation: Write in blog window
TODO: Documentation: Add Image Support to blog window.
TODO: Documentation: Add ? button to everything
TODO: Customization: Add color themes
TODO: Feature: Some form of category migration
TODO: Code: Centralize tooltips and other large texts
TODO: Stats: Basic stats for tea and reviews, like average rating, total amount of tea, etc.
TODO: Visualizeation: Pie chart for consumption of amount and types of tea, split over all, over years
TODO: Visualization: Solid fill line graph for consumption of types of tea over years
TODO: Tables: Non-tea items, like teaware, shipping, etc.
TODO: Category: Write in description for each category role











---Done---
Fix(0.5.6): Fix: Remove Year from teas and reviews, use dateAdded instead
Feat(0.5.6): Tables: Dynamic Sizing of columns based on content
Feat(0.5.6): Tables: Dynamic Sorting of columns based on content
'''


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


def parseDTToStringWithFallback(stringOrDT, fallbackString):
    output = None
    try:
        output = parseDTToString(stringOrDT)
    except:
        # If it fails, return the fallback string
        output = fallbackString
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
    format = settings["DATE_FORMAT"] + " %H:%M"
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

def parseStringToDT(string, default=None, format=None):
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
    return False  # Return False if no valid date found and no default provided
    


def DTToDateDict(dt):
    # Convert datetime to date dict
    # convert year to 2 digits
    year = dt.year
    if year > 1900:
        year = year - 1900
    return {
        'month_day': dt.day,
        'year': year,
        'month': dt.month,
    }
    
def DateDictToDT(dateDict):
    # Convert date dict to datetime
    year = dateDict['year']
    if year < 1900:
        year += 1900  # Convert 2-digit year to 4-digit year
    return dt.datetime(year, dateDict['month']+1, dateDict['month_day'])

def RichPrint(text, color):
    richPrintConsole.print(text, style=color)

def RichPrintError(text):
    RichPrint(text, "bold red")
def RichPrintInfo(text):
    RichPrint(text, "bold blue")
def RichPrintSuccess(text):
    RichPrint(text, "bold green")
def RichPrintWarning(text):
    RichPrint(text, "bold yellow")
def RichPrintSeparator():
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

def debugGetcategoryRole():
    allroleCategories = []
    for k, v in session["validroleCategory"].items():
        for i, cat in enumerate(v):
            allroleCategories.append(cat)

    # Dedup and remove UNUSED
    allroleCategories = list(set(allroleCategories))
    allroleCategories.remove("UNUSED")


    print(f"All role Categories: {allroleCategories}")
    for i, cat in enumerate(allroleCategories):
        hasCoorespondingCategory = getCategoryIDByrole(cat)
        if hasCoorespondingCategory == -1:
            print(f"Category {cat} does not have a cooresponding category")
        else:
            print(f"Category {cat} has a cooresponding category {hasCoorespondingCategory} of name {TeaCategories[hasCoorespondingCategory].name}")

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
    
    print(f"All role Categories: {allroleCategories}")
    for i, cat in enumerate(allroleCategories):
        hasCoorespondingCategory = getReviewCategoryIDByrole(cat)
        if hasCoorespondingCategory == -1:
            print(f"Category {cat} does not have a cooresponding category")
        else:
            print(f"Category {cat} has a cooresponding category {hasCoorespondingCategory} of name {TeaReviewCategories[hasCoorespondingCategory].name}")

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
                                "int": ["UNUSED", "Total Score", "Year", "Amount", "Remaining"],
                                "float": ["UNUSED", "Total Score", "Amount", "Remaining"],
                                "bool": ["UNUSED", "bool"],
                                "date": ["UNUSED", "date"],
                                "datetime": ["UNUSED", "date"]}
    
    session["validroleReviewCategory"] = {"string": ["UNUSED", "Notes (short)", "Notes (Long)", "Name", "Vendor", "Type"],
                                "int": ["UNUSED", "Score", "Final Score", "Year", "Amount"],
                                "float": ["UNUSED", "Score", "Final Score", "Amount"],
                                "bool": ["UNUSED", "bool"],
                                "date": ["UNUSED", "date"],
                                "datetime": ["UNUSED", "date"]}
    

def _table_sort_callback(sender, sortSpec):
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
        return item[1]
    sortableItems.sort(key=sort_key, reverse=not ascending)
    sorted_rows = [item[0] for item in sortableItems]
    # Reorder rows
    dpg.reorder_items(sender, 1, sorted_rows)
    RichPrintSuccess(f"Sorted table by column {column_index} in {'ascending' if ascending else 'descending'} order")



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
    def __init__(self, id, name, dateAdded=None, attributes={}):
        self.id = id
        self.name = name
        if dateAdded is None:
            dateAdded = dt.datetime.now(tz=dt.timezone.utc)
        self.dateAdded = dateAdded
        self.attributes = attributes
        self.reviews = []
        self.calculated = {}

    def addReview(self, review):
        self.reviews.append(review)
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
    finalScore = 0
    def __init__(self, id, name, dateAdded, attributes, rating):
        self.id = id
        self.name = name
        if dateAdded is None:
            dateAdded = dt.datetime.now(tz=dt.timezone.utc)
        self.dateAdded = dateAdded
        self.attributes = attributes
        self.rating = rating
        self.calculated = {}
        self.finalScore = 0
    def calculate(self):
        # call all the calculate functions
        self.calculateFinalScore()
    def calculateFinalScore(self):
        # calculate the final score
        self.finalScore = self.rating


class TeaCategory:
    name = ""
    categoryType = ""
    color = ""
    defaultValue = None
    widthPixels = 100
    categoryRole = None

    # If is required, for when talking about tea, or for all, like teaware and shipping
    isRequiredForTea = False
    isRequiredForAll = False

    # Autocalculated, if it is, it would be hidden in entry window and would rely on a calc step after submission
    # based on its role, would be Not Required if so.
    isAutoCalculated = False

    # Show as dropdown?
    isDropdown = False


    def __init__(self, name, categoryType, widthPixels=100):
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
            self.defaultValue = dt.datetime.now(tz=dt.timezone.utc)
        self.widthPixels = widthPixels
        self.categoryRole = "UNUSED"

        self.isRequiredForTea = False
        self.isRequiredForAll = False


class ReviewCategory:
    name = ""
    categoryType = ""
    widthPixels = 100
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

    def __init__(self, name, categoryType, widthPixels=100):
        self.name = name
        self.categoryType = categoryType
        self.widthPixels = widthPixels
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
        windowManager.deleteWindow(self.utitle)

    def windowDefintion(self, window):
        # Define the window
        pass
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
    w = 225 * settings["UI_SCALE"]
    h = 250 * settings["UI_SCALE"]
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
                    self.titleTextObject = dp.InputText(default_value=self.titleText, width=170, multiline=False, callback=self.updateTitleText)

            self.display = dp.Text(label=f"{self.formatTimeDisplay(self.timer)}")

            # in horizontal layout
            with dp.Group(horizontal=True):

                dp.Button(label="Start", callback=self.startTimer)
                dp.Button(label="Stop", callback=self.stopTimer)
                dp.Button(label="Reset", callback=self.resetTimer)

                dp.Checkbox(label="Persist", default_value=self.persist, callback=self.updatePersist)
                #tooltip
                dp.Button(label="?")
                with dpg.tooltip(dpg.last_item()):
                    tooltipText = '''Timer for timing tea steeps. Copy times to clipboard with the clipboard button.
                    \nPersist will save the timer between sessions (WIP)'''
                    dp.Text(tooltipText)

            # Group that contains an input text raw and a button to copy to clipboard
            with dp.Group(horizontal=True):
                dp.Button(label="Copy", callback=self.copyRawTimeToClipboard)
                self.rawDisplay = dp.InputText(default_value="Raw Times", readonly=True, callback=self.updateDefaultValueDisplay, width=200)
                

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
        w = 215 * settings["UI_SCALE"]
        h = 200 * settings["UI_SCALE"]
        self.childWindow = dp.ChildWindow(label="Previous Times (max 30)", width=w, height=h, parent=self.window)
        with self.childWindow:
            # add it in reverse order sop latest is at the top
            reversedTimes = self.previousTimes[::-1]
            for i, time in enumerate(reversedTimes):
                with dp.Group(horizontal=True):
                    dp.Button(label="Remove", callback=self.removeOneTime, user_data=i)
                    dp.Text(f"{i+1}: {self.formatTimeDisplay(time)}")
        

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
            time.sleep(0.1)

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
            defaultFont = settings["DEFAULT_FONT"]
            dp.Combo(label="Font", items=validFonts, default_value=defaultFont, callback=self.UpdateSettings, user_data="DEFAULT_FONT")

    # Callback function for the input text to update the settings
    def UpdateSettings(self, sender, data, user_data):
        settings[user_data] = data
        Settings_SaveCurrentSettings()
        # ui scale
        if user_data == "UI_SCALE":
            dpg.set_global_font_scale(settings["UI_SCALE"])

        # Start/Stop Autosave
        if user_data == "AUTOSAVE":
            shouldStart = settings["AUTO_SAVE"]
            startBackupThread(shouldStart) # Starts or stops the autosave thread

        # Update font
        if user_data == "DEFAULT_FONT":
            # Set the font for all windows
            dpg.set_global_font_scale(settings["UI_SCALE"])
            dpg.bind_font(data)

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
        self.GenerateEditReviewWindow(sender, app_data, user_data=(None, "add", user_data))  # Pass None for review to indicate new review
    def AddReview(self, sender, app_data, user_data):
        # Add a review to the tea
        allAttributes = {}
        teaID = user_data.id
        for k, v in self.addReviewList.items():
            if type(v) == dp.DatePicker:
                allAttributes[k] = DateDictToDT(v.get_value())
            else:
                allAttributes[k] = v.get_value()

        if "dateAdded" not in allAttributes:
            allAttributes["dateAdded"] = dt.datetime.now(tz=dt.timezone.utc)
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
        w = 600 * settings["UI_SCALE"]
        h = 700 * settings["UI_SCALE"]
        
        editReviewWindowItems = dict()
        review = user_data[0]
        parentTea = user_data[2]
        isEdit = user_data[1] if len(user_data) > 1 else False
        if isEdit != "edit":
            isEdit = False
        else:
            isEdit = True
        if not isEdit:
            # Assume add, drop review data if provided
            review = None

        windowName = "Edit Review" if isEdit else "Add New Review"
        self.editReviewWindow = dp.Window(label=windowName, width=w, height=h, modal=True, show=True)
        windowManager.addSubWindow(self.editReviewWindow)

        nameReview = ""
        idReview = 0
        if review is not None:
            idReview = review.id
            if review.attributes == None or review.attributes == "":
                review.attributes = {}
            if review.name == None or review.name == "":
                # Get from name of parent
                for i, tea in enumerate(TeaStash):
                    if tea.id == review.parentID:
                        nameReview = tea.name
                        review.name = nameReview
                        break
        else:
            # Infer parent name and ID from parent Tea instead of review
            if parentTea is not None:
                nameReview = parentTea.name
                idReview = len(parentTea.reviews)  # New review ID is the length of existing reviews
            else:
                nameReview = "New Review"

            
        with self.editReviewWindow:
            for cat in TeaReviewCategories:
                # Add it to the window
                dp.Text(cat.name)
                defaultValue = None

                try:
                    defaultValue = review.attributes[cat.categoryRole]
                except:
                    # also try to get from nameReview if review is None
                    defaultValue = f"{cat.defaultValue}"
                
                # If the category is a string, int, float, or bool, add the appropriate input type
                if cat.categoryType == "string":
                    if cat.categoryRole == "Name":
                        # For the name, use a single line input text
                        editReviewWindowItems[cat.categoryRole] = dp.InputText(label=cat.name, default_value=str(nameReview), width=300)
                    elif cat.categoryRole == "Notes (short)" or cat.categoryRole == "Notes (Long)":
                        # For notes, allow multiline input
                        editReviewWindowItems[cat.categoryRole] = dp.InputText(label=cat.name, default_value=str(defaultValue), multiline=True, height=100)
                    else:
                        # For other strings, single line input
                        editReviewWindowItems[cat.categoryRole] = dp.InputText(label=cat.name, default_value=defaultValue)
                elif cat.categoryType == "int":
                    editReviewWindowItems[cat.categoryRole] = dp.InputInt(label=cat.name, default_value=int(defaultValue))
                elif cat.categoryType == "float":
                    editReviewWindowItems[cat.categoryRole] = dp.InputFloat(label=cat.name, default_value=float(defaultValue))
                elif cat.categoryType == "bool":
                    if defaultValue == "True" or defaultValue == True:
                        defaultValue = True
                    else:
                        defaultValue = False
                    editReviewWindowItems[cat.categoryRole] = dp.Checkbox(label=cat.name, default_value=bool(defaultValue))
                elif cat.categoryType == "date" or cat.categoryType == "datetime":
                    # Date picker widget
                    try:
                        defaultValue = dt.datetime.strptime(defaultValue, settings["DATE_FORMAT"]).date()
                        defaultValue = DTToDateDict(defaultValue)
                    except:
                        defaultValue = DTToDateDict(dt.datetime.now(tz=dt.timezone.utc))
                    # If supported, display as date
                    editReviewWindowItems[cat.categoryRole] =  dp.DatePicker(level=dpg.mvDatePickerLevel_Day, label=cat.name, default_value=defaultValue)
                else:
                    editReviewWindowItems[cat.categoryRole] = dp.InputText(label=cat.name, default_value=f"Not Supported (Assume String): {cat.categoryType}, {cat.name}")
                    
            # Final Score input
            dp.Button(label="Save", callback=self.EditAddReview, user_data=(review, editReviewWindowItems, self.editReviewWindow, isEdit))
            dp.Button(label="Cancel", callback=self.deleteEditReviewWindow)


    def EditAddReview(self, sender, app_data, user_data):
        # Get the tea from the stash
        review = user_data[0]
        teaId = review.parentID if review else None
        editReviewWindowItems = user_data[1]
        isEdit = user_data[3]  # Check if it's an edit or add operation
        if not isEdit:
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
                allAttributes[k] = v.get_value()

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
            allAttributes["dateAdded"] = dt.datetime.now(tz=dt.timezone.utc)
        if "Final Score" not in allAttributes:
            allAttributes["Final Score"] = 0

        

        newReview = Review(teaId, reviewName, allAttributes["dateAdded"], allAttributes, allAttributes["Final Score"])

        if isEdit:
            # Transfer the reviews
            for i, tea in enumerate(TeaStash):
                if tea.id == teaId:
                    # Find the review and replace it
                    for j, rev in enumerate(tea.reviews):
                        if rev == review:
                            TeaStash[i].reviews[j] = newReview
                            break
        else:
            # Append to the tea's reviews if it's a new review
            for i, tea in enumerate(TeaStash):
                if tea.id == teaId:
                    TeaStash[i].addReview(newReview)
                    print(f"Teastash I is now {TeaStash[i]}, added new review: {newReview.name} with ID {newReview.id} to tea {teaId}")
                    break

        # Save to file
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])

        # hide the popup
        dpg.configure_item(self.reviewsWindow.tag, show=False)
        self.deleteEditReviewWindow()
        # Refresh the window
        self.refresh()
        self.parentWindow.refresh()
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
        # create a new window for the reviews
        with window:
            hbarinfoGroup = dp.Group(horizontal=True)
            numReviews = len(tea.reviews)
            with hbarinfoGroup:
                # Num reviews, average rating, etc
                dp.Text(f"Num Reviews: {numReviews}")
                dp.Text(f"Average Rating: X TODO")
            hbarActionGroup = dp.Group(horizontal=True)
            with hbarActionGroup:
                dp.Button(label="Add Review", callback=self.ShowAddReview, user_data=tea)
                # Add review popup
                w = 900 * settings["UI_SCALE"]
                h = 500 * settings["UI_SCALE"]
                self.reviewsWindow = dp.Window(label="Reviews", width=w, height=h, show=False, modal=True)
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
                    dp.Button(label="Add", callback=self.AddReview, user_data=tea)
            dp.Separator()
            # Add a table with reviews
            reviewsTable = dp.Table(header_row=True, no_host_extendX=True,
                                borders_innerH=True, borders_outerH=True, borders_innerV=True,
                                borders_outerV=True, row_background=True, hideable=True, reorderable=True,
                                resizable=True, sortable=True, policy=dpg.mvTable_SizingFixedFit,
                                scrollX=True, delay_search=True, scrollY=True, callback=_table_sort_callback)
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
                    tableRow = dp.TableRow()
                    with tableRow:

                        # Add ID index based on position in list
                        # (parentID) - (reviewID)
                        idValue = f"{review.parentID}-{review.id}"
                        dp.Text(label=idValue, default_value=idValue)
                        # Add the review attributes

                        cat: TeaCategory
                        for i, cat in enumerate(TeaReviewCategories):
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
                                    except KeyError:
                                        # If the key doesn't exist, set to N/A
                                        displayValue = "N/A"
                                    except Exception as e:
                                        RichPrintError(f"Error loading attributes: {e}")
                                        # If it fails, just set to N/A
                                        displayValue = f"Err (Exception {e})"
                                else:
                                    if cat.categoryRole in review.attributes:
                                        displayValue = review.attributes[cat.categoryRole]


                            if cat.categoryRole == "string" or cat.categoryRole == "float" or cat.categoryRole == "int":
                                dp.Text(label=displayValue, default_value=displayValue)
                            elif cat.categoryRole == "bool":
                                if displayValue == "True" or displayValue == True:
                                    displayValue = True
                                else:
                                    displayValue = False
                                dp.Checkbox(label=cat.name, default_value=True, enabled=False)
                            elif cat.categoryRole == "date" or cat.categoryRole == "datetime":
                                # Date picker widget
                                displayValue = parseStringToDT(displayValue)  # Ensure it's a datetime object first
                                displayValue = parseDTToStringWithFallback(displayValue, "None")
                                # If supported, display as date
                                dp.Text(label=displayValue, default_value=displayValue)
                            else:
                                # If not supported, just display as string
                                displayValue = str(displayValue)
                                dp.Text(label=displayValue, default_value=displayValue)
                        

                        # button that opens a modal with reviews
                        dp.Button(label="Edit", callback=self.GenerateEditReviewWindow, user_data=(review, "edit", self.tea))

    def deleteEditReviewWindow(self):
        # If window is open, close it first
        if self.editReviewWindow != None:
            self.editReviewWindow.delete()
            self.editReviewWindow = None
            self.addReviewList = list()
        else:
            print("No window to delete")

def Menu_Stash():
    w = 650 * settings["UI_SCALE"]
    h = 960 * settings["UI_SCALE"]
    stash = Window_Stash("Stash", w, h, exclusive=True)

class Window_Stash(WindowBase):
    addTeaList = dict()
    teasWindow = None

    def onDelete(self):
        # Close all popups
        if self.teasWindow != None and type(self.teasWindow) == dp.Window and self.teasWindow.exists():
            self.teasWindow.delete()
        elif self.teasWindow is not None:
            RichPrintInfo("Warning: Attempted to delete a non-existent teas window.")
            self.teasWindow = None
        # Invoke base class delete
        super().onDelete()


    def windowDefintion(self, window):
        self.addTeaList = dict()
        self.addReviewList = dict()
        with window:
            dp.Text("Stash")
            dp.Text("Teas")
            hgroupStats1 = dp.Group(horizontal=True)
            with hgroupStats1:
                # dummy stats
                dp.Text("Num Teas: 2 (TODO)")
                dp.Text("Num Reviews: 5(TODO)")
                dp.Text("Average Rating: X(TODO)")
            dp.Text(f"Last Tea Added: Tea 2 at {parseDTToString(dt.datetime.now(tz=dt.timezone.utc))}(TODO)")
            dp.Text(f"Last Review Added: Tea 2 at {parseDTToString(dt.datetime.now(tz=dt.timezone.utc))}(TODO)")
            dp.Separator()
            hgroupButtons = dp.Group(horizontal=True)
            with hgroupButtons:
                dp.Button(label="Add Tea", callback=self.ShowAddTea)
                dp.Button(label="Import Tea", callback=self.importOneTeaFromClipboard)
                dp.Button(label="Import All (TODO)", callback=self.DummyCallback)
                dp.Button(label="Export One (TODO)", callback=self.DummyCallback)
                dp.Button(label="Export All (TODO)", callback=self.DummyCallback)
                dp.Button(label="Refresh (TODO)", callback=self.DummyCallback)
            dp.Separator()

            # Table with collapsable rows for reviews
            teasTable = dp.Table(header_row=True, no_host_extendX=True,
                                borders_innerH=True, borders_outerH=True, borders_innerV=True,
                                borders_outerV=True, row_background=True, hideable=True, reorderable=True,
                                resizable=True, sortable=True, policy=dpg.mvTable_SizingFixedFit,
                                scrollX=True, delay_search=True, scrollY=True, callback=_table_sort_callback)
            with teasTable:
                # Add columns from teaCategories
                # Add ID
                dpg.add_table_column(label="ID", no_resize=False, no_clip=True, prefer_sort_ascending=True, width_fixed=True, 
                                     width=50, default_sort=True, no_hide=True, user_data="0")
                # Add the categories
                for i, cat in enumerate(TeaCategories):
                    dp.TableColumn(label=cat.name, no_resize=False, no_clip=True, user_data=f"{i+1}")
                dp.TableColumn(label="Reviews", no_resize=False, no_clip=True, width=300, no_hide=True)
                dp.TableColumn(label="Edit", no_resize=False, no_clip=True, width=50, no_hide=True)

                # Add rows
                for i, tea in enumerate(TeaStash):
                    tableRow = dp.TableRow()
                    with tableRow:
                        # Add ID index based on position in list
                        dp.Text(label=f"{i}", default_value=f"{i}")
                        # Add the tea attributes

                        cat: TeaCategory
                        for i, cat in enumerate(TeaCategories):
                            # Convert attributes to json
                            displayValue = "N/A"
                            if cat.name == "Name":
                                displayValue = tea.name
                            else:
                                if type(tea.attributes) == str:
                                    try:
                                        attrJson = loadAttributesFromString(tea.attributes)
                                        if cat.categoryRole in attrJson:
                                            displayValue = attrJson[cat.categoryRole]
                                    except json.JSONDecodeError:
                                        # If there's an error in decoding, set to N/A
                                        displayValue = "Err (JSON Decode Error)"
                                    except KeyError:
                                        # If the key doesn't exist, set to N/A
                                        displayValue = "N/A"
                                    except Exception as e:
                                        RichPrintError(f"Error loading attributes: {e}")
                                        # If it fails, just set to N/A
                                        displayValue = "Err (Exception)"
                                else:
                                    if cat.categoryRole in tea.attributes:
                                        displayValue = tea.attributes[cat.categoryRole]
                                    else:
                                        displayValue = "N/A"

                            if cat.categoryRole == "string" or cat.categoryRole == "float" or cat.categoryRole == "int":
                                dp.Text(label=displayValue, default_value=displayValue)
                            elif cat.categoryRole == "bool":
                                if displayValue == "True" or displayValue == True:
                                    displayValue = True
                                else:
                                    displayValue = False
                                dp.Checkbox(label=cat.name, default_value=bool(displayValue), enabled=False)
                            elif cat.categoryRole == "date" or cat.categoryRole == "datetime":
                                # Date picker widget
                                displayValue = parseStringToDT(displayValue)  # Ensure it's a datetime object first
                                displayValue = parseDTToStringWithFallback(displayValue, "None")
                                # If supported, display as date
                                dp.Text(label=displayValue, default_value=displayValue)
                            else:
                                # If not supported, just display as string
                                displayValue = str(displayValue)
                                dp.Text(label=displayValue, default_value=displayValue)

                        # button that opens a modal with reviews
                        numReviews = len(tea.reviews)
                        dp.Button(label=f"{numReviews} Reviews", callback=self.generateReviewListWindow, user_data=tea)
                        dp.Button(label="Edit", callback=self.ShowEditTea, user_data=tea)

            # Add seperator and import/export buttons
            dp.Separator()

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
        self.addTeaList = dict()
        if user_data[1] == "add":
            teasData = None
        elif user_data[1] == "edit":
            teasData = user_data[0]

        # Create a new window
        w = 500 * settings["UI_SCALE"]
        h = 500 * settings["UI_SCALE"]
        self.teasWindow = dp.Window(label="Teas", width=w, height=h, show=True)
        windowManager.addSubWindow(self.teasWindow)
        with self.teasWindow:
            dp.Text("Teas")

            for cat in TeaCategories:
                # Add it to the window
                dp.Text(cat.name)
                defaultValue = None
                try:
                    defaultValue = teasData.attributes[cat.categoryRole]
                except:
                    defaultValue = f"{cat.defaultValue}"

                # If the category is a string, int, float, or bool, add the appropriate input type
                catItem = None
                if cat.categoryType == "string":
                    # For notes, allow multiline input if it's a note
                    if cat.categoryRole == "Notes (short)" or cat.categoryRole == "Notes (Long)":
                        catItem = dp.InputText(label=cat.name, default_value=str(defaultValue), multiline=True, height=100)
                    else:
                        catItem = dp.InputText(label=cat.name, default_value=str(defaultValue), multiline=False)
                elif cat.categoryType == "int":
                    catItem = dp.InputInt(label=cat.name, default_value=int(defaultValue))
                elif cat.categoryType == "float":
                    catItem = dp.InputFloat(label=cat.name, default_value=float(defaultValue))
                elif cat.categoryType == "bool":
                    if defaultValue == "True" or defaultValue == True:
                        defaultValue = True
                    else:
                        defaultValue = False
                    catItem = dp.Checkbox(label=cat.name, default_value=bool(defaultValue))
                elif cat.categoryType == "date" or cat.categoryType == "datetime":
                    if teasData is None:
                        # Add, so default to now if no date is set
                        defaultValue = DTToDateDict(dt.datetime.now(tz=dt.timezone.utc))
                    # Date picker widget
                    try:
                        defaultValue = dt.datetime.strptime(defaultValue, settings["DATE_FORMAT"]).date()
                        defaultValue = DTToDateDict(defaultValue)
                    except:
                        defaultValue = DTToDateDict(dt.datetime.now(tz=dt.timezone.utc))
                        #defaultValue = dt.datetime.now(tz=dt.timezone.utc).date()  # Fallback to now if parsing fails
                    # If supported, display as date
                    catItem = dp.DatePicker(level=dpg.mvDatePickerLevel_Day, label=cat.name, default_value=defaultValue)
                else:
                    catItem = dp.InputText(label=cat.name, default_value=f"Not Supported (Assume String): {cat.categoryType}, {cat.name}")

                # Add it to the list
                if catItem != None:
                    self.addTeaList[cat.categoryRole] = catItem
                else:
                    RichPrintError(f"Error: {cat.categoryRole} not supported")

            # Add buttons
            if user_data[1] == "add":
                dp.Button(label="Add New Tea", callback=self.AddTea, user_data=teasData)
            elif user_data[1] == "edit":
                dp.Button(label="Confirm Edit", callback=self.EditTea, user_data=teasData)
                # Copy Values to string (json) for the edit window, use function
                dp.Button(label="Copy/Export Tea", callback=self.copyTeaValues, user_data=teasData)
                dp.Button( label="Paste Values", callback= self.pasteTeaValues, user_data=teasData)
            dp.Button(label="Cancel", callback=self.deleteTeasWindow)


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
                allAttributes[k] = v.get_value()

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
                        dt_value = parseStringToDT(allAttributes[k])
                        v.set_value(DTToDateDict(dt_value))
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
                    dt_value = parseStringToDT(allAttributes[k])
                    v.set_value(DTToDateDict(dt_value))
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




    def ShowAddTea(self, sender, app_data, user_data):
        self.generateTeasWindow(sender, app_data, user_data=(None,"add"))
    def ShowEditTea(self, sender, app_data, user_data):
        self.generateTeasWindow(sender, app_data, user_data=(user_data,"edit"))
                   
                    


    def AddTea(self, sender, app_data, user_data):
        # All input texts and other input widgets are in the addTeaGroup
        # create a new tea and add it to the stash
        allAttributes = {}
        for k, v in self.addTeaList.items():
            if type(v) == dp.DatePicker:
                allAttributes[k] = DateDictToDT(v.get_value())
            else:
                allAttributes[k] = v.get_value()

        RichPrintInfo(f"Adding tea: {allAttributes}")

        # Check if the dateAdded attribute is present, if not, set it to the current time
        if "dateAdded" not in allAttributes:
            allAttributes["dateAdded"] = dt.datetime.now(tz=dt.timezone.utc)

        # Create a new tea and add it to the stash
        newTea = StashedTea(len(TeaStash) + 1, allAttributes["Name"], allAttributes["dateAdded"], allAttributes)
        dateAdded = dt.datetime.now(tz=dt.timezone.utc)
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
                allAttributes[k] = v.get_value()


        
        dateAdded = None
        if hasattr(tea, 'dateAdded') and tea.dateAdded is not None:
            dateAdded = tea.dateAdded
        # Transfer the dateAdded if it exists, otherwise use the current time
        if dateAdded is None:
            dateAdded = dt.datetime.now(tz=dt.timezone.utc)
        newTea = StashedTea(tea.id, allAttributes["Name"], dateAdded, allAttributes)

        # Transfer the reviews
        newTea.reviews = tea.reviews
        # Transfer the calculated values
        newTea.calculated = tea.calculated

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
    w = 480 * settings["UI_SCALE"]
    h = 480 * settings["UI_SCALE"]
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
                dp.Button(label="Template", callback=self.copyNotepad)
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
            scaledWidth = 470 * settings["UI_SCALE"]
            scaledHeight = 400 * settings["UI_SCALE"]
            self.textInput = dp.InputText(default_value=defaultText, multiline=True, width=scaledWidth, height=scaledHeight, callback=self.updateText)
            dp.Separator()

    def clearNotepad(self, sender, data):
        self.textInput.set_value("")
    def copyNotepad(self, sender, data):
        pyperclip.copy(self.text)
    def updatePersist(self, sender, data):
        self.persist = data
    def updateText(self, sender, data):
        self.text = data

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


def Menu_Stats():
    w = 480 * settings["UI_SCALE"]
    h = 600 * settings["UI_SCALE"]
    stats = Window_Stats("Stats", w, h, exclusive=True)

class Window_Stats(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("Stats")
            dp.Text("Stats go here")


        
def Menu_EditCategories():
    w = 720 * settings["UI_SCALE"]
    h = 480 * settings["UI_SCALE"]
    editCategories = Window_EditCategories("Edit Categories", w, h, exclusive=True)

class Window_EditCategories(WindowBase):
    teaCategoryGroup = None
    teaReviewGroup = None
    reviewCategories = []
    def windowDefintion(self, window):
        with window:
            # vertical half half split, one for tea, one for review
            with dp.Group(horizontal=True):
                # Tea Categories
                scaledWidth = 350 * settings["UI_SCALE"]

                with dp.Group(horizontal=False):
                    dp.Text("Tea Categories")
                    dp.Button(label="Add Stash Category", callback=self.showAddCategory)
                    with dpg.child_window(label="Tea Categories", width=scaledWidth, height=600):
                        self.teaCategoryGroup = dp.Group(horizontal=False)
                        dp.Separator()
                        self.generateTeaCategoriesList(self.teaCategoryGroup)

                # Vertical split for review
                # Review
                with dp.Group(horizontal=False):
                    dp.Text("Review Categories")
                    dp.Button(label="Add Review Category", callback=self.shouldAddReviewCategory)
                    with dpg.child_window(label="Review Categories", width=scaledWidth, height=600):
                        dp.Separator()
                        self.teaReviewGroup = dp.Group(horizontal=False)
                        self.generateReviewCategoriesList()


    def generateTeaCategoriesList(self, window):
        with self.teaCategoryGroup:
            for i, category in enumerate(TeaCategories):
                with dp.Group(horizontal=True):
                    scaledWidth = 250 * settings["UI_SCALE"]
                    scaledHeight = 150 * settings["UI_SCALE"]
                    with dp.ChildWindow(width=scaledWidth, height=scaledHeight):
                        dp.Text(f"{i+1}: {category.name} -- {category.categoryType}")
                        dp.Text(f"Default Value: {category.defaultValue}")
                        dp.Text(f"Category Role: {category.categoryRole}")
                        dp.Text(label=f"Width: {category.widthPixels}")

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
                        dp.Text(f"{i+1}: {category.name} -- {category.categoryType}")
                        dp.Text(f"Default Value: {category.defaultValue}")
                        dp.Text(f"Category Role: {category.categoryRole}")
                        dp.Text(label=f"Width: {category.widthPixels}")

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
        windowManager.addSubWindow(addCategoryWindow)
        addCategoryWindowItems = dict()

        with addCategoryWindow:
            dp.Text("Add Category")
            category: TeaCategory
            # Declare category name, width, type
            dp.Text("Category Name")
            nameItem = dp.InputText(label="Name", default_value="")
            addCategoryWindowItems["Name"] = nameItem

            dp.Text("Width")
            widthItem = dp.InputInt(label="Width", default_value=100, step=1, min_value=50, max_value=500)
            addCategoryWindowItems["Width"] = widthItem

            dp.Text("Default Value")
            defaultValueItem = dp.InputText(label="Default Value", default_value="")
            addCategoryWindowItems["DefaultValue"] = defaultValueItem
            
            validTypes = session["validTypesCategory"]
            dp.Separator()
            dp.Text("Type of Category")
            catItem = dp.Listbox(items=validTypes, default_value="string", label="Type", num_items=5)
            addCategoryWindowItems["Type"] = catItem

            # Category role dropdown
            dp.Text("Category Role")
            typeCategory = f"{catItem.get_value()}"
            items = session["validroleCategory"][typeCategory]
            roleItem = dp.Listbox(items=items, default_value="UNUSED", num_items=5)
            addCategoryWindowItems["role"] = roleItem
            dp.Separator()

            # Additional flags: isRequired, isrequiredForAll, isAutocalculated, isDropdown
            dp.Separator()
            dp.Text("Additional Flags")
            # Explanation tooltip
            dp.Button(label="?")
            with dpg.tooltip(dpg.last_item()):
                tooltipTxt = '''Is Required (inc Teaware, fees): If this category is required for all teas, including teaware and fees. Supercedes isRequiredForTea.
                \nIs Required for Tea only: If this category is required for tea only, not teaware or fees.
                \nIs Dropdown: Will display a dropdown list of options if applicable. (string only currently, must be less than 50 characters)
                \nIs Autocalculated: Mark this category as autocalculated, WIP, does not do anything yet'''

                dp.Text(tooltipTxt)
            isRequiredItem = dp.Checkbox(label="Is Required (inc Teaware, fees)", default_value=False)
            addCategoryWindowItems["isRequiredForAll"] = isRequiredItem

            isRequiredTeaItem = dp.Checkbox(label="Is Required for Tea only", default_value=False)
            addCategoryWindowItems["isRequiredTea"] = isRequiredTeaItem

            isDropdownItem = dp.Checkbox(label="Is Dropdown", default_value=False)
            addCategoryWindowItems["isDropdown"] = isDropdownItem

            isAutocalculatedItem = dp.Checkbox(label="Is Autocalculated", default_value=False)
            addCategoryWindowItems["isAutocalculated"] = isAutocalculatedItem

                
            
            dp.Separator()
                    

            dp.Button(label="Add", callback=self.AddCategory, user_data=(addCategoryWindowItems, addCategoryWindow))
            dp.Button(label="Cancel", callback=addCategoryWindow.delete)
            # Help question mark
            dp.Button(label="?")
            # Hover tooltip
            with dpg.tooltip(dpg.last_item()):
                dp.Text("Add a new category to the stash")

    def shouldAddReviewCategory(self, sender, app_data, user_data):
        # Create a popup window to add a new the review category
        w = 500 * settings["UI_SCALE"]
        h = 500 * settings["UI_SCALE"]
        # Create a new window
        addReviewCategoryWindow = dp.Window(label="Add Review Category", width=w, height=h, modal=True, show=True)
        windowManager.addSubWindow(addReviewCategoryWindow)
        addReviewCategoryWindowItems = dict()

        with addReviewCategoryWindow:
            dp.Text("Add Review Category")
            category: ReviewCategory
            # Declare category name, width, type
            dp.Text("Category Name")
            nameItem = dp.InputText(label="Name", default_value="")
            addReviewCategoryWindowItems["Name"] = nameItem

            dp.Text("Width")
            widthItem = dp.InputInt(label="Width", default_value=100, step=1, min_value=50, max_value=500)
            addReviewCategoryWindowItems["Width"] = widthItem
            
            dp.Text("Default Value")
            defaultValueItem = dp.InputText(label="Default Value", default_value="")
            addReviewCategoryWindowItems["DefaultValue"] = defaultValueItem

            
            validTypes = session["validTypesReviewCategory"]
            dp.Separator()
            dp.Text("Type of Category")
            catItem = dp.Listbox(items=validTypes, default_value="string", label="Type", num_items=5)
            addReviewCategoryWindowItems["Type"] = catItem

            # Category role dropdown
            dp.Text("Category Role")
            typeCategory = f"{catItem.get_value()}"
            items = session["validroleReviewCategory"][typeCategory]
            roleItem = dp.Listbox(items=items, default_value="UNUSED", num_items=5)
            addReviewCategoryWindowItems["role"] = roleItem

            # Additional flags: isRequired, isrequiredForAll, isAutocalculated, isDropdown
            dp.Separator()
            dp.Text("Additional Flags")
            # Explanation tooltip
            dp.Button(label="?")
            with dpg.tooltip(dpg.last_item()):
                tooltipTxt = '''Is Required (inc Teaware, fees): If this category is required for all teas, including teaware and fees. Supercedes isRequiredForTea.
                \nIs Required for Tea only: If this category is required for tea only, not teaware or fees.
                \nIs Dropdown: Will display a dropdown list of options if applicable. (string only currently, must be less than 50 characters)
                \nIs Autocalculated: Mark this category as autocalculated, WIP, does not do anything yet'''

                dp.Text(tooltipTxt)
            isRequiredItem = dp.Checkbox(label="Is Required (inc Teaware, fees)", default_value=False)
            addReviewCategoryWindowItems["isRequiredForAll"] = isRequiredItem

            isRequiredTeaItem = dp.Checkbox(label="Is Required for Tea only", default_value=False)
            addReviewCategoryWindowItems["isRequiredTea"] = isRequiredTeaItem

            isDropdownItem = dp.Checkbox(label="Is Dropdown", default_value=False)
            addReviewCategoryWindowItems["isDropdown"] = isDropdownItem

            isAutocalculatedItem = dp.Checkbox(label="Is Autocalculated", default_value=False)
            addReviewCategoryWindowItems["isAutocalculated"] = isAutocalculatedItem
                
            
            dp.Separator()
                    

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
        newCategory = ReviewCategory(allAttributes["Name"], allAttributes["Type"], int(float(allAttributes["Width"])))
        defaultValue = allAttributes["DefaultValue"]
        if defaultValue != None and defaultValue != "":
            newCategory.defaultValue = defaultValue

        # Add role
        newCategory.categoryRole = allAttributes["role"]
        if newCategory.categoryRole not in session["validroleReviewCategory"][newCategory.categoryType]:
            newCategory.categoryRole = "UNUSED"

        ## Add flags
        newCategory.isRequiredForAll = allAttributes["isRequiredForAll"]
        newCategory.isRequiredForTea = allAttributes["isRequiredTea"]
        newCategory.isDropdown = allAttributes["isDropdown"]
        newCategory.isAutoCalculated = allAttributes["isAutocalculated"]

        
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
        editCategoryWindowItems = dict()
        category = TeaCategories[user_data]
        category: TeaCategory

        with editCategoryWindow:
            dp.Text(f"{category.name}")
            dp.Text(f"Width: {category.widthPixels}")
            editCategoryWindowItems["Width"] = dp.InputInt(label="Width", default_value=category.widthPixels, step=1, min_value=50, max_value=500)
            
            dp.Text(f"Default Value: {category.defaultValue}")
            editCategoryWindowItems["DefaultValue"] = dp.InputText(label="Default Value", default_value=category.defaultValue)
            
            validTypes = session["validTypesCategory"]
            dp.Separator()
            dp.Text(f"Type of Category")
            catItem = dp.Listbox(items=validTypes, default_value=category.categoryType, label="Type", callback=self.updateTypeDuringEdit, num_items=5)
            if category.categoryType not in validTypes:
                catItem.set_value("ERR: Assume String")

            editCategoryWindowItems["Type"] = catItem

            # Dropdown for category role
            dp.Text("Category Role")
            typeCategory = f"{category.categoryType}"
            items = session["validroleCategory"][typeCategory]
            roleItem = dp.Listbox(items=items, default_value=category.categoryRole, num_items=5)
            if category.categoryRole not in items:
                roleItem.set_value("ERR: Assume Unused")
            
            editCategoryWindowItems["role"] = roleItem

            # Additional flags: isRequired, isrequiredForAll, isAutocalculated, isDropdown
            dp.Separator()
            dp.Text("Additional Flags")
            # Question mark for tooltip
            dp.Button(label="?")
            with dpg.tooltip(dpg.last_item()):
                tooltipTxt = '''Is Required (inc Teaware, fees): If this category is required for all teas, including teaware and fees. Supercedes isRequiredForTea.
                \nIs Required for Tea only: If this category is required for tea only, not teaware or fees.
                \nIs Dropdown: Will display a dropdown list of options if applicable. (string only currently, must be less than 50 characters)
                \nIs Autocalculated: Mark this category as autocalculated, WIP, does not do anything yet'''

                dp.Text(tooltipTxt)
            isRequiredItem = dp.Checkbox(label="Is Required (inc Teaware, fees)", default_value=category.isRequiredForAll)
            editCategoryWindowItems["isRequiredForAll"] = isRequiredItem

            isRequiredTeaItem = dp.Checkbox(label="Is Required for Tea only", default_value=category.isRequiredForTea)
            editCategoryWindowItems["isRequiredTea"] = isRequiredTeaItem

            isDropdownItem = dp.Checkbox(label="Is Dropdown", default_value=category.isDropdown)
            editCategoryWindowItems["isDropdown"] = isDropdownItem

            isAutocalculatedItem = dp.Checkbox(label="Is Autocalculated", default_value=category.isAutoCalculated)
            editCategoryWindowItems["isAutocalculated"] = isAutocalculatedItem


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
        dpg.configure_item(roleItem.tag, items=validTypes)
        roleItem.set_value(validTypes[0])

    def EditCategory(self, sender, app_data, user_data):
        category = user_data[0]
        allAttributes = user_data[1]
        category.categoryType = allAttributes["Type"].get_value()
        if category.categoryType not in session["validTypesCategory"]:
            category.categoryType = "UNUSED"
        category.widthPixels = allAttributes["Width"].get_value()
        category.defaultValue = allAttributes["DefaultValue"].get_value()

        category.categoryRole = allAttributes["role"].get_value()
        if category.categoryRole not in session["validroleCategory"][allAttributes["Type"].get_value()]:
            category.categoryRole = "UNUSED"

        # Flags
        category.isRequiredForAll = allAttributes["isRequiredForAll"].get_value()
        category.isRequiredTea = allAttributes["isRequiredTea"].get_value()
        category.isDropdown = allAttributes["isDropdown"].get_value()
        category.isAutocalculated = allAttributes["isAutocalculated"].get_value()

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
        windowManager.addSubWindow(editReviewCategoryWindow)
        editReviewCategoryWindowItems = dict()
        category = TeaReviewCategories[user_data]

        with editReviewCategoryWindow:
            dp.Text(f"{category.name}")
            dp.Text(f"Width: {category.widthPixels}")
            editReviewCategoryWindowItems["Width"] = dp.InputInt(label="Width", default_value=category.widthPixels, step=1, min_value=50, max_value=500)

            dp.Text(f"Default Value: {category.defaultValue}")
            editReviewCategoryWindowItems["DefaultValue"] = dp.InputText(label="Default Value", default_value=category.defaultValue)

            validTypes = session["validTypesReviewCategory"]
            dp.Separator()
            dp.Text(f"Type of Category")
            catItem = dp.Listbox(items=validTypes, default_value=category.categoryType, label="Type", num_items=5, callback=self.updateTypeDuringEditReview)
            if category.categoryType not in validTypes:
                catItem.set_value("ERR: Assume String")

            editReviewCategoryWindowItems["Type"] = catItem

            dp.Text("Category role")
            # Dropdown for category role
            items = session["validroleReviewCategory"][category.categoryType]
            roleItem = dp.Listbox(items=items, default_value=category.categoryRole)
            editReviewCategoryWindowItems["role"] = roleItem
            if category.categoryRole not in items:
                roleItem.set_value("ERR: Assume Unused")
            dp.Separator()

            # Additional flags: isRequired, isrequiredForAll, isAutocalculated, isDropdown
            dp.Separator()
            dp.Text("Additional Flags")
            # Question mark for tooltip
            dp.Button(label="?")
            with dpg.tooltip(dpg.last_item()):
                tooltipTxt = '''Is Required (inc Teaware, fees): If this category is required for all teas, including teaware and fees. Supercedes isRequiredForTea.
                \nIs Required for Tea only: If this category is required for tea only, not teaware or fees.
                \nIs Dropdown: Will display a dropdown list of options if applicable. (string only currently, must be less than 50 characters)
                \nIs Autocalculated: Mark this category as autocalculated, WIP, does not do anything yet'''

                dp.Text(tooltipTxt)

            isRequiredItem = dp.Checkbox(label="Is Required (inc Teaware, fees)", default_value=category.isRequiredForAll)
            editReviewCategoryWindowItems["isRequiredForAll"] = isRequiredItem

            isRequiredTeaItem = dp.Checkbox(label="Is Required for Tea only", default_value=category.isRequiredForTea)
            editReviewCategoryWindowItems["isRequiredTea"] = isRequiredTeaItem

            isDropdownItem = dp.Checkbox(label="Is Dropdown", default_value=category.isDropdown)
            editReviewCategoryWindowItems["isDropdown"] = isDropdownItem

            isAutocalculatedItem = dp.Checkbox(label="Is Autocalculated", default_value=category.isAutoCalculated)
            editReviewCategoryWindowItems["isAutocalculated"] = isAutocalculatedItem

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
        category.widthPixels = allAttributes["Width"].get_value()
        category.defaultValue = allAttributes["DefaultValue"].get_value()

        category.categoryRole = allAttributes["role"].get_value()
        if category.categoryRole not in session["validroleReviewCategory"][allAttributes["Type"].get_value()]:
            category.categoryRole = "UNUSED"

        # Flags
        category.isRequiredForAll = allAttributes["isRequiredForAll"].get_value()
        category.isRequiredTea = allAttributes["isRequiredTea"].get_value()
        category.isDropdown = allAttributes["isDropdown"].get_value()
        category.isAutoCalculated = allAttributes["isAutocalculated"].get_value()


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
        newCategory = TeaCategory(allAttributes["Name"], allAttributes["Type"], int(allAttributes["Width"]))
        newCategory.defaultValue = defaultValue

        # Add in role
        newCategory.categoryRole = allAttributes["role"].get_value()
        if newCategory.categoryRole not in session["validroleCategory"][allAttributes["Type"].get_value()]:
            newCategory.categoryRole = "UNUSED"

        # Add in flags
        newCategory.isRequiredForAll = allAttributes["isRequiredForAll"].get_value()
        newCategory.isRequiredForTea = allAttributes["isRequiredTea"].get_value()
        newCategory.isAutoCalculated = allAttributes["isAutocalculated"].get_value()
        newCategory.isDropdown = allAttributes["isDropdown"].get_value()

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
    h = 140 * settings["UI_SCALE"]
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
            dp.Text(f"Welcome {settings['USERNAME']}!")
            dp.Text(f"This is a simple tea stash manager (V{settings["APP_VERSION"]}) to keep track of your teas and reviews.")
            dp.Text("This is a In-Progress demo, so expect bugs and missing features. - Rex")
            dp.Text("Head over to the settings then to the categories window to get started, "
            "\nOnce you have added some teas, you can add reviews to them and view your stats!")
            dp.Separator()
            dp.Button(label="OK", callback=window.delete)



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

    def exportPersistantWindows(self, filePath):
        # Export all windows to a file
        allData = []
        for key, value in self.windows.items():
            title = value.title
            if value.persist:
                yml = value.exportYML()
                allData.append({title: yml})

        WriteYaml(filePath, allData)
        print(allData)
        return allData
    
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
    print(f"Backup generated at {backupPath}")

def saveTeasReviews(stash, path):
    # Save as one file in yml format
    allData = []
    nowString = parseDTToString(dt.datetime.now(tz=dt.timezone.utc))  # Get current time as string for default dateAdded
    for tea in stash:
        print(tea.__dict__)  # Debugging line to see the tea object
        teaData = {
            "_index": tea.id,
            "Name": tea.name,
            "dateAdded": parseDTToStringWithFallback(tea.dateAdded, fallbackString=nowString),  # Save dateAdded as string, default to now if not specified
            "attributes": tea.attributes,
            "attributesJson": dumpAttributesToString(tea.attributes),  # Save attributes as JSON string for easier parsing
            "reviews": []
        }
        print(teaData["attributesJson"])
        for review in tea.reviews:
            print( review.__dict__)  # Debugging line to see the review object
            reviewData = {
                "_reviewindex": review.id,
                "parentIDX": tea.id,
                "Name": review.name,
                "dateAdded": parseDTToStringWithFallback(review.dateAdded, fallbackString=nowString),  # Save dateAdded as string, default to now if not specified
                "attributes": review.attributes,
                "attributesJson": dumpAttributesToString(review.attributes),  # Save review attributes as JSON string for easier parsing
                "rating": review.rating,
            }
            teaData["reviews"].append(reviewData)
        allData.append(teaData)

    WriteYaml(path, allData)

def loadTeasReviews(path):
    # If not exists, create the directory, return false
    if not os.path.exists(path):
        print(f"Directory {path} created")
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

        # Date added could be under dateAdded or Date Added
        dateAdded = teaData.get("dateAdded", None)
        if dateAdded is None:
            dateAdded = teaData.get("Date Added", None)

        tea = StashedTea(idx, name, dateAdded=dateAdded, attributes=teaData["attributes"])
        dateAdded = dt.datetime.now(tz=dt.timezone.utc)  # Default to now if not specified
        if "dateAdded" in teaData:
            dateAdded = parseStringToDT(teaData["dateAdded"], default=dt.datetime.now(tz=dt.timezone.utc))
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
        tea.dateAdded = dateAdded
        
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

            # dateAdded could be under dateAdded or Date Added
            dateAdded = reviewData.get("dateAdded", None)
            if dateAdded is None:
                dateAdded = reviewData.get("Date Added", None)
            if dateAdded is None:
                dateAdded = dt.datetime.now(tz=dt.timezone.utc)
            dateAdded = parseStringToDT(dateAdded, default=dt.datetime.now(tz=dt.timezone.utc))

            
            review = Review(idx2, name, dateAdded, reviewData["attributes"], rating)
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
            "widthPixels": category.widthPixels,
            "defaultValue": category.defaultValue,
            "categoryRole": category.categoryRole,
            "isAutoCalculated": category.isAutoCalculated,
            "isRequiredForTea": category.isRequiredForTea,
            "isRequiredForAll": category.isRequiredForAll,
            "isDropdown": category.isDropdown,
        }
        allData.append(categoryData)

    WriteYaml(path, allData)

def loadTeaCategories(path):
    # If not exists, create the directory, return false
    if not os.path.exists(path):
        print(f"Directory {path} created")
        return []
    
    # Load from one file in yml format
    allData = ReadYaml(path)
    TeaCategories = []
    for categoryData in allData:
        category = TeaCategory(categoryData["Name"], categoryData["categoryType"], categoryData["widthPixels"])
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
    return TeaCategories

def loadTeaReviewCategories(path):
    # If not exists, create the directory, return false
    if not os.path.exists(path):
        print(f"Directory {path} created")
        return []
    
    # Load from one file in yml format
    allData = ReadYaml(path)
    TeaReviewCategories = []
    for categoryData in allData:
        category = ReviewCategory(categoryData["Name"], categoryData["categoryType"], categoryData["widthPixels"])
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

    print(f"Number of Tea Categories: {len(TeaCategories)}")
    print(f"Number of Review Categories: {len(TeaReviewCategories)}")

    # Save the categories again
    SaveAll()

def saveTeaReviewCategories(categories, path):
    # Save as one file in yml format
    allData = []
    for category in categories:
        categoryData = {
            "Name": category.name,
            "categoryType": category.categoryType,
            "widthPixels": category.widthPixels,
            "defaultValue": category.defaultValue,
            "categoryRole": category.categoryRole,
            "isAutoCalculated": category.isAutoCalculated,
            "isRequiredForTea": category.isRequiredForTea,
            "isRequiredForAll": category.isRequiredForAll,
            "isDropdown": category.isDropdown,
        }
        allData.append(categoryData)

    WriteYaml(path, allData)

def SaveAll(altPath=None):
    # Save all data
    if altPath is not None:
        newBaseDirectory = altPath
        saveTeasReviews(TeaStash, f"{newBaseDirectory}/tea_reviews.yml")
        saveTeaCategories(TeaCategories, f"{newBaseDirectory}/tea_categories.yml")
        saveTeaReviewCategories(TeaReviewCategories, f"{newBaseDirectory}/tea_review_categories.yml")
        WriteYaml(f"{newBaseDirectory}/user_settings.yml", settings)
        windowManager.exportPersistantWindows(f"{newBaseDirectory}/persistant_windows.yml")
        print(f"All data saved to {newBaseDirectory}")
        return
    saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])
    saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
    saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
    WriteYaml(session["settingsPath"], settings)
    windowManager.exportPersistantWindows(settings["PERSISTANT_WINDOWS_PATH"])


# Start Backup Thread
def startBackupThread(shouldStart=False):
    # If ShouldStart and not started, start, else end
    global backupThread
    
    if shouldStart and backupThread == False:
        backupThread = threading.Thread(target=backupThreadFunc, daemon=True)
        backupThread.start()
        RichPrintInfo("Backup thread started")
    elif not shouldStart and backupThread != False:
        backupThread.join()
        backupThread = False
        RichPrintInfo("Backup thread stopped")
    else:
        RichPrintInfo("Backup thread already started or stopped, doing nothing")



def backupThreadFunc():
    # Start a loop to poll the time since start and save if needed
    while True:
        pollAndAutosaveIfNeeded()
        time.sleep(60)  # Poll every 5s

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
    print(f"Loaded settings from {path}")
    return settings

def LoadAll():
    # Load all data
    global settings
    baseDir = os.path.dirname(os.path.abspath(__file__))
    settingsPath = f"{baseDir}/{default_settings['SETTINGS_FILENAME']}"
    session["settingsPath"] = settingsPath
    settings = LoadSettings(session["settingsPath"])
    # Update version
    print(session)
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

    #windowManager.importPersistantWindows(settings["PERSISTANT_WINDOWS_PATH"])
    print(f"Loaded settings from {session['settingsPath']}")
    
    print(f"Loaded {len(TeaStash)} teas and {len(TeaCategories)} categories")

# Attributes to string, json, with special datetime handling
def dumpAttributesToString(attributes):
    returnDict = {}
    parseDict = json.loads(json.dumps(attributes, default=str))  # Convert datetime objects to string
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
            returnDict[key] = parseDTToString(value)
        else:
            returnDict[key] = value
    return json.dumps(returnDict)  # Ensure JSON is properly formatted with non-ASCII characters

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
                    parsed_date = parseStringToDT(value)
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
            returnDict[key] = parseDTToString(value)
        elif isinstance(value, dict):
            # Recursive handling
            returnDict[key] = dumpAttributesToString(value)
        else:
            returnDict[key] = value
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


#endregion

def UI_CreateViewPort_MenuBar():
    with dp.ViewportMenuBar():
        with dp.Menu(label="Session"):
            dp.MenuItem(label="Log", callback=Menu_Stash)
            dp.MenuItem(label="Summary", callback=Menu_Summary)
            dp.Button(label="Settings", callback=Menu_Settings)
        with dp.Menu(label="Stash"):
            dp.MenuItem(label="Reviews", callback=Menu_ReviewsTable)
            dp.MenuItem(label="Stats", callback=Menu_Stats)
            dp.MenuItem(label="Edit Categories", callback=Menu_EditCategories)
        with dp.Menu(label="Tools"):
            dp.MenuItem(label="Timer", callback=Menu_Timer)
            dp.MenuItem(label="Notepad", callback=Menu_Notepad)
        with dp.Menu(label="Visualize"):
            dp.MenuItem(label="Graph 1", callback=print_me)
            dp.MenuItem(label="Graph 2", callback=print_me)
        with dp.Menu(label="Settings"):
            dp.MenuItem(label="Setting 1", callback=print_me, check=True)
            dp.MenuItem(label="Setting 2", callback=print_me)
        dp.MenuItem(label="Help", callback=print_me)
        with dp.Menu(label="Library"):
            dp.Checkbox(label="Pick Me", callback=print_me)
            dp.Button(label="Press Me", callback=print_me)
            dp.ColorPicker(label="Color Me", callback=print_me)
        with dp.Menu(label="Debug"):
            dp.Button(label="Windows", callback=windowManager.printWindows)
            dp.Button(label="Settings", callback=printSettings)
            dp.Button(label="Threads", callback=printThreads)
            dp.Button(label="Check Categories", callback=verifyCategoriesReviewCategories)
            dp.Button(label="Generate Backup", callback=generateBackup)
            dp.Button(label="Sort Windows", callback=windowManager.sortWindows)
            dp.Button(label="Export Windows", callback=windowManager.exportPersistantWindows)
            dp.Button(label="Import Windows", callback=windowManager.importPersistantWindows)
        with dp.Menu(label="Debug 2"):
            dp.Button(label="Demo", callback=demo.show_demo)
            dp.Button(label="Poll Time", callback=pollTimeSinceStartMinutes)
            dp.Button(label="Stop Backup Thread", callback=startBackupThread)
            dp.Button(label="printTeasAndReviews", callback=printTeasAndReviews)
            dp.Button(label="Print Categories/Reviews", callback=printCategories)
            dp.Button(label="Print role Cat", callback=debugGetcategoryRole)
            dp.Button(label="Print role Rev Cat", callback=debugGetReviewcategoryRole)
            dp.Button(label="Renumber data", callback=renumberTeasAndReviews)
            

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

def main():
    RichPrintInfo("Starting Tea Tracker")
    global globalTimeLastSave
    globalTimeLastSave = dt.datetime.now(tz=dt.timezone.utc)
    # get monitor resolution
    monitor = screeninfo.get_monitors()[0]
    print(monitor)
    WindowSize = (1920, 1600)
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
        "USERNAME": "John Puerh",
        "DIRECTORY": "ratea-data",
        "DATE_FORMAT": "%Y-%m-%d",
        "TIMEZONE": "UTC", # default to UTC, doesn't really matter since time is not used
        "TIMER_WINDOW_LABEL": True,
        "TIMER_PERSIST_LAST_WINDOW": True, # TODO
        "TEA_REVIEWS_PATH": f"ratea-data/tea_reviews.yml",
        "BACKUP_PATH": f"ratea-data/backup",
        "PERSISTANT_WINDOWS_PATH": f"ratea-data/persistant_windows.yml",
        "APP_VERSION": "0.5.6", # Updates to most recently loaded
        "AUTO_SAVE": True,
        "AUTO_SAVE_INTERVAL": 15, # Minutes
        "AUTO_SAVE_PATH": f"ratea-data/auto_backup",
        "DEFAULT_FONT": "OpenSansRegular",
    }
    numSettings = len(default_settings)
    global settings
    settings = default_settings
    global session
    session = {}
    # Get a list of all valid types for Categories
    setValidTypes()
    session["validFonts"] = ["OpenSansRegular", "RobotoRegular", "RobotoBold", "MerriweatherRegular", "MontserratRegular"]
    global TeaStash
    global TeaCategories
    TeaCategories = []
    category = TeaCategory("Name", "string", False)
    category.defaultValue = "Tea Name"
    TeaCategories.append(category)
    category = TeaCategory("Type", "string", False)
    category.defaultValue = "Type"
    TeaCategories.append(category)
    category = TeaCategory("Year", "int", False)
    category.defaultValue = 2000
    TeaCategories.append(category)
    category = TeaCategory("Remaining", "float", False)
    category.defaultValue = 0.0
    TeaCategories.append(category)


    global TeaReviewCategories
    TeaReviewCategories = []
    TeaReviewCategory = ReviewCategory("Name", "string", False)
    TeaReviewCategory.defaultValue = "Tea Name"
    TeaReviewCategories.append(TeaReviewCategory)
    TeaReviewCategory = ReviewCategory("Date", "string", False)
    TeaReviewCategory.defaultValue = "Date"
    TeaReviewCategories.append(TeaReviewCategory)
    TeaReviewCategory = ReviewCategory("Rating", "int", True)
    TeaReviewCategory.defaultValue = 0
    TeaReviewCategories.append(TeaReviewCategory)
    TeaReviewCategory = ReviewCategory("Notes", "string", True)
    TeaReviewCategory.defaultValue = "Notes"
    TeaReviewCategories.append(TeaReviewCategory)


    '''

    settingsPath = f"{baseDir}/{default_settings['SETTINGS_FILENAME']}"
    session["settingsPath"] = settingsPath
    hasSettingsFile = os.path.exists(settingsPath)
    if hasSettingsFile and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found {default_settings["SETTINGS_FILENAME"]} at full path {settingsPath}")
        # Load the settings from json
        settings = ReadYaml(settingsPath)
        if len(settings) != numSettings:
            RichPrintError(f"Settings file {default_settings["SETTINGS_FILENAME"]} has {len(settings)} settings, expected {numSettings}")
            settings = default_settings
    else:
        RichPrintError(f"Could not find {default_settings["SETTINGS_FILENAME"]} at full path {settingsPath}")
        # Create the settings file and write the default settings
        WriteYaml(settingsPath, default_settings)
    for key, value in settings.items():
        print(f"Setting {key} is {value}")'
    

    


    
    categoriesPath = f"{baseDir}/{settings["TEA_CATEGORIES_PATH"]}"
    hasCategoriesFile = os.path.exists(categoriesPath)
    if hasCategoriesFile and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found tea_categories.yml at full path {categoriesPath}")
        # Load the settings from json
        TeaCategories = loadTeaCategories(categoriesPath)
    else:
        RichPrintError(f"Could not find tea_categories.yml at full path {categoriesPath}")
        # Create the settings file and write the default settings
        saveTeaCategories(TeaCategories, categoriesPath)

    teaReviewCategoriesPath = f"{baseDir}/{settings["TEA_REVIEW_CATEGORIES_PATH"]}"
    hasTeaReviewCategoriesFile = os.path.exists(teaReviewCategoriesPath)
    if hasTeaReviewCategoriesFile and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found tea_review_categories.yml at full path {teaReviewCategoriesPath}")
        # Load the settings from json
        TeaReviewCategories = loadTeaReviewCategories(teaReviewCategoriesPath)
    else:
        RichPrintError(f"Could not find tea_review_categories.yml at full path {teaReviewCategoriesPath}")
        # Create the settings file and write the default settings
        saveTeaReviewCategories(TeaReviewCategories, teaReviewCategoriesPath)

    '''

    LoadAll()  # Load all data including settings, teas, categories, reviews, etc



    dataPath = f"{baseDir}/{settings["DIRECTORY"]}"
    session["dataPath"] = dataPath
    hasDataDirectory = os.path.exists(dataPath)
    if hasDataDirectory and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
    else:
        RichPrintError(f"Could not find {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
        MakeFilePath(dataPath)
        RichPrintInfo(f"Made {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")

    #global TeaStash
    #TeaStash = loadTeasReviews(settings["TEA_REVIEWS_PATH"])
    if len(TeaStash) == 0:
        RichPrintError("No teas found in stash! Potentially issue with loading teas. ")
        '''
        Tea1 = StashedTea(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"})
        Tea1.dateAdded = dt.datetime.now(tz=dt.timezone.utc)  # Default to now if not specified
        Tea1.addReview(Review(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 90, "Good tea"))
        Tea1.addReview(Review(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 70, "Okay tea"))
        Tea1.addReview(Review(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 60, "Bad tea"))
        Tea2 = StashedTea(2, "Tea 2", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"})
        Tea2.addReview(Review(2, "Tea 2", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 80, "Good tea"))
        Tea2.addReview(Review(2, "Tea 2", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 75, "Okay tea"))
        Tea2.dateAdded = dt.datetime.now(tz=dt.timezone.utc)  # Default to now if not specified
        TeaStash.append(Tea1)
        TeaStash.append(Tea2)
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])'''
    
    UI_CreateViewPort_MenuBar()



    Settings_SaveCurrentSettings()
    # Set the DearPyGui theme
    # Load fonts
    with dpg.font_registry():
        dpg.add_font("assets/fonts/Roboto-Regular.ttf", 16, tag="RobotoRegular")
        dpg.add_font("assets/fonts/Roboto-Bold.ttf", 16, tag="RobotoBold")
        # Merriweather 24pt regular
        dpg.add_font("assets/fonts/Merriweather_24pt-Regular.ttf", 16, tag="MerriweatherRegular")
        # Montserrat-regular
        dpg.add_font("assets/fonts/Montserrat-Regular.ttf", 16, tag="MontserratRegular")
        # Opensans regular
        dpg.add_font("assets/fonts/OpenSans-Regular.ttf", 18, tag="OpenSansRegular")

        # Test
        if settings["DEFAULT_FONT"] in session["validFonts"]:
            RichPrintInfo(f"Font {settings["DEFAULT_FONT"]} loaded")
            dpg.bind_font(settings["DEFAULT_FONT"])
        else:
            RichPrintError(f"Font {settings["DEFAULT_FONT"]} not found, defaulting to OpenSansRegular")
            dpg.bind_font("OpenSansRegular")
        
    dpg.set_global_font_scale(settings["UI_SCALE"])

    # Start first welcome window
    Menu_Welcome(None, None, None)

    
    startBackupThread(settings["AUTO_SAVE"])
    # Start the backup thread
    dp.Viewport.title = "RaTea"
    dp.Viewport.width = WindowSize[0]
    dp.Viewport.height = WindowSize[1]
    dp.Runtime.start()



if __name__ == "__main__":
    main()
