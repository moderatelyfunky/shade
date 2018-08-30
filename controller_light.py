import weakref
from time import sleep
import pigpio
import time
import tty
import sys
import termios
import RPi.GPIO as GPIO #jge - using for step count movement
import operator #jge - used to find max array value and member

class Unit():
    #jge - this is the main point of entry for control from the gui

    def __init__(self):
        self.pi = pigpio.pi() # Connect to pigpiod daemon
        if not self.pi.connected:
           exit(0)

        ##########################################################
        #jge - Motor constructors 
        #jge - 1st argument = sleep Pin
        #jge - 2nd argument = dir Pin
        #jge - 3rd argument = step pin
        #jge - 4th argument = name
        #jge - 5th argument = Cover direction - so can compare when +- steps
        #jge - 6th argument = Uncover direction
        #jge - HomeSwitch constructors.  1st arg - gpio
        ##########################################################
        self.leftHomeSwitch = HomeSwitch(self, 1, 'left home switch')
        self.leftMotor = Motor(self, 6, 26, 19, 0, 'motor 3', 0, 1)
        self.leftShade = Shade(self, self.leftMotor, self.leftHomeSwitch, 'left shade')

        self.rightHomeSwitch = HomeSwitch(self, 1, 'right home switch')
        self.rightMotor = Motor(self, 12, 24, 23, 0, 'motor 1', 0, 1)
        self.rightShade = Shade(self, self.rightMotor, self.rightHomeSwitch, 'right shade')

        self.topHomeSwitch = HomeSwitch(self, 1, 'top home switch')
        self.topMotor = Motor(self, 5, 27, 17, 0, 'motor 2', 0, 1)
        self.topShade = Shade(self, self.topMotor, self.topHomeSwitch, 'top shade')

        self.botHomeSwitch = HomeSwitch(self, 1, 'bottom home switch')
        self.botMotor = Motor(self, 13, 20, 21, 0, 'motor 4', 1, 0)
        self.botShade = Shade(self, self.botMotor, self.botHomeSwitch, 'bottom shade')

        ##########################################################
        #jge - Environment constructor - setup common properties
        #jge - 1st argument = Microstep Mode - Full, 1/2, 1/4, 1/8, 1/16, 1/32
        #jge - 2nd argument = Mode pin 1 - shared by all motor drivers
        #jge - 3rd argument = Mode pin 2 - shared by all motor drivers
        #jge - 4th argument = Mode pin 3 - shared by all motor drivers
        #jge - 5th argument = Maximum microsecond delay between preset going pulses
        #jge - 6th argument = Minimum ""
        #jge - 7th argument - How much to gain between the min and max in each loop  
        #################################################################
        self.environment = Environment(self, 'Full', 14, 15, 18, 1100, 400, 1) 
        print('Created environment')
        self.allShades = [self.leftShade, self.rightShade, self.topShade, self.botShade]
        print('Created allshades array')
        print('Done with init')
        #unit = Unit([self.leftShade, self.rightShade, self.topShade, self.botShade], environment)
        #jge - end Unit init
        #################################################################
        
    def wakeUpAll(self):
        for i, thisShade in enumerate(self.allShades):
            thisShade.motor.wakeUp()

    def sleepAll(self):
        for i, thisShade in enumerate(self.allShades):
            thisShade.motor.sleep()
            
    def uncoverAll(self):
        print('Uncovering all')
        self.gotoPreset(5)

    def coverAll(self):
        print('Covering all')
        self.gotoPreset(6)

    def stopAll(self):
        for i, thisShade in enumerate(self.allShades):
            print('Stopping ' + thisShade.name)           
            print(self.allShades[i].name + ' steps from home = ' + str(self.allShades[i].motor.stepsFromHomeCount))
            thisShade.motor.stop()

    def cleanup(self):
        self.environment.restoreSettings()

        for i, thisShade in enumerate(self.allShades):
            print('Shutting down ' +  thisShade.name)
            thisShade.motor.stop()

        self.pi.stop()

    #def setPresetPositions(self):
        #jge - todo: some future method to save current step counts
        
    def getPresetPositions(self, presetNo):
        #jge - Use the preset number to retrieve the positions for each 
        #####################################
        #jge - hard coded preset building for now
                 
        self.leftShade.preset.append(3000)
        self.rightShade.preset.append(7000)
        self.topShade.preset.append(3200)
        self.botShade.preset.append(2500)

        self.leftShade.preset.append(8000)
        self.rightShade.preset.append(500)
        self.topShade.preset.append(100)
        self.botShade.preset.append(100)

        self.leftShade.preset.append(5000)
        self.rightShade.preset.append(4000)
        self.topShade.preset.append(3000)
        self.botShade.preset.append(2000)

        self.leftShade.preset.append(1000)
        self.rightShade.preset.append(2000)
        self.topShade.preset.append(3000)
        self.botShade.preset.append(4000)

        self.leftShade.preset.append(0)
        self.rightShade.preset.append(0)
        self.topShade.preset.append(0)
        self.botShade.preset.append(0)

        self.leftShade.preset.append(8900)
        self.rightShade.preset.append(8900)
        self.topShade.preset.append(10500)
        self.botShade.preset.append(10500)
        ################################
        for i, thisShade in enumerate(self.allShades):
            theDestination = self.allShades[i].preset[presetNo - 1]

            #jge - set the direction pin of each motor object also
            #jge - write to the gpio pin to set the direction and 
            #jge - set stepsToDest which is used in the wave creation.  
            if (theDestination > self.allShades[i].motor.stepsFromHomeCount):
                self.allShades[i].motor.direction = self.allShades[i].motor.coverDirection
                self.pi.write(self.allShades[i].motor.dirPin, self.allShades[i].motor.coverDirection)
                self.allShades[i].motor.stepsToDest = theDestination - self.allShades[i].motor.stepsFromHomeCount
            else:
                self.allShades[i].motor.direction = self.allShades[i].motor.uncoverDirection
                self.pi.write(self.allShades[i].motor.dirPin, self.allShades[i].motor.uncoverDirection)
                self.allShades[i].motor.stepsToDest = self.allShades[i].motor.stepsFromHomeCount - theDestination 
            
    def gotoPreset(self, presetNo):
        ################################
        #jge - preset init 
        self.wakeUpAll()
        self.getPresetPositions(presetNo)
        maxDelay = self.environment.maxDelay
        minDelay = self.environment.minDelay
        step = self.environment.stepSize
        #jge - end preset init
        ################################

        #jge - sort the shades by least steps to travel
        tempSortedShades = sorted(self.allShades, key=lambda x: x.motor.stepsToDest, reverse=False)
        sortedShades = []

        #jge - there must be a better way to do this
        for i, thisShade in enumerate(tempSortedShades):
            #jge - forget about shades who may already be in position
            if (tempSortedShades[i].motor.stepsToDest != 0):
                sortedShades.append(tempSortedShades[i])
                      
        #jge - build the starting ramp of the wave.  Only add the pins
        #jge - for the shades that still have steps to move.  The bitmask 
        #jge - is the container for all the pins that will be set high.
        #jge - It's an integer that is picked apart later by pigpio.
        
        wfStart = []
        pulseCount = 0
        for delay in range(maxDelay, minDelay, -step):
            bitmask = 0
            pulseCount += 1
            for i, thisShade in enumerate(sortedShades):
                if (thisShade.motor.stepsToDest > pulseCount):
                    if (bitmask == 0):
                        bitmask = int(1<<sortedShades[i].motor.stepPin)
                    else:
                        bitmask += int(1<<sortedShades[i].motor.stepPin)
                
            #jge - now build the pulse and add it to the array
            wfStart.append(pigpio.pulse(bitmask, 0, delay))
            wfStart.append(pigpio.pulse(0, bitmask, delay))

        
        stepsAlreadyTaken = pulseCount

        #jge - remove any shades who may have no more steps left
        for i, thisShade in enumerate(sortedShades):
            if (sortedShades[i].motor.stepsToDest <= stepsAlreadyTaken):
                sortedShades[i].motor.stepsToDest = 0
                sortedShades.remove(sortedShades[i])
                
        #jge - Build a wave that has the steady state pulses for all
        #jge - until the shade with the least steps is at its goal.
        #jge - Then remove that shade from the array and build for
        #jge - the rest until the step count is reached for the shade 
        #jge - with the next least amount of steps.  Do it two more times

        wfMiddle_A = []
        wfMiddle_B = []
        wfMiddle_C = []
        wfMiddle_D = []
        
        middleWave_A = 0
        wfMiddle_A_Singles = 0
        wfMiddle_A_LoopCount = 0

        middleWave_B = 0
        wfMiddle_B_Singles = 0
        wfMiddle_B_LoopCount = 0
        
        middleWave_C = 0
        wfMiddle_C_Singles = 0
        wfMiddle_C_LoopCount = 0
        
        middleWave_D = 0
        wfMiddle_D_Singles = 0
        wfMiddle_D_LoopCount = 0
        
        #jge - it's possible that the ramp used up all the steps
        if (len(sortedShades) > 0):
            wfMiddle_A, wfMiddle_A_LoopCount, wfMiddle_A_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_A_LoopCount * 256) + wfMiddle_A_Singles

        if (len(sortedShades) > 0):
            wfMiddle_B, wfMiddle_B_LoopCount, wfMiddle_B_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_B_LoopCount * 256) + wfMiddle_B_Singles

        if (len(sortedShades) > 0):
            wfMiddle_C, wfMiddle_C_LoopCount, wfMiddle_C_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_C_LoopCount * 256) + wfMiddle_C_Singles

        if (len(sortedShades) > 0):
            wfMiddle_D, wfMiddle_D_LoopCount, wfMiddle_D_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_D_LoopCount * 256) + wfMiddle_D_Singles

        #jge - Clear out any waves that may not have been cleaned up
        self.pi.wave_clear()

        #jge - Use Wave_add_generic to "convert" the arrays of pulses
        #jge - into waves that will be fed to pigpio with the wave_chain
        #jge - method
        self.pi.wave_add_generic(wfStart)

        #jge - make sure won't get empty wave errors
        if (len(wfStart) > 0):
            startRamp = self.pi.wave_create()

        if (len(wfMiddle_A) > 0):
            self.pi.wave_add_generic(wfMiddle_A)
            middleWave_A = self.pi.wave_create()

        if (len(wfMiddle_B) > 0):
            self.pi.wave_add_generic(wfMiddle_B)
            middleWave_B = self.pi.wave_create()

        if (len(wfMiddle_C) > 0):
            self.pi.wave_add_generic(wfMiddle_C)
            middleWave_C = self.pi.wave_create()

        if (len(wfMiddle_D) > 0):
            self.pi.wave_add_generic(wfMiddle_D)
            middleWave_D = self.pi.wave_create()

        #jge - Build an array of the waves to make clean up easier
        #allWaves = [startRamp, middleWave_A, middleWave_B, middleWave_C, middleWave_D]                                           

        #jge - this is the method that pushes the waves to the motors
        #jge - the blocks that start with 255 are loops.  The closing
        #jge - part of the loop tells pigpio how many times to loop
        #jge - each wave and how many single iterations of it after that 
        self.pi.wave_chain([
           startRamp,        
           255, 0,                       
              middleWave_A,    
           255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, #loop x + y*256 times
           255, 0,                       
              middleWave_B,    
           255, 1, wfMiddle_B_Singles, wfMiddle_B_LoopCount,          
           255, 0,                       
              middleWave_C,    
           255, 1, wfMiddle_C_Singles, wfMiddle_C_LoopCount,       
           255, 0,                       
              middleWave_D,    
           255, 1, wfMiddle_D_Singles, wfMiddle_D_LoopCount,                             
           ])

        #jge - Get control of the situation.  No more phone calls
        while self.pi.wave_tx_busy():
           time.sleep(0.1)

        pigpio.exceptions = True

        if (startRamp > 0):
            self.pi.wave_delete(startRamp)
        if (middleWave_A > 0):
            self.pi.wave_delete(middleWave_A)
        if (middleWave_B > 0):
            self.pi.wave_delete(middleWave_B)
        if (middleWave_C > 0):
            self.pi.wave_delete(middleWave_C)
        if (middleWave_D > 0):
            self.pi.wave_delete(middleWave_D)

        self.sleepAll()
        print('Finished going to preset')

    def buildMiddleWave(self, stepsAlreadyTaken, sortedShades):
        #jge - This method will build an array of pulses for the
        #jge - steady state portion of the movement.  It uses the
        #jge - same pigpio features as the ramp.  The additional
        #jge - work being done here is to figure out how many times
        #jge - the wave should be looped and run individually.  This
        #jge - is because pigpio has a limit of 256 iterations for
        #jge - each wave.  Anything over that means another loop or
        #jge - just the remainder if it's less than 256
        
        minDelay = self.environment.minDelay
        maxDelay = self.environment.maxDelay
        step = self.environment.stepSize

        wfMiddle = []

        #jge - store the count to feed to the wave_chain looper
        maxSingle = 256
        countMiddle = sortedShades[0].motor.stepsToDest - stepsAlreadyTaken
        
        if (countMiddle > 256):
            wfMiddle_LoopCount = int(countMiddle / maxSingle)
            wfMiddle_Singles = countMiddle % maxSingle
        else:
            wfMiddle_LoopCount = 0
            wfMiddle_Singles = countMiddle

        if (sortedShades[0].motor.stepsToDest > stepsAlreadyTaken):
            bitmask = 0
            for i, thisShade in enumerate(sortedShades):
                if (bitmask == 0):
                    bitmask = int(1<<sortedShades[i].motor.stepPin)
                else:
                    bitmask += int(1<<sortedShades[i].motor.stepPin)
            wfMiddle.append(pigpio.pulse(bitmask, 0, minDelay))
            wfMiddle.append(pigpio.pulse(0, bitmask, minDelay))            

        return wfMiddle, wfMiddle_LoopCount, wfMiddle_Singles

    #jge - end unit class
    ####################################################
    
