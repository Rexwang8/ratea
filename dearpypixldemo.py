import datetime as dt
import json
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
        print("Resized Window")
        print(sender, data)
    
    def create(self):
        self.onCreate()
        self.dpgWindow = dp.Window(label=self.title, on_close=self.onDelete)
        self.dpgWindow.width = self.width
        self.dpgWindow.height = self.height
        self.tag = self.dpgWindow.tag
        # Bind resize callback
        #dpg.add_item_resize_handler(callback=self.onResizedWindow, user_data=self.tag, parent=self.tag)
        self.windowDefintion(self.dpgWindow)

        print(self.dpgWindow)
        return self.dpgWindow
    def getTag(self):
        return self.tag
    def delete(self):
        self.onDelete()
        if self.dpgWindow is not None and self.dpgWindow.exists():
            dpg.delete_item(self.tag)
        
    def refresh(self):
        print(self.tag)
        print(self.dpgWindow.tag)
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


def Menu_Stash_Reviews(sender, app_data, user_data):
    w = 600 * settings["UI_SCALE"]
    h = 960 * settings["UI_SCALE"]
    stashReviews = Window_Stash_Reviews("Stash Reviews", w, h, exclusive=True, parentWindow=user_data[0], tea=user_data[1])

class Window_Stash_Reviews(WindowBase):
    parentWindow = None
    tea = None
    addReviewList = list()
    reviewsWindow = None
    def ShowAddReview(self, sender, app_data, user_data):
        self.reviewsWindow.set_value(user_data)
        self.reviewsWindow.show = True
    def AddReview(self, sender, app_data, user_data):
        # Add a review to the tea
        allAttributes = {}
        teaID = user_data.id
        for item in self.addReviewList:
            print(item)
            # If input text
            if type(item) == dp.InputText:
                allAttributes[item.label] = item.get_value()

        newReview = Review(teaID, user_data.name, user_data.year, allAttributes["Attributes"], allAttributes["Rating"], allAttributes["Notes"])
        user_data.addReview(newReview)

        # Save to file
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])
        
        # close the popup
        dpg.configure_item(self.reviewsWindow.tag, show=False)
        self.refresh()

    def GenerateEditReviewWindow(self, sender, app_data, user_data):
        print("Edit Review")
        editReviewWindow = dp.Window(label="Edit Review", width=500, height=500, modal=True, show=True)
        editReviewWindowItems = list()
        review = user_data
        with editReviewWindow:
            dp.Text("Edit Review")
            dp.Text("Attributes")
            defaultAttributes = review.attributes
            AttributesItem = dp.InputText(label="Attributes", default_value=defaultAttributes)
            dp.Text("Rating")
            defaultRating = review.rating
            RatingItem = dp.InputText(label="Rating", default_value=defaultRating)
            dp.Text("Notes")
            defaultNotes = review.notes
            notesItem = dp.InputText(label="Notes", default_value=defaultNotes)

            editReviewWindowItems.append(AttributesItem)
            editReviewWindowItems.append(RatingItem)
            editReviewWindowItems.append(notesItem)

            dp.Button(label="Save", callback=self.EditReview, user_data=(review, editReviewWindowItems, editReviewWindow))
            dp.Button(label="Cancel", callback=self.DummyCallback)
    def EditReview(self, sender, app_data, user_data):
        # Similar to adding a review, but will change the review
        review = user_data[0]
        allAttributes = {}
        for item in user_data[1]:
            # If input text
            if type(item) == dp.InputText:
                allAttributes[item.label] = item.get_value()
        
        review.attributes = allAttributes["Attributes"]
        review.rating = allAttributes["Rating"]
        review.notes = allAttributes["Notes"]
        self.refresh()
        # close the popup
        dpg.delete_item(user_data[2])

    def __init__(self, title, width, height, exclusive=False, parentWindow=None, tea=None):
        self.parentWindow = parentWindow
        self.tea = tea
        super().__init__(title, width, height, exclusive)

    def windowDefintion(self, window):
        tea = self.tea
        addReviewList = list()
        # create a new window for the reviews
        with window:
            hbarinfoGroup = dp.Group(horizontal=True)
            numReviews = len(tea.reviews)
            with hbarinfoGroup:
                # Num reviews, average rating, etc
                dp.Text(f"Num Reviews: {numReviews}")
                dp.Text(f"Average Rating: X")
            hbarActionGroup = dp.Group(horizontal=True)
            with hbarActionGroup:
                dp.Button(label="Add Review", callback=self.ShowAddReview, user_data=tea)
                # Add review popup
                self.reviewsWindow = dp.Window(label="Reviews", width=900, height=500, show=False, modal=True)
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
            reviewsTable = dp.Table(header=["Name", "Year", "Attributes", "Rating", "Notes", "Edit", "Delete"], resizable=True, reorderable=True, row_background=True)
            dpg.configure_item(reviewsTable, policy=dpg.mvTable_SizingFixedFit)
            with reviewsTable:
                # Add columns
                dp.TableColumn(label="Name" , width_stretch=True)
                dp.TableColumn(label="Year", width=75)
                dp.TableColumn(label="Attributes", width_stretch=True)
                dp.TableColumn(label="Rating", width=50)
                dp.TableColumn(label="Notes", width_stretch=True)
                dp.TableColumn(label="Edit", width=50)
                dp.TableColumn(label="Delete", width=50)
                # Add rows
                for i, review in enumerate(tea.reviews):
                    tableRow = dp.TableRow()
                    with tableRow:
                        dp.Text(label=review.name, default_value=review.name)
                        dp.Text(label=review.year, default_value=review.year)
                        
                        # Attribute
                        with dp.Group(horizontal=True):
                            dp.Text(label=review.attributes, default_value=review.attributes)
                            with dp.Tooltip(dpg.last_item()):
                                dp.Text(label=review.attributes, default_value=review.attributes)
                        dp.Text(label=review.rating, default_value=review.rating)
                        # Notes column
                        with dp.Group(horizontal=True):
                            dp.Text(label=review.notes, default_value=review.notes)
                            with dp.Tooltip(dpg.last_item()):
                                dp.Text(label=review.notes, default_value=review.notes)

                        dp.Button(label="Edit", callback=self.GenerateEditReviewWindow, user_data=review)
                        dp.Button(label="Delete", callback=self.DummyCallback)

