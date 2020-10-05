#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
pip3 freeze > requirements.txt


Qt Grafik
https://likegeeks.com/pyqt5-drawing-tutorial/
# Plot !!!
https://www.learnpyqt.com/courses/qt-creator/embed-pyqtgraph-custom-widgets-qt-app/

Designer nach Aenderung aufrufen
pyuic5 -o main_win.py main_win.ui

"""

import sys
import random
import serial
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtCore, QtGui , QtWidgets
from PyQt5.QtWidgets import *
#from PyQt5.QtGui import *
from PyQt5 import *
from PyQt5.QtGui import QPainter, QColor, QPen, qRgb
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import numpy as np
from numpy import arange, sin, pi
from scipy import signal

# https://pyqtgraph.readthedocs.io/en/latest/
from pyqtgraph import PlotWidget
import pyqtgraph as pg


from main_win import Ui_MainWindow


class MyMainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args):
        QtWidgets.QMainWindow.__init__(self, *args)
        self.debug = True
        self.locked = False
        self.usbConnect = False
        self.serial = None
        # Defaults
        self.d1Duty = 50
        self.d2Duty = 50
        self.d3Duty = 50
        self.frequency   = 800
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.centerOnScreen()
        self.setStyleSheet("QStatusBar{padding-left:8px;color:blue;font-weight:normal;}")
        self.statusBar().showMessage('Ready')
        self.uiSetup()
        self.createConnects()
        self.connectUsb()
        self.readUsb()
    # enddef

    def readUsb(self):
        if self.usbConnect:
            h = self.serial.write("read".encode())  # read current Values
            self.serial.flush()  # it is buffering. required to get the data out *now*
            readBytes = self.serial.readline().decode(encoding='UTF-8')
            print(readBytes)
            if len(readBytes.split(','))==5:
                print("Freq=",readBytes.split(',')[0])
                print("D1= ",readBytes.split(',')[1])
                #self.d1Duty = int(readBytes.split(',')[1].split(':'))

    def connectUsb(self):
        try:
            self.serial = serial.Serial(str(self.ui.comboBox.currentText()), baudrate = 9600)
            self.usbConnect = True
            self.statusBar().showMessage("Connect to "+self.ui.comboBox.currentText()+" Ok")
        except serial.SerialException as e:
            self.statusBar().showMessage(str(e))
            self.usbConnect = False

    def uiSetup(self):
        # 3.10 neu, nur Widget , plot ist im Qt-Designer zugeordnet
        self.plot(self.ui.pwm1View, (self.d1Duty/100),1)
        self.plot(self.ui.pwm2View, (self.d2Duty/100),2)
        self.plot(self.ui.pwm3View, (self.d3Duty/100),3)

        self.ui.edit_duty1.setText(str(self.d1Duty))
        self.ui.edit_duty2.setText(str(self.d2Duty))
        self.ui.edit_duty3.setText(str(self.d3Duty))
        self.ui.edit_freq.setText(str(self.frequency))

        self.ui.f1Button.setChecked(True)
        self.ui.freqSlider.setMinimum(0)
        self.ui.freqSlider.setMaximum(999)
        self.ui.freqSlider.setValue(800)

        self.setSlider(self.ui.sl_pwm1)
        self.setSlider(self.ui.sl_pwm2)
        self.setSlider(self.ui.sl_pwm3)

        self.ui.comboBox.addItems(["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2"])
    #enddef

    def update_freq_sl(self,value):
        self.ui.edit_freq.setText(str(value))

    def update_freq(self):
        value = self.getEditValue(self.ui.edit_freq)
        self.ui.freqSlider.setValue(value)

    def lockClicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.locked = True
            self.update_duty1()
            self.ui.sl_pwm2.setDisabled(True)
            self.ui.sl_pwm3.setDisabled(True)
            self.ui.edit_duty2.setDisabled(True)
            self.ui.edit_duty3.setDisabled(True)
        else:
            self.locked = False
            self.ui.sl_pwm2.setEnabled(True)
            self.ui.sl_pwm3.setEnabled(True)
            self.ui.edit_duty2.setEnabled(True)
            self.ui.edit_duty3.setEnabled(True)


    def setSlider(self,slider):
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(50)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(5)

    def getEditValue(self,line_edit):
        value = int(line_edit.text())
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        return(value)
    #enddef

    def update_duty1_sl(self,value):
        self.ui.edit_duty1.setText(str(value))
        #self.ui.pwm1View.clear()
        if self.locked:
            self.plot(self.ui.pwm1View, (value/100), 1)
            self.plot(self.ui.pwm2View, (value / 100), 2)
            self.ui.edit_duty2.setText(str(value))
            self.plot(self.ui.pwm3View, (value / 100), 3)
            self.ui.edit_duty3.setText(str(value))
            self.ui.sl_pwm2.setValue(value)
            self.ui.sl_pwm3.setValue(value)
        else:
            self.plot(self.ui.pwm1View, (value / 100), 1)

    def update_duty1(self):
        value = self.getEditValue(self.ui.edit_duty1)
        self.ui.sl_pwm1.setValue(value)
        if self.locked:
            self.plot(self.ui.pwm1View, (value/100), 1)
            self.plot(self.ui.pwm2View, (value / 100), 2)
            self.ui.edit_duty2.setText(str(value))
            self.plot(self.ui.pwm3View, (value / 100), 3)
            self.ui.edit_duty3.setText(str(value))
            self.ui.sl_pwm2.setValue(value)
            self.ui.sl_pwm3.setValue(value)
        else:
            self.plot(self.ui.pwm1View, (value / 100), 1)

    def update_duty2_sl(self,value):
        self.ui.edit_duty2.setText(str(value))
        self.plot(self.ui.pwm2View, (value/100), 1)

    def update_duty2(self):
        value = self.getEditValue(self.ui.edit_duty2)
        self.ui.sl_pwm2.setValue(value)
        self.plot(self.ui.pwm2View, (value/100), 2)

    def update_duty3_sl(self,value):
        self.ui.edit_duty3.setText(str(value))
        self.plot(self.ui.pwm3View, (value/100), 1)

    def update_duty3(self):
        value = self.getEditValue(self.ui.edit_duty3)
        self.ui.sl_pwm3.setValue(value)
        self.plot(self.ui.pwm3View, (value/100), 3)

    def plot(self,view,duty,channel):
        # https://pyqtgraph.readthedocs.io/en/latest/graphicsItems/plotitem.html
        pg.setConfigOptions(antialias=True)
        #view.enableAutoRange(enable=True,y=None)
        #view.setAutoPan(x=None, y=None)
        #view.setAspectLocked(lock=False, ratio=1)
        #view.setLimits(maxYRange=2,minYRange=0)
        #view.showLabel('bottom', show=False)
        #view.setLabel('bottom', "Y Axis", units='s')

        view.setYRange(-0.1, 2.5, padding=0)
        view.showAxis('bottom', show=False)
        view.showGrid(x=True, y=True)
        view.setTitle("Channel:"+str(channel)+" "+str(int(duty*100))+"%")
        t = np.linspace(0, 2, 1000, endpoint=False, retstep=False, dtype=None, axis=0)
        pwm = signal.square((2 * np.pi * 5 * t) + 0, duty=duty) + 1
        view.plot(pwm, clear=True, pen=(255, 255, 0, 200))
    #enddef


    def createConnects(self):
        # File-Menu , Exit
        self.ui.actionExit.triggered.connect(self.myexit)
        self.ui.pb_Test.clicked.connect(self.myexit)
        self.ui.edit_duty1.returnPressed.connect(self.update_duty1)
        self.ui.edit_duty2.returnPressed.connect(self.update_duty2)
        self.ui.edit_duty3.returnPressed.connect(self.update_duty3)
        self.ui.sl_pwm1.valueChanged.connect(self.update_duty1_sl)
        self.ui.sl_pwm2.valueChanged.connect(self.update_duty2_sl)
        self.ui.sl_pwm3.valueChanged.connect(self.update_duty3_sl)
        self.ui.freqSlider.valueChanged.connect(self.update_freq_sl)
        self.ui.edit_freq.returnPressed.connect(self.update_freq)
        self.ui.lockButton.toggled.connect(self.lockClicked)
        self.ui.comboBox.currentIndexChanged.connect(self.connectUsb)
        # Gibt aktuelle Zelle aus
        #QtCore.QObject.connect(self.ui.pdfTable, QtCore.SIGNAL("clicked(QModelIndex)"), self.cellClicked)
        #QtCore.QObject.connect(self.ui.pdfTable, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.dblcellClicked)
        ## Import eines PDF
        #self.ui.actionImportOnePDF.activated.connect(self.importOnePDF)
        ## Import PDF-Directory
        #self.ui.actionImportPDFDir.activated.connect(self.importPDFDir)
        #self.ui.actionImport_PDF_List.activated.connect(self.importPDFList)

    # enddef

    def centerOnScreen (self):
        '''centerOnScreen()
        Centers the window on the screen.'''
        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.width = resolution.width()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

    def resizeEvent(self, newSize):
        if self.debug:
            print("ResizeEvent:",newSize)
            print("geom1:", self.ui.pwm1View.geometry())
            print("geom2:", self.ui.pwm2View.geometry())
            print("geom3:", self.ui.pwm3View.geometry())
            print("FrameSize:", self.frameSize())
            print("Height:",self.ui.pwm3View.geometry().height())
            print("Width:", self.ui.pwm3View.geometry().width())

# Slots
    @QtCore.pyqtSlot()
    def myexit(self):
        sys.exit()
#endclass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mw = MyMainWindow()
    mw.show()
    sys.exit(app.exec_())
