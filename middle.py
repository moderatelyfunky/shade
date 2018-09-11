#jge - this class will act as a layer between the UI
#jge - and the controller, so dev work can be done
#jge - and the program run without being on the pi
import gotPi as gp #jge - figure out which libraries to load
thisGotPi = gp.PiRunning()
thisGP = thisGotPi.gotPi

class Middle():
    def __init__(self): 
        if (thisGP == '1'):
            import controller as con
            self.gUnit = con.Unit()

    def gotoPreset(self, event, presetNo):
        if (thisGP == '1'):
            self.gUnit.gotoPreset(event, presetNo)

    def writePreset(self, event, presetNo):
        if (thisGP == '1'):
            self.gUnit.writePreset(event, presetNo)

    def stop(self, event, shade):
        if (thisGP == '1'):
            if (shade == 'left'):
                self.gUnit.leftShade.motor.stop(event)
            elif (shade == 'right'):
                self.gUnit.rightShade.motor.stop(event)
            elif (shade == 'top'):
                self.gUnit.topShade.motor.stop(event)
            elif (shade == 'bot'):
                self.gUnit.botShade.motor.stop(event)

    def move(self, event, shade, direction):
        if (thisGP == '1'):
            if (shade == 'left'):
                self.gUnit.leftShade.motor.move(event, direction)
            elif (shade == 'right'):
                self.gUnit.rightShade.motor.move(event, direction)
            elif (shade == 'top'):
                self.gUnit.topShade.motor.move(event, direction)
            elif (shade == 'bot'):
                self.gUnit.botShade.motor.move(event, direction)