def Menu_Stash():
    w = 600 * settings["UI_SCALE"]
    h = 960 * settings["UI_SCALE"]
    stash = Window_Stash("Stash", w, h, exclusive=True)

class Window_Stash(WindowBase):
    addTeaList = list()
    teasWindow = None

    def onDelete(self):
        # Close all popups
        if self.teasWindow != None:
            self.teasWindow.delete()
        # Invoke base class delete
        super().onDelete()

    def windowDefintion(self, window):
        self.addTeaList = list()
        self.addReviewList = list()
        with window:
            dp.Text("Stash")
            dp.Text("Teas")
            hgroupStats1 = dp.Group(horizontal=True)
            with hgroupStats1:
                # dummy stats
                dp.Text("Num Teas: 2")
                dp.Text("Num Reviews: 5")
                dp.Text("Average Rating: X")
            dp.Text(f"Last Tea Added: Tea 2 at {parseDTToString(dt.datetime.now(tz=dt.timezone.utc))}")
            dp.Text(f"Last Review Added: Tea 2 at {parseDTToString(dt.datetime.now(tz=dt.timezone.utc))}")
            dp.Separator()
            hgroupButtons = dp.Group(horizontal=True)
            with hgroupButtons:
                dp.Button(label="Add Tea", callback=self.ShowAddTea)
                dp.Button(label="Delete Tea", callback=self.DeleteTea)
                dp.Button(label="Import(TODO)", callback=self.DummyCallback)
                dp.Button(label="Export(TODO)", callback=self.DummyCallback)
                dp.Button(label="Refresh(TODO)", callback=self.DummyCallback)
            dp.Separator()

            # Table with collapsable rows for reviews
            teasTable = dp.Table()
            with teasTable:
                # Add columns from teaCategories
                for i, cat in enumerate(TeaCategories):
                    dp.TableColumn(label=cat.name, width=int(cat.widthPixels))
                dp.TableColumn(label="Reviews", width=250)
                dp.TableColumn(label="Edit", width=50)

                # Add rows
                for i, tea in enumerate(TeaStash):
                    tableRow = dp.TableRow()
                    with tableRow:
                        cat: TeaCategory
                        for i, cat in enumerate(TeaCategories):
                            # Convert attribbutes to json
                            displayValue = "N/A"
                            if cat.name == "Name":
                                displayValue = tea.name
                            else:
                                if type(tea.attributes) == str:
                                    attrJson = json.loads(tea.attributes)
                                    if cat.name in attrJson:
                                        displayValue = attrJson[cat.name]
                                else:
                                    if cat.name in tea.attributes:
                                        displayValue = tea.attributes[cat.name]
                            dp.Text(label=displayValue, default_value=displayValue)

                        # button that opens a modal with reviews
                        numReviews = len(tea.reviews)
                        dp.Button(label=f"{numReviews} Reviews", callback=self.generateReviewListWindow, user_data=tea)
                        dp.Button(label="Edit", callback=self.ShowEditTea, user_data=tea)

            # Add seperator and import/export buttons
            dp.Separator()
            

    def generateReviewListWindow(self, sender, app_data, user_data):
        Menu_Stash_Reviews(sender, app_data, (self, user_data))

    def generateTeasWiundow(self, sender, app_data, user_data):
        # If window is open, close it first
        if self.teasWindow != None and type(self.teasWindow) == dp.Window:
            self.deleteTeasWindow()

        teasData = None
        if user_data[1] == "add":
            teasData = None
        elif user_data[1] == "edit":
            teasData = user_data[0]

        # Create a new window
        self.teasWindow = dp.Window(label="Teas", width=500, height=500, show=True)
        with self.teasWindow:
            dp.Text("Teas")
            dp.Text("Name")
            nameItem = dp.InputText(label="Name", default_value="")
            if teasData != None and teasData.name != None:
                nameItem.set_value(teasData.name)
            self.addTeaList.append(nameItem)

            for cat in TeaCategories:
                if cat.name == "Name":
                    continue
                dp.Text(cat.name)
                catItem = dp.InputText(label=cat.name, default_value=cat.defaultValue)
                if teasData != None and teasData.attributes != None:
                    print(teasData.attributes)
                    attrJson = None
                    try:
                        try:
                            attrJson = json.loads(teasData.attributes)
                        except:
                            attrJson = teasData.attributes.replace("'", "\"")
                            attrJson = json.loads(attrJson)
                    except:
                        attrJson = teasData.attributes
                    if cat.name in attrJson:
                        catItem.set_value(attrJson[cat.name])
                self.addTeaList.append(catItem)

            #dp.Text("Year")
            #yearItem = dp.InputText(label="Year", default_value="2021")
            #if teasData != None and teasData.year != None:
            #    yearItem.set_value(teasData.year)
            #self.addTeaList.append(yearItem)
            #dp.Text("Attributes")
            #attrItem = dp.InputText(label="Attributes", default_value="{'Type': 'Raw Puerh', 'Region': 'Yunnan'}")
            #if teasData != None and teasData.attributes != None:
            #    attrItem.set_value(teasData.attributes)
            #self.addTeaList.append(attrItem)
            # Add buttons
            if user_data[1] == "add":
                dp.Button(label="Add", callback=self.AddTea, user_data=teasData)
            elif user_data[1] == "edit":
                dp.Button(label="Edit", callback=self.EditTea, user_data=teasData)
            dp.Button(label="Delete", callback=self.DeleteTea)
            dp.Button(label="Cancel", callback=self.deleteTeasWindow)

    def deleteTeasWindow(self):
        # If window is open, close it first
        if self.teasWindow != None:
            self.teasWindow.delete()
            self.teasWindow = None
            self.addTeaList = list()
        else:
            print("No window to delete")



    def ShowAddTea(self, sender, app_data, user_data):
        self.generateTeasWiundow(sender, app_data, user_data=(None,"add"))
    def ShowEditTea(self, sender, app_data, user_data):
        self.generateTeasWiundow(sender, app_data, user_data=(user_data,"edit"))
                   
                    


    def AddTea(self, sender, app_data, user_data):
        # All input texts and other input widgets are in the addTeaGroup
        # create a new tea and add it to the stash
        allAttributes = {}
        for item in self.addTeaList:
            # If input text
            if type(item) == dp.InputText and item.exists():
                allAttributes[item.label] = item.get_value()

        
        newTea = StashedTea(len(TeaStash) + 1, allAttributes["Name"], allAttributes["Year"], allAttributes)
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
        for item in self.addTeaList:
            # If input text
            if type(item) == dp.InputText:
                allAttributes[item.label] = item.get_value()

        newTea = StashedTea(tea.id, allAttributes["Name"], allAttributes["Year"], allAttributes)
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
        print("Delete Tea")


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

