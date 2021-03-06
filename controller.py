import weakref
import configparser
from time import sleep
import pigpio
import time
import sys
import operator #jge - used to find max array value and member
import termios
import tty
import logging
import math

class Unit():
    #jge - this is the main point of entry for control from the gui

    def __init__(self):
        #jge - read the ini file
        self.iniFileName = 'shade.ini'
        self.config = configparser.RawConfigParser()
        self.config.optionxform = str
        self.config.read(self.iniFileName)
        #jge - set up logging
        logging.basicConfig(level=logging.INFO, 
                    filename='shade.log', # log to this file
                    format='%(asctime)s %(message)s') # include timestamp

        self.logToFile = self.config.get('config', 'logToFile')
        self.pAL('====================================================', 'info')
        self.pAL('program started', 'info') 
        self.pAL('====================================================', 'info')

        #jge - need a master flag to halt all when a limit switch is hit during a preset move
        self.haltAll = 0
        self.goingToPreset = 0
        self.maxStepDelay = self.config.get('config', 'maxStepDelay')
        self.minStepDelay = self.config.get('config', 'minStepDelay')
        self.stepsToGain = self.config.get('config', 'stepsToGain')

        #jge - get pin assignments
        self.modePin1 = self.config.get('pins', 'modePin1')
        self.modePin2 = self.config.get('pins', 'modePin2')
        self.modePin3 = self.config.get('pins', 'modePin3')

        self.leftSleepPin = self.config.get('pins', 'leftSleepPin')
        self.leftDirPin = self.config.get('pins', 'leftDirPin')
        self.leftStepPin = self.config.get('pins', 'leftStepPin')

        self.rightSleepPin = self.config.get('pins', 'rightSleepPin')
        self.rightDirPin = self.config.get('pins', 'rightDirPin')
        self.rightStepPin = self.config.get('pins', 'rightStepPin')

        self.topSleepPin = self.config.get('pins', 'topSleepPin')
        self.topDirPin = self.config.get('pins', 'topDirPin')
        self.topStepPin = self.config.get('pins', 'topStepPin')

        self.botSleepPin = self.config.get('pins', 'botSleepPin')
        self.botDirPin = self.config.get('pins', 'botDirPin')
        self.botStepPin = self.config.get('pins', 'botStepPin')

        self.leftSwitchPin = self.config.get('pins', 'leftSwitchPin')
        self.rightSwitchPin = self.config.get('pins', 'rightSwitchPin')
        self.topSwitchPin = self.config.get('pins', 'topSwitchPin')
        self.botSwitchPin = self.config.get('pins', 'botSwitchPin')

        #jge - until the homing is working, allow the manual
        #jge - buttons to move what they think is zero
        self.stopAtWideOpen = self.config.get('config', 'stopAtWideOpen')
        
        #jge - get dimensions for freehand work
        self.widthInSteps = self.config.get('config', 'widthInSteps')
        self.pAL('Width in steps = ' + str(self.widthInSteps), 'info')
        self.heightInSteps = self.config.get('config', 'heightInSteps')
        self.pAL('Height in steps = ' + str(self.heightInSteps), 'info')

        self.pi = pigpio.pi() # Connect to pigpiod daemon
        pigpio.exceptions = True
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
        #jge - 7th argument = related homeSwitch
        #jge - 8th argument = lag time for simulatenous homing issues
        #jge - HomeSwitch constructors.  1st arg - gpio
        ##########################################################
        self.leftHomeSwitch = HomeSwitch(self, self.leftSwitchPin, 'left home switch')
        self.leftMotor = Motor(self, self.leftSleepPin, self.leftDirPin, self.leftStepPin, 0, 'motor 3', 0, 1, self.leftHomeSwitch, .5)
        self.leftShade = Shade(self, self.leftMotor,'left shade')
        self.getPresets(self.leftShade)

        self.rightHomeSwitch = HomeSwitch(self, self.rightSwitchPin, 'right home switch')
        self.rightMotor = Motor(self, self.rightSleepPin, self.rightDirPin, self.rightStepPin, 0, 'motor 1', 0, 1, self.rightHomeSwitch, 1)
        self.rightShade = Shade(self, self.rightMotor, 'right shade')
        self.getPresets(self.rightShade)
        
        self.topHomeSwitch = HomeSwitch(self, self.topSwitchPin, 'top home switch')
        self.topMotor = Motor(self, self.topSleepPin, self.topDirPin, self.topStepPin, 0, 'motor 2', 0, 1, self.topHomeSwitch, 1.5)
        self.topShade = Shade(self, self.topMotor, 'top shade')
        self.getPresets(self.topShade)
        
        self.botHomeSwitch = HomeSwitch(self, self.botSwitchPin, 'bottom home switch')
        self.botMotor = Motor(self, self.botSleepPin, self.botDirPin, self.botStepPin, 0, 'motor 4', 1, 0, self.botHomeSwitch, 2)
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
        self.environment = Environment(self, 'Full', self.modePin1, self.modePin2, self.modePin3, self.maxStepDelay, self.minStepDelay, self.stepsToGain) 
        self.pAL('Created environment', 'info')
        self.allShades = [self.leftShade, self.rightShade, self.topShade, self.botShade]
        self.pAL('Created allshades array', 'info')
        self.sleepAll()
        self.pAL('Done with init', 'info')
        #jge - end Unit init
        #################################################################
    
    def pAL(self, message, msgLevel):
        #jge - write to console
        print(message)

        if (self.logToFile == '1'):
            #jge - write to log
            if (msgLevel == 'error'):
                logging.error(message)
            elif (msgLevel == 'info'):
                logging.info(message)

    def wakeUpAll(self):
        for i, thisShade in enumerate(self.allShades):
            self.allShades[i].motor.wakeUp()

    def sleepAll(self):
        for i, thisShade in enumerate(self.allShades):
            self.allShades[i].motor.sleep()
                
    def uncoverAll(self):
        self.pAL('Uncovering all', 'info')
        self.gotoPreset(self, 5)

    def coverAll(self):
        self.pAL('Covering all', 'info')
        self.gotoPreset(self, 6)

    def stopAll(self):
        for i, thisShade in enumerate(self.allShades):
            self.pAL('Stopping ' + thisShade.name, 'info')           
            self.pAL(self.allShades[i].name + ' steps from home = ' + str(self.allShades[i].motor.stepsFromHomeCount), 'info')
            thisShade.motor.stop('stopAll')

    def homeAll(self):
        for i, thisShade in enumerate(self.allShades):
            self.pAL('Homing ' + thisShade.name, 'info')
            sleep(.5)
            thisShade.motor.isHoming = 1
            thisShade.motor.moveToSwitch('homeAll')

    def cleanup(self):
        self.environment.restoreSettings()

        for thisShade in enumerate(self.allShades):
            self.pAL('Shutting down ' +  thisShade.name, 'info')
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
        #jge - read the ini for the particular preset that made this call       
        shade.preset.append(int(self.config.get('presets', shade.name + ' 1')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' 2')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' 3')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' 4')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' open full')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' closed center')))
        shade.preset.append(0)      

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

    def gotoFreehand(self, event, leftPct, rightPct, topPct, botPct):
        #jge - take the decimals from the freehand input and translate to 
        #jge - real world numbers and pass to the gotoPreset
        leftDest = math.trunc(leftPct * float(self.widthInSteps))
        rightDest = math.trunc(rightPct * float(self.widthInSteps))
        topDest = math.trunc(topPct * float(self.heightInSteps))
        botDest = math.trunc(botPct * float(self.heightInSteps))

        self.leftShade.preset[6] = leftDest
        self.rightShade.preset[6] = rightDest
        self.topShade.preset[6] = topDest
        self.botShade.preset[6] = botDest

        self.gotoPreset('freeHand', 7)

    def gotoPreset(self, event, presetNo):
        self.pAL('Going to preset', 'info')
        ################################
        #jge - preset init
        self.goingToPreset = 1
        self.wakeUpAll()
        self.getPresetPositions(presetNo)
        maxDelay = int(self.environment.maxDelay)
        minDelay = int(self.environment.minDelay)
        step = int(self.environment.stepSize)
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
            hasQualifier = 0
            for i, thisShade in enumerate(sortedShades):
                if (thisShade.motor.stepsToDest > pulseCount):
                    hasQualifier = 1
                    if (bitmask == 0):
                        bitmask = int(1<<sortedShades[i].motor.stepPin)
                    else:
                        bitmask += int(1<<sortedShades[i].motor.stepPin)                   

            if (hasQualifier == 1):    
                #jge - now build the pulse and add it to the array
                pulseCount += 1
                wfStart.append(pigpio.pulse(bitmask, 0, delay))
                wfStart.append(pigpio.pulse(0, bitmask, delay))
            else:
                #jge - all steps have been accounted for
                break
        stepsAlreadyTaken = pulseCount

        tempSortedShades.clear()
        #jge - remove any shades who may have no more steps left
        for i, thisShade in enumerate(sortedShades):
            if (sortedShades[i].motor.stepsToDest <= stepsAlreadyTaken):
                sortedShades[i].motor.stepsToDest = 0
            else:
                tempSortedShades.append(sortedShades[i])

        sortedShades.clear()
        sortedShades = tempSortedShades
                                              
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

        #jge - Use Wave_add_generic to "convert" the arrays of pulses into
        #jge - into waves that will be fed to pigpio with the wave_chain method
        self.pi.wave_add_generic(wfStart)
        
        #jge - Build an array of the waves to make clean up easier
        allWaves = []                                           

        #jge - make sure not to get empty wave errors
        if (len(wfStart) > 0):
            startRamp = self.pi.wave_create()
            allWaves.append(startRamp)

            if (len(wfMiddle_A) > 0):
                self.pi.wave_add_generic(wfMiddle_A)
                middleWave_A = self.pi.wave_create()
                allWaves.append(middleWave_A)
                
            if (len(wfMiddle_B) > 0):
                self.pi.wave_add_generic(wfMiddle_B)
                middleWave_B = self.pi.wave_create()
                allWaves.append(middleWave_B)

            if (len(wfMiddle_C) > 0):
                self.pi.wave_add_generic(wfMiddle_C)
                middleWave_C = self.pi.wave_create()
                allWaves.append(middleWave_C)

            if (len(wfMiddle_D) > 0):             
                self.pi.wave_add_generic(wfMiddle_D)
                middleWave_D = self.pi.wave_create()
                allWaves.append(middleWave_D)                

            #jge - this is the method that pushes the waves to the motors.
            #jge - The blocks that start with 255 are loops.  The closing
            #jge - part of the loop tells pigpio how many times to loop
            #jge - each wave and how many single iterations of it after that
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
                        #jge - C is last to have pulses
                        self.pi.wave_chain([
                           startRamp,        
                           255, 0,                       
                              middleWave_A,    
                           255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, 
                           255, 0,                       
                              middleWave_B,    
                           255, 1, wfMiddle_B_Singles, wfMiddle_B_LoopCount,          
                           255, 0,                       
                              middleWave_C,    
                           255, 1, wfMiddle_C_Singles, wfMiddle_C_LoopCount,                                  
                           ])                
                    else:
                        if (len(wfMiddle_B) > 0):                          
                            #jge - B is last to have pulses
                            self.pi.wave_chain([
                               startRamp,        
                               255, 0,                       
                                  middleWave_A,    
                               255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, 
                               255, 0,                       
                                  middleWave_B,    
                               255, 1, wfMiddle_B_Singles, wfMiddle_B_LoopCount,          
                               ])           
                        else:
                            if (len(wfMiddle_A) > 0):                           
                                #jge - A is last to have pulses
                                self.pi.wave_chain([
                                   startRamp,        
                                   255, 0,                       
                                      middleWave_A,    
                                   255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, 
                                   ])           
                            else:
                                if (len(wfStart) > 0):                                  
                                    #jge - startRamp is last to have pulses
                                    self.pi.wave_chain([
                                       startRamp,        
                                       ])           
            except Exception as e:
                self.pAL('in gotoPreset - trying wave chain - ' + str(e), 'error')
                
            #jge - Get control of the situation.  No more phone calls                
            while self.pi.wave_tx_busy():
                #jge - check for a stop message that a limit switch may
                #jge - have thrown.  It's at the unit because anyone could
                #jge - could have hit the switch
                
                if (self.haltAll == 1):
                    self.pAL('Halting all during a preset move', 'error')
                    self.pi.wave_tx_stop()
                    self.stopAll()

                time.sleep(0.1)
                
            pigpio.exceptions = True

            for i in range(len(allWaves)):
                try:
                    self.pi.wave_delete(allWaves[i])
                except Exception as e:
                    self.pAL('in gotoPreset deleting waves - ' + str(e), 'error')
                    self.pi.wave_clear()
        
        self.sleepAll()
        self.goingToPreset = 0

        if (self.haltAll == 1):
            #jge - by now, all motors should be stopped and ready 
            self.homeAll()
            self.haltAll = 0

        if (presetNo == 5):
            #jge - it's the wide open preset, so home all
            self.homeAll()
            
    def buildMiddleWave(self, stepsAlreadyTaken, sortedShades):
        #jge - This method will build an array of pulses for the
        #jge - steady state portion of the movement.  It uses the
        #jge - same pigpio features as the ramp.  The additional
        #jge - work being done here is to figure out how many times
        #jge - the wave should be looped and run individually.  This
        #jge - is because pigpio has a limit of 256 iterations for
        #jge - each wave.  Anything over that means another loop or
        #jge - just the remainder if it's less than 256
        
        minDelay = int(self.environment.minDelay)
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

    #jge - end Unit class
    ####################################################
    
