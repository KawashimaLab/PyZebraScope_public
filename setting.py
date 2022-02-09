# -*- coding: utf-8 -*-
"""
Created on Fri May  7 09:29:58 2021

@author: LS_User
"""



from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import QtTest  

import tkinter as tk
from tkinter import filedialog
import os
import xml.etree.cElementTree as ET
from xml.dom import minidom

class Setting(QObject):
    
    
    def __init__(self, parent=None):
        super().__init__()
        
        self.mainWindow=parent
        
        self.mainWindow.save_config_btn.clicked.connect(self.save_config)
        self.mainWindow.load_config_btn.clicked.connect(self.load_config)
        self.loading_file=""
        self.saving_file=""
        
        self.extension = [('xml', '*.xml')]
        
        root = tk.Tk()
        root.withdraw()
        
        self.signal_param_list=["cycle_duration","num_planes",
                         "ms_per_plane", "ms_exposure_per_plane",
                         "camera_first_trigger_v", "camera_trigger_v",
                         "piezo_start","piezo_end","piezo_shift",
                         "galvo1X_center", "galvo1X_width", 
                         "galvo1Y_start", "galvo1Y_end",    
                         "galvo2X_center", "galvo2X_width", 
                         "galvo2Y_start", "galvo2Y_end",    
                         "galvo3X_center", "galvo3X_width", 
                         "galvo3Y_start", "galvo3Y_end",
                         "laser1_enable", "laser2_enable", "laser3_enable"]
    
    def close(self):
        
        self.deleteLater()
    
    def save_config(self):
        
        self.saving_file = filedialog.asksaveasfilename(initialdir = self.mainWindow.root_dir+r'/config',
                                                        filetypes=self.extension, defaultextension=self.extension)
        
        if self.saving_file:
            
            self.write_imaging_params(self.saving_file)
            
            self.mainWindow.saved_setting_file.setText(r'config/'+os.path.basename(self.saving_file))
            self.mainWindow.setting_unsaved.setText("")
        
        
    def write_imaging_params(self,rec_info_file):
        

        root = ET.Element("root")
        doc = ET.SubElement(root, "imaging_params")
        # stage info
        ET.SubElement(doc, "Main_save_dir").text=self.mainWindow.save_dir
        
        # stage info
        ET.SubElement(doc, "StageY").text=str(self.mainWindow.stages.positions[0])
        ET.SubElement(doc, "StageX").text=str(self.mainWindow.stages.positions[1])
        ET.SubElement(doc, "StageZ").text=str(self.mainWindow.stages.positions[2])
        
        # camera info
        
        for cam in range(2):
            header='Camera'+str(cam+1)+'_'
                
            if self.mainWindow.cam_on_list[cam]:
                ET.SubElement(doc, header+"ON").text=str(1)
                ET.SubElement(doc, header+"Exposure").text=str(self.mainWindow.signals.ms_exposure_per_plane[0])                
                ET.SubElement(doc, header+"ROI").text = str(int(self.mainWindow.cam_list[cam].ROI))
                ET.SubElement(doc, header+"Width").text = str(self.mainWindow.cam_list[cam].roi_dims[3])
                ET.SubElement(doc, header+"Height").text= str(self.mainWindow.cam_list[cam].roi_dims[2])
            else:
                ET.SubElement(doc, header+"ON").text=str(0)             
                ET.SubElement(doc, header+"ROI").text = str(0)
                ET.SubElement(doc, header+"Exposure").text=str(0)
                ET.SubElement(doc, header+"Width").text  =str(0)
                ET.SubElement(doc, header+"Height").text =str(0)
                
        # filter info
        pos=self.mainWindow.nd_filters.pos
        for i in range(len(self.mainWindow.nd_filters.filter_list)):                
            ET.SubElement(doc, "NDFilter_"+str(i+1)+"_pos").text=str(pos[i])
            ET.SubElement(doc, "NDFilter_"+str(i+1)+"_name").text=str(self.mainWindow.nd_filters.filter_list[i][pos[i]-1])
        
        # piezo info
        ET.SubElement(doc, "Piezo_Autozero").text=str(self.mainWindow.piezo.autozero)
        ET.SubElement(doc, "Piezo_Servo").text=str(self.mainWindow.piezo.servo)
        
        # laser_info
        for i in range(len(self.mainWindow.lasers.laser_list)):                
            ET.SubElement(doc, "Laser_"+str(i+1)+'_name').text=self.mainWindow.lasers.laser_names[i]
            ET.SubElement(doc, "Laser_"+str(i+1)+'_ON').text=str(int(self.mainWindow.lasers.statuses[i]))
            ET.SubElement(doc, "Laser_"+str(i+1)+'_power').text=str(self.mainWindow.lasers.current_pows[i])
            mode=self.mainWindow.lasers.current_modes[i]
            ET.SubElement(doc, "Laser_"+str(i+1)+'_mode').text=str(mode)
            ET.SubElement(doc, "Laser_"+str(i+1)+'_mode_name').text=self.mainWindow.lasers.mode_box_item[i][mode]
        
        
        # signal_info

        for i in range(len(self.signal_param_list)):
            ET.SubElement(doc, 'Signal_'+self.signal_param_list[i]).text=str(self.mainWindow.signals.signal_parameter_list[i][0])
        
        
        # acquisition_info
        
        ET.SubElement(doc, "Scan_mode").text=str(self.mainWindow.scanning.scan_mode)
        ET.SubElement(doc, "Scan_mode_name").text="Plane" if self.mainWindow.scanning.scan_mode==0 else "Stack"
        ET.SubElement(doc, "Scan_stop_mode").text=str(self.mainWindow.scanning.stop_mode)
        ET.SubElement(doc, "Scan_stop_mode_name").text="Count" if self.mainWindow.scanning.stop_mode==0 else "Time" if self.mainWindow.scanning.stop_mode==1 else "None"          
        ET.SubElement(doc, "Scan_stop_count").text=str(self.mainWindow.scanning.limit_image)
        ET.SubElement(doc, "Scan_stop_time").text=str(self.mainWindow.scanning.limit_time) 
        
        tree = ET.ElementTree(root)
        tree.write(rec_info_file)
            
            
    def write_time_rec(self,rec_info_file,start_time, end_time):        
         
        tree = ET.parse(rec_info_file)
        
        root = tree.getroot()
        rec_info = ET.Element("rec_info")
         
        ET.SubElement(rec_info, "Recording_start_time").text = start_time
        ET.SubElement(rec_info, "Recording_stop_time").text  = end_time
        ET.SubElement(rec_info, "Recording_folder").text=self.mainWindow.exp_dir
         
        root.append(rec_info)
        tree.write(rec_info_file)
        
    def load_config(self):
        
        self.loading_file = filedialog.askopenfilename(initialdir = self.mainWindow.root_dir+r'/config',
                                                       filetypes=self.extension, defaultextension=self.extension)       
        
        if self.loading_file:
            
            #self.mainWindow.loaded_setting_file.setText(r'config/'+os.path.basename(self.loading_file))
            self.mainWindow.loaded_setting_file.setText(self.loading_file)
            
            try:
                
                xmldoc = minidom.parse(self.loading_file)
                
                ## savedir
                
                self.mainWindow.write_directory.setText(self.find_xml_element(xmldoc,'Main_save_dir'))
        
                ## stage_position
                
                print('Loading stage settings')
                
                self.mainWindow.stage_y_posv.setValue(float(self.find_xml_element(xmldoc,'StageY')))
                self.mainWindow.stage_x_posv.setValue(float(self.find_xml_element(xmldoc,'StageX')))
                self.mainWindow.stage_z_posv.setValue(float(self.find_xml_element(xmldoc,'StageZ')))
            
            
                # set camera
            
            
                for cam in range(2):
                    
                    header='Camera'+str(cam+1)+'_'
                    cam_on=int(self.find_xml_element(xmldoc,header+'ON'))
                    
                    if self.mainWindow.cam_on_list[cam]!=(cam_on==1):
                        
                        self.mainWindow.cam_check_list[cam].setChecked(cam_on==1)                
                        self.mainWindow.cam_switch(cam)                    
                        QtTest.QTest.qWait(500)
                        
                        self.mainWindow.cam_list[cam].start_cam_view()        
                        
                        QtTest.QTest.qWait(500)
                        
                        
                    if (cam_on==1) and (self.mainWindow.cam_on_list[cam]):
                        
                        
                        width=int(self.find_xml_element(xmldoc,header+"Width"))
                        height=int(self.find_xml_element(xmldoc,header+"Height"))
                        
                        self.mainWindow.cam_list[cam].cam_win.x_slide.setValue(width)
                        self.mainWindow.cam_list[cam].cam_win.y_slide.setValue(height)
                                     
                        ROI=int(self.find_xml_element(xmldoc,header+"ROI"))
                                                     
                        if ROI==1:
                            self.mainWindow.cam_list[cam].setROI()
                        
                    
                    # set nd filter
                    
                    print('Loading filter settings')
                    
                    for i in range(len(self.mainWindow.nd_filters.filter_list)):   
            
                        self.mainWindow.nd_filters.set_position(i,int(self.find_xml_element(xmldoc,"NDFilter_"+str(i+1)+"_pos")))
                    
                    
                    # set laser parameters
                    
                    print('Loading laser settings')
                    
                    for i in range(len(self.mainWindow.lasers.laser_list)):                
                        on_state = int(self.find_xml_element(xmldoc,"Laser_"+str(i+1)+'_ON'))==1 
                        power_state = int(self.find_xml_element(xmldoc,"Laser_"+str(i+1)+'_power'))
                        mode_state = int(self.find_xml_element(xmldoc,"Laser_"+str(i+1)+'_mode'))
                        
                        if self.mainWindow.lasers.sers[i]:
                            
                            self.mainWindow.lasers.checkbox_list[i].setChecked(on_state)
                            self.mainWindow.lasers.laser_switch(i)
                            QtTest.QTest.qWait(200)
                            self.mainWindow.lasers.slider_list[i][0].setValue(power_state)
                            QtTest.QTest.qWait(200)                    
                            self.mainWindow.lasers.mode_box_list[i].setCurrentIndex(mode_state)
                            QtTest.QTest.qWait(200)                    
                        
                    
                    # set signal parameters
                    
                    print('Loading imaging settings')
                    
                    for i in range(len(self.signal_param_list)):
                        
                        value=self.find_xml_element(xmldoc,'Signal_'+self.signal_param_list[i])
                        
                        if type(self.mainWindow.signals.signal_parameter_list[i][0])==bool:                    
                            self.mainWindow.signals.signal_parameter_box_list[i].setChecked(value=='True')
                            
                        elif type(self.mainWindow.signals.signal_parameter_list[i][0])==int:                    
                            self.mainWindow.signals.signal_parameter_box_list[i].setValue(int(value))
                            
                        else:                    
                            self.mainWindow.signals.signal_parameter_box_list[i].setValue(float(value))
                            
                        
                    # set acquisition parameters
                    
                    self.mainWindow.stop_count_box.setValue(int(self.find_xml_element(xmldoc,"Scan_stop_count")))
                    self.mainWindow.stop_time_box.setValue(int(self.find_xml_element(xmldoc,"Scan_stop_time")))
                    
                    self.mainWindow.scanning.stop_mode=int(self.find_xml_element(xmldoc,"Scan_stop_mode"))
                    self.mainWindow.stop_count.setChecked(self.mainWindow.scanning.stop_mode==0)
                    self.mainWindow.stop_time.setChecked(self.mainWindow.scanning.stop_mode==1)
                    self.mainWindow.stop_none.setChecked(self.mainWindow.scanning.stop_mode==2)
                    self.mainWindow.scanning.stop_mode_manage()
                    
                    self.mainWindow.scanning.scan_mode=int(self.find_xml_element(xmldoc,"Scan_mode"))
                    
                    if self.mainWindow.scanning.scan_mode==0:
                        self.mainWindow.scan_plane.setChecked(True)
                        
                    elif self.mainWindow.scanning.scan_mode==1:
                        self.mainWindow.scan_stack.setChecked(True)
    
                    self.mainWindow.scanning.scan_mode_manage()
                    
                
                    ### successfully loaded
                    
                    self.mainWindow.setting_load_error.setText('Settings successfully loaded')                    
                    self.mainWindow.setting_load_error.setStyleSheet('color: green')
                
                
            except:
                
                self.mainWindow.setting_load_error.setText('Error: xml format may be wrong')                
                self.mainWindow.setting_load_error.setStyleSheet('color: rgb(150, 0, 0)')
            
        
    
    def find_xml_element(self,doc,name):
        
        return doc.getElementsByTagName(name)[0].firstChild.data
            