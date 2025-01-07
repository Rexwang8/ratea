import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import os
import pickle
import re
import json
from rich.console import Console as RichConsole
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

def WriteJson(path, data):
    with open(path, "w") as file:
        json.dump(data, file)
    RichPrintSuccess(f"Written {path} to file")

def ReadJson(path):
    with open(path, "r") as file:
        RichPrintSuccess(f"Read {path} from file")
        return json.load(file)
    

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


class WindowObject:
    uuid = ""
    name = ""
    Window = None
    saveOnClose = False
    def __init__(self, name, uuid, saveOnClose):
        self.name = name
        self.uuid = uuid
        self.Window = dpg.add_window(label=name, tag=uuid, width=500, height=500, on_close=lambda: dpg.delete_item(uuid))
    def getReference(self):
        return self.Window
    
    def deleteWindow(self):
        if self.saveOnClose:
            Settings_SaveCurrentSettings()
        dpg.delete_item(self.uuid)
        dpg_windowManager.pop(self.name)

    def reDraw(self):
        dpg.delete_item(self.uuid)
        self.Window = dpg.add_window(label=self.name, tag=self.uuid, width=500, height=500, on_close=lambda: dpg.delete_item(self.uuid))
        return self.Window




# Window buttons for each tab
def create_window(base_window_name, saveOnClose=False):
    window_name = f"{base_window_name}"
    window_UUID = dpg.generate_uuid()

    # Create the window object
    windowObject = WindowObject(window_name, window_UUID, saveOnClose)

    dpg_windowManager[window_name] = windowObject

    return windowObject

def UI_CreateTimerWindow():
    # if a window with the same name already exists, close old window
    if "Timer" in dpg_windowManager:
        # close the window
        dpg_windowManager["Timer"].deleteWindow()
    timerWindow = create_window("Timer")
    ref = timerWindow.getReference()
    # update title of window
    dpg.add_text(label="Timer Window", default_value="Timer Window", parent=ref)
    dpg.add_button(label="Start Timer", callback=lambda: print("Start Timer"), parent=ref)
    dpg.add_button(label="Stop Timer", callback=lambda: print("Stop Timer"), parent=ref)


def Window_Settings():
    if "Settings" in dpg_windowManager:
        # close the window
        dpg_windowManager["Settings"].deleteWindow()
    settingsWindow = create_window("Settings", True)
    ref = settingsWindow.getReference()
    # update title of window
    dpg.add_text(label="Settings Window", parent=ref)
    # add text input for username
    dpg.add_input_text(label="Username", default_value=settings["USERNAME"], parent=ref, callback=Settings_UpdateUsername, on_enter=True)
    # UI Scale slider
    dpg.add_slider_float(label="UI Font Scale", default_value=settings["UI_SCALE"], min_value=1, max_value=2, parent=ref, callback=Settings_UpdateUIScale)

    # List all vendors with an add button in a child window
    vendorsRef = Settings_DrawVendors()
    dpg_windowManager["Settings_Vendors"] = vendorsRef




    # Re-save button
    dpg.add_button(label="Save", callback=lambda: print("Save"), parent=ref)

def Settings_DrawVendors():
    RichPrintInfo("Drawing Settings/Vendors")
    
    # Get the parent window reference
    ref = dpg_windowManager["Settings"].Window
    print(f"Settings Window Reference: {ref}")
    
    # Check for and delete any old Vendors UI
    old_ref = dpg_windowManager.get("Settings_Vendors", None)
    if old_ref:
        dpg.delete_item(old_ref)
    
    # Create a new collapsing header for vendors
    VendorsRef = dpg.add_collapsing_header(label="Vendors", parent=ref, id="Settings_Vendors")
    dpg_windowManager["Settings_Vendors"] = VendorsRef  # Save reference for later

    # Add child window inside the collapsing header
    with dpg.child_window(label="Vendors Child", parent=VendorsRef, autosize_x=True, autosize_y=True):
        dpg.add_text("All Vendors Currently in the system")
        
        # Loop through vendors and create UI elements for each
        for idx, vendor in enumerate(settings["VENDORS"]):
            with dpg.group(horizontal=True):
                # Editable text box
                input_field = dpg.add_input_text(
                    label=f"Vendor {idx}",
                    default_value=vendor,
                    callback=Settings_ConfirmVendorEdit,
                    user_data=idx,
                )
                
                # Delete button
                dpg.add_button(
                    label="Delete",
                    callback=Settings_DeleteVendor,
                    user_data=idx  # Pass the vendor index
                )

    return VendorsRef

def Settings_ConfirmVendorEdit(sender, app_data, user_data):
    """Saves the edited vendor name and resets the color to default."""
    idx = user_data  # Vendor index
    new_value = app_data  # New value from the input box
    
    # Save the new vendor name in the settings
    settings["VENDORS"][idx] = new_value
    print(f"Vendor {idx} updated to '{new_value}'")
    
    Settings_SaveCurrentSettings()