class Environment():
    #jge - housekeeping?

    def __init__(self, parent, microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0, maxDelay = 0, minDelay = 0, stepSize = 0):
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
        #jge - when making print statements to the console.         
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
        self.parent.pAL('Created ' + self.name, 'info')
                
class HomeSwitch():
    #jge - object to manage the limit switches used to find home
    def __init__(self, parent, switchPin, name = ''):
        self.parent = parent
        self.parentMotor = None
        self.switchPin = int(switchPin)
        self.name = name
        self.prevState = 0
        self.state = 0
        parent.pi.set_mode(self.switchPin, pigpio.INPUT)
        #jge - using internal resistors in addition to external
        parent.pi.set_pull_up_down(self.switchPin, pigpio.PUD_DOWN)
        #jge - set up callback function to look for a closing switch
        self.cbf = parent.pi.callback(self.switchPin, pigpio.EITHER_EDGE, self.callbackFunc)
        self.parent.pAL('Created ' + self.name, 'info')

    def callbackFunc(self, gpio, level, tick):     
        #jge - no matter what, if the switch is closed, stop the motor.
        #jge - also, set the haltAll at the unit to call a stop to the
        #jge - wave_chain in the case of a gotopreset.  If not going
        #jge - to preset, home the single running motor
        self.state = self.parent.pi.read(self.switchPin)

        if (self.state == 1 and self.prevState != self.state):
            #jge - the switch is newly closed
            self.parentMotor.isHoming = 0
            
            if (self.parent.goingToPreset == 1):
                #jge - the pi while loop in the goto preset method
                #jge - will hear this setting of the flag and will
                #jge - cancel the wave send.
                self.parent.haltAll = 1
            else:
                #jge - only call the homing if not going to preset.
                #jge - otherwise, let the gotoPreset method handle
                #jge - the timing of the call to home all
                self.parentMotor.moveOffSwitch('switch Called') 

        self.prevState = self.state

