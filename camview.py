# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'camwindow.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QWidget,QGridLayout
import pyqtgraph as pg
import numpy as np


#import sys
#sys.path.append('C:\\Program Files\\Micro-Manager-2.0beta')
#import MMCorePy
class CamView_Event(pg.ImageView):
    

    
    updateSignal = QtCore.pyqtSignal()
    
    def __init__(self, parent=None, camthread=None, **kargs):
        pg.ImageView.__init__(self, **kargs)
        
        self.setWindowTitle('Cam View')
        self.parent=parent
        self.camthread=camthread
        
        self.timer = pg.QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        
        #<--- define the center of the ROI --->
        self.origin = self.camthread.parent.max_size
        self.current_roi = pg.RectROI([self.origin[1]/2-20,self.origin[0]/2-20],[40,40], movable=False)
        self.ui.menuBtn.hide()
        self.ui.roiBtn.hide()
        self.ui.histogram.hide()
        self.addItem(self.current_roi)
        self.setImage(self.camthread.parent.image_buffer)
        self.pci=QtWidgets.QGraphicsEllipseItem(0, 0, 15, 15)
        self.pci.setPen(pg.mkPen(color=(255, 0, 0, 100),width=2))
        self.addItem(self.pci)
        
        self.scene.sigMouseClicked.connect(self.mouse_clicked)
        
        
    def update(self):
        
        self.updateSignal.emit()
        
    
    def region_changed(self):
        
        self.roi_size = self.current_roi.size()
        self.origin= self.current_roi.pos()
        self.roi_dimensions=[self.round_16(self.origin[1]),self.round_16(self.origin[0]),self.round_16(self.roi_size[1]),self.round_16(self.roi_size[0])] # dim0 y, dim1 x
        self.current_roi.show()
        
    def round_16(self,x):
        return 16*round(x/16)
    
    def mouse_clicked(self, evt):
        
        pos = self.getImageItem().mapFromScene(evt.pos())
        
        shape = self.camthread.parent.image_buffer.shape
        if (min(pos.x(),pos.y())>8) & (pos.x()<(shape[0]-8)) & (pos.y()<(shape[1]-8)):
            self.camthread.parent.cursor_pos[0]=int(pos.x())
            self.camthread.parent.cursor_pos[1]=int(pos.y())
            
            self.removeItem(self.pci)
            self.pci = QtWidgets.QGraphicsEllipseItem(pos.x()-8, pos.y()-8, 15, 15)
            self.pci.setPen(pg.mkPen(color=(255, 0, 0, 100),width=2))
            self.addItem(self.pci)
            
            self.camthread.parent.cam_win.cursor_pos.setText('('+str(int(pos.x()))+','+str(int(pos.y()))+')')


