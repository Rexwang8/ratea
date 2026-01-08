# Helper file to store all the texts used in the app



# Text definition that can be used to define things like fonts and colors in the future.

import textwrap
import time

def wrapLongLines(text, breakwidth=70):
        # Wraps long lines of text to a specified width
        lines = text.split("\n")
        wrappedLines = []
        for line in lines:
            if len(line) > breakwidth-20:
                wrappedLines.extend(textwrap.wrap(line, width=breakwidth, replace_whitespace=False, break_on_hyphens=False))
            else:
                wrappedLines.append(line)
        return "\n".join(wrappedLines)

def sanitizeInputLineString(string):
    # strip, remove single and double quotes, ascii only
    cleanString = string.strip()
    cleanString = cleanString.replace("'", "")
    cleanString = cleanString.replace('"', "")
    cleanString = ''.join(c for c in cleanString if ord(c) < 128)
    cleanString = cleanString.replace("\n", "")
    cleanString = cleanString.replace("\r", "")
    cleanString = cleanString.replace("\t", "")
    cleanString = cleanString.replace("\\", "")
    cleanString = cleanString.replace(";", "")
    cleanString = cleanString.replace("'", "")
    return cleanString

def sanitizeInputMultiLineString(string):
    # strip, remove single and double quotes, ascii only
    cleanString = string.strip()
    cleanString = cleanString.replace("'", "")
    cleanString = cleanString.replace('"', "")
    cleanString = ''.join(c for c in cleanString if ord(c) < 128)
    cleanString = cleanString.replace("\r", "")
    cleanString = cleanString.replace("\t", "")
    cleanString = cleanString.replace("\\", "")
    cleanString = cleanString.replace("'", "")
    return cleanString

def truncateString(string, length):
    # Truncates a string to a specified length
    if len(string) > length:
        return string[:length] + "..."
    else:
        return string

class Text:
    text = ""
    font = "Arial"
    size = 12
    color = "black"

    def __init__(self, text, font="Arial", size=12, color="black"):
        self.text = text
        self.font = font
        self.size = size
        self.color = color

    def __str__(self):
        return self.text
    
    def __repr__(self):
        return self.text
    
    def wrap(self):
        # Wraps the text to a specified width
        wrappedText = wrapLongLines(self.text, breakwidth=70)
        return wrappedText

# Text used for category and explainations
ListTextCategory = dict()

ListTextCategory["isDropdown"] = Text("If this category is a valid target for dropdowns, it will be displayed in the dropdown menu. If not, it will be displayed as a normal category.")

ListTextCategory["isAutoCalculated"] = Text("If an autocalculation is avaliable, it will be used as the default value for this category. If not, the user will have to enter a value manually.")

ListTextCategory["isRequiredForTea"] = Text("If this category is required to be filled out for tea specifically. If not, it will be optional. This is a validation step for better information.")

ListTextCategory["isRequiredForAll"] = Text("If this category is required to be filled out for entries, including shipping, and teaware. Supercedes isRequiredForTea. if not, it will be optional. This is a validation step for better information.")

ListTextCategory["CategoryType"] = Text("The type of category. This is used to determine how the category data is displayed and how it is used in the app.\n string - Text \n int - Whole number \n float - Decimal number \n bool - True/False \n datetime - Date")

ListTextCategory["CategoryRole"] = Text("The role of the category. This is used to determine how the category data is used for stats and visualizations. To ignore this category, select 'UNUSED'.\n")

ListTextCategory["gradingAsLetter"] = Text("If enabled, and this is a grading-related category, it will be displayed and entered as a letter grade using the grading system. It will still be treated as a float for calculations. If not, it will be displayed and entered as a float.")

