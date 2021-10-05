#!/usr/bin/env python3
import time
from flask import Flask
from flask import request
from flask import render_template
from rpi_ws281x import *
import threading
from pixelconfig import PixelConfig
from pixelseq import PixelSeq, SeqList

# Globals for passing information between threads
# needs default settings
upd_time = time.time()
seq_set = {
    "sequence" : "alloff",
    "delay" : 900,
    "reverse" : 0,
    "colors" : "ffffff"
    }


# List of sequences
seq_list = SeqList()

app = Flask(
    __name__,
    template_folder="www"
    )

@app.route("/")
def main():
    return render_template('index.html')


@app.route("/pixels.css")
def css():
    return render_template('pixels.css'), 200, {'Content-Type': 'text/css; charset=utf-8'}

    
    
@app.route("/pixels.js")
def js():
    return render_template('pixels.js'), 200, {'Content-Type': 'text/javascript; charset=utf-8'}
    
@app.route("/sequences.json")
def seqJSON ():
    return (seq_list.json())
    
@app.route("/set")
def setSeq():
    global seq_set, upd_time
    new_values = {}
    # perform first stage validation on data sent
    this_arg = request.args.get('seq', default = 'alloff', type = str)
    if (seq_list.validate_sequence(this_arg) == True):
        new_values["sequence"] = this_arg
    else:
        return "Invaild request"
    this_arg = request.args.get('delay', default = 1000, type = int)
    if (this_arg >= 0 and this_arg <= 1000):
        new_values["delay"] = this_arg
    else:
        return "Invalid delay"
    this_arg = request.args.get('reverse', default = '0', type = str)
    if (this_arg == "1"):
        new_values["reverse"] = True
    else:
        new_values["reverse"] = False
    this_arg = request.args.get('colors', default = '#ffffff', type = str)
    if (seq_list.validate_color_string(this_arg)):
        new_values["colors"] = this_arg
    else:
        return "Invalid colors"
    # If reach here then it was successful for copy temp dict to actual
    seq_set = new_values
    # update time to notify other thread it's changed
    upd_time = time.time()
    return "Ready"

def flaskThread():
    app.run(host='0.0.0.0', port=80)
    
# Setup pixel strip and then start the updatePixels loop
def mainThread():
    global seq_set, upd_time
    last_update = upd_time
    current_sequence = ""
    pixel_conf = PixelConfig()
    pixels = PixelSeq(pixel_conf)
    sequence_position = 0
    colors = [Color(255,255,255)]

    
    while(1):
        if (upd_time != last_update) :
            # Convert color string to list of colors (pre formatted for pixels)
            colors = seq_list.string_to_colors(seq_set['colors'])
            # If sequence changed then reset seq_position
            if (seq_set['sequence'] != current_sequence):
                sequence_position = 0
                current_sequence = seq_set['sequence']

        # returns sequence_position which is used for future calls
        sequence_position = pixels.updateSeq(
            seq_set['sequence'],
            sequence_position,
            seq_set['reverse'],
            colors) 
        last_update = upd_time
        # Sleep used for delay this means that there will be that long a delay between updates
        time.sleep(seq_set['delay']/1000)

if __name__ == "__main__":
    # run as two threads - main thread and flask thread
    mt = threading.Thread(target=mainThread)
    ft = threading.Thread(target=flaskThread)
    mt.start()
    ft.start()