class Motor():
    def __init__(self, parent, sleepPin = 0, dirPin = 0, stepPin = 0, direction = 0, name = '', coverDirection = 0, uncoverDirection = 0, homeSwitch = 0, lagTime = 0):
        self.parent = parent
        self.sleepPin = int(sleepPin)
        self.dirPin = int(dirPin)
        self.stepPin = int(stepPin)
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
        if (self.name == 'motor 1' or self.name == 'motor 3'):
            self.maxSteps = parent.widthInSteps
        else:
            self.maxSteps = parent.heightInSteps
        self.parent.pi.write(self.stepPin, 1)
        self.isHoming = 0
        self.prevStepsFromHomeCount = 0
        self.lagTime = lagTime

        self.parent.pAL('Created ' + self.name, 'info')

    def move(self, event, direction):        
        #jge - make sure it's not running against the wide open stops
        #jge - allow for a move when homing all due to a switch closed
        #jge - during a gotoPreset
        if ((direction == self.coverDirection and int(self.maxSteps) > self.stepsFromHomeCount) or
            (direction == self.uncoverDirection and self.stepsFromHomeCount > 0) or
            self.parent.stopAtWideOpen == '0' or
            self.parent.haltAll == 1 or
            self.isHoming == 1
            ):
            self.parent.pAL('Moving ' + self.name + ' motor in direction ' + str(direction), 'info')
            self.direction = direction
            self.wakeUp()
            self.parent.pi.write(self.sleepPin, 1)
            self.parent.pi.write(self.dirPin, direction)
            self.parent.pi.set_PWM_dutycycle(self.stepPin, 128)  # PWM 1/2 On 1/2 Off
            self.parent.pi.set_PWM_frequency(self.stepPin, 500)
            sleep(.05)
        else:
            self.parent.pAL('Cant open ' + self.name + ' any further', 'info')
        
    def callbackFunc(self, gpio, level, tick):     
        #jge - figure out whether to add or subtract the steps
        if (self.direction == self.coverDirection):
            self.stepsFromHomeCount += 1
        else:
            self.stepsFromHomeCount -= 1                
            
        #jge - stop the move if it's wide open or closed
        if (
            (
                (self.stepsFromHomeCount == 0 and self.direction == self.uncoverDirection) or
                (self.stepsFromHomeCount >= int(self.maxSteps) and self.direction == self.coverDirection)
            ) and
            self.isHoming == 0
           ):
            self.parent.pAL('in Motor cbf - Stopping motor ' + self.name +
                  ' haltAll = ' + str(self.parent.haltAll) +
                  ' stepsFromHome = ' + str(self.stepsFromHomeCount) +
                  ' dir = ' + str(self.direction) +
                  ' cov dir = ' + str(self.coverDirection), 'info')       
            self.stop(self)
                      
        if (self.stepsFromHomeCount < 0):
            self.stepsFromHomeCount = 0

        self.prevStepsFromHomeCount = self.stepsFromHomeCount
            
    def stop(self, event):
        #jge - stop motion then sleep
        self.parent.pi.write(self.stepPin, 0)
        self.parent.pi.write(self.sleepPin, 0)
        self.sleep()
    
    def moveToSwitch(self, event):
        self.parent.pAL('in moveToSwitch method', 'info')

        #jge - if the switch is closed, move away. otherwise, move in
        if (self.parent.pi.read(self.homeSwitch.switchPin) == 1):
            self.moveOffSwitch('faultFind')
        else:
            self.move('faultFind', self.uncoverDirection)

    def moveOffSwitch(self, event):
        self.wakeUp()
        
        while (self.parent.pi.read(self.homeSwitch.switchPin) == 1):
            sleep(.05)
            self.parent.pi.write(self.dirPin, self.coverDirection)
            self.parent.pi.set_PWM_dutycycle(self.stepPin, 128)  # PWM 1/2 On 1/2 Off
            self.parent.pi.set_PWM_frequency(self.stepPin, 500)

        t_end = time.time() + .25
        while time.time() < t_end:
            sleep(.05)
            self.parent.pi.write(self.dirPin, self.coverDirection)
            self.parent.pi.set_PWM_dutycycle(self.stepPin, 128)  # PWM 1/2 On 1/2 Off
            self.parent.pi.set_PWM_frequency(self.stepPin, 500)
            
        self.stop('limit')
        self.stepsFromHomeCount = 0      
        
    def sleep(self):
        #jge - this turns off motor voltage
        self.parent.pi.write(self.sleepPin, 0)
        
    def wakeUp(self):
        #jge - this restores power to the motor
        self.parent.pi.write(self.sleepPin, 1)
