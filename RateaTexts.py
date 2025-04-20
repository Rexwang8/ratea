# Helper file to store all the texts used in the app



# Text definition that can be used to define things like fonts and colors in the future.

import time


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
    
    def strWithWrap(self, width=80):
        # Respect words and spaces, don't break them
        spacesIndices = [i for i, char in enumerate(self.text) if char == " "]
        if not spacesIndices:
            return self.text
        
        if len(self.text) <= width:
            return self.text
        
        # Split the text into lines of at or more than width characters
        lines = []
        currentLine = ""
        timeout = 15 # If we don't find a space in 15 iterations, we break the line
        loopTimeout = 0 # If we don't find a space in 100 iterations, we break the line
        while len(self.text) > width and loopTimeout < 100:
            currentLine = ""

            # If the width is larger than the text, we can just return the text
            if len(self.text) <= width:
                lines.append(self.text)
                break

            # If there is a newline within the width, we can just split the text at that point
            newlineIndex = self.text.find("\n", 0, width)
            if newlineIndex != -1:
                currentLine = self.text[:newlineIndex]
                lines.append(currentLine)
                self.text = self.text[newlineIndex+1:]
                continue

            # Find the first space in the text that is at or before the width
            spaceIndex = None
            # Work backwards from the width to find the first space
            for i in range(width, 0, -1):
                if i in spacesIndices:
                    spaceIndex = i
                    break
                timeout -= 1
                if timeout <= 0:
                    break
            # If we found a space, we can split the text at that point
            if spaceIndex is not None:
                currentLine = self.text[:spaceIndex]
                lines.append(currentLine)
                self.text = self.text[spaceIndex+1:]
            else:
                # If we didn't find a space, we can just split the text at the width
                print("No space found, breaking line")
                currentLine = self.text[:width]
                lines.append(currentLine)
                self.text = self.text[width:]

            loopTimeout += 1

        # Add the remaining text to the lines
        if self.text:
            lines.append(self.text)

            
        return "\n".join(lines)


# Text used for category and explainations
ListTextCategory = dict()

ListTextCategory["isDropdown"] = Text("If this category is a valid target for dropdowns, it will be displayed in the dropdown menu. If not, it will be displayed as a normal category.")

ListTextCategory["isAutocalculated"] = Text("If an autocalculation is avaliable, it will be used as the default value for this category. If not, the user will have to enter a value manually.")

ListTextCategory["isRequiredTea"] = Text("If this category is required to be filled out for tea specifically. If not, it will be optional. This is a validation step for better information.")

ListTextCategory["isRequiredForAll"] = Text("If this category is required to be filled out for entries, including shipping, and teaware. Supercedes isRequiredForTea. if not, it will be optional. This is a validation step for better information.")

ListTextCategory["CategoryType"] = Text("The type of category. This is used to determine how the category data is displayed and how it is used in the app.\n string - Text \n int - Whole number \n float - Decimal number \n bool - True/False \n datetime - Date")

ListTextCategory["CategoryRole"] = Text("The role of the category. This is used to determine how the category data is used for stats and visualizations. To ignore this category, select 'UNUSED'.\n")