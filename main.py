from machine import Pin, I2C, Signal, ADC, Timer
import network
import max30100
import mlx90614
from esp32_gpio_lcd import GpioLcd
import time
import math
import ufirebase as firebase
import os as MOD_OS

print("________Welcome to our project________")

#Connect to Wifi
GLOB_WLAN=network.WLAN(network.STA_IF)
GLOB_WLAN.active(True)
GLOB_WLAN.connect("Vodafone_VDSL_13F6", "*2NEmY3*"


#Setting firebase URL
firebase.setURL("https://final-proj-c78d4-default-rtdb.firebaseio.com/")

#__LCD Pin Declaration__
lcd = GpioLcd(rs_pin=Pin(5),
              enable_pin=Pin(18),
              d4_pin=Pin(19),
              d5_pin=Pin(21),
              d6_pin=Pin(22),
              d7_pin=Pin(23),
              num_lines=2, num_columns=20)
              
#__Temperature Sensor Pin Declaration__
temp = I2C(scl= Pin(32), sda= Pin(33),freq=100000)
MLX_Sensor = mlx90614.MLX90614(temp)

#__Oxygen Sensor Pin Declaration__
i2c = I2C(scl=Pin(25),sda=Pin(26),freq=100000)

MAX_Sensor = max30100.MAX30100(i2c=i2c)
MAX_Sensor.enable_spo2()

#__Heat rate Sensor Pin Declaration__
adc = ADC(Pin(36))

#___ Variables Declaration ___
TOTAL_BEATS = 15

#_____________________________________Temperature Sensor____________________________________________#

#__Temperature Sensor function__
def Temperature_sensor():
  flag1 = 0
  for i in range(1):
    print("Temperature MEASUREMENT: ")
    print("  Ambient Temperature: " ,MLX_Sensor.read_ambient_temp()," C")
    if (MLX_Sensor.read_object_temp() >= 38) or (MLX_Sensor.read_object_temp() < 36) :
      print("  Object Temperature: " ,MLX_Sensor.read_object_temp()," C    -->    Not Nomal")
      lcd.clear()
      lcd.move_to(0, 0)
      lcd.putstr("Temperature: %d " % MLX_Sensor.read_object_temp() +"C \nNot Normal")
      flag1 = 1
      
    else:
      print("  Object Temperature: " ,MLX_Sensor.read_object_temp()," C    -->    Nomal range")
      lcd.clear()
      lcd.move_to(0, 0)
      lcd.putstr("Temperature: %d " % MLX_Sensor.read_object_temp() +"C \nNormal Range")
    time.sleep_ms(3000)
  return MLX_Sensor.read_object_temp(), flag1
  
#_______________________________________Oxygen Sensor_______________________________________________#

#__Oxygen Sensor function__  
def Oxygen_Sensor():
  flag2 = 0
  print("Oxygen MEASUREMENT: ")
  for i in range(1):
    MAX_Sensor.read_sensor()
    if (MAX_Sensor.ir==0 and MAX_Sensor.red==0):
      sp02 = 0
    else:
      R=(((math.log(MAX_Sensor.red))*650)/((math.log(MAX_Sensor.ir))*950))
      sp02=110-25*R
    time.sleep_ms(1000)
    
    if sp02 >= 90:
      print("  spo2=",sp02,"%    -->    Nomal range")
      lcd.clear()
      lcd.move_to(0, 0)
      lcd.putstr("SP02: %d " % sp02 +"% \nNormal range")
    else:
      print("  spo2=",sp02,"%    -->    Not Nomal")
      lcd.clear()
      lcd.move_to(0, 0)
      lcd.putstr("SP02: %d " % sp02 +"% \nNot Normal")
      flag2 = 1
    
    time.sleep_ms(3000)
  return sp02, flag2
  
#________________________________________Pulse Sensor_______________________________________________#

#___ Calculating Pulse per minute ___
def calculate_bpm(beats):
  beat_time = beats[-1] - beats[0]
  if beat_time:
    pulse = (len(beats) // (beat_time)) * 60        # calculating beat per minute
    return pulse

#___ Calculating Average of reading ___
def Calculating_Average(Nums):
  Nums.remove(Nums[0])
  if len(Nums) == 0:
    Average = 0
  else:
    Average = sum(Nums) // len(Nums)
  return Average
  
#___ Reading from Sensor___
def Pulse_Sensor():
  flag3       = 0
  bpm         = 0
  history     = []
  beats       = []
  PulseArr    = []
  #beat        = False
  
  print("Heart MEASUREMENT : ")
  for i in range(TOTAL_BEATS):
    v = adc.read()
    history.append(v)
    minimum, maximum = min(history), max(history)    
    threshold_on = (minimum + maximum * 3) // 4     # 3/4
    threshold_off = (minimum + maximum) // 2        # 1/2
    
    if v > threshold_on: #and beat == False:
      #beat = True
      beats.append(time.time())                     # inserting the time of each pulse in array
      PulseArr.append(calculate_bpm(beats))

    if v < threshold_off: #and beat == True:
      #beat = False
      pass
    
    time.sleep_ms(1000)
  
  if len(PulseArr) == 0:
    bpm = 0
  else:
    bpm = Calculating_Average(PulseArr)
  
  if bpm > 50 and bpm < 100:
    print(" pulses = " ,bpm ," bpm    -->    Nomal range")
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("pulses = %d" % bpm)
    lcd.putstr("\nNormal Range")
    
  elif bpm == 0 :
    print(" No beat")
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("No beat please put \nyour finger")
    flag3 = 1
    
  else:
    print(" pulses = " ,bpm ," bpm    -->    Not in normal range")
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("pulses = %d" % bpm)
    lcd.putstr("\nNot in normal range")
    flag3 = 1
    
  time.sleep_ms(3000)  
  return bpm, flag3

while True:
  time.sleep(10)
  flag = 0
  print("\n  _________________ \n")
  sensor1, flag1 = Temperature_sensor()
  firebase.put("Temperature Measurements",sensor1, bg=0)
  firebase.get("Temperature Measurements", "var1", bg=0)
  
  print("\n  _________________ \n")
  sensor2, flag2 = Oxygen_Sensor()
  firebase.put("Oxygen Measurements",sensor2, bg=0)
  firebase.get("oxygen Measurements", "var1", bg=0)
  
  print("\n  _________________ \n")
  sensor3, flag3 = Pulse_Sensor()
  firebase.put("Heart Measurements",sensor3, bg=0)
  firebase.get("Heart Measurements", "var1", bg=0)
  
  if (flag1 == 1) or (flag2 == 1) or (flag3 == 1):
    flag = 1
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("There is a problem\nAre u okay")
  else:
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("All Good\nStay safe")
    
  firebase.put("Flag",flag, bg=0)
  firebase.get("Flag", "var1", bg=0)
  print("\n ******************************* \n")
  
  
  time.sleep(10)