class CamView(QtCore.QThread):
    
    
    def __init__(self,parent=None):
        
        QtCore.QThread.__init__(self)
        self.cam_main=parent
        self.max_size=self.cam_main.max_size
        
    
    def setupUi(self, MainWindow):
        
        ## loacing Designer GUI for here was technically challenging.
        # So we write it down
        

        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        MainWindow.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(784, 772)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.master_layout = QGridLayout()
        self.centralwidget.setLayout(self.master_layout)
        
        MainWindow.setWindowTitle("Camera #" + str(self.cam_main.cam_number) + " View")
        
        # defining image widget class
        
        self.image_layout = QGridLayout()        
        #self.imv = CamView_Event(self.centralwidget,camthread=MainWindow)
        self.imv = CamView_Event(parent=self,camthread=MainWindow)
        self.master_layout.addLayout(self.image_layout,0,0,1,1)
        self.image_layout.addWidget(self.imv,0,0,1,1)
        #self.imv.setGeometry(QtCore.QRect(20, 10, 751, 441))
        self.imv.setObjectName("imv")
        self.imv.adjustSize()
        
        self.z_slider_box = QtWidgets.QWidget(MainWindow)
        self.z_slider_box.setObjectName("z_slider_box")
        self.image_layout.addWidget(self.z_slider_box,0,1,1,1)
        self.image_layout.setColumnMinimumWidth(1,80)
        self.image_layout.setColumnStretch(0,1)
        self.image_layout.setColumnStretch(1,0)
        
        
        self.z_slider = QtWidgets.QSlider(self.z_slider_box)
        self.z_slider.setGeometry(QtCore.QRect(5, 100, 20, 300))
        self.z_slider.setMaximum(45) # default of the software
        self.z_slider.setMinimum(1)
        self.z_slider.setValue(1)
        self.z_slider.setSingleStep(1)
        self.z_slider.setOrientation(QtCore.Qt.Vertical)
        self.z_slider.setInvertedAppearance(True)
        self.z_slider.setObjectName("z_slider")
        self.z_plane=1
        self.z_slider.setEnabled(False)
        
        self.z_slider_label = QtWidgets.QLabel(self.z_slider_box)
        self.z_slider_label.setGeometry(QtCore.QRect(30, 200, 50, 20))
        self.z_slider_label.setFont(font)
        self.z_slider_label.setText("Z plane")
        self.z_slider_label.setObjectName("z_slider_label")
        
        self.z_plane_num = QtWidgets.QLabel(self.z_slider_box)
        self.z_plane_num.setGeometry(QtCore.QRect(50, 220, 20, 20))
        #self.z_plane_num.setFont(font)
        self.z_plane_num.setText("1")
        self.z_plane_num.setObjectName("z_plane_num")
        
        self.cursor_label = QtWidgets.QLabel(self.z_slider_box)
        self.cursor_label.setGeometry(QtCore.QRect(10,420, 60, 20))
        self.cursor_label.setFont(font)
        self.cursor_label.setText("Cursor")
        self.cursor_label.setObjectName("cursor_label")
        
        self.cursor_label2 = QtWidgets.QLabel(self.z_slider_box)
        self.cursor_label2.setGeometry(QtCore.QRect(10,433, 60, 20))
        self.cursor_label2.setFont(font)
        self.cursor_label2.setText("Value")
        self.cursor_label2.setObjectName("cursor_label2")
        
        
        self.cursor_pos = QtWidgets.QLabel(self.z_slider_box)
        self.cursor_pos.setGeometry(QtCore.QRect(10, 453, 60, 20))
        self.cursor_pos.setText('(0,0)')
        self.cursor_pos.setObjectName("cursor_pos")
        
        self.cursor_value = QtWidgets.QLabel(self.z_slider_box)
        self.cursor_value.setGeometry(QtCore.QRect(10, 468, 60, 20))
        self.cursor_value.setFont(font)
        self.cursor_value.setText("0")
        self.cursor_value.setObjectName("cursor_value")
        
        
        
        # defining button widget class
        
        self.buttonwidget = QtWidgets.QWidget(MainWindow)
        self.buttonwidget.setObjectName("buttonwidget")
        self.master_layout.addWidget(self.buttonwidget,1,0,1,1)
        self.master_layout.setRowStretch(0,1)
        self.master_layout.setRowStretch(1,0)
        self.master_layout.setRowMinimumHeight(1,240)
        
        
        self.line = QtWidgets.QFrame(self.buttonwidget)
        self.line.setGeometry(QtCore.QRect(20, 0, 751, 10))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        
        
        self.startStream_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.startStream_btn.setGeometry(QtCore.QRect(120, 50, 80, 51))
        self.startStream_btn.setObjectName("startStream_btn")
        self.startStream_btn.setText("Start Stream")
        
        
        self.capture_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.capture_btn.setGeometry(QtCore.QRect(220, 50, 80, 51))
        self.capture_btn.setObjectName("capture_btn")
        self.capture_btn.setText("Capture")
        
        self.stopStream_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.stopStream_btn.setGeometry(QtCore.QRect(20, 50, 80, 51))
        self.stopStream_btn.setObjectName("stopStream_btn")
        self.stopStream_btn.setText("Stop Stream")
        
        self.resetROI_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.resetROI_btn.setGeometry(QtCore.QRect(120, 120, 80, 51))
        self.resetROI_btn.setObjectName("resetROI_btn")
        self.resetROI_btn.setText("Reset ROI")
        
        self.setROI_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.setROI_btn.setGeometry(QtCore.QRect(20, 120, 80, 51))
        self.setROI_btn.setObjectName("setROI_btn")
        self.setROI_btn.setText("Set ROI")
        
        
        self.pushROI_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.pushROI_btn.setGeometry(QtCore.QRect(440, 120, 80, 51))
        self.pushROI_btn.setObjectName("pushROI_btn")
        self.pushROI_btn.setText("Push ROI \n to Cam"+str(3-self.cam_main.cam_number))
        
        self.overlay_btn = QtWidgets.QPushButton(self.buttonwidget)
        self.overlay_btn.setGeometry(QtCore.QRect(540, 120, 80, 51))
        self.overlay_btn.setObjectName("overlay_btn")
        self.overlay_btn.setText("Overlay")
        
        
        self.max_frame_rate_label = QtWidgets.QLabel(self.buttonwidget)
        self.max_frame_rate_label.setGeometry(QtCore.QRect(320, 90, 220, 20))
        self.max_frame_rate_label.setFont(font)
        self.max_frame_rate_label.setObjectName("max_frame_plane_label")        
        self.max_frame_rate_label.setText("(Max rate: )")
        
        self.cur_frame_rate_label = QtWidgets.QLabel(self.buttonwidget)
        self.cur_frame_rate_label.setGeometry(QtCore.QRect(320, 70, 220, 20))
        self.cur_frame_rate_label.setFont(font)
        self.cur_frame_rate_label.setText("Curr. rate: ")
        self.cur_frame_rate_label.setObjectName("cur_frame_plane_label")
        
        self.image_size = QtWidgets.QLabel(self.buttonwidget)
        self.image_size.setGeometry(QtCore.QRect(320, 50, 220, 20))
        self.image_size.setFont(font)
        self.image_size.setObjectName("image_size")
        self.image_size.setText("Image Size : ")
        
        
        self.x_slide_label = QtWidgets.QLabel(self.buttonwidget)
        self.x_slide_label.setGeometry(QtCore.QRect(180, 190, 220, 20))
        self.x_slide_label.setFont(font)
        self.x_slide_label.setText("Horizontal size")
        self.x_slide_label.setObjectName("x_slide_label")
        
        self.y_slide_label = QtWidgets.QLabel(self.buttonwidget)
        self.y_slide_label.setGeometry(QtCore.QRect(450, 190, 220, 20))
        self.y_slide_label.setFont(font)
        self.y_slide_label.setText("Vertical size")
        self.y_slide_label.setObjectName("y_slide_label")
        
        self.size_x = QtWidgets.QLabel(self.buttonwidget)
        self.size_x.setGeometry(QtCore.QRect(280, 190, 50, 20))
        self.size_x.setFont(font)
        self.size_x.setText("")
        self.size_x.setObjectName("size_x")
        self.size_y = QtWidgets.QLabel(self.buttonwidget)
        self.size_y.setGeometry(QtCore.QRect(550, 190, 50, 20))
        self.size_y.setFont(font)
        self.size_y.setText("")
        self.size_y.setObjectName("size_y")
        
        self.x_slide = QtWidgets.QSlider(self.buttonwidget)
        self.x_slide.setGeometry(QtCore.QRect(160, 220, 221, 20))
        self.x_slide.setMaximum(self.max_size[0])
        self.x_slide.setMinimum(0)
        self.x_slide.setSingleStep(4)
        self.x_slide.setOrientation(QtCore.Qt.Horizontal)
        self.x_slide.setObjectName("x_slide")
        
        self.y_slide = QtWidgets.QSlider(self.buttonwidget)
        self.y_slide.setGeometry(QtCore.QRect(440, 220, 221, 20))
        self.y_slide.setMaximum(self.max_size[1])
        self.y_slide.setMinimum(0)
        self.y_slide.setSingleStep(4)
        self.y_slide.setOrientation(QtCore.Qt.Horizontal)
        self.y_slide.setObjectName("y_slide")
        
        
        self.auto_scale = QtWidgets.QCheckBox(self.buttonwidget)
        self.auto_scale.setGeometry(QtCore.QRect(400, 10, 140, 21))
        self.auto_scale.setObjectName("auto_scale")
        self.auto_scale.setText("AutoScale image")
        self.auto_scale.setChecked(True)
        self.auto_scale.setFont(font)
        
        self.warning = QtWidgets.QLabel(self.buttonwidget)
        self.warning.setGeometry(QtCore.QRect(10, 10, 280, 21))
        self.warning.setObjectName("warning")
        self.warning.setFont(font)
        self.warning.setStyleSheet('color: rgb(150, 0, 0)')      
        
        self.br_label = QtWidgets.QLabel(self.buttonwidget)
        self.br_label.setGeometry(QtCore.QRect(650, 10, 120, 20))
        self.br_label.setFont(font)
        self.br_label.setText("Adjust brightness")
        self.br_label.setObjectName("br_label")
        
        self.br_slide = QtWidgets.QSlider(self.buttonwidget)
        self.br_slide.setGeometry(QtCore.QRect(660, 40, 22, 120))
        self.br_slide.setMaximum(100)
        self.br_slide.setMinimum(0)
        self.br_slide.setValue(100)
        self.br_slide.setSingleStep(1)
        self.br_slide.setOrientation(QtCore.Qt.Vertical)
        self.br_slide.setObjectName("br_slide")
        
        self.br_perc = QtWidgets.QLabel(self.buttonwidget)
        self.br_perc.setGeometry(QtCore.QRect(655, 170, 25, 21))
        self.br_perc.setObjectName("br_perc")
        self.br_perc.setText("100")
        self.br_perc.setEnabled(False)
        
        self.br_perc_label = QtWidgets.QLabel(self.buttonwidget)
        self.br_perc_label.setGeometry(QtCore.QRect(680, 170, 20, 20))
        self.br_perc_label.setText("%")
        self.br_perc_label.setEnabled(False)
        
        self.br_absolute = QtWidgets.QCheckBox(self.buttonwidget)
        self.br_absolute.setGeometry(QtCore.QRect(700, 105, 80, 21))
        self.br_absolute.setObjectName("br_absolute")
        self.br_absolute.setText("Absolute")
        
        self.br_max = QtWidgets.QSpinBox(self.buttonwidget)
        self.br_max.setGeometry(QtCore.QRect(700, 40, 55, 21))
        self.br_max.setObjectName("br_max")
        self.br_max.setValue(200)
        self.br_max.setMaximum(99999)
        self.br_max.setMinimum(0)
        
        self.br_min = QtWidgets.QSpinBox(self.buttonwidget)
        self.br_min.setGeometry(QtCore.QRect(700, 170, 55, 21))
        self.br_min.setObjectName("br_min")
        self.br_min.setValue(0)
        self.br_min.setMaximum(99999)
        self.br_min.setMinimum(0)
        
        self.br_max_label = QtWidgets.QLabel(self.buttonwidget)
        self.br_max_label.setGeometry(QtCore.QRect(700, 60, 55, 20))
        self.br_max_label.setFont(font)
        self.br_max_label.setText("max")
        
        self.br_min_label = QtWidgets.QLabel(self.buttonwidget)
        self.br_min_label.setGeometry(QtCore.QRect(700, 150, 55, 20))
        self.br_min_label.setFont(font)
        self.br_min_label.setText("min")
        
        
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 784, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
    
                
        self.setROI_btn.clicked.connect(self.cam_main.setROI)
        self.pushROI_btn.clicked.connect(self.cam_main.pushROI)
        self.overlay_btn.clicked.connect(self.cam_main.setOverlay)
        self.resetROI_btn.clicked.connect(self.cam_main.resetROI)
        self.stopStream_btn.clicked.connect(self.cam_main.stopStream)
        self.startStream_btn.clicked.connect(self.cam_main.startStream)
        self.capture_btn.clicked.connect(self.cam_main.capture)
        
        self.x_slide.setValue(40)
        self.y_slide.setValue(40)
        self.size_x.setText(str(40))
        self.size_y.setText(str(40))
        
        self.z_slider.valueChanged.connect(self.z_slider_changed)
        self.x_slide.valueChanged.connect(self.sliders_changed)
        self.y_slide.valueChanged.connect(self.sliders_changed)
        self.br_slide.valueChanged.connect(self.br_slider_changed)
        self.br_max.valueChanged.connect(self.br_max_changed)
        self.br_min.valueChanged.connect(self.br_min_changed)
        self.br_absolute.clicked.connect(self.br_absolute_clicked)
        
        

    
    def sliders_changed(self):
        
        x = int(np.floor(self.x_slide.value()/4))*4
        y = int(np.floor(self.y_slide.value()/4))*4
        self.size_x.setText(str(x))
        self.size_y.setText(str(y))
        
        self.rx = self.cam_main.roi_dims[3]/2 - x/2
        self.ry = self.cam_main.roi_dims[2]/2 - y/2
        
        self.imv.current_roi.setPos(self.rx,self.ry) # dim 0 x, dim 1 y
        self.imv.current_roi.setSize([x,y])
        self.imv.region_changed()
        
        self.image_size.setText('Image Size : H'+str(self.imv.roi_dimensions[3])+' x V'+str(self.imv.roi_dimensions[2]))
        
        self.cam_main.max_frame_rate=self.cam_main.calc_max_frame_rate(x)        
        self.max_frame_rate_label.setText("(Max rate: {:.1f}/s, ".format(self.cam_main.max_frame_rate)+ "{:.1f} ms/fr.)".format(1000/self.cam_main.max_frame_rate))
        
        
    def z_slider_changed(self):
        self.z_plane = int(self.z_slider.value())
        self.z_plane_num.setText(str(self.z_plane))
        
        if not self.cam_main.mmc.isSequenceRunning():
            
            self.cam_main.pix_buffer = self.cam_main.sample_stack[self.z_plane-1,:,:]
            br_max = self.cam_main.pix_buffer.max()
            br_min = self.cam_main.pix_buffer.min()
            
            
            if br_max>br_min:
                self.cam_main.set_disp_params()
                self.cam_main.set_image()
                
        
    def br_slider_changed(self):
        self.cam_main.vpercentile = self.br_slide.value()
        self.cam_main.set_disp_params()
        self.cam_main.set_image()
        
        
    def br_max_changed(self):
        
        if self.cam_main.vabsolute:
            self.cam_main.br_max = self.br_max.value()
            self.cam_main.set_disp_params()
            self.cam_main.set_image()
                
        
    def br_min_changed(self):
        
        if self.cam_main.vabsolute:
            self.cam_main.br_min = self.br_min.value()            
            self.cam_main.set_disp_params()
            self.cam_main.set_image()
                
    
        
    def br_absolute_clicked(self):
        
        state=self.br_absolute.isChecked()
        self.cam_main.vabsolute = state
        self.cam_main.update_br_console()

        
