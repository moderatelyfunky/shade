import weakref
import configparser
from time import sleep
import pigpio
import time
import sys
import operator #jge - used to find max array value and member
import termios
import tty

class Unit():
    #jge - this is the main point of entry for control from the gui

    def __init__(self):
        #jge - read the ini file
        self.iniFileName = 'shade.ini'
        self.config = configparser.RawConfigParser()
        self.config.optionxform = str
        self.config.read(self.iniFileName)
        #jge - need a master flag to halt all when a limit switch is hit during a preset move
        self.haltAll = 0
        self.goingToPreset = 0
        
        #jge - until the homing is working, allow the manual
        #jge - buttons to move what they think is zero
        self.stopAtWideOpen = self.config.get('config', 'stopAtWideOpen')
    
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
        self.leftHomeSwitch = HomeSwitch(self, 16, 'left home switch')
        self.leftMotor = Motor(self, 6, 26, 19, 0, 'motor 3', 0, 1, self.leftHomeSwitch)
        self.leftShade = Shade(self, self.leftMotor,'left shade')
        self.getPresets(self.leftShade)

        self.rightHomeSwitch = HomeSwitch(self, 22, 'right home switch')
        self.rightMotor = Motor(self, 12, 24, 23, 0, 'motor 1', 0, 1, self.rightHomeSwitch)
        self.rightShade = Shade(self, self.rightMotor, 'right shade')
        self.getPresets(self.rightShade)
        
        self.topHomeSwitch = HomeSwitch(self, 4, 'top home switch')
        self.topMotor = Motor(self, 5, 27, 17, 0, 'motor 2', 0, 1, self.topHomeSwitch)
        self.topShade = Shade(self, self.topMotor, 'top shade')
        self.getPresets(self.topShade)
        
        self.botHomeSwitch = HomeSwitch(self, 25, 'bottom home switch')
        self.botMotor = Motor(self, 13, 20, 21, 0, 'motor 4', 1, 0, self.botHomeSwitch)
        self.botShade = Shade(self, self.botMotor, 'bot shade')
        self.getPresets(self.botShade)
        
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
        self.sleepAll()
        print('Done with init')
        #jge - end Unit init
        #################################################################
        
    def wakeUpAll(self):
        for i, thisShade in enumerate(self.allShades):
            self.allShades[i].motor.wakeUp()

    def sleepAll(self):
        for i, thisShade in enumerate(self.allShades):
            self.allShades[i].motor.sleep()
                
    def uncoverAll(self):
        print('Uncovering all')
        self.gotoPreset(self, 5)

    def coverAll(self):
        print('Covering all')
        self.gotoPreset(self, 6)

    def stopAll(self):
        for i, thisShade in enumerate(self.allShades):
            print('Stopping ' + thisShade.name)           
            print(self.allShades[i].name + ' steps from home = ' + str(self.allShades[i].motor.stepsFromHomeCount))
            thisShade.motor.stop('stopAll')

    def cleanup(self):
        self.environment.restoreSettings()

        for thisShade in enumerate(self.allShades):
            print('Shutting down ' +  thisShade.name)
            thisShade.motor.stop()

        self.pi.stop()

    def writePreset(self, event, presetNo):
        #jge - write out the current position of each motor
        for i, thisShade in enumerate(self.allShades):
            self.config.set('presets', self.allShades[i].name + ' ' + str(presetNo), str(self.allShades[i].motor.stepsFromHomeCount))
            #jge - update the current preset that's in memory
            self.allShades[i].preset[presetNo -1] = self.allShades[i].motor.stepsFromHomeCount
        with open(self.iniFileName, "w") as config_file:
            self.config.write(config_file)

    def getPresets(self, shade):
        #jge - read the ini for presets       
        shade.preset.append(int(self.config.get('presets', shade.name + ' 1')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' 2')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' 3')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' 4')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' open full')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' closed center')))        

    def getPresetPositions(self, presetNo):
        #jge - Use the preset number to retrieve the positions for each 
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
            
    def gotoPreset(self, event, presetNo):
        ################################
        #jge - preset init
        self.goingToPreset = 1
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
        #jge - don't add to the array when all steps have been used
        hasQualifier = 0
        for delay in range(maxDelay, minDelay, -step):
            bitmask = 0
            pulseCount += 1
            for i, thisShade in enumerate(sortedShades):
                if (thisShade.motor.stepsToDest > pulseCount):
                    hasQualifier = 1
                    if (bitmask == 0):
                        bitmask = int(1<<sortedShades[i].motor.stepPin)
                    else:
                        bitmask += int(1<<sortedShades[i].motor.stepPin)                   

            if (hasQualifier == 1):    
                #jge - now build the pulse and add it to the array
                wfStart.append(pigpio.pulse(bitmask, 0, delay))
                wfStart.append(pigpio.pulse(0, bitmask, delay))
            else:
                #jge - all steps have been accounted for
                break
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

            ###################################
            #jge - original
                
            #self.pi.wave_chain([
            #   startRamp,        
            #   255, 0,                       
            #      middleWave_A,    
            #   255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, #loop x + y*256 times
            #   255, 0,                       
            #      middleWave_B,    
            #   255, 1, wfMiddle_B_Singles, wfMiddle_B_LoopCount,          
            #   255, 0,                       
            #      middleWave_C,    
            #   255, 1, wfMiddle_C_Singles, wfMiddle_C_LoopCount,       
            #   255, 0,                       
            #      middleWave_D,    
            #   255, 1, wfMiddle_D_Singles, wfMiddle_D_LoopCount,                             
            #   ])
            #jge - end original
            ######################################

            ######################################
            #jge- new
            try:
                if (len(wfMiddle_D) > 0):
                    #jge - all elements have length
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
                else:
                    if (len(wfMiddle_C) > 0):
                        #jge - C is last
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
                           ])                
                    else:
                        if (len(wfMiddle_B) > 0):
                            #jge - B is last
                            self.pi.wave_chain([
                               startRamp,        
                               255, 0,                       
                                  middleWave_A,    
                               255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, #loop x + y*256 times
                               255, 0,                       
                                  middleWave_B,    
                               255, 1, wfMiddle_B_Singles, wfMiddle_B_LoopCount,          
                               ])           
                        else:
                            if (len(wfMiddle_A) > 0):
                                #jge - A is last
                                self.pi.wave_chain([
                                   startRamp,        
                                   255, 0,                       
                                      middleWave_A,    
                                   255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, #loop x + y*256 times
                                   ])           
                            else:
                                if (len(wfStart) > 0):
                                    #jge - startRamp is last
                                    self.pi.wave_chain([
                                       startRamp,        
                                       ])           

            except Exception as e:
                print(str(e))
            #jge - end new
            ######################################
            
            tempSortedShades = sorted(self.allShades, key=lambda x: x.motor.stepsToDest, reverse=False)
                   
            #jge - Get control of the situation.  No more phone calls                
            while self.pi.wave_tx_busy():
                #jge - check for a stop message that a limit switch may
                #jge - have thrown.  It's at the unit because anyone could
                #jge - could have hit the switch
                time.sleep(0.1)
                if (self.haltAll == 1):
                    self.pi.wave_tx_stop()
                    self.pi.wave_clear()
                    self.stopAll()
                    #jge - set the flag to indicate to the switch that it's
                    #jge - okay to proceed with homing
                    self.goingToPreset = 0

            pigpio.exceptions = True

            #jge - only try the clean up if it's normal operation
            if (self.haltAll != 1):
                if (startRamp > 0):
                    print('deleting startRamp')
                    self.pi.wave_delete(startRamp)
                if (middleWave_A > 0):
                    print('deleting a')
                    self.pi.wave_delete(middleWave_A)
                if (middleWave_B > 0):
                    print('deleting b')
                    self.pi.wave_delete(middleWave_B)
                if (middleWave_C > 0):
                    print('deleting c')
                    self.pi.wave_delete(middleWave_C)
                if (middleWave_D > 0):
                    print('deleting d')
                    self.pi.wave_delete(middleWave_D)
                    
        self.sleepAll()
        self.goingToPreset = 0
        self.pi.wave_clear()

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
    def __init__(self, parent, motor, name = ''):
        self.parent = parent 
        self.motor = motor
        self.name = name
        self.preset = []
        print('Created ' + self.name)
                
