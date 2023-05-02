import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42 # important for vector text output
matplotlib.rcParams['ps.fonttype'] = 42  # important for vector text output

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import medfilt
from scipy.optimize import minimize
from PyQt5 import QtCore, QtGui, QtWidgets, uic,QtTest
from PyQt5.QtCore import QThread, QObject
from PyQt5.QtCore import QThread, QObject
from PyQt5.QtWidgets import QWidget,QGridLayout
import h5py
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from scipy.interpolate import interp1d

import cupy as cp
import cupyx.scipy.ndimage as ndigpu

# from scipy.fft import fft2, fftshift
# from skimage.transform import warp_polar

class auto_focus_win(QtCore.QThread):
    
    
    def __init__(self,parent=None):
        
        QtCore.QThread.__init__(self)
        self.auto_focus_main=parent
        
    
    def setupUi(self, MainWindow):
        

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(350,700)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.layout = QGridLayout()
        self.centralwidget.setLayout(self.layout)
        self.vpercentile=100
        
        self.gv1 = QtWidgets.QGraphicsView(MainWindow)
        self.gv1.setObjectName("gv1")
        self.layout.addWidget(self.gv1,0,0,1,1)
        
        self.gv2 = QtWidgets.QGraphicsView(MainWindow)
        self.gv2.setObjectName("gv2")
        self.layout.addWidget(self.gv2,1,0,1,1)
        
        

        
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        
    def retranslateUi(self, MainWindow):
        
        self._translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(self._translate("MainWindow","AutoFocusing view"))
        
        

class AutoFocusing_GUI(QtWidgets.QMainWindow):
    
    # this class is necessary to defining closeEvent for GUI
    
    def __init__(self,parent=None):
        QtWidgets.QMainWindow.__init__(self)
        self.parent=parent

    def closeEvent(self, event):
        self.parent.close_af_view()
        self.close()
        

