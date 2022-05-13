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
    
    def __init__ (self):
        # default config file name (if not exist then uses default)
        self.defaultcfg = "defaults.cfg" 
        self.customcfg = "pixelserver.cfg"
        self.customlightcfg = "customlight.cfg"
        self.errormsg = ""

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
                    # validate value and store
                    if (key == "ledcount"):
                        value_int = int(value)
                        if (value_int > 0):
                            self.ledcount = value_int
                        else:
                            self.errormsg = "Invalid ledcount value "+value
                            return -2
                    elif (key == "gpiopin"):
                        value_int = int(value)
                        # Only basic check in a valid range - may not be valid gpio number
                        if (value_int >=0 and value_int <=60):
                            self.gpiopin = value_int
                        else:
                            self.errormsg = "Invalid gpiopin value "+value
                            return -2
                    elif (key == "ledfreq"):
                        value_int = int(value)
                        if (value_int >= 1000 and value_int <= 2000000):
                            self.ledfreq = value_int
                        else:
                            self.errormsg = "Invalid ledfeq value "+value
                            return -2
                    elif (key == "leddma"):
                        value_int = int(value)
                        if (value_int >= 0 and value_int <= 20):
                            self.leddma = value_int
                        else:
                            self.errormsg = "Invalid leddma value "+value
                            return -2
                    elif (key == "ledmaxbrightness"):
                        value_int = int(value)
                        if (value_int > 0 and value_int <= 255):
                            self.ledmaxbrightness = value_int
                        else:
                            self.errormsg = "Invalid ledmaxbrightness value "+value
                            return -2
                    elif (key == "ledinvert"):
                        if (value.lower() == "false"):
                            self.ledinvert = False
                        elif (value.lower() == "true"):
                            self.ledinvert = True
                        else :
                            self.errormsg = "Invalid ledinvert value "+value
                            return -2
                    elif (key == "ledchannel"):
                        value_int = int(value)
                        if (value_int >= 0 and value_int <= 10):
                            self.ledchannel = value_int
                        else :
                            self.errormsg = "Invalid ledchannel value "+value
                            return -2
                    elif (key == "striptype"):
                        # Allows abbreviated version (eg. RGB = WS2811_STRIP_RGB)
                        # or long version
                        # If it's short 3 chars add WS2811
                        # If it's short 4 chars add SK6812
                        # first remove any whitespace
                        value = value.strip()
                        if (len(value) == 3):
                            strip_value = "WS2811_STRIP_"+value
                        elif (len(value) == 4):
                            strip_value = "SK6812_STRIP_"+value
                        else:
                            strip_value = value
                        if strip_value in PixelConfig.strip_types:
                            self.striptype = PixelConfig.strip_types[strip_value]
                        else:
                            self.errormsg = "Invalid striptype value "+value
                            return -2
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
            

	
