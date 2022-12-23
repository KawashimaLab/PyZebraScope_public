# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 14:48:17 2020

@author: admin
"""

''' Stages ''' 

from serial import Serial
import time
from PyQt5.QtCore import pyqtSignal, QObject, QTimer
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtTest
from math import isclose
import numpy as np

class Piezo(QObject):
        
    def __init__(self,parent=None):
        super().__init__()
        
        
            
        # 1  We may need to add a message box before duing FRF
        # 2  Also, probably better to move to ref position in unreferenced mode
        
        self.mainWindow=parent
        
        self.autozero=0
        self.servo=0
        

        
        try:
            self.ser = Serial('COM15', baudrate=57600, timeout=2) # factory setting
            
            self.piezo_init()
            
    
            print('Piezo connected')
            
        except:
            self.ser=None
            
                
            print('Piezo not available')
        
        
    def close(self):
        
        if self.ser:
            
            self.ser.write(("SVO Z 0\n").encode())      
            
            self.ser.close()
            print('Piezo disconnected')
        
        self.deleteLater()
    
        
    def piezo_init(self):
        
        ## checking autozero
        
        self.ser.write(("ATZ?\n").encode())
        self.autozero = int(self.ser.readline().decode()[2])
        
        if not self.autozero == 1:
            print('Piezo Autozero OFF: setting it ON...')
            self.ser.write(("ATZ Z 1\n").encode())
            
            QtTest.QTest.qWait(5000)    
            
            self.ser.write(("ATZ?\n").encode())
            self.autozero = int(self.ser.readline().decode()[2])
            
            if state==1:
                print('Piezo Autozero set')
                
            else:
                print('Cannot set AutoZero')
        
        
        
        ## setting the servo ON
        
        self.ser.write(("SVO Z 1\n").encode())
        
        QtTest.QTest.qWait(1000)    
        
        self.ser.write(("SVO?\n").encode())
        self.servo=int(self.ser.readline().decode()[2])
        
        if self.servo==1:
            print('Piezo servo ON')      
        else:
            print('Cannot turn on Servo')
        
            
            
     