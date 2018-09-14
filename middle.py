#jge - this class is a layer between the UI and the 
#jge - controller, so the program run without being 
#jge - on the pi.  If the INI has a 0 for the gotPi
#jge - the controller isn't built.

import configparser

class Middle():
    def __init__(self): 
        self.piHere = self.isRunningOnPi()
        #jge - only instantiate the controller when needed
        if (self.piHere == '1'):
            import controller as con
            self.gUnit = con.Unit()

    def isRunningOnPi(self):
        #jge - read the ini to get the gotPi value.
        self.iniFileName = 'shade.ini'
        self.config = configparser.RawConfigParser()
        self.config.optionxform = str
        self.config.read(self.iniFileName)
        self.gotPi = self.config.get('config', 'gotPi')
        if (self.gotPi == '1'):
            print('Running Pifull')
            return self.gotPi
        else:
            print('Running Piless')
            return self.gotPi

    def gotoPreset(self, event, presetNo):
        if (self.piHere == '1'):
            self.gUnit.gotoPreset(event, presetNo)
            
        print('Finished going to preset ' + str(presetNo))  

    def writePreset(self, event, presetNo):
        if (self.piHere == '1'):
            self.gUnit.writePreset(event, presetNo)
            
        print('Preset ' + str(presetNo) + ' stored ')
    
    def stop(self, event, shade):
        if (self.piHere == '1'):
            if (shade == 'left'):
                self.gUnit.leftShade.motor.stop(event)
            elif (shade == 'right'):
                self.gUnit.rightShade.motor.stop(event)
            elif (shade == 'top'):
                self.gUnit.topShade.motor.stop(event)
            elif (shade == 'bot'):
                self.gUnit.botShade.motor.stop(event)
        print('Stopped ' + shade + ' shade')

    def move(self, event, shade, direction):
        if (self.piHere == '1'):
            if (shade == 'left'):
                self.gUnit.leftShade.motor.move(event, direction)
            elif (shade == 'right'):
                self.gUnit.rightShade.motor.move(event, direction)
            elif (shade == 'top'):
                self.gUnit.topShade.motor.move(event, direction)
            elif (shade == 'bot'):
                self.gUnit.botShade.motor.move(event, direction)
        print('Moving ' + shade + ' shade in direction ' + str(direction))
