# This file is executed on a M5Stack device GRBL GoPlus2
# It is connected to a M5Stack device with
# a RFID reader
# a stepper motor
# a LCD screen (320x240)
# 3 buttons

from m5stack import *
from m5ui import *
from uiflow import *
import module
import urequests
import json
import unit

motor_speed = 200
motor_step = 1

programRunning = True
colors = {
  "green": 0x64c466,
  "orange": 0xef8c00,
  "red": 0xea4d3d
}
distanceToDestination = 4.1

#region API controllers
headersList = {
 "Accept": "*/*",
 "User-Agent": "Thunder Client (https://www.thunderclient.com)",
 "DOLAPIKEY": "81d718e2cc4e82abfb0b15ebb8fdc7b1f56fff96",
 "Content-Type": "application/json"
}

def getPackageFromAPI(packageId):
  try:
    url = "https://iot-alpha-roll.saas1.doliondemand.fr/api/index.php/products?sqlfilters=t.ref=%27" + packageId + "%27"
    response = urequests.get(url, headers=headersList)
    data = response.json()[0]
    # if package status is 0, it means it is not available to be picked up by the conveyor
    if int(data["status"]) == 0:
      message_on_display.setText("Package " + packageId + " is not available")
      wait(1)
      return None
    newDist = distanceToDestination
    if (data["country_code"] != "DE"):
      newDist = distanceToDestination + 0.5
    return createItem(code=data["ref"], destination=data["country_code"], distance=newDist)
  except:
    return None

#endregion

#region Screen controllers
debugRect = M5Rect(0, 30, 320, 150, 0x000000, 0x000000)
debug = M5TextBox(0, 30, "text debug", lcd.FONT_Default, 0xFFFFFF, rotate=0)
isDebugOpen = False

motor_status_display = M5Title(title="Statut du moteur : OK", x=20, fgcolor=0x000000, bgcolor=colors["green"])

message_on_display = M5TextBox(0, 40, "", lcd.FONT_Ubuntu, 0xFFFFFF, rotate=0)

text_button_left = M5TextBox(31, 216, "Run/Stop", lcd.FONT_Ubuntu, 0x000000, rotate=0)
text_button_center = M5TextBox(140, 216, "Reset", lcd.FONT_Ubuntu, 0x000000, rotate=0)
text_button_right = M5TextBox(225, 216, "Menu", lcd.FONT_Ubuntu, 0x000000, rotate=0)
footer_rectangle = M5Rect(0, 210, 320, 30, 0xFFFFFF, 0xFFFFFF)

def initScreen():
  hideDebug()
  setScreenColor(0x222222)
  setHeader("green", "OK")
  setFooter("main")

def hideDebug():
  global isDebugOpen
  isDebugOpen = False
  debugRect.hide()
  debug.hide()

def setHeader(color, status):
  motor_status_display.setTitle("Statut du moteur : " + status)
  motor_status_display.setBgColor(colors[color])

def setFooter(type):
  global buttons, text_button_left, text_button_center, text_button_right, footer_rectangle
  footer_rectangle = M5Rect(0, 210, 320, 30, 0xFFFFFF, 0xFFFFFF)
  if (type == "main"):
    text_button_left = M5TextBox(31, 216, "Run/Stop", lcd.FONT_Ubuntu, 0x000000, rotate=0)
    text_button_center = M5TextBox(140, 216, "Reset", lcd.FONT_Ubuntu, 0x000000, rotate=0)
    text_button_right = M5TextBox(225, 216, "Menu", lcd.FONT_Ubuntu, 0x000000, rotate=0)
  elif (type == "menu"):
    text_button_left = M5TextBox(31, 216, "Down", lcd.FONT_Ubuntu, 0x000000, rotate=0)
    text_button_center = M5TextBox(140, 216, "Up", lcd.FONT_Ubuntu, 0x000000, rotate=0)
    text_button_right = M5TextBox(225, 216, "Select", lcd.FONT_Ubuntu, 0x000000, rotate=0)

def printToScreen(text):
  global isDebugOpen
  isDebugOpen = True
  debug.setText(text)
  debugRect.show()
  debug.show()

initScreen()
#endregion

#region Motors controllers
go_plus_2 = module.get(module.GOPLUS2)
stepmotor1 = module.get(module.STEP_MOTOR, 0x70)
stepmotor1.g_code("~")
stepmotor1.set_mode("distance")
motorKilled = False
# distanceBetweenPackages = 10

def startMotor():
  global motorKilled
  stepmotor1.g_code("~")
  motorKilled = False
  setHeader("green", "OK")

def pauseMotor():
  global motorKilled
  stepmotor1.g_code("!")
  motorKilled = True
  setHeader("orange", "PAUSE")

