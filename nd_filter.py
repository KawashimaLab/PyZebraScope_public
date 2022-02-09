# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 14:48:17 2020

@author: admin
"""

''' Stages ''' 

from serial import Serial
import time
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import QtTest  

class ND_Filter(QObject):
    
    
    def __init__(self, parent=None):
        super().__init__()
        
        self.mainWindow=parent
        
        self.filter_list=[['No Filter','ND1.0','ND1.5','ND2.0','ND3.0','ND4.0'],
                          ['No Filter','ND1.0','ND1.5','ND2.0','ND3.0','ND4.0'],
                          ['No Filter','ND1.0','ND1.5','ND2.0','ND3.0','ND4.0']]
        
        self.com_list=['COM4','COM3','COMX']
        self.sers=[]
        self.pos=[1,1,1]
        self.filter_box_list=[self.mainWindow.filter1_box,self.mainWindow.filter2_box,self.mainWindow.filter3_box]
        
        for i in range(3): 
            self.start_filter(i)
        
        
    def start_filter(self,num):
        
        try:
            ser = Serial(self.com_list[num], baudrate=115200)                        
            self.filter_box_list[num].setEnabled(True)
            self.filter_box_list[num].addItems(self.filter_list[num])
            pos = self.get_position(ser)
            self.filter_box_list[num].setCurrentIndex(pos-1)
            self.filter_box_list[num].currentIndexChanged.connect(lambda s : self.position_change(s=num))            
            print('Filter '+str(num+1)+' connected')
            
        except:
            ser=[]
            pos=1
            print('Filter '+str(num+1)+' not connected')
            self.filter_box_list[num].setEnabled(False)
        
        self.sers.append(ser)
        self.pos[num]=pos
                
        
        
    def close(self):
        
        for i in range(2):
            self.close_port(i)    
            
        self.deleteLater()
        print("Filter disconnected")
        
        
    def close_port(self,num):
        
        if self.sers[num]:
           self.sers[num].close()
            
        
    def get_position(self,ser):
        
        ser.write(b"pos?\r")        
        ser.read_until(b"\r") # discard echoed question 
        ans = ser.read_until(b"\r").decode()         
        ser.reset_input_buffer()
        return int(ans[0])
    
    
    def set_position(self,num,pos):
        
        self.pos[num]=pos            
        self.filter_box_list[num].setCurrentIndex(pos-1)
    
        
    def position_change(self,s=0):

        self.pos[s]=int(self.filter_box_list[s].currentIndex()+1)
        if self.sers[s]:
            self.sers[s].write(("pos=" + str(self.pos[s]) + "\r").encode())        
            self.sers[s].reset_input_buffer()
            
                    

            
            