class Environment():
    #jge - housekeeping?

    def __init__(self, parent, microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0, maxDelay = 0, minDelay = 0, stepSize = 0):
        #self.parent = weakref.ref(parent)
        self.parent = parent
        #jge - no need for this with GUI? self.getSettings()
        self.commonPinSetup(microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0)
        #jge - maxDelay is the lowest frequency between pulses
        self.maxDelay = maxDelay
        #jge - minDelay is the quickest pace
        self.minDelay = minDelay
        #jge - how much to gain between high and low frequencies
        self.stepSize = stepSize

    def getSettings(self):
        #jge - this has to do with setting up keyboard input
        #jge - making this change is what goofs up the format
        #jge - when making print statements.         
        self.orig_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin) 

    def restoreSettings(self):
        #jge - this puts the terminal back as it was so line feeds work
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
            self.parent.pi.write(self.mode[i], self.resolution[microstep][i])

class Shade():
    #jge - container for shade elements
    def __init__(self, parent, motor, switch, name = ''):
        self.parent = weakref.ref(parent) 
        self.motor = motor
        self.name = name
        self.homeSwitch = switch
        self.preset = []
        print('Created ' + self.name)

class HomeSwitch():
    #jge - object to manage the limit switches used to find home
    def __init__(self, parent, switchPin, name = ''):
        self.parent = weakref.ref(parent) 
        self.switchPin = switchPin
        self.name = name
        print('Created ' + self.name)