class Auto_focusing(QObject):
    
    
    def __init__(self, parent=None):
        super().__init__()
        
        self.scanning = parent
        self.mainWindow = parent.mainWindow
        
        self.auto_focusing_window = AutoFocusing_GUI(self) #QtWidgets.QMainWindow()
        self.af_window = auto_focus_win(self)
        self.af_window.setupUi(self.auto_focusing_window)
        self.af_thread = self.af_window
        
        self.subplot1 = QtWidgets.QGraphicsScene()
        self.subplot2 = QtWidgets.QGraphicsScene()
        self.af_window.gv1.setScene(self.subplot1)
        self.af_window.gv2.setScene(self.subplot2)
        self.axes1=None
        self.axes2=None
        self.br_threshold=150
        
        
        self.mainWindow.auto_focus_btn.clicked.connect(self.start_auto_focus)
        
        self.param_fields = [self.mainWindow.LE_cycle_duration, self.mainWindow.LE_num_planes, 
                             self.mainWindow.LE_time_plane, self.mainWindow.LE_exposure_plane,
                             self.mainWindow.LE_piezo_start,   self.mainWindow.LE_piezo_end,
                             self.mainWindow.LE_start_Y1,    self.mainWindow.LE_end_Y1,
                             self.mainWindow.LE_start_Y2,    self.mainWindow.LE_end_Y2,                                    
                             self.mainWindow.LE_laser1,      self.mainWindow.LE_laser2]
        
        self.stack_bin=5
        
        
    def close(self):
        
        self.auto_focusing_window.close()          
        self.deleteLater()
        
        
    def close_af_view(self):
        
        self.af_thread.terminate()
        self.af_thread.wait()
        
            
    def start_af_view(self):        
        if not self.af_thread.isRunning():
            self.af_thread.start()
        self.auto_focusing_window.show()
        
        
    
        
    def cupy_fft_transform_warp_polar(self,image):
    
        def warp_polar_gpu(image, radius):
            
            # This funciton was developed by Niels Cautaerts
            
            cx, cy = image.shape[1] / 2, image.shape[0] / 2
            output_shape = (360, radius)
            T = cp.linspace(0, 2*np.pi, output_shape[0]).reshape(output_shape[0], 1)
            R = cp.arange(output_shape[1]).reshape(1, output_shape[1])
            X = R * cp.cos(T) + cx
            Y = R * cp.sin(T) + cy
            coordinates = cp.stack([Y, X])
            polar = ndigpu.map_coordinates(image, coordinates, order=1)
            
            return polar
        
        radius = int(np.ceil(np.sqrt((image.shape[0] / 2)**2 + (image.shape[1] / 2)**2)))
        img_polar = np.zeros((image.shape[0], 360, radius))    
        
        for i in range(image.shape[0]):
            
            tmp=cp.absolute(cp.fft.fftshift(cp.fft.fft2(cp.asarray(image[i]))))
            img_polar[i]= warp_polar_gpu(tmp,radius).get()
            
        return img_polar
    
    
    
    # def fft_transform(image): # function for CPU
    #     img_fft = np.zeros(image.shape)    
    #     for i in range(image.shape[0]):
    #         img_fft[i] = np.abs(fftshift(fft2(image[i])))
    #     return img_fft
    
    
    # def polar_tform(image, radius=600): # function for CPU
    #     # radius = 2000
    #     img_polar = np.zeros((image.shape[0], 360, radius))
    #     for i in range(image.shape[0]):
    #         img_polar[i] = warp_polar(image[i], radius=radius)  #, scaling='log')
    #     return img_polar
    
    
    def projection_img(self,image):
        
        img_project = np.zeros((image.shape[0], image.shape[2]))
        for i in range(image.shape[0]):
            img_project[i] = np.log((np.sum(image[i], axis=0)))
        return img_project
    
    
    def focus_measure(self,image):
        img_measure = np.zeros(image.shape[0])
    
        base_ind=int(image.shape[1]*0.5)
        for i in range(image.shape[0]):
            
            baseline=image[i][base_ind:]
            inds=np.where(medfilt(image[i][:base_ind],11)<(baseline.mean()+baseline.std()*3))[0]
            if isinstance(inds, np.ndarray):           
                img_measure[i] = inds.min()
            else:
                img_measure[i] = 0
            
        return img_measure
    
    def detect_peak(self,trace):
        
        def func(x,args):
            
            target=args
            x_axis=np.arange(len(target))
    
            y=np.exp(-x[0]*(x_axis-x[1])**2)
            
            return np.sum((target-y)**2)
        
        trace_norm=(trace-trace.min())/(trace.max()-trace.min())
        x_init=[0.001,len(trace)/2]
        x_bound=[[0,0.01],[5,len(trace)-5]]
        result=minimize(func, x_init, args=(trace_norm), method='L-BFGS-B',bounds=x_bound)
        
        x=np.arange(len(trace_norm))
        
        self.subplot1.clear()
        self.panel1 = Figure(figsize=(3,3))
        self.axes1 = self.panel1.gca()
        self.axes1.set_position([0.2,0.15,0.75,0.8])
        self.canvas1 = FigureCanvas(self.panel1)
        self.subplot1.addWidget(self.canvas1)
        
        self.axes1.cla()
        self.axes1.plot(x-20, trace_norm,'o')
        self.axes1.plot(x-20,np.exp(-result.x[0]*(x-result.x[1])**2))
        self.axes1.plot([result.x[1]-20,result.x[1]-20],[0,1],'r:')
        self.axes1.set_ylabel('Resolution measure')
        self.axes1.set_xlabel('Searched plane (μm)')
        
        
        return int(result.x[1])
        
    
    def detect_best_focus(self,stack):
        
        
        img_polar = self.cupy_fft_transform_warp_polar(stack) # for GPU
              
        # img_fft = fft_transform(img) # for CPU
        # img_polar = polar_tform(img_fft) # for CPU
        
        img_project = self.projection_img(img_polar)
        img_mea     = self.focus_measure(img_project)
        best_plane  = self.detect_peak(img_mea)
        
        return best_plane
    
    
    def load_original_parameters(self):
        
        params=[]
        for i in range(len(self.param_fields)):
            
            if i<len(self.param_fields)-2:                            
                params.append(self.param_fields[i].value())     
            else:
                params.append(self.param_fields[i].isChecked())    
                
        return params
                
    
    def set_parameters(self,params):
    
        for i in range(len(self.param_fields)-2):
            self.param_fields[i].setValue(params[i])        
            
        for i in range(len(self.param_fields)-2,len(self.param_fields)):
            self.param_fields[i].setChecked(params[i])
            
    def create_autofocus_parameters(self,original_params,l,p,y1,y2,):
    
        autofocus_params = [1000,41,20,20,
                            p,p, # stop piezo
                            y1-20 if l==0 else original_params[6],
                            y1+20 if l==0 else original_params[7],
                            y2-20 if l==1 else original_params[8],
                            y2+20 if l==1 else original_params[9],
                            l==0,
                            l==1]
        
        return autofocus_params
    
    
    def execute_auto_focus(self,original_params,autofocus_params):
        
        
        self.set_parameters(autofocus_params)
        
        original_scan_mode= self.scanning.scan_mode
        self.scanning.scan_mode=1
        
        # get stack
        self.scanning.startScanning()        
        while self.scanning.scan_started:
            QtTest.QTest.qWait(100)
            
        for cam in range(2):
            if self.mainWindow.cam_on_list[cam]:
                stack=self.mainWindow.cam_list[cam].sample_stack     
        
        ## put back parameters
        
        self.scanning.scan_mode = original_scan_mode
        self.set_parameters(original_params)
                            
                
        stack_max=stack.max(axis=0)
        y_range=np.where(stack_max.max(axis=1)>self.br_threshold)[0]
        x_range=np.where(stack_max.max(axis=0)>self.br_threshold)[0]
        
        if ((y_range[-1]-y_range[0])<200) or ((x_range[-1]-x_range[0])<200):
            
            peak_ind=np.unravel_index(np.argmax(gaussian_filter(stack_max,20)),stack_max.shape)
            y_range[0]  = max(peak_ind[0]-100,0)
            y_range[-1] = min(peak_ind[0]+100,stack_max.shape[0]-1)
            x_range[0]  = max(peak_ind[1]-100,0)
            x_range[-1] = min(peak_ind[1]+100,stack_max.shape[1]-1)
        
        
        focus_stack=stack[:,y_range[0]:y_range[-1],:][:,:,x_range[0]:x_range[-1]]
        
        
        
        best_plane = self.detect_best_focus(focus_stack)
        
        return best_plane

    
    def start_auto_focus(self):
        
        self.start_af_view()
        
        self.mainWindow.auto_focus_btn.setEnabled(False)
        self.autofocus=True
        
        for cam in range(2):
            if self.mainWindow.cam_on_list[cam]:
                self.autofocus=True
                
                
        
        if self.autofocus:
            
            laser_on=[self.mainWindow.LE_laser1.isChecked(), self.mainWindow.LE_laser2.isChecked()]

            if self.scanning.scan_mode==0:   
            
                for l in range(2):
                    
                    if laser_on[l]:
                        
                        self.mainWindow.auto_focus_btn.setText('Focusing Arm'+str(l+1))
                        
                        original_params=self.load_original_parameters()  
                        autofocus_params=self.create_autofocus_parameters(original_params,l,original_params[4],original_params[6],original_params[8])                               
                        best_plane=self.execute_auto_focus(original_params,autofocus_params)
                        
                        self.param_fields[l*2+6].setValue(autofocus_params[l*2+6]+best_plane)
                        
                        for cam in range(2):
                            if self.mainWindow.cam_on_list[cam]:
                                stack=self.mainWindow.cam_list[cam].cam_win.z_slider.setValue(best_plane+1) 
                        
            else:   
            
                self.subplot2.clear()
                self.panel2 = Figure(figsize=(3,3))
                self.axes2 = self.panel2.gca()
                self.axes2.set_position([0.2,0.15,0.75,0.8])
                        
                legend_names=[]
                        
                for l in range(2):
                    
                    if laser_on[l]:
                        
                        self.mainWindow.auto_focus_btn.setText('Focusing Arm'+str(l+1))
                        
                        original_params=self.load_original_parameters()  
                        
                        p_pos_list=[]
                        y_init_pos_list=[]
                        y_best_pos_list=[]
                        
                        for i in range(self.stack_bin):
                            p_pos  = original_params[4]+(original_params[5]-original_params[4])/(self.stack_bin-1)*i
                            y1_pos = original_params[6]+(original_params[7]-original_params[6])/(self.stack_bin-1)*i
                            y2_pos = original_params[8]+(original_params[9]-original_params[8])/(self.stack_bin-1)*i
                            autofocus_params=self.create_autofocus_parameters(original_params,l,p_pos,y1_pos,y2_pos)
                               
                            best_plane=self.execute_auto_focus(original_params,autofocus_params)
                            
                            p_pos_list.append(p_pos)
                            y_init_pos_list.append(y1_pos if l==0 else y2_pos)
                            y_best_pos_list.append(y1_pos-20+best_plane if l==0 else y2_pos-20+best_plane)
                            
                            for cam in range(2):
                                if self.mainWindow.cam_on_list[cam]:
                                    stack=self.mainWindow.cam_list[cam].cam_win.z_slider.setValue(best_plane+1) 
                            
                        self.param_fields[l*2+6].setValue(y_best_pos_list[0])
                        self.param_fields[l*2+7].setValue(y_best_pos_list[self.stack_bin-1])
                            
                        
                        x_interp=np.linspace(p_pos_list[0],p_pos_list[self.stack_bin-1],100)
                        y_interp        = np.linspace(y_best_pos_list[0],y_best_pos_list[self.stack_bin-1],100)
                        y_interp_binned = np.linspace(y_best_pos_list[0],y_best_pos_list[self.stack_bin-1],self.stack_bin)
                        

                        
                        if l==0:
                            self.mainWindow.signals.galvoY1_interpf = interp1d(y_interp_binned,y_best_pos_list,kind='quadratic',bounds_error=False,fill_value="extrapolate") # conversion function
                            y_interp_conv = self.mainWindow.signals.galvoY1_interpf(y_interp)
                            self.mainWindow.af_status_1.setText('Set')
                            self.mainWindow.af_status_1.setStyleSheet('color: green')
                        else:
                            self.mainWindow.signals.galvoY2_interpf = interp1d(y_interp_binned,y_best_pos_list,kind='quadratic',bounds_error=False,fill_value="extrapolate")# conversion function
                            y_interp_conv = self.mainWindow.signals.galvoY2_interpf(y_interp)
                            self.mainWindow.af_status_2.setText('Set')
                            self.mainWindow.af_status_2.setStyleSheet('color: green')
                    
                        self.canvas2 = FigureCanvas(self.panel2)
                        self.subplot2.addWidget(self.canvas2)
                    
                        if l==0:
                            self.axes2.plot(p_pos_list,y_best_pos_list,'mo',fillstyle='none')
                            legend_names.append('Beam 1')
                        else:
                            self.axes2.plot(p_pos_list,y_best_pos_list,'co',fillstyle='none')
                            legend_names.append('Beam 2')                            
                            
                        if l==0:
                            self.axes2.plot(x_interp,y_interp_conv,'m',linewidth=1, label='_nolegend_')                            
                        else:
                            self.axes2.plot(x_interp,y_interp_conv,'c',linewidth=1, label='_nolegend_')  
                        
                        self.axes2.set_ylabel('Y Galvo position (μm)')
                        self.axes2.set_xlabel('Piezo position (μm)')
                        
                
                self.axes2.legend(legend_names)
                    
            self.autofocus=False
        
        self.mainWindow.auto_focus_btn.setEnabled(True)
        self.mainWindow.auto_focus_btn.setText('Auto focus') 
        
    

                    
        
