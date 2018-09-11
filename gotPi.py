#jge - class to figure out if a Pi is running the code
import configparser

class PiRunning():
    def __init__(self):
        self.iniFileName = 'shade.ini'
        self.config = configparser.RawConfigParser()
        self.config.optionxform = str
        self.config.read(self.iniFileName)
        self.gotPi = self.config.get('config', 'gotPi')