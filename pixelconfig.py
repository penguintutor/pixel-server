from rpi_ws281x import *
class PixelConfig():
    
    # Dictionary of types
    # Based on ws281x library - these are the most common ones
    # Note that WS2812 works same as WS2812
    strip_types = {
        'WS2811_STRIP_RGB' : ws.WS2811_STRIP_RGB,
        'WS2811_STRIP_RBG' : ws.WS2811_STRIP_RBG,
        'WS2811_STRIP_GRB' : ws.WS2811_STRIP_GRB,
        'WS2811_STRIP_BGR' : ws.WS2811_STRIP_BGR,
        'WS2811_STRIP_BRG' : ws.WS2811_STRIP_BRG,
        'WS2811_STRIP_BGR' : ws.WS2811_STRIP_BGR,
        'WS2812_STRIP' : ws.WS2812_STRIP,
        'SK6812_STRIP_RGBW' : ws.SK6812_STRIP_RGBW,
        'SK6812_STRIP_RBGW' : ws.SK6812_STRIP_RBGW,
        'SK6812_STRIP_GRBW' : ws.SK6812_STRIP_GRBW,
        'SK6812_STRIP_GBRW' : ws.SK6812_STRIP_GBRW,
        'SK6812_STRIP_BRGW' : ws.SK6812_STRIP_BRGW,
        'SK6812_STRIP_BGRW' : ws.SK6812_STRIP_BGRW,
        'SK6812_STRIP' : ws.SK6812_STRIP,
        'SK6812W_STRIP' : ws.SK6812W_STRIP
        
    }
    
    # What configs options can be set
    # Min and max are just general check mainly for numbers
    # number = int ; float = floating point
    # For text = string max is maximum number characters
    # min and max are required even if ignored / None (eg bool)
    # For list / dictionary then minimum is name of list / dictionary and maximum = "radio" or "checkbox"
    # dictionary shows value as option (key as value)
    # dictionary-keys is a compromise - dictionary for loading, uses keys only for options
    # Can instead use list and .keys() if want to use keys
    # Comment can be used for tooltips
    # configsetting: list [Label, type, min, max, comment]
    config_settings = {
        'ledcount' : ["Number LEDs", "number", 1, 10000, "Number of LEDs on strip"],
        'gpiopin' : ["GPIO Pin No.", "number", 0, 100, "Raspberry Pi GPIO number (eg. 18)"],
        'ledfreq' : ["LED Frequency", "number", 0, 1000000, "Normally 800000"],
        'leddma' : ["LED DMA", "number", 0, 100, "DMA number, normally 5"],
        'ledmaxbrightness': ["Brightness", "number", 0, 255, "0 to 255"],
        'ledinvert' : ['Invert LED?', "bool", "", "", "True or False"],
        'ledchannel' : ["LED Channel", "number", 0, 10, "Normally 0"],
        'striptype' : ["LED Strip", "dictionary-keys", strip_types, "radio", "Strip type"]
    }
    
    def __init__ (self, default_config, custom_config, light_config):
        # default config file name (if not exist then uses default)
        self.defaultcfg = default_config
        self.customcfg = custom_config
        self.customlightcfg = light_config
        self.errormsg = ""
        
        # store the actual settings in this dictionary
        self.settings= {}

        ''' 
        Example defaults
        
        self.default_led_settings = {
        'ledcount': 44,
        'gpiopin': 18,
        'ledfreq': 800000,
        'leddma' : 5,
        'ledmaxbrightness': 50,
        'ledinvert': False,
        'ledchannel': 0,
        'striptype': ws.WS2811_STRIP_GRB
        '''

        if (self.load_config (self.defaultcfg) != 1):
            print ("Error loading config: "+self.errormsg)
        success = self.load_config (self.customcfg)
        if (success == 0):
            print ("No custom config "+self.customcfg+" using defaults")
        elif (success < 1):
            print ("Error loading custom config "+self.customcfg)
            print (self.errormsg)


    # load config if it exists
    # If not exist return 0, if successful return 1, if not successful return -1 (file error) -2 (data error)
    # After error stop reading rest of file
    # If error also populate self.error_msg
    # It does not matter if custom fails as long as default works
    # Includes some validation checks, but these are very crude
    # to detect mistakes rather than security reasons
    def load_config(self, filename):
        # Try and open file - if not exist then just return
        try:
            with open (filename, "r") as cfg_file:
                lines = cfg_file.readlines()
                for line in lines:
                    # remove training / leading chars
                    line = line.strip()
                    # If comment or blank line ignore
                    if (line.startswith('#') or len(line) < 1):
                        continue
                    # split based on =
                    (key, value) = line.split('=', 1)
                    # strip any spaces
                    key = key.strip()
                    value = value.strip()
                    
                    if key in PixelConfig.config_settings.keys():
                        # validate based on type
                        this_setting = PixelConfig.config_settings[key]
                        
                        # Special case striptype allows shortened versions to maintain compatibility
                        
                        if (key == "striptype"):
                            # # Allows abbreviated version (eg. RGB = WS2811_STRIP_RGB)
                            # or long version
                            # If it's short 3 chars add WS2811
                            # If it's short 4 chars add SK6812
                            if (len(value) == 3):
                                value = "WS2811_STRIP_"+value
                            elif (len(value) == 4):
                                value = "SK6812_STRIP_"+value
                        # Now changed this to full strip type so will be accepted using normal dictionary check
                        
                        # Generic values
                        if (this_setting[1] == "number"):
                            value_int = int(value)
                            if (value_int >= this_setting[2] and value_int <= this_setting[3]):
                                self.settings[key] = value_int
                            else:
                                self.errormsg = "Invalid number for {} - value {}".format(key, value)
                                
                        elif (this_setting[1] == "bool"):
                            if (value.lower() == "false"):
                                self.settings[key] = False
                            elif (value.lower() == "true"):
                                self.settings[key] = True
                            else :
                                self.errormsg = "Invalid boolean for {} - value   {}".format(key, value)
                                return -2
                        # List - only radio supported at the moment
                        elif (this_setting[1] == "dictionary" or this_setting[1] == "dictionary-keys"):
                            if value in this_setting[2].keys():
                                self.settings[key] = this_setting[2][value]
                            else:
                                self.errormsg = "Invalid dictionary for {} value {}".format(key, value)
                                print (self.errormsg)
                                return -2 
                        ## List not yet implemented

                    else:
                        self.errormsg = "Unknown entry "+key+" in "+filename
                        return -2

                    

	    # File not found 
        except FileNotFoundError:
            self.errormsg = "File not found "+filename
            return 0
        # Other file read error
        except OSError:
            self.errormsg = "Error reading file "+filename
            return -1
            
        return 1


    # Returns tuple (status, value / message)
    # status = True (success)
    # status = False (invalid parameter)
    def validate_parameter (self, parameter, value):
        if not parameter in PixelConfig.config_settings.keys():
            return (False, "Invalid parameter {}".parameter)
        config_params = PixelConfig.config_settings[parameter]
        if config_params[1] == "number":
            try:
                temp_value = int(value)
            except: 
                return (False, "Parameter is not a number {}".format(parameter))
            if (temp_value < config_params[2] or temp_value > config_params[3]):
                return (False, "Invalid value for number {}".format(parameter))
            # otherwise valid number, return true
            return (True, temp_value)
        elif config_params[1] == "text":
            if len(value) < config_params[2] or len(value) > config_params[2]:
                return (False, "Invalid string length {}".format(parameter))
            else: 
                return (True, value)
        elif (config_params[1] == "bool"):
            if value == True or value == "True" or value == "on" or value == "1":
                return (True, True)
            elif value == False or value =="False" or value == "off" or value == "0":
                return (True, False)
            else :
                return (False, "Invalid parameter value {}".format(parameter))
        elif (config_params[1] == "dictionary" or config_params[1] == "dictionary-keys"):
            if (value in config_params[2].keys()):
                return (True, value)
            else:
                return (False, "Invalid parameter value {}".format(parameter))
        elif (config_params[1] == "list"):
            if (value in config_params[2]):
                return (True, value)
            else:
                return (False, "Invalid parameter value {}".format(parameter))
        else: 
            return (False, "Invalid parameter type {}".format(parameter))
                
        
    # Does not validate - use validate_parameter prior to calling this
    # Also call save after making all changes
    # value is normally passed as a string regardless
    # It does check for the correct type for number / bool, but not within range
    # Returns True for success False for fail
    def update_parameter (self, parameter, value):
        if not parameter in PixelConfig.config_settings.keys():
            return (False)
        config_params = PixelConfig.config_settings[parameter]
        
        if (config_params[1] == "number"):
            try:
                self.settings[parameter] = int(value)
            except: 
                return False
        elif (config_params[1] == "bool"):
            if value == True:
                self.settings[parameter] = True
            elif value == False:
                self.settings[parameter] = False
            else:
                return False
        # For other values store as a string
        else:
            self.settings[parameter] = value
        return True
            
        

    # returns config options as form for html
    # does not include <form> or </form> which can be set seperately
    def to_html_form(self):
        html_string = ""
        for key, value in PixelConfig.config_settings.items():
            html_string += "<label for=\"{}\" title=\"{}\">{}:</label>\n".format(key, value[4], value[0])
            # Text or number is the same input type
            if value[1] == "number" or value[1] == "text":
                html_string += "<input type=\"text\" id=\"{}\" name=\"{}\" value=\"{}\">".format(key, key, self.settings[key])
            elif value[1] == "bool":
                if self.settings[key]:
                    html_string += "<input type=\"checkbox\" id=\"{}\" name=\"{}\" checked=\"checked\">".format(key, key)
                else:
                    html_string += "<input type=\"checkbox\" id=\"{}\" name=\"{}\">".format(key, key)
            elif value[1] == "dictionary":
                html_string += "<select name=\"{}\" id=\"{}\">\n".format(key, key)
                for this_key, this_value in value[2].items():
                    if self.settings[key] == this_key:
                        html_string += "<option value=\"{}\" selected>{}</option>\n".format(this_key, this_value)
                    else:
                        html_string += "<option value=\"{}\">{}</option>\n".format(this_key, this_value)
                html_string += "</select>\n"
            # List is same as dictionary, but key and value are same
            elif value[1] == "list":
                html_string += "<select name=\"{}\" id=\"{}\">\n".format(key, key)
                for this_value in value[2]:
                    if self.settings[key] == this_value:
                        html_string += "<option value=\"{}\" selected>{}</option>\n".format(this_value, this_value)
                    else:
                        html_string += "<option value=\"{}\">{}</option>\n".format(this_value, this_value)
                html_string += "</select>\n"
            # special case - it is a dictionary, but treat like a list (use keys)
            elif value[1] == "dictionary-keys":
                html_string += "<select name=\"{}\" id=\"{}\">\n".format(key, key)
                for this_value in value[2].keys():
                    if self.settings[key] == this_value:
                        html_string += "<option value=\"{}\" selected>{}</option>\n".format(this_value, this_value)
                    else:
                        html_string += "<option value=\"{}\">{}</option>\n".format(this_value, this_value)
                html_string += "</select>\n"
                
            html_string += "<span title=\"{}\">?</span><br />\n".format(value[4])
        return html_string
        
    def get_settings_dict(self):
        return self.config_settings


    def save_settings (self):
        try:
            with open(self.customcfg, "w") as write_file:
                for key, value in self.settings.items():
                    write_file.write("{}={}\n".format(key, value))
        except Exception as e:
            print ("Error saving file to "+self.filename+" "+str(e))
            return False
        return True
