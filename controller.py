from time import sleep
import pigpio
import time
import tty
import sys
import termios
import RPi.GPIO as GPIO #jge - using for step count movement
import operator #jge - used to find max array value and member

class Unit():
    #jge - store the collection of shades for common methods

    def __init__(self, initShades = [], environment = None):
        self.allShades = initShades
        self.environment = environment

    def wakeUpAll(self):
        for i, thisShade in enumerate(self.allShades):
            thisShade.motor.wakeUp()

    def sleepAll(self):
        for i, thisShade in enumerate(self.allShades):
            thisShade.motor.sleep()
            
    def uncoverAll(self):
        leftShade.motor.move(1)
        rightShade.motor.move(1)
        topShade.motor.move(1)
        botShade.motor.move(0)

    def coverAll(self):
        leftShade.motor.move(0)
        rightShade.motor.move(0)
        topShade.motor.move(0)
        botShade.motor.move(1)

    def stopAll(self):
        for i, thisShade in enumerate(unit.allShades):
            print('Stopping ' + thisShade.name)           
            print(self.allShades[i].name + ' steps from home = ' + str(self.allShades[i].motor.stepsFromHomeCount))
            thisShade.motor.stop()

    def cleanup(self):
        self.environment.restoreSettings()

        for i, thisShade in enumerate(self.allShades):
            print('Shutting down ' +  thisShade.name)
            thisShade.motor.stop()

        pi.stop()

    #def setPresetPositions(self):
        #jge - todo: some future method to save current step counts
        
    def getPresetPositions(self, presetNo):
        #####################################
        #jge - hard coded dev magic for now

        if (presetNo == 1):          
            leftShade.preset.append(5000)
            rightShade.preset.append(4100)
            topShade.preset.append(3200)
            botShade.preset.append(2500)
        elif (presetNo == 2):
            leftShade.preset[1] = 5000
            rightShade.preset[1] = 4100
            topShade.preset[1] = 3200
            botShade.preset[1] = 2500
        elif (presetNo == 2):
            leftShade.preset[2] = 5000
            rightShade.preset[2] = 4100
            topShade.preset[2] = 3200
            botShade.preset[2] = 2500
        elif (presetNo == 4):
            leftShade.preset[3] = 5000
            rightShade.preset[3] = 4100
            topShade.preset[3] = 3200
            botShade.preset[3] = 2500             
        ################################
        
        #jge - Use the preset number to retrieve the positions for each 
        for i, thisShade in enumerate(unit.allShades):
            #jge - determine the difference between current and preset
            theDestination = unit.allShades[i].preset[presetNo - 1]
            print('theDestination for ' + unit.allShades[i].name + str(theDestination))
            #jge - set the direction pin of each motor, also set stepsToDest
            #jge - which is used in the wave creation.  
            if (theDestination > unit.allShades[i].motor.stepsFromHomeCount):
                unit.allShades[i].motor.direction = unit.allShades[i].motor.coverDirection
                unit.allShades[i].motor.stepsToDest = theDestination - unit.allShades[i].motor.stepsFromHomeCount
            else:
                unit.allShades[i].motor.direction = unit.allShades[i].motor.uncoverDirection
                unit.allShades[i].motor.stepsToDest = unit.allShades[i].motor.stepsFromHomeCount - theDestination 

            #jge - Even though it hasn't happened yet, assume the best
            #jge - and update the stepsFromHomeCount            
            #unit.allShades[i].motor.stepsFromHomeCount = theDestination
            
    def gotoPreset(self, presetNo):
        ################################
        #jge - preset init 
        unit.wakeUpAll()
        self.getPresetPositions(presetNo)
        maxDelay = unit.environment.maxDelay
        minDelay = unit.environment.minDelay
        step = unit.environment.stepSize
        #jge - end preset init
        ################################

        #jge - sort the shades by least steps to travel
        tempSortedShades = sorted(unit.allShades, key=lambda x: x.motor.stepsToDest, reverse=False)
        sortedShades = []

        #jge - there is a better way to do this
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
        #stepsAlreadyTaken = len(wfStart)
        print('wfStart length = ' + str(len(wfStart)))
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
        
        print('length of sortedShades = ' + str(len(sortedShades)))
        for i, thisShade in enumerate(sortedShades):
            print('this shade is still in the running ' + sortedShades[i].name)

        #jge - it's possible that the ramp used up all the steps
        if (len(sortedShades) > 0):
            wfMiddle_A, wfMiddle_A_LoopCount, wfMiddle_A_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_A_LoopCount * 256) + wfMiddle_A_Singles
            print('middle a stepsAlreadyTaken = ' + str(stepsAlreadyTaken))

        if (len(sortedShades) > 0):
            wfMiddle_B, wfMiddle_B_LoopCount, wfMiddle_B_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_B_LoopCount * 256) + wfMiddle_B_Singles
            print('middle b stepsAlreadyTaken = ' + str(stepsAlreadyTaken))

        if (len(sortedShades) > 0):
            wfMiddle_C, wfMiddle_C_LoopCount, wfMiddle_C_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_C_LoopCount * 256) + wfMiddle_C_Singles
            print('middle c stepsAlreadyTaken = ' + str(stepsAlreadyTaken))

        if (len(sortedShades) > 0):
            wfMiddle_D, wfMiddle_D_LoopCount, wfMiddle_D_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_D_LoopCount * 256) + wfMiddle_D_Singles
            print('middle d stepsAlreadyTaken = ' + str(stepsAlreadyTaken))

        #jge - Clear out any waves that may not have been cleaned up
        pi.wave_clear()

        #jge - Use Wave_add_generic to "convert" the arrays of pulses
        #jge - into waves that will be fed to pigpio with the wave_chain method
        pi.wave_add_generic(wfStart)

        #jge - make sure won't get empty wave error
        if (len(wfStart) > 0):
            startRamp = pi.wave_create()

        if (len(wfMiddle_A) > 0):
            pi.wave_add_generic(wfMiddle_A)
            middleWave_A = pi.wave_create()

        if (len(wfMiddle_B) > 0):
            pi.wave_add_generic(wfMiddle_B)
            middleWave_B = pi.wave_create()

        if (len(wfMiddle_C) > 0):
            pi.wave_add_generic(wfMiddle_C)
            middleWave_C = pi.wave_create()

        if (len(wfMiddle_D) > 0):
            pi.wave_add_generic(wfMiddle_D)
            middleWave_D = pi.wave_create()

        #jge - Build an array of the waves to make clean up easier
        #allWaves = [startRamp, middleWave_A, middleWave_B, middleWave_C, middleWave_D]                                           

        #jge - this is the method that pushes the waves to the motors
        #jge - the blocks that start with 255 are loops.  The closing
        #jge - part of the loop tells pigpio how many times to loop
        #jge - each wave and how many single iterations of it after that 
        pi.wave_chain([
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
        while pi.wave_tx_busy():
           time.sleep(0.1)

        pigpio.exceptions = True

        if (startRamp > 0):
            pi.wave_delete(startRamp)
        if (middleWave_A > 0):
            pi.wave_delete(middleWave_A)
        if (middleWave_B > 0):
            pi.wave_delete(middleWave_B)
        if (middleWave_C > 0):
            pi.wave_delete(middleWave_C)
        if (middleWave_D > 0):
            pi.wave_delete(middleWave_D)

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
        
        minDelay = unit.environment.minDelay
        maxDelay = unit.environment.maxDelay
        step = unit.environment.stepSize

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

    def __init__(self, microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0, maxDelay = 0, minDelay = 0, stepSize = 0):
        self.getSettings()
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
            pi.write(self.mode[i], self.resolution[microstep][i])

class Shade():
    #jge - container for shade elements
    def __init__(self, motor, switch, name = ''):
        self.motor = motor
        self.name = name
        self.homeSwitch = switch
        self.preset = []
        print('Created ' + self.name)

class HomeSwitch():
    #jge - object to manage the limit switches used to find home
    def __init__(self, switchPin, name = ''):
        self.switchPin = switchPin
        self.name = name
        print('Created ' + self.name)

class Motor():
    def __init__(self, sleepPin = 0, dirPin = 0, stepPin = 0, direction = 0, name = '', coverDirection = 0, uncoverDirection = 0):
        self.sleepPin = sleepPin
        self.dirPin = dirPin
        self.stepPin = stepPin
        self.direction = direction
        self.name = name
        self.stepsToDest = 0
        self.stepsFromHomeObject = None
        self.stepsFromHomeCount = 0
        self.coverDirection = coverDirection
        self.uncoverDirection = uncoverDirection
        #jge - set up callback function to keep track of steps
        self.stepsFromHomeObject = pi.callback(self.stepPin, pigpio.RISING_EDGE, self.callbackFunc)
        print('Created ' + self.name)

    def move(self, direction):        
        #jge - make sure it's not running against the wide open stops
        
        if (direction == self.coverDirection or (direction != self.coverDirection and self.stepsFromHomeCount > 0)):
            self.direction = direction
            self.wakeUp()
            pi.write(self.sleepPin, 1)
            pi.write(self.dirPin, direction)
            pi.write(self.stepPin, 1)
            pi.set_PWM_dutycycle(self.stepPin, 128)  # PWM 1/2 On 1/2 Off
            pi.set_PWM_frequency(self.stepPin, 500)
            sleep(.05)
        else:
            print('Cant open any further')

        """
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
        #print(str(self.stepsFromHomeCount))

        #jge - stop the move if it's wide open
        if (self.stepsFromHomeCount == 0 and self.direction != self.coverDirection):
            self.stop()
            print('Stopping motor because it is wide open')
            
    def stop(self):
        #jge - stop motion then sleep
        pi.write(self.stepPin, 0)
        pi.write(self.sleepPin, 0)
        self.sleep()
        
    def sleep(self):
        #jge - this turns off motor voltage
        pi.write(self.sleepPin, 0)
        
    def wakeUp(self):
        #jge - this restores power to the motor
        pi.write(self.sleepPin, 1)
            
#################################################################
#jge - init

pi = pigpio.pi() # Connect to pigpiod daemon
if not pi.connected:
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
leftHomeSwitch = HomeSwitch(1, 'left home switch')
leftMotor = Motor(6, 26, 19, 0, 'motor 3', 0, 1)
leftShade = Shade(leftMotor, leftHomeSwitch, 'left shade')

rightHomeSwitch = HomeSwitch(1, 'right home switch')
rightMotor = Motor(12, 24, 23, 0, 'motor 1', 0, 1)
rightShade = Shade(rightMotor, rightHomeSwitch, 'right shade')

topHomeSwitch = HomeSwitch(1, 'top home switch')
topMotor = Motor(5, 27, 17, 0, 'motor 2', 0, 1)
topShade = Shade(topMotor, topHomeSwitch, 'top shade')

botHomeSwitch = HomeSwitch(1, 'bottom home switch')
botMotor = Motor(13, 20, 21, 0, 'motor 4', 1, 0)
botShade = Shade(botMotor, botHomeSwitch, 'bottom shade')

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
environment = Environment('Full', 14, 15, 18, 1100, 400, 1) 
unit = Unit([leftShade, rightShade, topShade, botShade], environment)

#################################################################
#jge - This would be main.  Infinite loop to check for user input

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
            unit.uncoverAll()

        elif (dirKey == 'x'):
            print('Covering All')
            unit.coverAll()
            
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

#jge - end main loop
############################################
