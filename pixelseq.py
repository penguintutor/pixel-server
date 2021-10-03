from rpi_ws281x import PixelStrip, Color
import _rpi_ws281x as ws
from pixelconfig import PixelConfig
from flask import json
import re

# Sequence methods follow same format as arduino-pixels except
# no need for num_colors as that can be determined from colors list length

class SeqList():
    def __init__ (self):
        self.pixel_sequences = [
            {"seq_name" :"alloff",
             "title": "All Off",
             "description" : "Turn all LEDs off",
             "group" : 0
             },
            {"seq_name" :"allon",
             "title": "All On",
             "description" : "Turn all LEDs on",
             "group" : 0
             },
            {"seq_name" :"flash",
             "title": "Flash",
             "description" : "Flash all LEDs on and off",
             "group" : 1
             }
            ]
    # Return list of sequences in json format      
    def json (self):
        sequences = []
        for this_seq in self.pixel_sequences:
            sequences.append({
                "seq_name": this_seq["seq_name"],
                 "title": this_seq["title"],
                 "description": this_seq["description"],
                 "group": str(this_seq["group"])
                 })
        return json.jsonify(sequences)
    
    # returns true if valid sequence, otherwise false
    def validate_sequence (self, supplied_seq_name):
        for this_seq in self.pixel_sequences:
            if this_seq["seq_name"] == supplied_seq_name:
                return True
        return False
    
    # Include some color handling methods 
    # Check for valid color string - simple pattern matching ONLY
    def validate_color_string (self, color_string):
        pattern = r'[0-9a-f,]*'
        result = re.fullmatch(pattern, color_string)
        if result:
            return True
        else:
            return False
    
    def string_to_colors(self, color_string):
        # split based on , - assumes no # in string
        return_list = []
        parts = color_string.split(",")
        for this_part in parts:
            rgb = self.hex_to_rgb("#"+this_part)
            return_list.append(Color(*rgb))
        return return_list
    
    def hex_to_rgb(self, hx, hsl=False):
        """Converts a HEX code into RGB or HSL.
        Args:
            hx (str): Takes both short as well as long HEX codes.
            hsl (bool): Converts the given HEX code into HSL value if True.
        Return:
            Tuple of length 3 consisting of either int or float values.
            If not valid return white (255,255,255)
            """
        if re.compile(r'#[a-fA-F0-9]{3}(?:[a-fA-F0-9]{3})?$').match(hx):
            div = 255.0 if hsl else 0
            if len(hx) <= 4:
                return tuple(int(hx[i]*2, 16) / div if div else
                             int(hx[i]*2, 16) for i in (1, 2, 3))
            return tuple(int(hx[i:i+2], 16) / div if div else
                         int(hx[i:i+2], 16) for i in (1, 3, 5))
        else :
            return (255,255,255)
    


class PixelSeq():
    
    
    def __init__ (self, pixel_config):
        self.pixel_config = pixel_config
        
        self.seq_methods = {
            'allon' : self.allOn,
            'alloff' : self.allOff,
            'flash' : self.flash
            }
        
        self.strip = PixelStrip (
            pixel_config.ledcount,
            pixel_config.gpiopin,
            pixel_config.ledfreq,
            pixel_config.leddma,
            pixel_config.ledinvert,
            pixel_config.ledmaxbrightness,
            pixel_config.ledchannel
            )
        self.strip.begin()
        # During startup turn all LEDs off
        self.allOff (0, 0, [0])
        
    def updateSeq (self, seq_name, seq_position, reverse, colors):
        return self.seq_methods[seq_name](seq_position, reverse, colors)
    
    def allOff(self, seq_position, reverse, colors):
        for i in range (0, self.strip.numPixels()):
            self.strip.setPixelColor (i, Color(0,0,0))
        self.strip.show()
        return seq_position
    
    def allOn(self, seq_position, reverse, colors):
        color_pos = 0
        # if reverse then need color to start at far end
        if (reverse):
            color_pos = (self.strip.numPixels() % len(colors)) -1
        if color_pos < 0:
            color_pos = len(colors) - 1
        for i in range (0, self.strip.numPixels()):
            self.strip.setPixelColor(i, colors[color_pos])
            color_pos = self._color_inc (color_pos, len(colors), reverse)
        self.strip.show()
        return seq_position

    def flash(self, seq_position, reverse, colors):
        color_pos = 0
        # if reverse then need color to start at far end
        if (reverse):
            color_pos = (self.strip.numPixels() % len(colors)) -1
        if color_pos < 0:
            color_pos = len(colors) - 1
        for i in range (0, self.strip.numPixels()):
            # If flash off then set to off
            if (seq_position != 0) :
                self.strip.setPixelColor(i, Color(0,0,0))
            else:
                self.strip.setPixelColor(i, colors[color_pos])
                color_pos = self._color_inc (color_pos, len(colors), reverse)
        self.strip.show()
        if (seq_position != 0) :
            return 0
        return 1


    # Helper function to increment or decrement color based on reverse = true / false
    def _color_inc (self, current_color, num_colors, reverse):
        if reverse == False:
            current_color += 1
            if (current_color >= num_colors):
                current_color = 0
        else:
            current_color -= 1
            if (current_color < 0):
                current_color = num_colors -1
        return current_color
        
        