#jge - committing this with a tag from Windows 
#du
from time import sleep
import pigpio
import time
import tty
import sys
import termios
import RPi.GPIO as GPIO #jge - using for step count movement
import operator #jge - used to find max array value and member

class Environment():
    #jge - object to handle housekeeping jobs

    def __init__(self, microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0):
        self.getSettings()
        self.commonPinSetup(microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0)
     
    def getSettings(self):
        #jge - this has to do with setting up keyboard input
        #jge - making this change is what goofs up the format
        #jge - when making print statements.         

        self.orig_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin) 

    def restoreSettings(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.orig_settings)

    def commonPinSetup(self, microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0):
        #jge - As wired now, these GPIO pins are shared by all motor drivers.
        #jge - Doesn't seem like there will be a need for motors to use different
        #jge - microstepping values.  Also, I don't think there are enough pins on 
        #jge - the pi to accomodate.  

        self.mode = (modePin1, modePin2, modePin3)

        self.resolution = {'Full': (0, 0, 0),
                      'Half': (1, 0, 0),
                      '1/4': (0, 1, 0),
                      '1/8': (1, 1, 0),
                      '1/16': (0, 0, 1),
                      '1/32': (1, 0, 1)}

        for i in range(3):
            pi.write(self.mode[i], self.resolution[microstep][i])

class Motor():
    #jge - Object to act like a motor

    def __init__(self, motorSleepPin = 0, motorDirPin = 0, motorStepPin = 0, direction = 0, name = ''):
        self.motorSleepPin = motorSleepPin
        self.motorDirPin = motorDirPin
        self.motorStepPin = motorStepPin
        self.direction = direction
        self.name = name
        self.stepsToDestination = 0
        print('Created ' + self.name)

    def move(self, direction):
        self.wakeUp()
        pi.write(self.motorSleepPin, 1)
        pi.write(self.motorDirPin, direction)
        pi.write(self.motorStepPin, 1)
        pi.set_PWM_dutycycle(self.motorStepPin, 128)  # PWM 1/2 On 1/2 Off
        pi.set_PWM_frequency(self.motorStepPin, 500)
        sleep(.05)        

    def wakeUp(self):
        #jge - this restores power to the motor
        pi.write(self.motorSleepPin, 1)

    def sleep(self):
        #jge - this turns off motor voltage
        pi.write(self.motorSleepPin, 0)

    def stop(self):
        pi.write(self.motorStepPin, 0)
        pi.write(self.motorSleepPin, 0)   
        self.sleep()

    def gotoPreset(self):
        ####################
        #jge - temporary things for dev tests
        self.wakeUp()
        topShade.motor.wakeUp()

        leftShade.motor.stepsToDestination = 100
        rightShade.motor.stepsToDestination = 88
        topShade.motor.stepsToDestination = 1000
        botShade.motor.stepsToDestination = 900
        #jge - end temporary
        ####################

        #jge - initialize the wave
        pi.wave_clear()
        wfComplete = []
        
        #jge - construct the three sections of the wave.
        wfStart = self.buildRamp(1100, 400, 1)
        wfEnd = self.buildRamp(400, 1100, -1)
        wfMiddle = self.buildSteadyWave(400, len(wfStart) + len(wfEnd), )
        wfComplete = wfStart + wfMiddle + wfEnd
    
        #jge - send the combined waveform to pigpiod.pi
        #jge - spent time trying to send three discrete waves for
        #jge - the ramps and middle, but timing was glitchy
        pi.wave_add_generic(wfComplete)
        widComplete = pi.wave_create()
        pi.wave_send_once(widComplete)
        
    def buildRamp(self, startDelay, finalDelay, step):
        #jge - startDelay - higher number = lower starting freq
        #jge - finalDelay - higher number = lower final frequency
        #jge - step - Lower number = more gradual and more steps

        wfStart=[]
        for delay in range(startDelay, finalDelay, -step):
            wfStart.append(pigpio.pulse((1<<19)|(1<<17), 0, delay))
            wfStart.append(pigpio.pulse(0, (1<<19)|(1<<17), delay))

        return wfStart 

    def buildSteadyWave(self, delay, stepsAlreadyEatenByRamps):
        #jge - this is going to be the method that receives an integer
        #jge - that is the greatest step count that needs to be made
        #jge - of all the shades.

        leftStepsToDest = leftShade.motor.stepsToDestination - stepsAlreadyEatenByRamps
        rightStepsToDest = rightShade.motor.stepsToDestination - stepsAlreadyEatenByRamps
        topStepsToDest = topShade.motor.stepsToDestination - stepsAlreadyEatenByRamps
        botStepsToDest = botShade.motor.stepsToDestination - stepsAlreadyEatenByRamps
        #adjustedMaxStepCount = maxSteps - startStopRampSteps

        #jge - put into array to figure out which has most with the operator method
        lrtbStepsToDest = [leftStepsToDest, rightStepsToDest, topStepsToDest, botStepsToDest]
        max_value = max(lrtbStepsToDest)
        print('max value = ' + str(max_value))
        max_index = lrtbStepsToDest.index(max_value)
        print('the shade with the greatest step count is ' + allShades[max_index].name)

        countOfLowSteps = []
        lrtbOnOffRatios = []
        #jge - now get the step difference from the max to all others
        #jge - Also do the math to figure out the ratio of on vs off
        #jge - so that when in the wave building for loop, can
        #jge - check if the current iteration is divisible by this number

        for i, thisShade in enumerate(allShades):
            thisCountOfLowSteps = max_value - lrtbStepsToDest[i]
            countOfLowSteps.append(thisCountOfLowSteps)
            lrtbOnOffRatios.append(int(max_value / lrtbStepsToDest[i]))
            print('Low steps for ' + allShades[i].name + ' = ' + str(thisCountOfLowSteps)) 
            print('Ratio for ' + allShades[i].name + ' = ' + str(int(max_value / lrtbStepsToDest[i])))

        #jge - hard coded 1000 steps just to see how the sandwich works
            
        wfMiddle = []
        for thisStep in range(1000):
            wfMiddle.append(pigpio.pulse((1<<19)|(1<<17), 0, delay))
            wfMiddle.append(pigpio.pulse(0, (1<<19)|(1<<17), delay))

        return wfMiddle