# Text used for the menu/Window help text
ListTextHelpMenu = dict()
ListTextHelpMenu["menuStopwatchHelp"] = Text("This is a tool to help you time your tea sessions. Copy the times into your notes!")
ListTextHelpMenu["menuTeaStash"] = Text('''This is one of the primary windows of the app. It shows a list of all the teas in your stash. You can add, edit, and delete teas from this window. You can also filter the list of teas by category, type, and other criteria. You can right click the column header for some filter options. Columns can be customized at the respective column window.
                                        Green - Autocalculated
                                        Light Blue - Finished/0g remaining
                                        Red - Invalid/Empty
                                        ''')
ListTextHelpMenu["menuTeaReviews"] = Text('''This is one of the primary windows of the app. It shows a list of all the teas in your stash. You can add, edit, and delete teas from this window. You can also filter the list of teas by category, type, and other criteria. You can right click the column header for some filter options. Columns can be customized at the respective column window.
                                        Green - Autocalculated
                                        Light Blue - Finished/0g remaining
                                        Red - Invalid/Empty
                                        ''')

ListTextHelpMenu["menuTeaStash_ExportReviews"] = Text('''This button will export this specific review to a text format that can be copy-pasted into other apps. It will also export an image of the tea review, which can be used for sharing on social media or other platforms.
                                                      If you select a review that is not the most recent, it will exclude later reviews from averaging calculations.
                                                      
                                                      WIP''')
ListTextHelpMenu["menuTeaStash_Filter"] = Text('''You can filter your teas by name with the search bar at the top of the "Tea Stash" window.
                                               You can change the filter key by clicking the "Filter by" button.
                                               
                                               You can hide finished teas by clicking the "Hide Finished" button.
                                               You can hide invalid entries by clicking the "Hide Invalid" button. (Invalid entries are those that are missing required fields or have invalid data.)''')

ListTextHelpMenu["menuTeaStash_Operations"] = Text('''Operations that affect the entire stash. Use them with caution. I suggest making a backup of your data first. Most are intended to "Fix" common issues with the stash. or do bulk operations.
                                               renumber IDs - Renumbers all teas in the stash to be sequential. This is useful if you have deleted teas and want to clean up the IDs. This is (probably) "Safe" and will not delete any teas.
                                               Mark all teas finished - Marks all teas with 0g remaining as finished. This is useful if you have teas that you have finished but haven't marked as such.
                                               Also WIP 
                                               ''')

ListTextHelpMenu["menuCategories_TeaCategory"] = Text('''Your Tea stash is made up of Teas which are defined by a few basic attribbutes as well as user-defined Categories.
                                                      These categories can be customized to fit your needs. Be careful when adding or removing categories, as this can affect your existing teas and reviews.
                                                      This may delete data, so be sure to back up your data before making any changes. 

                                                      You can move the order of categories around, as well as change number of dropdown items, rounding and prefix/suffix without much risk.
                                                      You can also change the name of a category without much risk. Changing role, adding or removing categories has, adding duplicates, etc is more risky (ie untested, likely to break stuff.)
                                                      
                                                      NOT AS DEVELOPED AS I WOULD LIKE, MAKE SURE TO BACKUP, USE CAUTION. I SET THE DEFAULT VALUES TO WHAT I PERSONALLY USE.
                                                      ''')

ListTextHelpMenu["menuCategories_ReviewCategory"] = Text('''Reviews are made up of a few basic attribbutes as well as user-defined Categories.
                                                      These categories can be customized to fit your needs. Be careful when adding or removing categories, as this can affect your existing teas and reviews.
                                                      This may delete data, so be sure to back up your data before making any changes.
                                                         
                                                      You can move the order of categories around, as well as change number of dropdown items, rounding and prefix/suffix without much risk.
                                                      You can also change the name of a category without much risk. Changing role, adding or removing categories has, adding duplicates, etc is more risky (ie untested, likely to break stuff.)

                                                      NOT AS DEVELOPED AS I WOULD LIKE, MAKE SURE TO BACKUP, USE CAUTION. I SET THE DEFAULT VALUES TO WHAT I PERSONALLY USE.
                                                      ''')

# User Guide Text
ListTextUserGuide = dict()