class TeaCategory:
    name = ""
    categoryType = ""
    editable = False
    color = ""
    defaultValue = None
    widthPixels = 100
    def __init__(self, name, categoryType, editable, widthPixels=100):
        self.name = name
        self.categoryType = categoryType
        self.editable = editable
        if categoryType == "string":
            self.defaultValue = ""
        elif categoryType == "int":
            self.defaultValue = 0
        elif categoryType == "float":
            self.defaultValue = 0.0
        self.widthPixels = widthPixels

class ReviewCategory:
    name = ""
    categoryType = ""
    editable = True
    widthPixels = 100
    def __init__(self, name, categoryType, editable, widthPixels=100):
        self.name = name
        self.categoryType = categoryType
        self.editable = editable
        self.widthPixels = widthPixels
        

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
                    dp.Button(label="Add Stash Category", callback=self.addCategory)
                    with dpg.child_window(label="Tea Categories", width=scaledWidth, height=600):
                        self.teaCategoryGroup = dp.Group(horizontal=False)
                        dp.Separator()
                        self.generateTeaCategoriesList(self.teaCategoryGroup)

                # Vertical split for review
                # Review
                with dp.Group(horizontal=False):
                    dp.Text("Review Categories")
                    dp.Button(label="Add Review Category", callback=self.DummyCallback)
                    with dpg.child_window(label="Review Categories", width=scaledWidth, height=600):
                        dp.Separator()
                        self.teaReviewGroup = dp.Group(horizontal=False)
                        self.generateReviewCategoriesList()


    def generateTeaCategoriesList(self, window):
        with self.teaCategoryGroup:
            for i, category in enumerate(TeaCategories):
                with dp.Group(horizontal=True):
                    scaledWidth = 250 * settings["UI_SCALE"]
                    scaledHeight = 60 * settings["UI_SCALE"]
                    with dp.ChildWindow(width=scaledWidth, height=scaledHeight):
                        dp.Text(f"{i+1}: {category.name} -- {category.categoryType}")
                        dp.Text(f"Editable: {category.editable}")
                        with dp.Group(horizontal=True):
                            if category.editable:
                                dp.Button(label="Edit", callback=self.showEditCategory, user_data=i)
                                dp.Button(label="Delete", callback=self.deleteCategory, user_data=i)
                            else:
                                dp.Text("[-X-]")
                                dp.Text("[-X-]")
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
            dp.Separator()

    def generateReviewCategoriesList(self):
        with self.teaReviewGroup:
            for i, category in enumerate(TeaReviewCategories):
                with dp.Group(horizontal=True):
                    scaledWidth = 250 * settings["UI_SCALE"]
                    scaledHeight = 60 * settings["UI_SCALE"]
                    with dp.ChildWindow(width=scaledWidth, height=scaledHeight):
                        dp.Text(f"{i+1}: {category.name} -- {category.categoryType}")
                        dp.Text(f"Editable: {category.editable}")
                        with dp.Group(horizontal=True):
                            if category.editable:
                                dp.Button(label="Edit", callback=self.showEditReviewCategory, user_data=i)
                                dp.Button(label="Delete", callback=self.deleteReviewCategory, user_data=i)
                            else:
                                dp.Text("[-X-]")
                                dp.Text("[-X-]")
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

    

    def showEditCategory(self, sender, app_data, user_data):
        # Create a popup window to edit the category
        editCategoryWindow = dp.Window(label="Edit Category", width=500, height=500, modal=True, show=True)
        editCategoryWindowItems = dict()
        category = TeaCategories[user_data]

        with editCategoryWindow:
            dp.Text(f"{category.name}")
            dp.Text(f"Editable: {category.editable}")
            dp.Text(f"Width: {category.widthPixels}")
            validTypes = session["validTypesCategory"]
            dp.Separator()
            dp.Text(f"Type of Category")
            catItem = dp.Listbox(items=validTypes, default_value=category.categoryType)
            if category.categoryType not in validTypes:
                catItem.set_value("ERR: Assume String")

            editCategoryWindowItems["Type"] = catItem
            dp.Separator()

            with dp.Group(horizontal=True):
                dp.Button(label="Save", callback=self.EditCategory, user_data=(category, editCategoryWindowItems, editCategoryWindow))
                dp.Button(label="Cancel", callback=editCategoryWindow.delete)
                # Help question mark
                dp.Button(label="?")
                # Hover tooltip
                with dpg.tooltip(dpg.last_item()):
                    dp.Text("Edit the category name, type, and width in pixels")
        print("Edit Category")

    def EditCategory(self, sender, app_data, user_data):
        category = user_data[0]
        allAttributes = user_data[1]
        category.categoryType = allAttributes["Type"].get_value()
        if category.categoryType not in session["validTypesCategory"]:
            category.categoryType = "string"
        #category.editable = allAttributes["Editable"]
        #category.widthPixels = int(float(allAttributes["Width"]))

        saveTeaCategories(TeaCategories, settings["TEA_CATEGORIES_PATH"])
        # close the popup
        self.refresh()
        dpg.delete_item(user_data[2])

    def showEditReviewCategory(self, sender, app_data, user_data):
        print("Edit Review Category")
        # Create a popup window to edit the review category
        editReviewCategoryWindow = dp.Window(label="Edit Review Category", width=500, height=500, modal=True, show=True)
        editReviewCategoryWindowItems = dict()
        category = TeaReviewCategories[user_data]

        with editReviewCategoryWindow:
            dp.Text(f"{category.name}")
            dp.Text(f"Editable: {category.editable}")
            dp.Text(f"Width: {category.widthPixels}")
            validTypes = session["validTypesReviewCategory"]
            dp.Separator()
            dp.Text(f"Type of Category")
            catItem = dp.Listbox(items=validTypes, default_value=category.categoryType)
            if category.categoryType not in validTypes:
                catItem.set_value("ERR: Assume String")

            editReviewCategoryWindowItems["Type"] = catItem
            dp.Separator()

            with dp.Group(horizontal=True):
                dp.Button(label="Save", callback=self.EditReviewCategory, user_data=(category, editReviewCategoryWindowItems, editReviewCategoryWindow))
                dp.Button(label="Cancel", callback=editReviewCategoryWindow.delete)
                # Help question mark
                dp.Button(label="?")
                # Hover tooltip
                with dpg.tooltip(dpg.last_item()):
                    dp.Text("Edit the review category name, type, and width in pixels")

    def EditReviewCategory(self, sender, app_data, user_data):
        category = user_data[0]
        allAttributes = user_data[1]
        category.categoryType = allAttributes["Type"].get_value()
        if category.categoryType not in session["validTypesReviewCategory"]:
            category.categoryType = "string"
        #category.editable = allAttributes["Editable"]
        #category.widthPixels = int(float(allAttributes["Width"]))


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
        print(f"Delete Review Category - {user_data}")
        # Delete the category
        TeaReviewCategories.pop(user_data)
        saveTeaReviewCategories(TeaReviewCategories, settings["TEA_REVIEW_CATEGORIES_PATH"])
        
        # Refresh the window
        self.refresh()

    def addCategory(self, sender, app_data, user_data):
        addCategoryWindow = dp.Window(label="Add Category", width=500, height=500, modal=True, show=True)
        addCategoryWindowItems = list()
        with addCategoryWindow:
            dp.Text("Add Category")
            for i, category in enumerate(TeaCategories):
                dp.Text(f"{i+1}: {category.name} -- {category.categoryType}")
                dp.Text(f"Editable: {category.editable}")
                dp.Text(f"Width: {category.widthPixels}")
                catItem = dp.InputText(label=category.name, default_value=category.categoryType)
                addCategoryWindowItems.append(catItem)

            dp.Button(label="Add", callback=self.AddCategory, user_data=(addCategoryWindowItems, addCategoryWindow))
            dp.Button(label="Cancel", callback=addCategoryWindow.delete)

    def AddCategory(self, sender, app_data, user_data):
        allAttributes = {}
        for item in user_data[0]:
            # If input text
            if type(item) == dp.InputText:
                allAttributes[item.label] = item.get_value()
        newCategory = TeaCategory(allAttributes["Name"], allAttributes["Type"], True)
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

