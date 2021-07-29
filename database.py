from typing import cast
import RPi.GPIO as GPIO
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("myev-ug-firebase-adminsdk-rofzi-572fec6620.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
relay_pin = 23


class Database:
    def __init__(self, vehicleID):
        self.vehicleID = vehicleID
        self.vRef = db.collection('vehicles').document(self.vehicleID)

        # self.vRef.update({
        #     'command': 'vehicle_online'
        # })

        self.battery_current = 0.0
        self.battery_voltage = 0.0
        self.measured_resistance = 0.0
        self.battery_health = 120.0
        self.battery_health_range = 'healthy'
        self.avg_system_temp = 0.0
        self.battery_temperature_range = 'Normal'
        self.charge_start = firestore.SERVER_TIMESTAMP
        self.charge_stop = firestore.SERVER_TIMESTAMP
        self.current_percentage = 0.0
        self.initial_percentage = 0.0
        self.final_percentage = 0.0
        self.internal_resistance = 5.1

        
        if self.vRef.get().exists:
            self.vRef.on_snapshot(self.onSnapshot)
        else:
            self.vRef.set({
                'command': 'new_vehicle',
                'battery_voltage': self.battery_voltage,
                'battery_current': self.battery_current,
                'battery_temperature': self.battery_current,
                'battery_temperature_range': self.battery_temperature_range,
                'battery_health': self.battery_health,
                'battery_health_range': self.battery_health_range,
                'battery_percentage': self.current_percentage,
                'measured_resistance': self.measured_resistance,
                'internal_resistance': self.internal_resistance,
                'password': '12345678'
            })
            self.vRef.on_snapshot(self.onSnapshot)



    def updateTemperature(self, temp):
        self.avg_system_temp = temp
        temp_range = 'Low' if temp < 15 else 'Normal' if temp < 35.0 else 'High'
        self.vRef.update({
            'battery_temperature': temp,
            'battery_temperature_range': temp_range
        })

    def updateCurrentAndVoltage(self, current, voltages):
        self.battery_voltage = voltages
        self.battery_current = current
        time_left = 150 - ((15 - self.battery_current) / 0.1)
        self.measured_resistance = (self.battery_voltage -180) / self.battery_current
        self.current_percentage = ((15 - self.battery_current) / 15 ) * 100
        self.battery_health = health = 200 - (((self.battery_voltage - 180) / (5.1 * self.battery_current)) *100)
        
        # health_range = 'Unhealthy' if health > 160 else 'Good' if health > 120 else 'Healthy'
        if (self.battery_health < 40): health_range = 'Unhealthy'
        else: health_range = 'Healthy'

        
        self.vRef.update({
            'battery_current': self.battery_current,
            'battery_voltage': self.battery_voltage,
            'battery_percentage': self.current_percentage,
            'battery_health': self.battery_health,
            'battery_health_range': health_range,
            'measured_resistance': self.measured_resistance,
            'current_charge.time_left': time_left,
            'last_online': firestore.SERVER_TIMESTAMP
        })

    def onSnapshot(self, doc_snapshot, changes, read_time):
        # callback_done.set()
        for doc in doc_snapshot:
            if not doc.exists: print("haha")
            data = doc.to_dict()
            command = data['command']
            
            if command == 'stop_charge':
                if relaysOFF(): 
                    self.charge_stop = firestore.SERVER_TIMESTAMP
                    self.final_percentage = self.current_percentage
                    self.vRef.update({
                        'command': 'charge_stopped',
                        'current_charge.avg_system_temp': self.avg_system_temp,
                        'current_charge.initial_percentage': self.initial_percentage,
                        'current_charge.stop': self.charge_stop,
                        'current_charge.battery_current': self.battery_current
                    })
                    self.vRef.collection('history').add({
                        'start': self.charge_start,
                        'stop': self.charge_stop,
                        'avg_system_temp': self.avg_system_temp,
                        'initial_percentage': self.initial_percentage,
                        'final_percentage': self.final_percentage,
                        'battery_current': self.battery_current,
                        'battery_health': self.battery_health,
                        'battery_voltage': self.battery_voltage
                    })
                else: self.vRef.update({'command': 'charge_stop_failed'})
            
            if command == 'start_charge':
                if relaysON():
                    self.charge_start = firestore.SERVER_TIMESTAMP
                    self.initial_percentage = self.current_percentage
                    self.vRef.update({
                        'command': 'charge_started',
                        'current_charge.start': self.charge_start
                    })
                else: self.vRef.update({'command': 'charge_start_failed'})
            

def relaysOFF():
    try:
        #set low
        print ("Setting low - EV CHARGING HAS STOPPED")
        print("    ")
        GPIO.output (relay_pin,GPIO.LOW)
        return True
    except:
        GPIO.cleanup()
        print ("Failed to stop charging")
        return False

def relaysON():
    try:
        #set high
        print ("Setting high - EV CHARGING ONGOING")
        GPIO.output (relay_pin, GPIO.HIGH)
        return True
    except:
        GPIO.cleanup()
        print ("Failed to start charging")
        return False