class Motor():
    def __init__(self, parent, sleepPin = 0, dirPin = 0, stepPin = 0, direction = 0, name = '', coverDirection = 0, uncoverDirection = 0):
        #self.parent = weakref.ref(parent)
        self.parent = parent
        self.sleepPin = sleepPin
        self.dirPin = dirPin
        self.stepPin = stepPin
        self.direction = coverDirection
        self.name = name
        self.stepsToDest = 0
        self.stepsFromHomeObject = None
        self.stepsFromHomeCount = 0
        self.coverDirection = coverDirection
        self.uncoverDirection = uncoverDirection
        #jge - set up callback function to keep track of steps
        self.stepsFromHomeObject = parent.pi.callback(self.stepPin, pigpio.RISING_EDGE, self.callbackFunc)
        print('Created ' + self.name)

    def move(self, direction):        
        #jge - make sure it's not running against the wide open stops
        
        if (direction == self.coverDirection or (direction != self.coverDirection and self.stepsFromHomeCount > 0)):
            self.direction = direction
            self.wakeUp()
            self.parent.pi.write(self.sleepPin, 1)
            self.parent.pi.write(self.dirPin, direction)
            self.parent.pi.write(self.stepPin, 1)
            self.parent.pi.set_PWM_dutycycle(self.stepPin, 128)  # PWM 1/2 On 1/2 Off
            self.parent.pi.set_PWM_frequency(self.stepPin, 500)
            sleep(.05)
        else:
            print('Cant open ' + self.name + ' any further')

        """
        #jge - keeping this block around to easily comment the block above
        #jge - when the shades are not in zero positions, but the program
        #jge - thinks they are and won't allow them to be rolled up
        self.direction = direction
        self.wakeUp()
        pi.write(self.sleepPin, 1)
        pi.write(self.dirPin, direction)
        pi.write(self.stepPin, 1)
        pi.set_PWM_dutycycle(self.stepPin, 128)  # PWM 1/2 On 1/2 Off
        pi.set_PWM_frequency(self.stepPin, 500)
        sleep(.05)
        """
        
    def callbackFunc(self, gpio, level, tick):     
        #jge - figure out whether to add or subtract the steps
        if (self.direction == self.coverDirection):
            self.stepsFromHomeCount += 1
        else:
            self.stepsFromHomeCount -= 1

        #jge - stop the move if it's wide open
        if (self.stepsFromHomeCount == 0 and self.direction != self.coverDirection):
            self.stop()
            print('Stopping motor ' + self.name + 'because the shade is wide open')
            
    def stop(self):
        #jge - stop motion then sleep
        self.parent.pi.write(self.stepPin, 0)
        self.parent.pi.write(self.sleepPin, 0)
        self.sleep()
        
    def sleep(self):
        #jge - this turns off motor voltage
        self.parent.pi.write(self.sleepPin, 0)
        
    def wakeUp(self):
        #jge - this restores power to the motor
        self.parent.pi.write(self.sleepPin, 1)

