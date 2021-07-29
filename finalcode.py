import time, threading
import board
import RPi.GPIO as GPIO
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from w1thermsensor import W1ThermSensor

from database import Database

mydb = Database('EV001')

sensor = W1ThermSensor()

# PIN connected to IN1
relay_pin = 23
 
# Set mode BCM
GPIO.setmode(GPIO.BCM)
 
#Type of PIN - output
GPIO.setup(relay_pin,GPIO.OUT)

def run_i2c():
    while True:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            ads = ADS.ADS1115(i2c)
            chan = AnalogIn(ads, ADS.P0)
            chan1 = AnalogIn(ads, ADS.P1)
        
            p_voltage =  chan.voltage
            p_voltage = round(p_voltage, 3)

            batt_voltage = round(chan1.voltage, 3)
                        
            print("{:>5.3f},{:>5.3f}".format(chan.voltage, chan1.voltage))
            time.sleep(1)
            
            current = ((p_voltage- 2.5)/0.00625)
            voltages = batt_voltage * 5
            
            print ("Current = %.3f" %current)
            print ("ev battery = %.3f" %voltages)
            mydb.updateCurrentAndVoltage(current, voltages)
            print("    ")
        except:
            print("somethig happened")


def relays():
    try:
        #set low
        print ("Setting low - EV CHARGING HAS STOPPED")
        print("    ")
        GPIO.output (relay_pin,GPIO.LOW)
        time.sleep(2)
        #set high
        print ("Setting high - EV CHARGING ONGOING")
        GPIO.output (relay_pin, GPIO.HIGH)
        time.sleep(6)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print ("Bye")


def temperature():
    while True:
        averages=[]

        for sensor in W1ThermSensor.get_available_sensors():
            averages.append(sensor.get_temperature())
            print("Batt Temp: %.2f" % (sensor.get_temperature()))
            
        average=sum(averages)/len(averages)
        print("    ")
        
        print("EV Batt Temp %.2f C" %average)
        mydb.updateTemperature(average)
        print(".......................................................................................................................")
        print("    ")
        # run_i2c()
        # relays()
        
        
    time.sleep(1)
    
temperature_thread = threading.Thread(target=temperature).start()
i2c_thread = threading.Thread(target=run_i2c).start()