def stopMotor():
  global motorKilled
  stepmotor1.g_code("!")
  motorKilled = True
  setHeader("red", "STOP")

def runMotor(speed, distance):
  stepmotor1.turn(x=distance, y=0, z=0, speed=speed)

angle = 30
def moveDoor(angle):
  go_plus_2.set_servo_angle(go_plus_2.S1, angle)
moveDoor(30)
def getDoorAngle(destination):
  if destination == "FR":
    return 18
  elif destination == "DE":
    return 30
  return 50
#endregion

#region Buttons controllers
def buttonA_wasPressed():
  global programRunning
  if programRunning:
    pauseChronometer()
  else:
    resumeChronometer()
  programRunning = not programRunning
btnA.wasPressed(buttonA_wasPressed)

def buttonB_wasPressed():
  global programRunning
  programRunning = True
  resumeChronometer()
btnB.wasPressed(buttonB_wasPressed)

def buttonC_wasPressed():
  # global programRunning
  # programRunning = False
  printToScreen(currentTag)
btnC.wasPressed(buttonC_wasPressed)

def buttonC_wasReleased():
  hideDebug()
btnC.wasReleased(buttonC_wasReleased)
#endregion

#region RFID controllers
rfid_1 = unit.get(unit.RFID, unit.PORTA)

def isTagDetected():
  return rfid_1.isCardOn()

def getTag():
  return rfid_1.readUid()
#endregion

#region Package controllers
package = None
packageList = []

def createItem(code: str, destination: str, distance: float):
  return {'c':code,'de':destination,'di':distance*1000}

def packageListHasItems():
  global packageList
  return len(packageList) > 0

# packageList.append(createItem("6deed6df8a", "FR", 2))
# packageList.append(createItem("5de7d6dfb3", "DE", 4))
# packageList.append(createItem("9de7d6df73", "ES", 10))
#endregion

#region Timer controllers
import time

# Initialise la variable pour stocker le temps
chronometer = None
pauseTime = None

def resetChronometer():
  global chronometer
  chronometer = time.ticks_ms()

def pauseChronometer():
  global pauseTime
  pauseTime = time.ticks_ms()

def resumeChronometer():
  global chronometer, pauseTime
  chronometer += time.ticks_ms() - pauseTime
  pauseTime = None

def getChronometer():
  global chronometer
  elapsed_time = time.ticks_ms() - chronometer
  return elapsed_time
#endregion

currentTag = None
resetChronometer()
while True:
  if not programRunning:
    if not motorKilled:
      pauseMotor()
      setHeader("orange", "Program stopped")
    wait(1)
    continue
  else:
    newTag = str(getTag())
    if newTag != currentTag and newTag != "None" and newTag != "":
      pauseMotor()
      pauseChronometer()
      elapsed_time = getChronometer()
      message_on_display.setText("Chrono stopped at : " + str(elapsed_time) + "ms")
      package = getPackageFromAPI(newTag)
      if package != None:
        # message_on_display.setText("Code : " + package['c'])
        packageList.append(package)
        currentTag = newTag
        setHeader("green", "Package added")
        # message_on_display.setText("please wait...")
        # message_on_display.setText(str(chronometer) + " " + str(pauseTime) + " ----- " + str(getChronometer()) + "\n\n\n" + "\n".join([str(x) for x in packageList]))
        if packageListHasItems() and pauseTime != None:
          for i in range(len(packageList) - 1):
            # PATCH base 2000
            packageList[i]['di'] -= elapsed_time - 300
        # wait(1)
        # runMotor(motor_speed, motor_step)
        resumeChronometer()
        resetChronometer()
      else:
        stopMotor()
        programRunning = False
        setHeader("red", "Error with package")
        printToScreen("No package found")


    else:
      message_on_display.setText(str(chronometer) + " " + str(pauseTime) + " ----- " + str(getChronometer()) + "\n\n\n" + "\n".join([str(x) for x in packageList]))
      if isDebugOpen:
        initScreen()
      if motorKilled:
        startMotor()
      if packageListHasItems():
        pkg = packageList[0]
        if getChronometer() >= pkg['di']:
          destination = packageList[0]['de']
          # PATCH : changer la destination
          #region Random destination
          # import random
          # rndIdx = random.randint(0, 2)
          # rndDoor = ["FR", "DE", "ES"]
          # destination = rndDoor[rndIdx]
          #endregion
          angle = getDoorAngle(destination)
          moveDoor(angle)
          if packageList[0]['c'] == currentTag:
            currentTag = None
          packageList.pop(0)
      # else:
      #   if (angle != 30):
      #     angle = 30
      #     wait(1)
      #     moveDoor(angle)
      runMotor(motor_speed, motor_step*10)
    wait(0.02)