class Manager_Windows:
    windows = {}
    def __init__(self):
        self.windows = {}
    def addWindow(self, window):
        self.windows[window.title] = window
    def removeWindow(self, window: WindowBase):
        # Trigger the delete function
        del self.windows[window.utitle]
        window.delete()
        
            
        
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

    def exportPersistantWindows(self):
        # Export all windows to a file
        allData = []
        for key, value in self.windows.items():
            title = value.title
            if value.persist:
                yml = value.exportYML()
                allData.append({title: yml})

        filePath = f"{settings['DIRECTORY']}/persistant_windows.yml"
        WriteYaml(filePath, allData)
        print(allData)
        return allData
    
    def importPersistantWindows(self):
        # Import all windows from a file
        filePath = f"{settings['DIRECTORY']}/persistant_windows.yml"
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

def saveTeasReviews(stash, path):
    # Save as one file in yml format
    allData = []
    for tea in stash:
        teaData = {
            "name": tea.name,
            "year": tea.year,
            "attributes": tea.attributes,
            "reviews": []
        }
        for review in tea.reviews:
            reviewData = {
                "name": review.name,
                "year": review.year,
                "attributes": review.attributes,
                "rating": review.rating,
                "notes": review.notes
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
    for teaData in allData:
        tea = StashedTea(i, teaData["name"], teaData["year"], teaData["attributes"])
        for reviewData in teaData["reviews"]:
            review = Review(i, reviewData["name"], reviewData["year"], reviewData["attributes"], reviewData["rating"], reviewData["notes"])
            tea.addReview(review)
        TeaStash.append(tea)
        i += 1
    return TeaStash

def saveTeaCategories(categories, path):
    # Save as one file in yml format
    allData = []
    for category in categories:
        categoryData = {
            "name": category.name,
            "categoryType": category.categoryType,
            "editable": category.editable,
            "widthPixels": category.widthPixels
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
        category = TeaCategory(categoryData["name"], categoryData["categoryType"], categoryData["editable"], categoryData["widthPixels"])
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
        category = ReviewCategory(categoryData["name"], categoryData["categoryType"], categoryData["editable"], categoryData["widthPixels"])
        TeaReviewCategories.append(category)
    return TeaReviewCategories

def saveTeaReviewCategories(categories, path):
    # Save as one file in yml format
    allData = []
    for category in categories:
        categoryData = {
            "name": category.name,
            "categoryType": category.categoryType,
            "editable": category.editable,
            "widthPixels": category.widthPixels
        }
        allData.append(categoryData)

    WriteYaml(path, allData)

def SaveAll():
    # Save all data
    saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])
    saveTeaCategories(TeaCategories, session["categoriesPath"])
    saveTeaReviewCategories(TeaReviewCategories, session["reviewCategoriesPath"])
    WriteYaml(session["settingsPath"], settings)

