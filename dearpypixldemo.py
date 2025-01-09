import datetime as dt
import time
import uuid
import dearpypixl as dp
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import os
import pickle
import re
from rich.console import Console as RichConsole
import screeninfo
import yaml
import threading
import pyperclip

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

def parseDTToString(stringOrDT):
    format = settings["DATE_FORMAT"]
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
    return datetimeobj.strftime(format)
    

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

# Callback function to sort and re-layout windows
def sort_and_layout_windows():
    global dpg_windowManager

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
    sorted_windows = sorted(dpg_windowManager.items(), key=lambda x: x[0])

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




# Defines one tea that has been purchased and may have reviews
class StashedTea:
    id = 0
    name = ""
    year = 1900
    attributes = {}
    reviews = []
    calculated = {}
    def __init__(self, id, name, year, attributes):
        self.id = id
        self.name = name
        self.year = year
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
    name = ""
    year = 1900
    attributes = {}
    calculated = {}
    finalScore = 0
    def __init__(self, parentID, name, year, attributes, rating, notes):
        self.parentID = parentID
        self.name = name
        self.year = year
        self.attributes = attributes
        self.rating = rating
        self.notes = notes
        self.calculated = {}
        self.finalScore = 0
    def calculate(self):
        # call all the calculate functions
        self.calculateFinalScore()
    def calculateFinalScore(self):
        # calculate the final score
        self.finalScore = self.rating

class WindowBase:
    tag = 0
    dpgWindow = None
    exclusive = False
    def __init__(self, title, width, height, exclusive=False):
        self.title = title
        self.width = width
        self.height = height
        self.exclusive = exclusive

        # if not exclusive, create a random number to add to the title
        utitle = title
        if not exclusive:
            rand = uuid.uuid4().hex[:6]
            utitle = f"{title} {rand}"
            while utitle in dpg_windowManager:
                rand = uuid.uuid4().hex[:6]
                utitle = f"{title} {rand}"
        
        # add the window to the window manager, if exclusive, overwrite the title
        if exclusive and title in dpg_windowManager:
            dpg_windowManager[title].delete()
        dpg_windowManager[utitle] = self
            
        self.onCreateFirstTime()
        self.create()
    
    def create(self):
        self.onCreate()
        self.dpgWindow = dp.Window(label=self.title, on_close=self.onDelete)
        self.dpgWindow.width = self.width
        self.dpgWindow.height = self.height
        self.tag = self.dpgWindow.tag
        self.windowDefintion(self.dpgWindow)

        print(self.dpgWindow)
        return self.dpgWindow
    def getTag(self):
        return self.tag
    def delete(self):
        self.onDelete()
        dpg.delete_item(self.tag)
        del dpg_windowManager[self.title]
    def refresh(self):
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
        del dpg_windowManager[self.title]

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

def Menu_Timer():
    w = 225 * settings["UI_SCALE"]
    h = 250 * settings["UI_SCALE"]
    timer = Window_Timer("Timer", w, h, exclusive=False)
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
    def onCreateFirstTime(self):
        # init new addresses for variables
        self.previousTimes = list()
    def onCreate(self):
        self.timer = 0
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
                    dp.InputText(default_value=self.titleText, width=170, multiline=False, callback=self.updateTitleText)

            self.display = dp.Text(label=f"{self.formatTimeDisplay(self.timer)}")

            # in horizontal layout
            with dp.Group(horizontal=True):

                dp.Button(label="Start", callback=self.startTimer)
                dp.Button(label="Stop", callback=self.stopTimer)
                dp.Button(label="Reset", callback=self.resetTimer)

            # Group that contains an input text raw and a button to copy to clipboard
            with dp.Group(horizontal=True):
                dp.Button(label="Clipboard", callback=self.copyRawTimeToClipboard)
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
            displayResult = f"{int(m):02d}:{int(s):.2f} ({timeRaw:.2f}s)"
        if m > 60:
            m = timeRaw % 60
            h = timeRaw // 60
            displayResult = f"{int(h):02d}:{int(m):02d}:{int(s):.2f} ({timeRaw:.2f}s)"
        return displayResult
    
    # Thread update 10x per second
    def updateTimerLoop(self):
        while not self.stopThreadFlag:
            if self.timerRunning:
                self.timer = time.time() - self.startTime
                self.display.set_value(self.formatTimeDisplay(self.timer))
            time.sleep(0.1)

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
        self.updateChildWindow()
        self.updateDefaultValueDisplay()


            



def Menu_Settings():
    settingsWindow = Window_Settings("Settings", 500, 500, exclusive=True)

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
    # Callback function for the input text to update the settings
    def UpdateSettings(self, sender, data, user_data):
        settings[user_data] = data
        Settings_SaveCurrentSettings()
        # ui scale
        if user_data == "UI_SCALE":
            dpg.set_global_font_scale(settings["UI_SCALE"])

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