#################################################################
#jge - This would be main.  Infinite loop to check for user input
"""
try:
    while True:
        dirKey = sys.stdin.read(1)[0]

        if (dirKey == 'n') :
            print('Bottom Cover')
            botShade.motor.move(1)
        elif (dirKey == 'v'):
            print('Bottom Uncover')
            botShade.motor.move(0)
        elif (dirKey ==  'b'):
            print('Bottom Stop')
            botShade.motor.stop()
            
        elif (dirKey == 'd'):
            print('Left Cover')
            leftShade.motor.move(0)
        elif (dirKey == 'a'):
            print('Left Uncover')
            leftShade.motor.move(1)
        elif (dirKey == 's'):
            print('Left stop')           
            leftShade.motor.stop()
            
        elif (dirKey == 'u') :
            print('Top Cover')           
            topShade.motor.move(0)
        elif (dirKey == 't'):
            print('Top Uncover')            
            topShade.motor.move(1)
        elif (dirKey ==  'y'):
            print('Top Stop') 
            topShade.motor.stop()
            
        elif (dirKey == 'j') :
            print('Right Cover')
            rightShade.motor.move(0)
        elif (dirKey == 'l'):
            print('Right Uncover')
            rightShade.motor.move(1)
        elif (dirKey ==  'k'):
            print('Right Stop')
            rightShade.motor.stop()
            
        elif (dirKey == 'z'):
            print('Uncovering All')
            #unit.uncoverAll()
            unit.gotoPreset(5)
            
        elif (dirKey == 'x'):
            print('Covering All')
            unit.gotoPreset(6)
            
        elif (dirKey == 'p'):
            print('All Stop')
            unit.stopAll()

        elif (dirKey == '1'):
            print('Goto preset 1')
            unit.gotoPreset(1)

        elif (dirKey == '2'):
            print('Goto preset 2')
            unit.gotoPreset(2)

        elif (dirKey == '3'):
            print('Goto preset 3')
            unit.gotoPreset(3)

        elif (dirKey == '4'):
            print('Goto preset 4')
            unit.gotoPreset(4)
            
        elif (dirKey == 'q'):
            raise Exception('Quitting')
    
        else:
            pass
except Exception as e :
    print ('\nOh goooood for you')
    raise
finally:
    unit.cleanup()
"""
#jge - end main loop
############################################
