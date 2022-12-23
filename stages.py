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

class Stages(QObject):
        
    def __init__(self,parent=None):
        super().__init__()
        
        
            
        # 1  We may need to add a message box before duing FRF
        # 2  Also, probably better to move to ref position in unreferenced mode
        
        self.mainWindow=parent
        
        self.sample_y_pos = 165
        self.sample_x_pos = 52.57
        self.axis_names = ['Y','X','Z']
        self.axis_max   = [204., 102., 12.5]
        self.axis_signs = [-1., -1., 1.]
        self.tol        = [[1,30], [self.sample_x_pos-3,self.axis_max[1]-self.sample_x_pos-3], [0.1,0]] ## do not change this
        self.offsets    = [1., self.sample_x_pos, 0.1]
        
        self.home       = [0., 0., 0]
        self.vels       = [10, 0.5, 0.5]
        self.accs       = [0.1,0.1, 0.1]
        
        self.positions = np.asarray([0.,0.,0.]) # YXZ
        self.steps     = np.asarray([.1,.1,.1]) 
        self.stop      = False        
            
        self.pos_box = [self.mainWindow.stage_y_pos,self.mainWindow.stage_x_pos,self.mainWindow.stage_z_pos]
        self.pos_boxv =[self.mainWindow.stage_y_posv,self.mainWindow.stage_x_posv,self.mainWindow.stage_z_posv]
        self.step_box =[self.mainWindow.y_step,self.mainWindow.x_step,self.mainWindow.z_step]
        
        self.step_button=[[self.mainWindow.y_plus_btn,self.mainWindow.y_minus_btn],
                          [self.mainWindow.x_plus_btn,self.mainWindow.x_minus_btn],
                          [self.mainWindow.z_plus_btn,self.mainWindow.z_minus_btn]]
        
        try:
            self.ser = Serial('COM6', baudrate=115200, timeout=2) # factory setting
            
            self.mainWindow.halt_stages_btn.clicked.connect(self.stop_stages)
            self.mainWindow.home_stages_btn.clicked.connect(self.home_stage)
            
            self.mainWindow.stage_set.clicked.connect(self.set_move)
            
            self.step_box[0].setValue(self.steps[0])
            self.step_box[1].setValue(self.steps[1])
            self.step_box[2].setValue(self.steps[2])
            self.step_box[0].valueChanged.connect(lambda axis:  self.step_changed(axis=0))
            self.step_box[1].valueChanged.connect(lambda axis:  self.step_changed(axis=1))
            self.step_box[2].valueChanged.connect(lambda axis:  self.step_changed(axis=2))
            
            self.step_button[0][0].clicked.connect(lambda args:  self.step_move(args=(0,1)))
            self.step_button[0][1].clicked.connect(lambda args: self.step_move(args=(0,-1)))
            self.step_button[1][0].clicked.connect(lambda args:  self.step_move(args=(1,1)))
            self.step_button[1][1].clicked.connect(lambda args: self.step_move(args=(1,-1)))
            self.step_button[2][0].clicked.connect(lambda args:  self.step_move(args=(2,1)))
            self.step_button[2][1].clicked.connect(lambda args: self.step_move(args=(2,-1)))
            
            self.stage_init()
            
    
            
            self.timer = QTimer()
            self.timer.setInterval(500) # refresh position info at 2 Hz
            self.timer.timeout.connect(self.get_positions)
            self.timer.start()
            
            print('Stage connected')
            
        except:
            self.ser=None
            
            self.mainWindow.stage_set.setEnabled(False)            
            self.mainWindow.halt_stages_btn.setEnabled(False)
            self.mainWindow.home_stages_btn.setEnabled(False)
            
            for i in range(3):
                self.pos_box[i].setEnabled(False)     
                self.pos_boxv[i].setEnabled(False)              
                self.step_box[i].setEnabled(False)
                self.step_button[i][0].setEnabled(False)
                self.step_button[i][1].setEnabled(False)
                
            print('Stage not available')
        
        
    def close(self):
        
        if self.ser:
            
            print('homing the stage...')
            #self.safe_move_axes(self.home)
            self.timer.stop()
            
            for axis in range(3):
                self.ser.write(("SVO "+str(axis+1)+" 0 \n").encode())
            
            self.ser.close()
            print('Stage disconnected')
            
        self.deleteLater()
    
        
    def get_positions(self):

        get_position_command=("POS?\n").encode()
        self.ser.write(get_position_command)
        
        for axis in range(3):
            
            v = float(self.ser.readline().decode()[2:])
            self.positions[axis] = (self.axis_signs[axis]*v) % self.axis_max[axis]-self.offsets[axis]
            self.pos_box[axis].setText(format(self.positions[axis],'.3f'))
            
    def home_stage(self):
        
        reply = QMessageBox.question(self.mainWindow, 'Home stage?', 'Do you want to move the stage home?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:        
            
            self.safe_move_axes(self.home)
    
    
    ### moving functions ###
        
    def move_axis(self,axis,pos):
                
        def move(axis,pos):
            
            new_pos=self.axis_signs[axis]*(pos + self.offsets[axis]) % self.axis_max[axis]
            move_command=("MOV "+str(axis+1)+" {} \n".format(new_pos)).encode()
            self.ser.write(move_command)
            
        
        if self.isValid(axis,pos) and not self.stop:   
            
            if (abs(pos-self.positions[axis])<15):
                
                move(axis,pos)
        
            else:
                
                self.set_acc(axis,10)
                move(axis,pos)
                self.wait()
                self.set_acc(axis,1)
                
            
    def safe_move_axes(self,target,safe=True):
        
        self.stop=False
        
        for axis in range(3):
            self.pos_boxv[axis].setValue(target[axis])    
        
        if safe:
            self.move_axis(2,self.home[2])
            self.wait()
            self.move_axis(1,target[1])
            self.move_axis(0,target[0])
            self.wait()                
            self.move_axis(2,target[2])
        else:
            self.move_axis(1,target[1])
            self.move_axis(0,target[0])
            self.move_axis(2,target[2])
            
        
        
    def isValid(self,axis,pos):
        
        
        # Allow the stage to go up only when the Y coordinate is  160 ± 5mm from the imaging center 
        
        if ((axis==2) and (pos>self.positions[axis]) and 
            ((self.positions[0]<(self.sample_y_pos-3)) or (self.positions[0]>(self.sample_y_pos+3)))):
               
            self.mainWindow.info_area.setText('Z moving up is only allowed when ' + str(self.sample_y_pos-3) +" <= Y <= " + str(self.sample_y_pos+3))                          
            return False
        
        # Forbid stage to move Y beyond 160 ± 5mm when Z is nonzero 
        
        if ((axis==0) and (self.positions[2]>0.01) and 
            ((pos<(self.sample_y_pos-5)) or (pos>(self.sample_y_pos+5)))):
               
            self.mainWindow.info_area.setText('Y movement beyond ' + str(self.sample_y_pos-3) +" <= Y <= " + str(self.sample_y_pos+3)
                                              +' is not allowed when Z>0.01')                          
            return False
        
        ## Check the value within the limit
        
        pos=pos+self.offsets[axis]
        
        
        if (pos>=self.tol[axis][0]) and (pos<=(self.axis_max[axis]-self.tol[axis][1])):
            return True
        
        else:
            self.mainWindow.info_area.setText(self.axis_names[axis]+' axis  beyond the range')
            self.mainWindow.info_area.append('The value should be between '+str(self.tol[axis][0]-self.offsets[axis]) 
                                             +' and ' +str(self.axis_max[axis]-self.tol[axis][1]-self.offsets[axis]))
            return False
        
    def wait(self):
        
        moving = True

        while moving:   
            QtTest.QTest.qWait(500)      # Check every .5 second     
            self.ser.write(b'\x05')
            s=int(self.ser.readline().decode("utf-8"))
            moving = False if s==0 else True
            
    
    #### Interface functions ####
    
    def set_move(self,axis): 
        
        
        target=[self.pos_boxv[axis].value() for axis in range(3)]
        XYdist=np.sqrt((target[0]-self.positions[0])**2+(target[1]-self.positions[1])**2)
        Zdist=np.abs(target)
        
        if XYdist>10:
            self.safe_move_axes(target)
        else:
            self.safe_move_axes(target,safe=False)
            
            
    
    def step_move(self,args): 
        
        axis      = args[0]
        direction = args[1] # sign should be 1 or -1
        
        self.stop=False
        #pos=self.positions[axis]+self.steps[axis]*direction
        pos=self.pos_boxv[axis].value()+self.steps[axis]*direction
        
        self.pos_boxv[axis].setValue(pos)    
        self.move_axis(axis,pos)    
        
        
    ### msc functions ###   
    
    
    def step_changed(self,axis):
        
        self.steps[axis] = self.step_box[axis].value()
        
    
    def stop_stages(self):
        
        self.stop=True
        
        stop_command = ("STP\n").encode()
        self.ser.write(stop_command)
        
        
    def set_acc(self,axis,scaling):
        
        self.ser.write(("ACC "+str(axis+1)+" {} \n".format(self.accs[axis]*scaling)).encode())
        self.ser.write(("DEC "+str(axis+1)+" {} \n".format(self.accs[axis]*scaling)).encode())
        
        
    def stage_init(self):
        
        ## initializing the stage
        
        for axis in range(3):
            self.ser.write(("SVO "+str(axis+1)+" 1 \n").encode())
         
        reference = 1
        self.ser.write("FRF? \n".encode())
        
        for axis in range(3):
            reference *= int(self.ser.readline().decode()[2])
        
        if reference==1:
            print('stage initialized')
        else:
                    
            print('stage not initialized')
            print('stage initialing...')
            self.ser.write(("FRF \n").encode())      ## This is extremely slow. Needs improvement
            self.wait()                 
            print('stage initialized')
        
        ## Setting preferences, homing stages
        
        for axis in range(3):
            self.ser.write(("VEL "+str(axis+1)+" {} \n".format(self.vels[axis])).encode())
            self.set_acc(axis,1)
        
        self.get_positions()
        print('homing the stage...')
        #self.safe_move_axes(target=self.home)
        self.wait()                 
        
        self.get_positions()
        for axis in range(3):
            self.pos_boxv[axis].setValue(self.positions[axis])
            
            
            
     