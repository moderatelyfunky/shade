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

    def wakeUp(self):
        #jge - this restores power to the motor
        pi.write(self.sleepPin, 1)

    def sleep(self):
        #jge - this turns off motor voltage
        pi.write(self.sleepPin, 0)

    def stop(self):
        pi.write(self.stepPin, 0)
        pi.write(self.sleepPin, 0)   
        self.sleep()
        
    def buildRamp(self, startDelay, finalDelay, step):
        #jge - startDelay - higher number = lower starting freq
        #jge - finalDelay - higher number = lower final frequency
        #jge - step - Lower number = more gradual and more steps

        wfStart=[]
        for delay in range(startDelay, finalDelay, -step):
            wfStart.append(pigpio.pulse((1<<19)|(1<<17), 0, delay))
            wfStart.append(pigpio.pulse(0, (1<<19)|(1<<17), delay))

        return wfStart 

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

class AllShades():
    #jge - store the collection of shades so can have methods for all

    def __init__(self, initShades = []):
        self.allShades = initShades

    def wakeUp(self):
        for i, thisShade in enumerate(self.allShades):
            thisShade.motor.wakeUp()

    def stop(self):
        for i, thisShade in enumerate(self.allShades):
            thisShade.motor.stop()

    def sleep(self):
        for i, thisShade in enumerate(self.allShades):
            thisShade.motor.sleep()                 
    
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

shades = AllShades([leftShade, rightShade, topShade, botShade])

#jge - end init
#################################################################


###################################################
#jge - preset refactor
def gotoPreset():
    ################################
    #jge - temp variables for dev
    #allShades.wakeUp()
    
    leftShade.motor.stepsToDest = 5000
    rightShade.motor.stepsToDest = 4100
    topShade.motor.stepsToDest = 3200
    botShade.motor.stepsToDest = 2500

    maxDelay = 1100
    minDelay = 400
    step = 1
    #jge - end temp variables for dev
    ################################

    ################################
    #jge - start of start wave construction

    #jge - sort the shades by least steps to travel
    sortedShades = sorted(shades.allShades, key=lambda x: x.motor.stepsToDest, reverse=False)
        
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

    wfMiddle_A, wfMiddle_A_LoopCount, wfMiddle_A_Singles = buildMiddleWave(stepsAlreadyTaken, sortedShades, minDelay, maxDelay, step)    
    sortedShades.remove(sortedShades[0])
    stepsAlreadyTaken += (wfMiddle_A_LoopCount * 256) + wfMiddle_A_Singles

    wfMiddle_B, wfMiddle_B_LoopCount, wfMiddle_B_Singles = buildMiddleWave(stepsAlreadyTaken, sortedShades, minDelay, maxDelay, step)    
    sortedShades.remove(sortedShades[0])
    stepsAlreadyTaken += (wfMiddle_B_LoopCount * 256) + wfMiddle_B_Singles

    wfMiddle_C, wfMiddle_C_LoopCount, wfMiddle_C_Singles = buildMiddleWave(stepsAlreadyTaken, sortedShades, minDelay, maxDelay, step)    
    sortedShades.remove(sortedShades[0])
    stepsAlreadyTaken += (wfMiddle_C_LoopCount * 256) + wfMiddle_C_Singles

    wfMiddle_D, wfMiddle_D_LoopCount, wfMiddle_D_Singles = buildMiddleWave(stepsAlreadyTaken, sortedShades, minDelay, maxDelay, step)    
    sortedShades.remove(sortedShades[0])
    stepsAlreadyTaken += (wfMiddle_D_LoopCount * 256) + wfMiddle_D_Singles

    print('A loopcount = ' + str(wfMiddle_A_LoopCount))
    print('A singles = ' + str(wfMiddle_A_Singles))
    print('B loopcount = ' + str(wfMiddle_B_LoopCount))
    print('B singles = ' + str(wfMiddle_B_Singles))
    print('C loopcount = ' + str(wfMiddle_C_LoopCount))
    print('C singles = ' + str(wfMiddle_C_Singles))
    print('D loopcount = ' + str(wfMiddle_D_LoopCount))
    print('D singles = ' + str(wfMiddle_D_Singles))    

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

def buildMiddleWave(stepsAlreadyTaken, sortedShades, minDelay, maxDelay, step):
    #jge - create a slice of the steady state wave
    print('bmw 1 = ' + str(stepsAlreadyTaken))
    print('bmw 2 = ' + str(len(sortedShades)))
    print('bmw 3 = ' + str(minDelay))
    print('bmw 4 = ' + str(maxDelay))
    print('bmw 5 = ' + str(step))

    wfMiddle_Slice = []

    #jge - store the count to feed to the wave_chain looper
    maxSingle = 256
    countMiddle_Slice = sortedShades[0].motor.stepsToDest - stepsAlreadyTaken
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
            if (bitmask == 0):
                bitmask = int(1<<sortedShades[i].motor.stepPin)
            else:
                bitmask += int(1<<sortedShades[i].motor.stepPin)
        wfMiddle_Slice.append(pigpio.pulse(bitmask, 0, minDelay))
        wfMiddle_Slice.append(pigpio.pulse(0, bitmask, minDelay))            

    return wfMiddle_Slice, wfMiddle_Slice_LoopCount, wfMiddle_Slice_Singles

#jge - end refactor
###################################################


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
            for i, thisShade in enumerate(shades.allShades):
                thisShade.stop('Stopping ' + thisShade.name)
        elif (dirKey == 'q'):
            raise Exception('Quitting')
        elif (dirKey == 'e'):
            print('gradual with Count')
            leftShade.motor.gradual()
        elif (dirKey == 'r'):
            print('Goto newSchoolpreset')
            gotoPreset()
        else:
            pass
except Exception as e :
    print ('\nOh goooood for you')
    raise
finally:
    environment.restoreSettings()

    for i, thisShade in enumerate(shades.allShades):
        thisShade.stop('Shutting down ' + thisShade.name)

    pi.stop()

#jge - end main loop
############################################
