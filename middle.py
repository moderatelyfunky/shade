#jge - this class will act as a layer between the UI
#jge - and the controller, so dev work can be done
#jge - and the program run without being on the pi
gotPi = 0

import controller as con
gUnit = con.Unit()

def gotoPreset(event, presetNo):
    if (gotPi == 1):
        gUnit.gotoPreset(event, presetNo)

def writePreset(event, presetNo):
    if (gotPi == 1):
        gUnit.writePreset(event, presetNo)

def stop(event, shade):
    if (gotPi == 1):
        if (shade == 'left'):
            gUnit.leftShade.motor.stop(event)
        elif (shade == 'right'):
            gUnit.rightShade.motor.stop(event)
        elif (shade == 'top'):
            gUnit.topShade.motor.stop(event)
        elif (shade == 'bot'):
            gUnit.botShade.motor.stop(event)

def move(event, shade, direction):
    if (gotPi == 1):
        if (shade == 'left'):
            gUnit.leftShade.motor.move(event, direction)
        elif (shade == 'right'):
            gUnit.rightShade.motor.move(event, direction)
        elif (shade == 'top'):
            gUnit.topShade.motor.move(event, direction)
        elif (shade == 'bot'):
            gUnit.botShade.motor.move(event, direction)
