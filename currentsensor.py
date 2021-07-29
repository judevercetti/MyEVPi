import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

def run_i2c():
     
    while True:
        
        try:
            
            i2c = busio.I2C(board.SCL, board.SDA)
            ads = ADS.ADS1115(i2c)
            chan = AnalogIn(ads, ADS.P0)
           
            p_voltage =  chan.voltage
            p_voltage = round(p_voltage, 3)
                        
            print("{:>5.3f}".format(chan.voltage))
            time.sleep(1)
            
            current = ((p_voltage- 2.5)/0.00625)
            
            print ("Current = %.3f" %current)
            
            
        except:
            
            
            continue
               
run_i2c()

        #ads.stopadc()      