def Menu_Stash():
    w = 480 * settings["UI_SCALE"]
    h = 600 * settings["UI_SCALE"]
    stash = Window_Stash("Stash", w, h, exclusive=True)

class Window_Stash(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("Stash")
            dp.Text("Teas")
            hgroupStats1 = dp.Group(horizontal=True)
            with hgroupStats1:
                # dummy stats
                dp.Text("Num Teas: 2")
                dp.Text("Num Reviews: 5")
                dp.Text("Average Rating: X")
            #timezone = zoneinfo.ZoneInfo(settings["TIMEZONE"])
            dp.Text(f"Last Tea Added: Tea 2 at {parseDTToString(dt.datetime.now(tz=dt.timezone.utc))}")
            dp.Text(f"Last Review Added: Tea 2 at {parseDTToString(dt.datetime.now(tz=dt.timezone.utc))}")
            dp.Separator()
            hgroupButtons = dp.Group(horizontal=True)
            with hgroupButtons:
                dp.Button(label="Add Tea", callback=self.AddTea)
                dp.Button(label="Edit Tea", callback=self.EditTea)
                dp.Button(label="Delete Tea", callback=self.DeleteTea)
                dp.Button(label="Import", callback=self.DummyCallback)
                dp.Button(label="Export", callback=self.DummyCallback)
            dp.Separator()

            # Table with collapsable rows for reviews
            teasTable = dp.Table(header=["Name", "Year", "Attributes", "Reviews"], width=650, height=100)
            with teasTable:
                # Add columns
                dp.TableColumn(label="Name", width=100)
                dp.TableColumn(label="Year", width=100)
                dp.TableColumn(label="Attributes", width=200)
                dp.TableColumn(label="Reviews", width=250)

                # Add rows
                for i, tea in enumerate(TeaStash):
                    tableRow = dp.TableRow()
                    with tableRow:
                                
                        dp.Text(label=tea.name, default_value=tea.name)
                        dp.Text(label=tea.year, default_value=tea.year)
                        dp.Text(label=tea.attributes, default_value=tea.attributes)

                        # button that opens a modal with reviews
                        numReviews = len(tea.reviews)
                        dp.Button(label=f"{numReviews} Reviews", user_data=tea)
                        with dpg.popup(modal=True, parent=dpg.last_item(), mousebutton=dpg.mvMouseButton_Left):
                            
                            hbarinfoGroup = dp.Group(horizontal=True)
                            with hbarinfoGroup:
                                # Num reviews, average rating, etc
                                dp.Text(f"Num Reviews: {numReviews}")
                                dp.Text(f"Average Rating: X")

                            hbarActionGroup = dp.Group(horizontal=True)
                            with hbarActionGroup:
                                dp.Button(label="Add Review", callback=self.AddReview)

                            #seperator
                            dp.Separator()

                            reviewsTable = dp.Table(header=["Name", "Year", "Attributes", "Rating", "Notes", "Edit", "Delete"], width=750, height=100)
                            with reviewsTable:
                                # Add columns
                                dp.TableColumn(label="Name", width=100)
                                dp.TableColumn(label="Year", width=100)
                                dp.TableColumn(label="Attributes", width=200)
                                dp.TableColumn(label="Rating", width=50)
                                dp.TableColumn(label="Notes", width=200)
                                dp.TableColumn(label="Edit", width=50)
                                dp.TableColumn(label="Delete", width=50)
                                # Add rows
                                for i, review in enumerate(tea.reviews):
                                    tableRow = dp.TableRow()
                                    with tableRow:
                                        dp.Text(label=review.name, default_value=review.name)
                                        dp.Text(label=review.year, default_value=review.year)
                                        dp.Text(label=review.attributes, default_value=review.attributes)
                                        dp.Text(label=review.rating, default_value=review.rating)
                                        dp.Text(label=review.notes, default_value=review.notes)
                                        dp.Button(label="Edit", callback=self.DummyCallback)
                                        dp.Button(label="Delete", callback=self.DummyCallback)
            # Add seperator and import/export buttons
            dp.Separator()
            



                   
                    


    def AddTea(self, sender, data):
        print("Add Tea")
    def EditTea(self, sender, data):
        print("Edit Tea")
    def DeleteTea(self, sender, data):
        print("Delete Tea")
    def AddReview(self, sender, data):
        print("Add Review")
    def EditReview(self, sender, data):
        print("Edit Review")
    def DeleteReview(self, sender, data):
        print("Delete Review")


def Menu_Notepad():
    w = 480 * settings["UI_SCALE"]
    h = 600 * settings["UI_SCALE"]
    notepad = Window_Notepad("Notepad", w, h, exclusive=False)

class Window_Notepad(WindowBase):
    text = ""
    textInput = None
    def windowDefintion(self, window):
        with window:
            dp.Text("Notepad")
            # Toolbar with clear
            hgroupToolbar = dp.Group(horizontal=True)
            with hgroupToolbar:
                dp.Button(label="Clear", callback=self.clearNotepad)

            # Text input
            defaultText = "Some space for your notes!"
            self.textInput = dp.InputText(label="Notes", default_value=defaultText, multiline=True, width=450, height=550)
            dp.Separator()

    def clearNotepad(self, sender, data):
        self.textInput.set_value("")


def UI_CreateViewPort_MenuBar():
    with dp.ViewportMenuBar():
        with dp.Menu(label="Session"):
            dp.MenuItem(label="Timer", callback=Menu_Timer)
            dp.MenuItem(label="Log", callback=Menu_Stash)
            dp.MenuItem(label="Notepad", callback=Menu_Notepad)
            dp.Button(label="Settings", callback=Menu_Settings)
        with dp.Menu(label="Stash"):
            dp.MenuItem(label="Reviews", callback=print_me)
            dp.MenuItem(label="Edit", callback=print_me)
            dp.MenuItem(label="Stats", callback=print_me)
        with dp.Menu(label="Tools"):
            dp.MenuItem(label="Timer", callback=print_me)
            dp.MenuItem(label="Calculator", callback=print_me)
            dp.MenuItem(label="Notepad", callback=print_me)
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
            dp.Button(label="Windows", callback=printWindowManager)
            dp.Button(label="Settings", callback=printSettings)
            dp.Button(label="Threads", callback=printThreads)
            dp.Button(label="Sort Windows", callback=sort_and_layout_windows)
            dp.Button(label="Demo", callback=demo.show_demo)



def printWindowManager():
    print(dpg_windowManager)
def printSettings():
    for key, value in settings.items():
        print(f"Setting {key} is {value}")
def printThreads():
    print(threading.enumerate())
def main():
    RichPrintInfo("Starting Tea Tracker")
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

    DEBUG_ALWAYSNEWJSON = True

    global dpg_windowManager
    dpg_windowManager = {}

    global default_settings
    default_settings = {
        "UI_SCALE": Monitor_Scale,
        "SETTINGS_FILENAME": "user_settings.yml", # do not change
        "USERNAME": "John Puerh",
        "DIRECTORY": "ratea-data",
        "DATE_FORMAT": "%Y-%m-%d",
        "TIMEZONE": "UTC", # default to UTC, doesn't really matter since time is not used
        "TIMER_WINDOW_LABEL": True,
        "TIMER_PERSIST_LAST_WINDOW": True # TODO
    }
    global settings
    settings = default_settings
    global session
    session = {}
    global TeaStash
    TeaStash = []
    Tea1 = StashedTea(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"})
    Tea1.addReview(Review(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 90, "Good tea"))
    Tea1.addReview(Review(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 70, "Okay tea"))
    Tea1.addReview(Review(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 60, "Bad tea"))
    Tea2 = StashedTea(2, "Tea 2", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"})
    Tea2.addReview(Review(2, "Tea 2", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 80, "Good tea"))
    TeaStash.append(Tea1)
    TeaStash.append(Tea2)

    settingsPath = f"{baseDir}/{default_settings['SETTINGS_FILENAME']}"
    session["settingsPath"] = settingsPath
    hasSettingsFile = os.path.exists(settingsPath)
    if hasSettingsFile and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found {default_settings["SETTINGS_FILENAME"]} at full path {settingsPath}")
        # Load the settings from json
        settings = ReadYaml(settingsPath)
    else:
        RichPrintError(f"Could not find {default_settings["SETTINGS_FILENAME"]} at full path {settingsPath}")
        # Create the settings file and write the default settings
        WriteYaml(settingsPath, default_settings)



    dataPath = f"{baseDir}/{settings["DIRECTORY"]}"
    session["dataPath"] = dataPath
    hasDataDirectory = os.path.exists(dataPath)
    if hasDataDirectory and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
    else:
        RichPrintError(f"Could not find {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
        MakeFilePath(dataPath)
        RichPrintInfo(f"Made {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
    
    UI_CreateViewPort_MenuBar()

    Settings_SaveCurrentSettings()
    # Set the DearPyGui theme
    dpg.set_global_font_scale(settings["UI_SCALE"])

    dp.Viewport.title = "DearPyGui Demo"
    dp.Viewport.width = WindowSize[0]
    dp.Viewport.height = WindowSize[1]
    dp.Runtime.start()



if __name__ == "__main__":
    main()
