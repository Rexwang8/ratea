import uuid
import dearpypixl as dp
import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import os
import pickle
import re
import json
from rich.console import Console as RichConsole
import screeninfo
import yaml

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

def print_me():
    print("Hello World")

def Settings_SaveCurrentSettings():
    RichPrintSuccess("Saving settings")
    WriteYaml(session["settingsPath"], settings)

def UI_CreateViewPort_MenuBar():
    '''
    with dpg.viewport_menu_bar():
        with dpg.menu(label="Session"):
            dpg.add_menu_item(label="Timer", callback=UI_CreateTimerWindow)
            dpg.add_menu_item(label="Log", callback=print_me)
            dpg.add_menu_item(label="Stats", callback=print_me)
        with dpg.menu(label="Stash"):
            dpg.add_menu_item(label="Reviews", callback=print_me)
            dpg.add_menu_item(label="Edit", callback=UI_CreateTimerWindow)
            dpg.add_menu_item(label="Stats", callback=print_me)
        with dpg.menu(label="Tools"):
            dpg.add_menu_item(label="Timer", callback=UI_CreateTimerWindow)
            dpg.add_menu_item(label="Calculator", callback=print_me)
            dpg.add_menu_item(label="Notepad", callback=print_me)
        with dpg.menu(label="Visualize"):
            dpg.add_menu_item(label="Graph 1", callback=UI_CreateTimerWindow)
            dpg.add_menu_item(label="Graph 2", callback=print_me)
        

        with dpg.menu(label="Settings"):
            dpg.add_menu_item(label="Setting 1", callback=print_me, check=True)
            dpg.add_menu_item(label="Setting 2", callback=print_me)

        dpg.add_menu_item(label="Help", callback=Window_Settings)

        with dpg.menu(label="Library"):
            dpg.add_checkbox(label="Pick Me", callback=print_me)
            dpg.add_button(label="Press Me", callback=print_me)
            dpg.add_color_picker(label="Color Me", callback=print_me)
    '''
    with dp.ViewportMenuBar():
        with dp.Menu(label="Session"):
            dp.MenuItem(label="Timer", callback=Menu_Timer)
            dp.MenuItem(label="Log", callback=print_me)
            dp.MenuItem(label="Stats", callback=print_me)
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
        self.dpgWindow = dp.Window(label=self.title)
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
        pass
    def windowDefintion(self, window):
        # Define the window
        pass
    def DummyCallback(self, sender, data):
        print(f"Sender: {sender}, Data: {data}")

def Menu_Timer():
    Window_Timer("Timer", 500, 500)
# Window for timer
class Window_Timer(WindowBase):
    timer = 0
    def onCreateFirstTime(self):
        self.timer = 0
    def onCreate(self):
        self.timer = 0
    def onRefresh(self):
        self.timer = 0

    def windowDefintion(self, window):
        with window:
            dp.Text("Timer")
            dp.Text("Time: 0")
            dp.Button(label="Start", callback=self.DummyCallback)
            dp.Button(label="Stop", callback=self.DummyCallback)
            dp.Button(label="Reset", callback=self.DummyCallback)


def Menu_Settings():
    Window_Settings("Settings", 500, 500, exclusive=True)

class Window_Settings(WindowBase):
    def windowDefintion(self, window):
        with window:
            dp.Text("Settings")
            dp.Text("Username")
            dp.InputText(label="Username", default_value=settings["USERNAME"], callback=self.DummyCallback)
            dp.Text("Directory")
            dp.InputText(label="Directory", default_value=settings["DIRECTORY"], callback=self.DummyCallback)
            dp.Button(label="Save", callback=self.DummyCallback)
            dp.Button(label="Cancel", callback=self.DummyCallback)

def printWindowManager():
    print(dpg_windowManager)
def printSettings():
    for key, value in settings.items():
        print(f"Setting {key} is {value}")
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

    default_settings = {
        "UI_SCALE": Monitor_Scale,
        "SETTINGS_FILENAME": "user_settings.yml", # do not change
        "USERNAME": "John Puerh",
        "DIRECTORY": "ratea-data",
    }
    global settings
    settings = default_settings
    global session
    session = {}
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


    windowTest = WindowBase("Test Window", 500, 500)

    tagOfWindow = windowTest.getTag()
    getWindowFromTag = dpg.get_item_info(tagOfWindow)
    print(f"Tag of window: {tagOfWindow}")
    print(getWindowFromTag)

    demo.show_demo()
    dp.Viewport.title = "DearPyGui Demo"
    dp.Viewport.width = WindowSize[0]
    dp.Viewport.height = WindowSize[1]
    dp.Runtime.start()



if __name__ == "__main__":
    main()
