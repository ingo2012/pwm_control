#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
pwm_control 1.0  , IGE 11.10.2020

pip3 freeze > requirements.txt
https://protosupplies.com/product/xy-lpwm-pwm-signal-generator-module/

Qt Grafik
https://likegeeks.com/pyqt5-drawing-tutorial/
# Plot !!!
https://www.learnpyqt.com/courses/qt-creator/embed-pyqtgraph-custom-widgets-qt-app/

Designer nach Aenderung aufrufen
pyuic5 -o main_win.py main_win.ui

"""

import sys
import re
import serial
import time
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtCore, QtGui , QtWidgets
from PyQt5.QtWidgets import *
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
        self.debug = False
        self.locked = False
        self.usbConnect = False
        self.serial = None
        self.sliderDrag = False
        # Defaults
        self.d1Duty = 50
        self.d2Duty = 50
        self.d3Duty = 50
        self.frequency = 800
        self.freqDivider = 1
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.centerOnScreen()
        self.setStyleSheet("QStatusBar{padding-left:8px;color:blue;font-weight:normal;}")
        self.statusBar().showMessage('Ready')
        self.uiSetup()
        self.timer = QtCore.QTimer()
        # read from usb , interval 2 seconds
        self.timer.start(500.0)
        self.createConnects()
        self.connectUsb()
        self.readUsb()
    # enddef

    def setNewValues(self):
        self.ui.setButton.setEnabled(False)
        self.enableSliderFreq(drag=True)
        time.sleep(2.0)
        self.enableSliderD1(drag=True)
        time.sleep(1.0)
        self.enableSliderD2(drag=True)
        time.sleep(1.0)
        self.enableSliderD3(drag=True)
        time.sleep(1.0)
        self.sliderDrag = False

    def stopSlider(self):
        self.sliderDrag = True
        self.statusBar().showMessage("Reading disabled !")

    def stopEdit(self):
        self.sliderDrag = True
        self.ui.setButton.setEnabled(True)
        self.ui.freqSlider.setMinimum(0)
        self.ui.freqSlider.setMaximum(150000)
        self.ui.freqSlider.setSingleStep(1)
        self.statusBar().showMessage("Reading disabled ! Press Set to set new values")

    # Simple function to generate String in the form x.x.x Khz for Freq > 99950 Hz
    def xkhzconvert(value):
        x = "%3d" % round((value / 1000), 0)
        print("x=", x)
        s = ''
        count = 0
        for i in x:
            if count < 2:
                s = s + i + "."
            else:
                s = s + i
            count = count + 1
        return s

    def enableSliderFreq(self,drag=False):
        # Read Values and set the device
        # Fxxx, Fx.xx, Fxx.x or Fx.x.x
        if self.usbConnect:
            myTemp = self.ui.freqSlider.value()
            if myTemp > 99940:
                print("x0")
                myStr = xkhzconvert(myTemp)
            elif myTemp < 1000:
                myStr = "%03d" % myTemp
            elif myTemp < 10000:
                myStr = "%.2f" % (myTemp / 1000)
            elif myTemp < 99950:
                myStr = "%.1f" % (myTemp / 1000)
            self.writeUsb("F"+myStr)
            self.sliderDrag = drag

    def enableSliderD1(self,drag=False):
        # Read Values and set the device
        if self.usbConnect:
            myTemp = self.ui.sl_pwm1.value()
            myStr = "D1:{:03d}".format(myTemp)
            self.writeUsb(myStr)
            #print("Set")
            if self.locked:
                self.statusBar().showMessage("Setting channels")
                time.sleep(0.5)
                myStr = "D2:{:03d}".format(myTemp)
                self.writeUsb(myStr)
                time.sleep(0.5)
                myStr = "D3:{:03d}".format(myTemp)
                self.writeUsb(myStr)
                time.sleep(0.5)
            self.sliderDrag = drag


    def enableSliderD2(self,drag=False):
        # Read Values and set the device
        if self.usbConnect:
            myTemp = self.ui.sl_pwm2.value()
            myStr = "D2:{:03d}".format(myTemp)
            self.writeUsb(myStr)
            self.sliderDrag = drag

    def enableSliderD3(self,drag=False):
        # Read Values and set the device
        if self.usbConnect:
            myTemp = self.ui.sl_pwm3.value()
            myStr = "D3:{:03d}".format(myTemp)
            self.writeUsb(myStr)
            self.sliderDrag = drag

    def writeUsb(self,value):
        self.serial.write(value.encode())  # set current Value
        self.serial.flush()

    def readUsb(self):
        if self.usbConnect and self.sliderDrag==False:
            tempFreq = "0"
            decCounter = 0
            self.serial.write("read".encode())  # read current Values
            self.serial.flush()  # it is buffering. required to get the data out *now*
            readBytes = self.serial.readline().decode(encoding='UTF-8')
            #print("readBytes:",readBytes)
            # After new frequency setting we receive readBytes: FIII,D1:050,D2:035,D3:015,
            if len(readBytes.split(','))==5 and not readBytes.split(',')[0] == 'FIII':
                self.statusBar().showMessage("Ok: Read "+readBytes)
                m = re.search('F(\d+?\.?\d+?.?\d+),D1:(\d+),D2:(\d+),D3:(\d+)', readBytes.rstrip())
                tempFreq = m.group(1)
                decCounter = tempFreq.count('.')
                freqArray = tempFreq.split(".")
                #print("freqArr ",freqArray)
                if decCounter==0:
                    self.frequency = int(tempFreq)
                    # 1 Hz Control aktiv
                    self.ui.f1Button.setChecked(True)
                    self.ui.freqSlider.setMinimum(1)
                    self.ui.freqSlider.setMaximum(999)
                    self.ui.freqSlider.setSingleStep(1)
                    self.freqDivider = 1
                elif decCounter==1 and int(freqArray[0])<10:
                    self.frequency = int(freqArray[0])*1000 + int(freqArray[1])*10
                    # 10 Hz Control aktiv
                    self.ui.f10Button.setChecked(True)
                    self.ui.freqSlider.setMinimum(1000)
                    self.ui.freqSlider.setMaximum(9990)
                    self.ui.freqSlider.setSingleStep(10)
                    self.ui.freqSlider.setPageStep(10)
                    self.freqDivider = 10
                elif decCounter == 1 and int(freqArray[0]) > 9:
                    self.frequency = int(freqArray[0]) * 1000 + int(freqArray[1]) * 100
                    # 100 Hz Control aktiv
                    self.ui.f100Button.setChecked(True)
                    self.ui.freqSlider.setMinimum(10000)
                    self.ui.freqSlider.setMaximum(99900)
                    self.ui.freqSlider.setSingleStep(100)
                    self.ui.freqSlider.setPageStep(100)
                    self.freqDivider = 100
                elif decCounter == 2:
                    self.frequency = int(freqArray[0]) * 100000 + int(freqArray[1]) * 10000 + int(freqArray[2]) * 1000
                    # 1000 Hz Control aktiv
                    self.ui.f1000Button.setChecked(True)
                    self.ui.freqSlider.setMinimum(100000)
                    self.ui.freqSlider.setMaximum(150000)
                    self.ui.freqSlider.setSingleStep(1000)
                    self.ui.freqSlider.setPageStep(1000)
                    self.freqDivider = 1000
                # wenn decCounter = 1 und Array0 > 9 , dann 100er aktive , 11.3 = 11300 Hz , evtl. Darstellung anpassen
                # print("Group1 Freq",tempFreq ," Counter ",decCounter)
                self.d1Duty = int(m.group(2))
                self.d2Duty = int(m.group(3))
                self.d3Duty = int(m.group(4))
                self.updateDutyValues()
            else:
                self.statusBar().showMessage("Error: Read unexpected String "+readBytes)

    def updateDutyValues(self):
        self.ui.edit_duty1.setText(str(self.d1Duty))
        self.update_duty1()
        self.ui.edit_duty2.setText(str(self.d2Duty))
        self.update_duty2()
        self.ui.edit_duty3.setText(str(self.d3Duty))
        self.update_duty3()
        self.ui.edit_freq.setText(str((self.frequency)))
        self.update_freq()

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
        # Deactivate setButton
        self.ui.setButton.setDisabled(True)
    #enddef

    def update_freq_sl(self,value):
        self.ui.edit_freq.setText(str(value))

    def update_freq(self):
        value = self.ui.edit_freq.text()
        self.ui.freqSlider.setValue(int(value))

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
        self.timer.timeout.connect(self.readUsb)
        # Lock reading when slider moved
        self.ui.sl_pwm1.sliderPressed.connect(self.stopSlider)
        self.ui.sl_pwm1.sliderReleased.connect(self.enableSliderD1)
        self.ui.sl_pwm2.sliderPressed.connect(self.stopSlider)
        self.ui.sl_pwm2.sliderReleased.connect(self.enableSliderD2)
        self.ui.sl_pwm3.sliderPressed.connect(self.stopSlider)
        self.ui.sl_pwm3.sliderReleased.connect(self.enableSliderD3)
        self.ui.freqSlider.sliderPressed.connect(self.stopSlider)
        self.ui.freqSlider.sliderReleased.connect(self.enableSliderFreq)
        # Lock when focusIn editLine
        self.ui.edit_freq.selectionChanged.connect(self.stopEdit)
        self.ui.edit_duty1.selectionChanged.connect(self.stopEdit)
        self.ui.edit_duty2.selectionChanged.connect(self.stopEdit)
        self.ui.edit_duty3.selectionChanged.connect(self.stopEdit)
        self.ui.setButton.clicked.connect(self.setNewValues)
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
