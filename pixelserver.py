import pixelserver
from pixelserver import create_app
from pixelserver.pixelconfig import PixelConfig
from pixelserver.pixelseq import PixelSeq
from pixelserver.customlight import CustomLight
import threading
from rpi_ws281x import *
import time


# Custom settings - filenames with further configs
default_config_filename = "defaults.cfg" 
custom_config_filename = "pixelserver.cfg"
custom_light_config_filename = "customlight.cfg"



def flaskThread():
    app.run(host='0.0.0.0', port=80)
    
# Setup pixel strip and then start the updatePixels loop
def mainThread():
    
    last_update = pixelserver.upd_time
    current_sequence = ""
    pixelserver.pixel_conf = pixelserver.load_config(default_config_filename, custom_config_filename, custom_light_config_filename)
    pixels = PixelSeq(pixelserver.pixel_conf)
    
    # Use for custom color lights (eg CheerLights)
    custom_light = CustomLight(pixelserver.pixel_conf.customlightcfg)
    
    sequence_position = 0
    colors = [Color(255,255,255)]

    
    while(1):
        # Check for change in custom light colors
        # Reloads files if updated
        if custom_light.is_updated():
            pixelserver.upd_time = time.time()
        
        # If updated sequence / value etc.
        if (pixelserver.upd_time != last_update) :
            # convert colors to list instead of comma string
            color_list = pixelserver.seq_set['colors'].split(",")
            # handle custom colors
            color_list = custom_light.subs_custom_colors(color_list)   
            # Convert color string to list of colors (pre formatted for pixels)
            # Value returned as seq_colors is a list of Colors(), but may also include "custom" for any custom colors
            colors = pixelserver.seq_list.string_to_colors(color_list)
                     
            # If sequence changed then reset seq_position
            if (pixelserver.seq_set['sequence'] != current_sequence):
                sequence_position = 0
                current_sequence = pixelserver.seq_set['sequence']

        # returns sequence_position which is used for future calls
        sequence_position = pixels.updateSeq(
            pixelserver.seq_set['sequence'],
            sequence_position,
            pixelserver.seq_set['reverse'],
            colors) 
        last_update = pixelserver.upd_time
        # Sleep used for delay this means that there will be that long a delay between updates
        time.sleep(pixelserver.seq_set['delay']/1000)


app = create_app()

# run as two threads - main thread and flask thread
mt = threading.Thread(target=mainThread)
ft = threading.Thread(target=flaskThread)
mt.start()
ft.start()


