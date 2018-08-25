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

    def wakeUp(self):
        for i, thisShade in enumerate(self.allShades):
            thisShade.motor.wakeUp()

    def stop(self):
        for i, thisShade in enumerate(self.allShades):
            thisShade.motor.stop()

    def sleep(self):
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
            thisShade.motor.stop()

    def cleanup(self):
        self.environment.restoreSettings()

        for i, thisShade in enumerate(self.allShades):
            print('Shutting down ' +  thisShade.name)
            thisShade.motor.stop()

        pi.stop()
            
    def getPresetPositions(self, presetNo):
        #jge - take the preset number and get the steps for each from zero

        ###################
        #jge - hard coded dev magic
        if (presetNo == 1):          
            leftShade.motor.stepsToDest = 5000
            rightShade.motor.stepsToDest = 4100
            topShade.motor.stepsToDest = 3200
            botShade.motor.stepsToDest = 2500
        elif (presetNo == 2):
            leftShade.motor.stepsToDest = 2500
            rightShade.motor.stepsToDest = 4100
            topShade.motor.stepsToDest = 3200
            botShade.motor.stepsToDest = 1900
        elif (presetNo == 2):
            leftShade.motor.stepsToDest = 4100
            rightShade.motor.stepsToDest = 5000
            topShade.motor.stepsToDest = 3200
            botShade.motor.stepsToDest = 2500
        elif (presetNo == 4):
            leftShade.motor.stepsToDest = 2500
            rightShade.motor.stepsToDest = 3200
            topShade.motor.stepsToDest = 4100
            botShade.motor.stepsToDest = 5000                
        ###################

    def gotoPreset(self, presetNo):
        ################################
        #jge - temp variables for dev
        unit.wakeUp()
        self.getPresetPositions(presetNo)
        maxDelay = unit.environment.maxDelay
        minDelay = unit.environment.minDelay
        step = unit.environment.stepSize
        #jge - end temp variables for dev
        ################################

        ################################
        #jge - start of wave construction
        #jge - startDelay - higher number = lower starting freq
        #jge - finalDelay - higher number = lower final frequency
        #jge - step - Lower number = more gradual and more steps

        #jge - sort the shades by least steps to travel
        
        sortedShades = sorted(unit.allShades, key=lambda x: x.motor.stepsToDest, reverse=False)
            
        wfStart_A = []
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

            #jge - now build the pulse for all the pins who need it
            wfStart_A.append(pigpio.pulse(bitmask, 0, delay))
            wfStart_A.append(pigpio.pulse(0, bitmask, delay))

        wfStart = wfStart_A
        print('Steps used by startRamp = ' + str(len(wfStart)))

        stepsAlreadyTaken = len(wfStart)

        wfMiddle_A, wfMiddle_A_LoopCount, wfMiddle_A_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
        print('listen here - ' + str(len(wfMiddle_A)))
        sortedShades.remove(sortedShades[0])
        stepsAlreadyTaken += (wfMiddle_A_LoopCount * 256) + wfMiddle_A_Singles

        wfMiddle_B, wfMiddle_B_LoopCount, wfMiddle_B_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
        sortedShades.remove(sortedShades[0])
        stepsAlreadyTaken += (wfMiddle_B_LoopCount * 256) + wfMiddle_B_Singles

        wfMiddle_C, wfMiddle_C_LoopCount, wfMiddle_C_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
        sortedShades.remove(sortedShades[0])
        stepsAlreadyTaken += (wfMiddle_C_LoopCount * 256) + wfMiddle_C_Singles

        wfMiddle_D, wfMiddle_D_LoopCount, wfMiddle_D_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
        sortedShades.remove(sortedShades[0])
        stepsAlreadyTaken += (wfMiddle_D_LoopCount * 256) + wfMiddle_D_Singles

        #jge - now create and send the waves from the arrays
        pi.wave_clear()

        pi.wave_add_generic(wfStart)
        startRamp = pi.wave_create()

        pi.wave_add_generic(wfMiddle_A)
        middleWave_A = pi.wave_create()

        pi.wave_add_generic(wfMiddle_B)
        middleWave_B = pi.wave_create()

        pi.wave_add_generic(wfMiddle_C)
        middleWave_C = pi.wave_create()

        pi.wave_add_generic(wfMiddle_D)
        middleWave_D = pi.wave_create()

        allWaves = [startRamp, middleWave_A, middleWave_B, middleWave_C, middleWave_D]                                           

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

        while pi.wave_tx_busy():
           time.sleep(0.1)

        pigpio.exceptions = True
        print('done transmitting bro')
        pi.wave_delete(startRamp)
        pi.wave_delete(middleWave_A)
        pi.wave_delete(middleWave_B)
        pi.wave_delete(middleWave_C)
        pi.wave_delete(middleWave_D)    

    def buildMiddleWave(self, stepsAlreadyTaken, sortedShades):
        #jge - create a slice of the steady state wave
        minDelay = unit.environment.minDelay
        maxDelay = unit.environment.maxDelay
        step = unit.environment.stepSize
        
        print('bmw 1 = ' + str(stepsAlreadyTaken))
        print('bmw 2 = ' + str(len(sortedShades)))
        print('bmw 3 = ' + str(minDelay))
        print('bmw 4 = ' + str(maxDelay))
        print('bmw 5 = ' + str(step))
        print('bmw 6 - ' + str(sortedShades[0].motor.stepsToDest))

        wfMiddle_Slice = []

        #jge - store the count to feed to the wave_chain looper
        maxSingle = 256
        countMiddle_Slice = sortedShades[0].motor.stepsToDest - stepsAlreadyTaken
        print('countMiddle_Slice = ' + str(countMiddle_Slice))
        
        if (countMiddle_Slice > 256):
            #loop x + y*256 times
            wfMiddle_Slice_LoopCount = int(countMiddle_Slice / maxSingle)
            wfMiddle_Slice_Singles = countMiddle_Slice % maxSingle
        else:
            wfMiddle_Slice_LoopCount = 0
            wfMiddle_Slice_Singles = countMiddle_Slice

        if (sortedShades[0].motor.stepsToDest > stepsAlreadyTaken):
            #jge - if the least steps are more than the start ramp, it means all are
            bitmask = 0
            for i, thisShade in enumerate(sortedShades):
                print('Found some shade ' + sortedShades[i].name)
                if (bitmask == 0):
                    bitmask = int(1<<sortedShades[i].motor.stepPin)
                else:
                    bitmask += int(1<<sortedShades[i].motor.stepPin)
            wfMiddle_Slice.append(pigpio.pulse(bitmask, 0, minDelay))
            wfMiddle_Slice.append(pigpio.pulse(0, bitmask, minDelay))            

        return wfMiddle_Slice, wfMiddle_Slice_LoopCount, wfMiddle_Slice_Singles
    #jge - end unit class
    
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
    def __init__(self, sleepPin = 0, dirPin = 0, stepPin = 0, direction = 0, name = ''):
        self.sleepPin = sleepPin
        self.dirPin = dirPin
        self.stepPin = stepPin
        self.direction = direction
        self.name = name
        self.stepsToDest = 0
        print('Created ' + self.name)

    def move(self, direction):
        self.wakeUp()
        pi.write(self.sleepPin, 1)
        pi.write(self.dirPin, direction)
        pi.write(self.stepPin, 1)
        pi.set_PWM_dutycycle(self.stepPin, 128)  # PWM 1/2 On 1/2 Off
        pi.set_PWM_frequency(self.stepPin, 500)
        sleep(.05)
        
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

class Shade():
    def __init__(self, motor, name = ''):
        self.motor = motor
        self.name = name
        print('Created ' + self.name)
            
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
##########################################################
leftMotor = Motor(6, 26, 19, 0, 'motor 3')
leftShade = Shade(leftMotor, 'left shade')

rightMotor = Motor(12, 24, 23, 0, 'motor 1')
rightShade = Shade(rightMotor, 'right shade')

topMotor = Motor(5, 27, 17, 0, 'motor 2')
topShade = Shade(topMotor, 'top shade')

botMotor = Motor(13, 20, 21, 0, 'motor 4')
botShade = Shade(botMotor, 'bottom shade')

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