class Shade():
    #jge - Object to stand in for a blind assembly 

    def __init__(self, motor, name = ''):
        self.motor = motor
        self.name = name
        print('Created ' + self.name)

    def move(self, displayMessage, direction):
        self.motor.move(direction)
        print(displayMessage)

    def stop(self, displayMessage):
        self.motor.stop()
        print(displayMessage)

#################################################################
#jge - init

pi = pigpio.pi() # Connect to pigpiod daemon
if not pi.connected:
   exit(0)

#jge - setup generic hardware and software 
environment = Environment('Full', 14, 15, 18) 

leftMotor = Motor(6, 26, 19, 0, 'motor 3')
leftShade = Shade(leftMotor, 'left shade')

rightMotor = Motor(12, 24, 23, 0, 'motor 1')
rightShade = Shade(rightMotor, 'right shade')

topMotor = Motor(5, 27, 17, 0, 'motor 2')
topShade = Shade(topMotor, 'top shade')

botMotor = Motor(13, 20, 21, 0, 'motor 4')
botShade = Shade(botMotor, 'bottom shade')

allShades = [leftShade, rightShade, topShade, botShade]

#jge - end init
#################################################################

#################################################################
#jge - This would be main.  Infinite loop to check for user input

try:
    while True:
        dirKey = sys.stdin.read(1)[0]

        if (dirKey == 'n') :
            botShade.move('Bottom Cover', 1)
        elif (dirKey == 'v'):
            botShade.move('Bottom Uncover', 0)
        elif (dirKey ==  'b'):
            botShade.stop('Bottom Stop')
        elif (dirKey == 'd'):
            leftShade.move('Left Cover', 0)
        elif (dirKey == 'a'):
            leftShade.move('Left Uncover', 1)
        elif (dirKey == 's'):
            leftShade.stop('Left Stop')
        elif (dirKey == 'u') :
            topShade.move('Top Cover', 0)
        elif (dirKey == 't'):
            topShade.move('Top Uncover', 1)
        elif (dirKey ==  'y'):
            topShade.stop('Top Stop')
        elif (dirKey == 'j') :
            rightShade.move('Right Cover', 0)
        elif (dirKey == 'l'):
            rightShade.move('Right Uncover', 1)
        elif (dirKey ==  'k'):
            rightShade.stop('Right Stop')
        elif (dirKey == 'z'):
            #print('Uncovering All')
            leftShade.move('', 1)
            rightShade.move('', 1)
            topShade.move('', 1)
            botShade.move('', 0)
        elif (dirKey == 'x'):
            #print('Covering All')
            leftShade.move('', 0)
            rightShade.move('', 0)
            topShade.move('', 0)
            botShade.move('', 1) 
        elif (dirKey == 'p'):
            print('All Stop')
            for i, thisShade in enumerate(allShades):
                thisShade.stop('Stopping ' + thisShade.name)
        elif (dirKey == 'q'):
            raise Exception('Quitting')
        elif (dirKey == 'e'):
            print('gradual with Count')
            leftShade.motor.gradual()
        elif (dirKey == 'r'):
            print('Goto preset')
            leftShade.motor.gotoPreset()
        else:
            pass
except Exception as e :
    print ('\nOh goooood for you')
    raise
finally:
    environment.restoreSettings()

    for i, thisShade in enumerate(allShades):
        thisShade.stop('Shutting down ' + thisShade.name)

    pi.stop()

#jge - end main loop
############################################