ListTextUserGuide["About"] = Text('''
RateaTea is a tea tracking app that helps you keep track of your tea stash, reviews, and more.
It is designed to be easy to use and customizable, so you can track your tea drinking habits in a way that works for you.
It is written in Python and uses the dearpygui library for the GUI.
It is open source and available on GitHub at https://github.com/Rexwang8/ratea
Ratea is fully local, MIT licensed, and free to use.

                                  
Find me on discord at bts_bighit (long story)
''')


ListTextUserGuide["introduction"] = Text('''
Welcome to RateaTea, the tea tracking app that helps you keep track of your tea stash, reviews, and more! 
This user guide will help you get started with the app and explain how to use its features.
''')

ListTextUserGuide["windows"] = Text('''
Windows
RateaTea has several windows that you can use to manage your tea stash and reviews.
- Tea Stash: This window shows a list of all the teas in your stash. You can add, edit, and delete teas from this window. You can also filter the list of teas by category, type, and other criteria.
- Tea Reviews: This window shows a list of all the reviews in your stash. You can add, edit, and delete reviews from this window. You can also filter the list of reviews by category, type, and other criteria.
- Categories: This window allows you to add, edit, and delete categories for your teas and reviews. You can also set the type and role of each category.
- Stats: This window shows various stats and visualizations about your tea drinking habits. You can see your most consumed teas, your average rating, and more.
- Settings: This window allows you to change the app settings, backup your data, and more.
- Stopwatch: This window allows you to time your tea sessions. You can start, stop, and reset the timer. You can also copy the time to your clipboard.
- Notes: This window allows you to take notes about your tea sessions. You can write down your thoughts and observations about the tea.
- User Guide: This window shows this user guide (you are here).
- About: This window shows information about the app, including the version number and the developer's contact information.
''')


ListTextUserGuide["stashBasics"] = Text('''
Adding Teas
To add a new tea to your stash, go to the "Tea Stash" window and click the "Add Tea" button.
You can also click "Duplicate Tea" to create a copy of the last tea in your stash. (Usually your last tea added)
Null/Invalid values are red.
                                      
Editing Teas
To edit a tea, select it from the list and click the "Edit Tea" button.
                                        
Adjusting Teas:
The standard adjustment assumes that you drank the tea but didn't record it.
The "Gift" adjustment assumes that you gave the tea away, so it will remove the tea from your stash but won't count it as drunk.
The "Sale" adjustment assumes that you sold the tea, so it will remove the tea from your stash and count the cost as negative, seperately from the tea.
If you mark the tea as "Finished" the remaining is counted as "Standard" aka drunk.
You can move a tea around by index. If you want to move a tea to ID=10, it will place it after the old ID=10 and renumber it as the new ID=10
                                        
Adding Reviews
To add a new review, first add a tea to your stash.
Then go to the "Tea Reviews" window and click the "Add Review" button.
''')

ListTextUserGuide["stashFunctions"] = Text('''
Free Tea and Samples
Add a tea but keep the price at 0 or 0.1 to indicate that it is a free tea or sample.

Grouping Teas
You can group teas purchased together by adding it to the notes and duplicating it to each tea.
This will allow you to see the group of teas together in the "Tea Stash" window.
                                      
Logging a Trade
You should log a trade by logging a sale at fair market value, and then logging a purchase at the same value.
This will allow you to keep track of the trade and the value of the tea.
                                      
Filtering your teas
You can filter your teas by name with the search bar at the top of the "Tea Stash" window.
You can sort your teas by clicking the column headers in the "Tea Stash" window.
Columns can be reordered, hidden, and resized by right clicking the column header.
More methods WIP
                                           
Adding fees, shipping, and teaware
Work in progress
''')

