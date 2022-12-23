# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtTest, uic
from PyQt5.QtCore import QThread, QObject
from PyQt5.QtWidgets import QMessageBox

import pymmcore
import sys
from queue import Queue
import numpy as np
import os
import h5py
import time
from serial import Serial



        

class Laser(QObject):

    
    def __init__(self, parent=None, app=None, laser_number=0):
        
        super().__init__()
        
        self.mainWindow=parent
        self.laser_number=laser_number
        self.app=app
        
        self.laser_names=["","","","","",""]
        
        self.laser_list=[["LuxX",'COM8',500000],
                         ["OBIS",'COM9',115200],
                         ["OBIS",'COM10',115200],
                         ["OBIS",'COM11',115200],
                         ["LuxX",'COM18',500000],
                         ["OBIS",'COM17',115200]]
        
        self.checkbox_list=[self.mainWindow.Laser1_1_check,
                            self.mainWindow.Laser1_2_check,
                            self.mainWindow.Laser1_3_check,
                            self.mainWindow.Laser1_4_check,                            
                            self.mainWindow.Laser2_1_check,
                            self.mainWindow.Laser2_2_check]
        
        self.mode_box_list=[self.mainWindow.Laser1_1_mode,
                           self.mainWindow.Laser1_2_mode,
                           self.mainWindow.Laser1_3_mode,
                           self.mainWindow.Laser1_4_mode,
                           self.mainWindow.Laser2_1_mode,
                           self.mainWindow.Laser2_2_mode]
        
        self.mode_box_item=[["Standby","ACC","APC","ACC+A"],
                           ["APC","ACC+D","ACC+A","ACC+DA"],
                           ["APC","ACC+D","ACC+A","ACC+DA"],
                           ["APC","ACC+D","ACC+A","ACC+DA"],
                           ["Standby","ACC","APC","ACC+A"],
                           ["APC","ACC+D","ACC+A","ACC+DA"]]
        
        self.slider_list=[[self.mainWindow.Laser1_1_pow,self.mainWindow.Laser1_1_slider],
                          [self.mainWindow.Laser1_2_pow,self.mainWindow.Laser1_2_slider],
                          [self.mainWindow.Laser1_3_pow,self.mainWindow.Laser1_3_slider],
                          [self.mainWindow.Laser1_4_pow,self.mainWindow.Laser1_4_slider],
                          [self.mainWindow.Laser2_1_pow,self.mainWindow.Laser2_1_slider],
                          [self.mainWindow.Laser2_2_pow,self.mainWindow.Laser2_2_slider]]
        
        self.sers= []
        self.statuses= []
        self.current_pows= []
        self.current_modes= []
        self.time=time.time()
        
        try:
            for i in range(6):
                
                self.mode_box_list[i].addItems(self.mode_box_item[i])
                
                self.laser_start(i)  
                
                self.mode_box_list[i].currentIndexChanged.connect(lambda t,x=i : self.laser_mode(x))    
                self.checkbox_list[i].clicked.connect(lambda t,x=i : self.laser_switch(x))   
                
                self.slider_list[i][0].valueChanged.connect(lambda t,laser_num=i: self.laser_power_text(laser_num)) 
                self.slider_list[i][1].sliderReleased.connect(lambda laser_num=i: self.laser_power_slider(laser_num))  
        except:
            print('Laser not loaded correctly')
                
            
            
            
    
        
    def close(self):
        
        if any(self.statuses):
            reply = QMessageBox.question(self.mainWindow, 'Lasers off?', 'Do you want to turn the lasers off?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.lasers_off()
                    
        for i in range(len(self.sers)):
            self.close_port(self.sers[i])
            print('Laser '+str(i+1)+' closed')
            
        self.deleteLater()
            
        
        
    def close_port(self,ser):
        
        if ser:
            ser.close()
            
    def laser_start(self,laser_num):
        
        prop=self.laser_list[laser_num]
        
        try:
            ser = Serial(prop[1], baudrate=prop[2])
            
            (name,status,current_pow, mode)=self.device_start(ser,prop[0])
            
            print('Laser '+str(laser_num+1)+' loaded: '+name)
            self.laser_names[laser_num]=name
            self.checkbox_list[laser_num].setEnabled(True)
            self.checkbox_list[laser_num].setChecked(status)
            
            
            self.mode_box_list[laser_num].setCurrentIndex(mode)
            self.mode_box_list[laser_num].setEnabled(status)
            
            self.slider_list[laser_num][0].setValue(current_pow)
            self.slider_list[laser_num][0].setEnabled(status)
            self.slider_list[laser_num][1].setValue(current_pow)
            self.slider_list[laser_num][1].setEnabled(status)
        
        
        except:
            ser=None
            status=False
            current_pow=0
            mode=0
            print("Laser "+ str(laser_num+1) + ' not available')
            
            self.laser_names[laser_num]="None"
            
            self.checkbox_list[laser_num].setEnabled(False)
            self.mode_box_list[laser_num].setEnabled(False)
            self.slider_list[laser_num][0].setEnabled(False)
            self.slider_list[laser_num][1].setEnabled(False)
            
        
        self.sers.append(ser)
        self.statuses.append(status)
        self.current_pows.append(current_pow)
        self.current_modes.append(mode)
    
    
    def laser_switch(self,laser_num):
        
        prop=self.laser_list[laser_num]
        
        status=self.checkbox_list[laser_num].isChecked()
        self.statuses[laser_num]=status
        self.device_switch(self.sers[laser_num],status,prop[0])
        
        self.slider_list[laser_num][0].setEnabled(status)
        self.slider_list[laser_num][1].setEnabled(status)
        self.mode_box_list[laser_num].setEnabled(status)
        
    def lasers_off(self):

        for laser_num in range(len(self.sers)):
            
            if self.statuses[laser_num]:
                prop=self.laser_list[laser_num]
                self.device_switch(self.sers[laser_num],False,prop[0])
            
        
    def laser_power_text(self,laser_num):
        
        prop=self.laser_list[laser_num]
        
        power = self.slider_list[laser_num][0].value()
        if power>100:
            power=100
        if power<0:
            power=0
            
        self.slider_list[laser_num][0].setValue(power)
        self.slider_list[laser_num][1].setValue(power)   
        self.current_pows[laser_num]=power            
    
        self.device_power(self.sers[laser_num],self.current_pows[laser_num],prop[0])

            
        
    def laser_power_slider(self,laser_num):
        
        power = int(self.slider_list[laser_num][1].value())
        self.current_pows[laser_num]=power            
        self.slider_list[laser_num][0].setValue(power) # change of text automatically trigger power change
            
        
        
    def laser_mode(self,laser_num):
        
        prop=self.laser_list[laser_num]
        mode=int(self.mode_box_list[laser_num].currentIndex())
        self.current_modes[laser_num]=mode
        self.device_mode(self.sers[laser_num],mode,prop[0])
        
        
        
            
    ### start functions
    
        
    def device_start(self,ser,device_name):
        
        mode = 1
        
        if device_name=="LuxX":
        
            # check device
            ser.write(b"?GFw\r")
            model_name=ser.read_until(b"\r").decode('ascii', 'ignore')[:-1]
            ser.reset_input_buffer()
            
            model_name=model_name[4:8]
            
            # check wavelength & Power
            ser.write(b"?GSI\r")    
            wavelength=ser.read_until(b"\r").decode('ascii', 'ignore')[:-1]
            ser.reset_input_buffer()
            wl = wavelength[4:7]
            power = wavelength[7:9]
            model_name += " " + wl + "-"+power
            max_pow=float(power)
            
            # check device status
            ser.write(b"?GAS\r")
            ser.read(4)
            status_txt=ser.read_until(b"\r").decode('ascii', 'ignore')[:-1]
            status_txt= "{:016b}".format(int(status_txt,16))
            ser.reset_input_buffer()
            status=(int(status_txt[14])==1)
            
            # setting autostart off
            # ser.write(b"?SAS0\r")
            # status_txt=ser.read_until(b"\r").decode('ascii', 'ignore')[:-1]
            # print(status_txt)
            # ser.write(b"?SAS\r")
            # status_txt=ser.read_until(b"\r").decode('ascii', 'ignore')[:-1]
            # print(status_txt)
            
            ser.write(b"?GLP\r")
            pow_txt=ser.read_until(b"\r").decode('ascii', 'ignore')[:-1]
            ser.reset_input_buffer()
            current_pow=int(round(float(int(pow_txt[4:],16))/4095*100))
            
            ser.write(b"?ROM1\r")      
            QtTest.QTest.qWait(200)
            ser.reset_input_buffer()
            mode = 1
                            
        
        elif device_name=="OBIS":
            
            # check device
            ser.write(b"SYSTem:INFormation:MODel?\r")
            model_name=ser.readline().decode()[:-1]
            ser.reset_input_buffer()
            
            # check devide status
            ser.write(b"SOURce:AM:STATe?\r")
            status_txt=ser.readline().decode()[:-2]
            status= (status_txt=='ON')
            ser.reset_input_buffer()
            
            # set autostart off
            # ser.write(b"SYSTem:AUTostart OFF\r")                      
            # QtTest.QTest.qWait(200)
            # ser.reset_input_buffer()                
            # ser.write(b"SYSTem:AUTostart?\r")
            # status_txt=ser.readline().decode()[:-2]
            # print(status_txt)
            # #status= (status_txt=='ON')
            # ser.reset_input_buffer()
            
            # check max power
            ser.write(b"SOURce:POWer:NOMinal?\r")
            #power_txt=ser.readline().decode()[:-1]
            power_txt=ser.readline().decode()[:-1]
            max_pow=float(power_txt)*1000
            ser.reset_input_buffer()
            
            # check current power
            ser.write(b"SOURce:POWer:LEVel:IMMediate:AMPLitude?\r")
            power_txt=ser.readline().decode()[:-1]
            current_pow=float(power_txt)*1000
            ser.reset_input_buffer()
            current_pow=int(round(current_pow/max_pow*100))
            
            ser.write(b"SOURce:AM:SOURce?\r")      
            mode_txt=ser.readline().decode()[:-2]
            ser.reset_input_buffer()
            
            
            if mode_txt=='CWP':
                mode=0
                
            if mode_txt=='DIGITAL':
                mode=1
                
            if mode_txt=='ANALOG':
                mode=2
                
            if mode_txt=='MIXED':
                mode=3
                
        
        return (model_name, status, current_pow,mode)

        
        
        
        
    ### switch functions
    
    
    def device_switch(self,ser,status,device_name):
            
        if device_name=="LuxX":
            if status:
                command=b"?LOn\r"
            else:
                command=b"?LOf\r"
                
        
        elif device_name=="OBIS":
            
            command=b"SOURce:AM:STATe "
            if status:
                command += b"ON\r"
            else:
                command += b"OFF\r"
            
        ser.write(command)                
        QtTest.QTest.qWait(200)
        ser.reset_input_buffer()
            
        
    ### power modulation functions    
        
    def device_power(self,ser,power,device_name):
        
        if device_name=="LuxX":
            
            power_hex=(power*4095/100)  
            power_txt="{0:#0{1}x}".format(int(power_hex),3)[2:]
            command=b"?SLP"+power_txt.encode()+b"\r"
        
        elif device_name=="OBIS":
            
            ser.reset_input_buffer()
            ser.write(b"SOURce:POWer:NOMinal?\r")
            power_txt=ser.readline().decode()[:-1]
            ser.reset_input_buffer()
            
            max_pow=float(power_txt)
            set_pow=max_pow*float(power)/100
            
            command=b"SOURce:POWer:LEVel:IMMediate:AMPLitude "
            command += ("{:.4f}".format(set_pow)).encode()+b"\r"
        
        ser.write(command)                
        QtTest.QTest.qWait(200)
        ser.reset_input_buffer()
        
        
        
    ### power modulation functions    
        
    def device_mode(self,ser,mode,device_name):
        
        if device_name=="LuxX":
            #Note: if the laser-enable/led-enable input is not connected it will stay active
                
            command=b"?ROM"+str(mode).encode()+b"\r" 
        
        elif device_name=="OBIS":
            
            ser.write(b"SOURce:AM:STATe OFF\r")                
            QtTest.QTest.qWait(200)
            ser.reset_input_buffer()
                
            if mode==0:
                command=b"SOURce:AM:INTernal CWP\r" # APC with no modulation
            else:
                
                if mode==1:    
                    command=b"SOURce:AM:EXTernal DIGital\r"   # Stable ACC with modulation
                    
                if mode==2:    
                    command=b"SOURce:AM:EXTernal ANALog\r"   # Stable ACC with modulation
                    
                if mode==3:    
                    command=b"SOURce:AM:EXTernal MIXed\r"   # Stable ACC with modulation
                    
                
        ser.write(command)                
        QtTest.QTest.qWait(200)
        ser.reset_input_buffer()
        
        if device_name=="OBIS":                
            
            ser.write(b"SOURce:AM:STATe ON\r")                
            QtTest.QTest.qWait(200)
            ser.reset_input_buffer()
            
        
    ### power modulation functions    