class HomeSwitch():
    #jge - object to manage the limit switches used to find home
    def __init__(self, parent, switchPin, name = ''):
        self.parent = parent
        self.parentMotor = None
        self.switchPin = switchPin
        self.name = name
        #self.homing = 0
        self.prevState = 0
        self.state = 0
        parent.pi.set_mode(switchPin, pigpio.INPUT)
        #jge - using internal resistors in addition to external
        parent.pi.set_pull_up_down(switchPin, pigpio.PUD_DOWN)
        self.cbf = parent.pi.callback(self.switchPin, pigpio.RISING_EDGE, self.callbackFunc)
        print('Created ' + self.name)

    def callbackFunc(self, gpio, level, tick):     
        #jge - no matter what, if the switch is closed, stop the motor.
        #jge - take care of zeroing in the motor stop method
        #jge - also, set the haltAll at the unit to call a stop to the
        #jge - wave_chain in the case of a preset.
        self.state = self.parent.pi.read(self.switchPin)
        print('In homeswitch cbf - 1 - ' + self.name + ' state = ' + str(self.state) + ' prev state = ' + str(self.prevState))

        if (self.state == 1 and self.prevState != self.state):
            print('in homeswitch cbf - 2 - ' + self.name + ' switch closed')

            if (self.parent.goingToPreset == 1):
                #jge - the pi while loop in the goto preset method
                #jge - will hear this setting of the flag and will
                #jge - cancel the wave send.
             
                print('in homeswitch cbf - 3 - ' + self.name + ' Interrupting a preset move because a switch has been closed')
                #jge - set a flag and wait for the gotoPreset to confirm that
                #jge - the goto preset wave_chain has been canceled
                self.parent.haltAll = 1
                while (self.parent.goingToPreset == 1):
                    print('in homeswitch cbf - 4 ' + self.name + ' - waiting for gotoPreset to be set to 0')
                    time.sleep(0.1)

            #jge todo - need to home all the motors at this point
            print('in homeswitch cbf - 5 ' + self.name + ' - about to call homing method')
            self.parentMotor.findHome('switch Called')
            
            #self.homing = 1
            #self.parentMotor.stop('limit')
            print('In homeSwitch cbf - 6 ' + self.name + ' -  finished homing')  
            #self.homing = 0
            #jge - reset the checker
            self.state = self.parent.pi.read(self.switchPin)
            self.prevState = self.state
            print('In homswitch cbf  - 7 ' + self.name + ' = self.state = ' + str(self.state))
            
            self.parent.haltAll = 0