def Settings_UpdateUsername(sender, app_data):
    settings["USERNAME"] = app_data
    print(f"Username: {settings['USERNAME']}")
    Settings_SaveCurrentSettings()


def Settings_DeleteVendor(sender, app_data, user_data):
    idx = user_data
    settings["VENDORS"].pop(idx)
    Settings_DrawVendors()
    Settings_SaveCurrentSettings()
    
def default_button(sender, app_data, user_data):
    item = dpg.get_item_info(sender)
    # Get the index of the sender
    print(f"Button: {sender} with data: {app_data} and user data: {user_data}")

def Settings_UpdateUIScale(sender, app_data):
    settings["UI_SCALE"] = app_data
    print(f"UI Scale: {settings['UI_SCALE']}")
    dpg.set_global_font_scale(settings["UI_SCALE"])
    # Save the settings
    Settings_SaveCurrentSettings()

def Settings_SaveCurrentSettings():
    RichPrintSuccess("Saving settings")
    WriteJson(session["settingsPath"], settings)
# Tab functionality
def add_tab_content(tab_name, button1, button2):
    dpg.add_button(button1, callback=lambda: create_window(tab_name, button1))
    dpg.add_button(button2, callback=lambda: create_window(tab_name, button2))

def print_me(sender):
    print(f"Menu Item: {sender}")


def UI_CreateViewPort_MenuBar():
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

# Main application
def main():
    RichPrintInfo("Starting Tea Tracker")
    baseDir = os.path.dirname(os.path.abspath(__file__))
    dpg.create_context()
    dpg.create_viewport(title='Custom Title', width=1600, height=1200)


    DEBUG_ALWAYSNEWJSON = True

    
    # Manages the UUIDs of the windows to allow for referencing them and multiple duplicate windows
    global dpg_windowManager
    dpg_windowManager = {}
    

   
    # Create the viewport menu bar
    UI_CreateViewPort_MenuBar()


    # Check if the file system can be accessed and has the settings file
    default_settings = {
        "UI_SCALE": 1.25,
        "SETTINGS_FILENAME": "user_settings.json", # do not change
        "USERNAME": "John Puerh",
        "DIRECTORY": "tmi-data",
        "VENDORS_FILENAME": "defaults/default_vendors.txt",
        "VENDORS": [],
        "TEATYPES_FILENAME": "defaults/default_types.txt",
        "TEATYPES": {},
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
        settings = ReadJson(settingsPath)
    else:
        RichPrintError(f"Could not find {default_settings["SETTINGS_FILENAME"]} at full path {settingsPath}")
        # Create the settings file and write the default settings
        WriteJson(settingsPath, default_settings)



    dataPath = f"{baseDir}/{settings["DIRECTORY"]}"
    session["dataPath"] = dataPath
    hasDataDirectory = os.path.exists(dataPath)
    if hasDataDirectory and not DEBUG_ALWAYSNEWJSON:
        RichPrintSuccess(f"Found {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
    else:
        RichPrintError(f"Could not find {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")
        MakeFilePath(dataPath)
        RichPrintInfo(f"Made {settings["DIRECTORY"]} at full path {os.path.abspath(settings["DIRECTORY"])}")

    vendorsPath = f"{baseDir}/{settings["VENDORS_FILENAME"]}"
    session["vendorsPath"] = vendorsPath
    hasVendorsFile = os.path.exists(vendorsPath)
    vendors = []
    if hasVendorsFile:
        RichPrintSuccess(f"Found {settings["VENDORS_FILENAME"]} at full path {os.path.abspath(settings["VENDORS_FILENAME"])}")
        # Load the vendors from the file
        with open(vendorsPath, "r") as file:
            data = file.readlines()

        for line in data:
            vendors.append(line.strip())

        for vendor in vendors:
            RichPrintInfo(f"Vendor: {vendor}")

        settings["VENDORS"] = vendors

    typesPath = f"{baseDir}/{settings["TEATYPES_FILENAME"]}"
    session["typesPath"] = typesPath
    hasTypesFile = os.path.exists(typesPath)
    types = {}
    if hasTypesFile:
        RichPrintSuccess(f"Found {settings["TEATYPES_FILENAME"]} at full path {os.path.abspath(settings["TEATYPES_FILENAME"])}")
        # Load the types from the file
        with open(typesPath, "r") as file:
            data = file.readlines()

        parent = None
        for line in data:
            level = line.count("-")
            name = line.replace("-", "").strip()

            if level == 0:
                parent = name
                types[parent] = []
            else:
                types[parent].append(name)

        for parent, children in types.items():
            RichPrintInfo(f"Parent: {parent}")
            for child in children:
                RichPrintInfo(f"Child: {child}")

        settings["TEATYPES"] = types
    

    for key, value in settings.items():
        RichPrintInfo(f"Setting {key} is {value}")

    Settings_SaveCurrentSettings()
    # Set the DearPyGui theme
    dpg.set_global_font_scale(settings["UI_SCALE"])

    if DEBUG_ALWAYSNEWJSON:
        #pop up settings window
        Window_Settings()
    

    demo.show_demo()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