def LoadAll():
    # Load all data
    global settings
    settings = ReadYaml(session["settingsPath"])
    global TeaStash
    TeaStash = loadTeasReviews(settings["TEA_REVIEWS_PATH"])
    global TeaCategories
    TeaCategories = loadTeaCategories(session["categoriesPath"])
    global TeaReviewCategories
    TeaReviewCategories = loadTeaReviewCategories(session["reviewCategoriesPath"])
    
    print(f"Loaded {len(TeaStash)} teas and {len(TeaCategories)} categories")



def UI_CreateViewPort_MenuBar():
    with dp.ViewportMenuBar():
        with dp.Menu(label="Session"):
            dp.MenuItem(label="Log", callback=Menu_Stash)
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
            dp.Button(label="Sort Windows", callback=windowManager.sortWindows)
            dp.Button(label="Export Windows", callback=windowManager.exportPersistantWindows)
            dp.Button(label="Import Windows", callback=windowManager.importPersistantWindows)
            dp.Button(label="Demo", callback=demo.show_demo)

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

    DEBUG_ALWAYSNEWJSON = False

    global windowManager
    windowManager = Manager_Windows()
    windowManager.sortWindows()

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
    }
    numSettings = len(default_settings)
    global settings
    settings = default_settings
    global session
    session = {}
    global TeaStash
    global TeaCategories
    TeaCategories = []
    TeaCategories.append(TeaCategory("Name", "string", False))
    TeaCategories.append(TeaCategory("Type", "string", True))
    TeaCategories.append(TeaCategory("Year", "int", True))
    TeaCategories.append(TeaCategory("Remaining", "float", False))

    global TeaReviewCategories
    TeaReviewCategories = []
    TeaReviewCategories.append(ReviewCategory("Name", "string", False))
    TeaReviewCategories.append(ReviewCategory("Date", "string", False))
    TeaReviewCategories.append(ReviewCategory("Rating", "int", True))
    TeaReviewCategories.append(ReviewCategory("Notes", "string", True))


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

    # Get a list of all valid types for Categories
    session["validTypesCategory"] = ["string", "int", "float"]
    session["validTypesReviewCategory"] = ["string", "int", "float"]



    dataPath = f"{baseDir}/{settings["DIRECTORY"]}"
    session["dataPath"] = dataPath
    hasDataDirectory = os.path.exists(dataPath)
    if hasDataDirectory and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
    else:
        RichPrintError(f"Could not find {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
        MakeFilePath(dataPath)
        RichPrintInfo(f"Made {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")

    global TeaStash
    TeaStash = loadTeasReviews(settings["TEA_REVIEWS_PATH"])
    if len(TeaStash) == 0:
        Tea1 = StashedTea(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"})
        Tea1.addReview(Review(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 90, "Good tea"))
        Tea1.addReview(Review(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 70, "Okay tea"))
        Tea1.addReview(Review(1, "Tea 1", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 60, "Bad tea"))
        Tea2 = StashedTea(2, "Tea 2", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"})
        Tea2.addReview(Review(2, "Tea 2", 2021, {"Type": "Raw Puerh", "Region": "Yunnan"}, 80, "Good tea"))
        TeaStash.append(Tea1)
        TeaStash.append(Tea2)
        saveTeasReviews(TeaStash, settings["TEA_REVIEWS_PATH"])
    
    UI_CreateViewPort_MenuBar()

    Settings_SaveCurrentSettings()
    # Set the DearPyGui theme
    dpg.set_global_font_scale(settings["UI_SCALE"])

    dp.Viewport.title = "RaTea"
    dp.Viewport.width = WindowSize[0]
    dp.Viewport.height = WindowSize[1]
    dp.Runtime.start()



if __name__ == "__main__":
    main()