class Motor():
    def __init__(self, parent, sleepPin = 0, dirPin = 0, stepPin = 0, direction = 0, name = '', coverDirection = 0, uncoverDirection = 0, homeSwitch = 0):
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
        self.homeSwitch = homeSwitch
        self.homeSwitch.parentMotor = self
        #jge - todo - need to find out how many would be fully closed
        #jge - for now set it so it doesn't interfere
        self.maxSteps = 1000000
        self.parent.pi.write(self.stepPin, 1)
        self.moving = 0
        
        print('Created ' + self.name)

    def move(self, event, direction):        
        #jge - make sure it's not running against the wide open stops
        if ((direction == self.coverDirection and self.maxSteps > self.stepsFromHomeCount) or
            (direction == self.uncoverDirection and self.stepsFromHomeCount > 0) or
            self.parent.stopAtWideOpen == '0'
            ):
            self.direction = direction
            self.wakeUp()
            self.parent.pi.write(self.sleepPin, 1)
            self.parent.pi.write(self.dirPin, direction)
            '''
            ##########################
            #jge - new way
            self.parent.pi.wave_clear()
            mover = []
            wid = 0
            #jge - build a generic single pulse
            mover.append(pigpio.pulse(1<<self.stepPin, 0, 1100))
            mover.append(pigpio.pulse(0, 1<<self.stepPin, 1100))

            #self.moving = 1
            ############
            self.parent.pi.wave_add_generic(mover)
            wid = self.parent.pi.wave_create()
            self.parent.pi.wave_send_once(wid)
            while self.parent.pi.wave_tx_busy():
                time.sleep(0.1)
            print('in move.  Just moved')
            ################
            
            while (self.moving == 1):
                wid = self.parent.pi.wave_create()
                self.parent.pi.wave_send_once(wid)
                while self.parent.pi.wave_tx_busy():
                    time.sleep()
                self.wave_delete(wid)
            #jge - end new way
            ##########################
            '''
            ##########################
            #jge - old way
            self.parent.pi.set_PWM_dutycycle(self.stepPin, 128)  # PWM 1/2 On 1/2 Off
            self.parent.pi.set_PWM_frequency(self.stepPin, 500)
            sleep(.05)
            #jge- end old way
            #########################
            
        else:
            print('Cant open ' + self.name + ' any further')
        
    def callbackFunc(self, gpio, level, tick):     
        #jge - figure out whether to add or subtract the steps
        if (self.direction == self.coverDirection):
            self.stepsFromHomeCount += 1
        else:
            self.stepsFromHomeCount -= 1

        #jge - stop the move if it's wide open or closed
        if ((self.stepsFromHomeCount == 0 and self.direction == self.uncoverDirection) or
            (self.stepsFromHomeCount >= self.maxSteps and self.direction == self.coverDirection) or
            (self.parent.haltAll == 1)
           ):
            print('Stopping motor ' + self.name + 'because of a master halt or the shade is wide open or closed')       
            self.stop(self)
            
    def stop(self, event):
        #jge - if the motor was stopped because the shade has closed
        #jge - a limit switch, then zero the motor
        #if (self.homeSwitch.state == 1 and self.homeSwitch.homing == 1):
        #    print('In Motor.stop method.  About to call findHome')
        #    if (self.parent.haltAll != 1):
        #        self.findHome(event)
        #    else:
        #        print('In motor stop method during a haltAll')
        print('in stop.  writing self.moving to 0')
        self.moving = 0
        #jge - stop motion then sleep
        ########################################
        #jge - old way
        self.parent.pi.write(self.stepPin, 0)
        self.parent.pi.write(self.sleepPin, 0)
        #jge - end old way
        ########################################
        
        self.sleep()

    def findHome(self, event):
        print('in findhome method')
        movingOut = []    
        wid = 0
        cushion = []
        cushionStepCount = 10

        #jge - move the motor away until the switch is open

        #jge - set the direction pin
        self.parent.pi.write(self.dirPin, self.coverDirection)
        #jge - build a generic single pulse
        movingOut.append(pigpio.pulse(1<<self.stepPin, 0, 1100))
        movingOut.append(pigpio.pulse(0, 1<<self.stepPin, 1100))

        while (self.parent.pi.read(self.homeSwitch.switchPin) == 1):
            self.parent.pi.wave_clear()
            self.parent.pi.wave_add_generic(movingOut)
            wid = self.parent.pi.wave_create()
            self.parent.pi.wave_send_once(wid)
            while self.parent.pi.wave_tx_busy():
                time.sleep(0.1)
                
        #jge - add some number of steps to completely clear the switch 
        x = 1
        while (x < cushionStepCount):
            cushion.append(pigpio.pulse(1<<self.stepPin, 0, 1100))
            cushion.append(pigpio.pulse(0, 1<<self.stepPin, 1100))
            x+=1
                
        self.parent.pi.wave_clear()
        self.parent.pi.wave_add_generic(movingOut)
        wid = self.parent.pi.wave_create()
        self.parent.pi.wave_send_once(wid)
        while self.parent.pi.wave_tx_busy():
            time.sleep(0.1)

        #jge - now that off of switch and cushioned, set to 0
        self.stepsFromHomeCount = 0
        
        self.stop('limit')
        
    def sleep(self):
        #jge - this turns off motor voltage
        self.parent.pi.write(self.sleepPin, 0)
        
    def wakeUp(self):
        #jge - this restores power to the motor
        self.parent.pi.write(self.sleepPin, 1)
