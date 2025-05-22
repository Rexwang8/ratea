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

# Text used for the menu/Window help text
ListTextHelpMenu = dict()
ListTextHelpMenu["menuStopwatchHelp"] = Text("This is a tool to help you time your tea sessions. Copy the times into your notes!")
ListTextHelpMenu["menuTeaStash"] = Text("This is one of the primary windows of the app. It shows a list of all the teas in your stash. You can add, edit, and delete teas from this window. You can also filter the list of teas by category, type, and other criteria. You can right click the column header for some filter options. Columns can be customized at the respective column window.\n\n Green - Autocalculated \n Red - Invalid/Empty\n")
ListTextHelpMenu["menuTeaReviews"] = Text("This is one of the primary windows of the app. It shows a list of all the reviews in your stash. You can add, edit, and delete reviews from this window. You can also filter the list of reviews by category, type, and other criteria. You can right click the column header for some filter options. Columns can be customized at the respective column window.\n\n Green - Autocalculated \n Red - Invalid/Empty\n")