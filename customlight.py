from time import time
import os
import re

# Class used to support cheerlights or other custom light color
class CustomLight():

    def __init__ (self, filename):
        self.filename = filename
        # Create empty list - must always add one entry
        self.colors = []

        # If file not found or an error then custom colors is disabled
        self.load_colors() 
        
        self.last_updated = self.get_file_mtime()
        
    # Load colors. Also check we have at least one color
    def load_colors(self):
        self._file_load_colors()
        
        # if no colors then add default ffffff
        if len(self.colors) < 1:
            self.colors.append("ffffff")


    def get_file_mtime(self):
        try:
            mtime = os.path.getmtime(self.filename)
        except:
            mtime = 0
        return mtime


    # load config if it exists
    # If not exist return 0, if successful return 1, if not successful return -1 (file error) -2 (no colors defined)
    # If error also populate self.error_msg
    # It does not matter if custom fails as long as default works
    # Includes some validation checks, but these are very crude
    # to detect mistakes rather than security reasons
    def _file_load_colors(self):
        # Reset list of colors
        self.colors.clear()
        # Compile regexp for more efficient matching
        re_color = re.compile("^#?([\dA-Fa-f]{6})")
        
        # Try and open file - if not exist then just will be caught as exception
        try:
            with open (self.filename, "r") as color_file:
                lines = color_file.readlines()
                for line in lines:
                    # remove training / leading chars
                    line = line.strip()
                    result = re_color.match(line)
                    if (result != None):
                        self.colors.append(result.group(1))
	    # File not found 
        except FileNotFoundError:
            return 0
        # Other file read error
        except OSError:
            return -1

        return 1
        
    
    # Checks if updated. 
    # If so reloads file and updates last_updated as well as 
    def is_updated(self):
        mtime = self.get_file_mtime()
        if (mtime != self.last_updated):
            self.load_colors()
            self.last_updated = self.get_file_mtime()
            return True
        return False
        
        
    # Substitute any "custom" entries with appropriate color
    def subs_custom_colors(self, colors):
        return_colors = []
        custom_color_count = 0
        for this_color in colors:
            if this_color == "custom":
                return_colors.append(self.colors[custom_color_count])
                custom_color_count += 1
                if (custom_color_count >= len (self.colors)):
                    custom_color_count = 0
            else:
                return_colors.append(this_color)
        return return_colors

	