ListTextUserGuide["stashReviews"] = Text('''
Welcome to RateaTea, the tea tracking app that helps you keep track of your tea stash, reviews, and more! 
This user guide will help you get started with the app and explain how to use its features.
                                         
Tools for reviewing
You can use the "Timer" tool to time your tea sessions.
You can also use the "Notes" tool to write down your thoughts and observations about the tea.
Notes can be copy-pasted into the review for a easy way to keep track of your thoughts.

Cannonical rating system for RaTea
I made the program so I call the shots. I use this system.
The system is a 5 point float system where 5 cooresponds to S+, 4.5 to S, 4.25 to S-, 4 to A+, etc.
The grade of the tea determines the letter grade, while supporting details like value determine the decimal.
I personally grade the tea based on the Letter than add the + or - based on value.
''')

ListTextUserGuide["editCategories"] = Text('''
Adding or Editing Categories
To add or edit categories, go to the "Categories" window. Be careful when adding or removing categories, as this can affect your existing teas and reviews.
This may delete data, so be sure to back up your data before making any changes.
                                      
Autocalcualted entries
Some categories support autocalculation, which means that the value is automatically calculated based on other categories.
This has to be enabled in the "Categories" window. Autocalculated categories are green and ignore their value in favor of the autocalculated value.
                                      
Dropdown Entries
Some data types support dropdown entries which populate from previously entered data, by most commonly used first.
The number of entries can be configured in "Categories" window.
''')


ListTextUserGuide["userGuide"] = Text('''                                                                          
Persistant Data
Windows that can be closed and will save their data: Work in Progress
- Stopwatch
- Notes
                                      
Saving and Backing Up Data
Ratea will autmatically autosave everyy 15 minutes to an "autobackup" folder. You can trigger a manual backup at any time by clicking the "Backup" button in the "Settings" window.
Saving occurs whenever a setting or tea is changed, you can trigger a save by clicking the "Save" button in the "Settings" window.
                                      
Restoring Data
If you need to restore your data, delete the current data and just copy the backup file to the data folder. May or may not work, not well tested.
                                      
Importing and Exporting Data
You can export your data to a CSV file by clicking the "Export" button in the "Settings" window. This is work in progress and will support more formats in the future.
                                      
Stats and Visualizations
RateaTea provides various stats and visualizations to help you understand your tea drinking habits. The stats are available in the "Stats" window, where you can see your tea drinking habits, most consumed teas, and more.
Visualizations are work in progress and will be added in the future.
                                      
Settings
Settings are available in the "Settings" window. You can change the app settings, backup your data, and more. Work in progress.        
''')


ListTextUserGuide["changelog"] = Text(
'''---Changelog---
Feat(0.25.0): Add 2 graphs to review img
Feat(0.24.0): add meaning key to reviews
Feat(0.23.0): Fixed table sorting. Added a table and plot to stats
Feat(0.22.0): Fix counting bug, add one stats tab
Feat(0.21.0): Expanded review exports to include some more stats.
Feat(0.20.0): Added button to generate exportable reviews and text format reviews.
Feat(0.19.0): Added changelog to aboutme
Feat(0.18.0): Add copy-to-clipboard button to terminal
Feat(0.17.0): small housekeeping adjustment for finished, added a button to adjust to remaining amt
Feat(0.16.0): Added a spend per month table to stats
Feat(0.15.0): Update stats window, few new stats
Feat(0.14.0): Filter invalid and finished teas flag
Feat(0.13.0): Terminal logs window
Feat(0.12.0): Sale adjustment
Feat(0.11.0): Cache and pre-calc numbers for major optimizations
Feat(0.10.0): Rework the stats UI Layout page
Feat(0.9.0): First refresh icon for soft reload
Feat(0.8.0): Reorder button for reviews
Feat(0.7.0): Notepad and timer now have save and load buttons that call persist
Feat(0.6.0): Move to end or top buttons for adjustments
< Semantic change, any feature will get it's own minor version >
Feat(0.5.9): StatsTeas Tried
Feat(0.5.8): Add filter key change
Feat(0.5.8): Optional rating system dropdown
Feat(0.5.9): basic about and userguide
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
''')