class PixelConfig():
    
    
    def __init__ (self):
        self.default_led_settings = {
        'ledcount': 44,
        'gpiopin': 18,
        'ledfreq': 800000,
        'leddma' : 5,
        'ledmaxbrightness': 50,
        'ledinvert': False,
        'ledchannel': 0           #       
        }
        self.ledcount = self.default_led_settings['ledcount']
        self.gpiopin = 21
        self.ledfreq = self.default_led_settings['ledfreq']
        self.leddma = self.default_led_settings['leddma']
        self.ledmaxbrightness = self.default_led_settings['ledmaxbrightness']
        self.ledinvert = self.default_led_settings['ledinvert']
        self.ledchannel = self.default_led_settings['ledchannel']

    def get_defaults (self):
        return self.default_led_settings
