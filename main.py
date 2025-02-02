import sys
import os
import json
from glob import glob

from PyQt5 import uic
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QImage, QPixmap, QKeySequence
from PyQt5.QtWidgets import QApplication, QCheckBox, QComboBox, QFileDialog, QMainWindow, QLabel, QPushButton, QSlider, QShortcut, QTextEdit
import cv2
import numpy as np
import os
import importlib


def generateSolidColorPixmap(w, h, color):
    canvas = QImage(QSize(w, h), QImage.Format_RGB30)
    for baris in range(0, h):
        for kolom in range(0, w):
            canvas.setPixel(kolom, baris, color.rgb())
    return canvas


class MainWindow(QMainWindow):
    selectedHue        = 359
    selectedSaturation = 255
    selectedValue      = 255

    lowerHSV    = (0, 0, 0)
    upperHSV    = (179, 255, 255)
    fileName    = ""
    settings    = {}

    imgRaw      = None
    imgMask     = None
    imgMasked   = None
    imgHsvSpace = None

    plugin      = None

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "./assets/main_window.ui"), self)
        self.showMaximized()

        self.sliderH              = self.findChild(QSlider,     "sliderH"             )
        self.sliderS              = self.findChild(QSlider,     "sliderS"             )
        self.sliderV              = self.findChild(QSlider,     "sliderV"             )

        self.lblH                 = self.findChild(QLabel,      "lblH"                )
        self.lblS                 = self.findChild(QLabel,      "lblS"                )
        self.lblV                 = self.findChild(QLabel,      "lblV"                )

        self.lblLower             = self.findChild(QLabel,      "lblLower"            )
        self.lblUpper             = self.findChild(QLabel,      "lblUpper"            )

        self.previewH             = self.findChild(QLabel,      "previewH"            )
        self.previewS             = self.findChild(QLabel,      "previewS"            )
        self.previewV             = self.findChild(QLabel,      "previewV"            )

        self.previewRaw           = self.findChild(QLabel,      "previewRaw"          )
        self.previewMask          = self.findChild(QLabel,      "previewMask"         )
        self.previewMaskedRaw     = self.findChild(QLabel,      "previewMaskedRaw"    )
        self.previewHsvSpace      = self.findChild(QLabel,      "previewHsvSpace"     )

        self.cboxSetMode          = self.findChild(QComboBox,   "cboxSetMode"         )
        self.cboxInverseHSV       = self.findChild(QCheckBox,   "cboxInverseHSV"      )
        self.cboxInverseMask      = self.findChild(QCheckBox,   "cboxInverseMask"     )

        self.cboxErode            = self.findChild(QCheckBox,   "cboxErode"           )
        self.sliderErosion        = self.findChild(QSlider,     "sliderErosion"       )
        self.cboxDilate           = self.findChild(QCheckBox,   "cboxDilate"          )
        self.sliderDilation       = self.findChild(QSlider,     "sliderDilation"      )
        self.cboxErode2           = self.findChild(QCheckBox,   "cboxErode2"          )
        self.sliderErosion2       = self.findChild(QSlider,     "sliderErosion2"      )
        self.cboxDilate2          = self.findChild(QCheckBox,   "cboxDilate2"         )
        self.sliderDilation2      = self.findChild(QSlider,     "sliderDilation2"     )

        self.cboxTrimHeader       = self.findChild(QCheckBox,   "cboxTrimHeader"      )
        self.sliderTrimHeader     = self.findChild(QSlider,     "sliderTrimHeader"    )
        self.cboxTrimFooter       = self.findChild(QCheckBox,   "cboxTrimFooter"      )
        self.sliderTrimFooter     = self.findChild(QSlider,     "sliderTrimFooter"    )
        self.cboxTrimLeft         = self.findChild(QCheckBox,   "cboxTrimLeft"        )
        self.sliderTrimLeft       = self.findChild(QSlider,     "sliderTrimLeft"      )
        self.cboxTrimRight        = self.findChild(QCheckBox,   "cboxTrimRight"       )
        self.sliderTrimRight      = self.findChild(QSlider,     "sliderTrimRight"     )

        self.pluginOutput         = self.findChild(QTextEdit,   "pluginOutput"        )
        self.btnOpenPluginFile    = self.findChild(QPushButton, "btnOpenPluginFile"   )
        self.cboxSwitchPluginFile = self.findChild(QComboBox,   "cboxSwitchPluginFile")
        self.btnDropPluginFile    = self.findChild(QPushButton, "btnDropPluginFile"   )
        self.btnReloadPluginFile  = self.findChild(QPushButton, "btnReloadPluginFile" )
        self.btnUnloadPluginFile  = self.findChild(QPushButton, "btnUnloadPluginFile" )

        self.btnOpen              = self.findChild(QPushButton, "btnOpen"             )
        self.btnPrint             = self.findChild(QPushButton, "btnPrint"            )

        self.btnFirst             = self.findChild(QPushButton, "btnFirst"            )
        self.btnPrev              = self.findChild(QPushButton, "btnPrev"             )
        self.btnNext              = self.findChild(QPushButton, "btnNext"             )
        self.btnLast              = self.findChild(QPushButton, "btnLast"             )
        self.lblFileName          = self.findChild(QLabel,      "lblFileName"         )
        self.cboxFolderName       = self.findChild(QComboBox,   "cboxFolderName"      )
        self.btnDropFolderName    = self.findChild(QPushButton, "btnDropFolderName"   )

        self.btnLoad              = self.findChild(QPushButton, "btnLoad"             )
        self.btnSave              = self.findChild(QPushButton, "btnSave"             )

        self.cboxProfile          = self.findChild(QComboBox,   "cboxProfile"         )
        self.btnSnapshotProfile   = self.findChild(QPushButton, "btnSnapshotProfile"  )
        self.btnDeleteProfile     = self.findChild(QPushButton, "btnDeleteProfile"    )
        self.btnResetProfile      = self.findChild(QPushButton, "btnResetProfile"     )

        self.sliderTrimHeader.setMaximum(480)
        self.sliderTrimHeader.setValue(0)
        self.sliderTrimFooter.setMaximum(480)
        self.sliderTrimFooter.setValue(480)
        self.sliderTrimLeft.setMaximum(640)
        self.sliderTrimLeft.setValue(0)
        self.sliderTrimRight.setMaximum(640)
        self.sliderTrimRight.setValue(640)

        self.init_handler()
        self.loadHsvSpace()
        self.updateHSVPreview()
        self.loadSettings()

    def resizeEvent(self, event):
        self.refreshAllImg()

    def loadHsvSpace(self):
        self.imgHsvSpace = cv2.imread(os.path.join(os.path.dirname(__file__), "assets", "hsv_color.png"))
        
    def init_handler(self):
        self.sliderH.valueChanged.connect(self.onHChanged)
        self.sliderS.valueChanged.connect(self.onSChanged)
        self.sliderV.valueChanged.connect(self.onVChanged)
        self.cboxSetMode.currentTextChanged.connect(self.onCBoxModeChanged)
        self.cboxInverseHSV.stateChanged.connect(self.updateMask)
        self.cboxInverseMask.stateChanged.connect(self.updateMask)
        self.btnOpen.clicked.connect(self.onBtnOpenClicked)
        self.btnPrint.clicked.connect(self.onBtnPrintClicked)

        self.btnFirst.clicked.connect(self.onBtnFirstClicked)
        self.btnPrev.clicked.connect(self.onBtnPrevClicked)
        self.btnNext.clicked.connect(self.onBtnNextClicked)
        self.btnLast.clicked.connect(self.onBtnLastClicked)
        self.cboxFolderName.textActivated.connect(self.onChangeFolder)
        self.btnDropFolderName.clicked.connect(self.onBtnDropFolderName)

        self.btnLoad.clicked.connect(self.loadSettings)
        self.btnSave.clicked.connect(self.saveSettings)

        self.keyUp     = QShortcut(QKeySequence("Up"    ), self); self.keyUp.activated.connect(self.onBtnPrevClicked)
        self.keyDown   = QShortcut(QKeySequence("Down"  ), self); self.keyDown.activated.connect(self.onBtnNextClicked)
        self.keyLeft   = QShortcut(QKeySequence("Left"  ), self); self.keyLeft.activated.connect(self.onBtnPrevClicked)
        self.keyRight  = QShortcut(QKeySequence("Right" ), self); self.keyRight.activated.connect(self.onBtnNextClicked)
        self.keyPgUp   = QShortcut(QKeySequence("PgUp"  ), self); self.keyPgUp.activated.connect(self.onBtnFirstClicked)
        self.keyPgDown = QShortcut(QKeySequence("PgDown"), self); self.keyPgDown.activated.connect(self.onBtnLastClicked)
        self.keyHome   = QShortcut(QKeySequence("Home"  ), self); self.keyHome.activated.connect(self.onBtnFirstClicked)
        self.keyEnd    = QShortcut(QKeySequence("End"   ), self); self.keyEnd.activated.connect(self.onBtnLastClicked)

        self.cboxDilate.stateChanged.connect(self.updateMask)
        self.cboxErode.stateChanged.connect(self.updateMask)
        self.sliderErosion.valueChanged.connect(self.onSliderErodeChanged)
        self.sliderDilation.valueChanged.connect(self.onSliderDilateChanged)
        self.cboxDilate2.stateChanged.connect(self.updateMask)
        self.cboxErode2.stateChanged.connect(self.updateMask)
        self.sliderErosion2.valueChanged.connect(self.onSliderErode2Changed)
        self.sliderDilation2.valueChanged.connect(self.onSliderDilate2Changed)

        self.cboxTrimHeader.stateChanged.connect(self.updateMask)
        self.cboxTrimFooter.stateChanged.connect(self.updateMask)
        self.cboxTrimLeft.stateChanged.connect(self.updateMask)
        self.cboxTrimRight.stateChanged.connect(self.updateMask)
        self.sliderTrimHeader.valueChanged.connect(self.onSliderTrimHeaderChanged)
        self.sliderTrimFooter.valueChanged.connect(self.onSliderTrimFooterChanged)
        self.sliderTrimLeft.valueChanged.connect(self.onSliderTrimLeftChanged)
        self.sliderTrimRight.valueChanged.connect(self.onSliderTrimRightChanged)

        self.cboxProfile.textActivated.connect(self.onActivateProfile)
        self.btnSnapshotProfile.clicked.connect(self.onSnapshotProfile)
        self.btnDeleteProfile.clicked.connect(self.onDeleteProfile)
        self.btnResetProfile.clicked.connect(self.onResetProfile)

        self.btnOpenPluginFile.clicked.connect(self.onOpenPluginFile)
        self.cboxSwitchPluginFile.textActivated.connect(self.onSwitchPluginFile)
        self.btnDropPluginFile.clicked.connect(self.onDropPluginFile)
        self.btnReloadPluginFile.clicked.connect(self.onReloadPluginFile)
        self.btnUnloadPluginFile.clicked.connect(self.onUnloadPluginFile)


    def onBtnPrintClicked(self):
        seq  = 0
        info = []
        info.append(("Lower HSV:", f"{self.lowerHSV}"))
        info.append(("Upper HSV:", f"{self.upperHSV}"))

        if self.cboxInverseHSV.isChecked():
            info.append(("Inverse HSV Selection:", f"yes"))

        if self.cboxErode.isChecked() and self.sliderErosion.value() > 1:
            info.append(("Erode Kernel:", f"{self.sliderErosion.value()}"))
        if self.cboxDilate.isChecked() and self.sliderDilation.value() > 1:
            info.append(("Dilate Kernel:", f"{self.sliderDilation.value()}"))
        if self.cboxErode2.isChecked() and self.sliderErosion2.value() > 1:
            info.append(("Erode Kernel:", f"{self.sliderErosion2.value()}"))
        if self.cboxDilate2.isChecked() and self.sliderDilation2.value() > 1:
            info.append(("Dilate Kernel:", f"{self.sliderDilation2.value()}"))

        if self.cboxTrimHeader.isChecked() and self.sliderTrimHeader.value() > 0:
            info.append(("Trim Header:", f"{self.sliderTrimHeader.value()}"))
        if self.cboxTrimFooter.isChecked() and self.sliderTrimFooter.value() < self.sliderTrimFooter.maximum():
            info.append(("Trim Footer:", f"{self.sliderTrimFooter.value()}"))
        if self.cboxTrimLeft.isChecked() and self.sliderTrimLeft.value() > 0:
            info.append(("Trim Left:", f"{self.sliderTrimLeft.value()}"))
        if self.cboxTrimRight.isChecked() and self.sliderTrimRight.value() < self.sliderTrimRight.maximum():
            info.append(("Trim Right:", f"{self.sliderTrimRight.value()}"))

        if self.cboxInverseMask.isChecked():
            info.append(("Inverse Mask:", f"yes"))

        self.pluginOutput.setHtml("<table>" + "\n".join(f"<tr><td>{key}</td><td>{value}</td></tr>" for (key, value) in info) + "</table>")


    # =========== Helper ===========
    def updatePreviewHsvSpace(self):
        if self.imgHsvSpace is None:
            return

        frame_HSV = cv2.cvtColor(self.imgHsvSpace, cv2.COLOR_BGR2HSV)
        lower_range = np.array(self.lowerHSV)
        upper_range = np.array(self.upperHSV)

        frame_threshold = cv2.inRange(frame_HSV, lower_range, upper_range)
        frame_threshold = cv2.bitwise_and(self.imgHsvSpace, self.imgHsvSpace, mask=frame_threshold)

        _asQImage = QImage(frame_threshold.data, frame_threshold.shape[1], frame_threshold.shape[0], frame_threshold.shape[1]*3,  QtGui.QImage.Format_RGB888)
        _asQImage = _asQImage.rgbSwapped()
        self.previewHsvSpace.setPixmap(QPixmap.fromImage(_asQImage).scaledToWidth(self.previewMask.size().width()))


    def updateHSVPreview(self):
        prevH = generateSolidColorPixmap(200, 300, QColor.fromHsv(self.selectedHue, 255, 255))
        self.previewH.setPixmap(QPixmap.fromImage(prevH))

        prevS = generateSolidColorPixmap(200, 300, QColor.fromHsv(self.selectedHue, self.selectedSaturation, 255))
        self.previewS.setPixmap(QPixmap.fromImage(prevS))

        prevV = generateSolidColorPixmap(200, 300, QColor.fromHsv(self.selectedHue, self.selectedSaturation, self.selectedValue))
        self.previewV.setPixmap(QPixmap.fromImage(prevV))

        if self.cboxSetMode.currentIndex() == 0:
            self.upperHSV = (self.selectedHue // 2, self.selectedSaturation, self.selectedValue)
            self.lblUpper.setText(f"{self.upperHSV[0]}, {self.upperHSV[1]}, {self.upperHSV[2]}")
        elif self.cboxSetMode.currentIndex() == 1:
            self.lowerHSV = (self.selectedHue // 2, self.selectedSaturation, self.selectedValue)
            self.lblLower.setText(f"{self.lowerHSV[0]}, {self.lowerHSV[1]}, {self.lowerHSV[2]}")
        
        self.updateMask()
        self.updatePreviewHsvSpace()


    def updateRawImg(self, img):
        # _dsize = (self.previewRaw.size().height(),
        #           self.previewRaw.size().width())
        self.imgRaw = img
        self.refreshAllImg()


    def refreshAllImg(self):
        if self.imgRaw is None:
            self.updateHSVPreview()
            return

        _imgAsQImg = QImage(self.imgRaw.data, self.imgRaw.shape[1], self.imgRaw.shape[0], QImage.Format_RGB888).rgbSwapped()

        # self.imgRaw = img.scaled(200,100, QtCore.KeepAspectRatio)
        # self.imgRaw = img.scaledToHeight(self.previewMask.size().height())
        self.previewRaw.setPixmap(QPixmap.fromImage(_imgAsQImg).scaledToWidth(self.previewRaw.size().width()))
        self.updateMask()
        self.updateHSVPreview()

        height, width = self.imgRaw.shape[:2]
        self.sliderTrimHeader.setMaximum(height)

        if self.sliderTrimFooter.maximum() == self.sliderTrimFooter.value():
            self.sliderTrimFooter.setMaximum(height)
            self.sliderTrimFooter.setValue(height)
        else:
            self.sliderTrimFooter.setMaximum(height)

        self.sliderTrimLeft.setMaximum(width)

        if self.sliderTrimRight.maximum() == self.sliderTrimRight.value():
            self.sliderTrimRight.setMaximum(width)
            self.sliderTrimRight.setValue(width)
        else:
            self.sliderTrimRight.setMaximum(width)


    def updateMask(self):
        if self.imgRaw is None:
            return

        frame_HSV = cv2.cvtColor(self.imgRaw, cv2.COLOR_BGR2HSV)
        lower_range = np.array(self.lowerHSV)
        upper_range = np.array(self.upperHSV)

        frame_threshold = cv2.inRange(frame_HSV, lower_range, upper_range)

        if self.cboxInverseHSV.isChecked():
            frame_threshold = cv2.bitwise_not(frame_threshold, frame_threshold)

        if self.cboxErode.isChecked():
            _kernel = self.sliderErosion.value()
            frame_threshold = cv2.erode(frame_threshold, np.ones((_kernel, _kernel), dtype=np.uint8))
        
        if self.cboxDilate.isChecked():
            _kernel = self.sliderDilation.value()
            frame_threshold = cv2.dilate(frame_threshold, np.ones((_kernel, _kernel), dtype=np.uint8))

        if self.cboxErode2.isChecked():
            _kernel = self.sliderErosion2.value()
            frame_threshold = cv2.erode(frame_threshold, np.ones((_kernel, _kernel), dtype=np.uint8))
        
        if self.cboxDilate2.isChecked():
            _kernel = self.sliderDilation2.value()
            frame_threshold = cv2.dilate(frame_threshold, np.ones((_kernel, _kernel), dtype=np.uint8))

        if self.cboxTrimHeader.isChecked():
            _trim_header = self.sliderTrimHeader.value()
            frame_threshold = cv2.rectangle(frame_threshold, (0, 0), (frame_threshold.shape[1], _trim_header), False, -1)

        if self.cboxTrimFooter.isChecked():
            _trim_footer = self.sliderTrimFooter.value()
            frame_threshold = cv2.rectangle(frame_threshold, (0, _trim_footer), (frame_threshold.shape[1], frame_threshold.shape[0]), False, -1)

        if self.cboxTrimLeft.isChecked():
            _trim_left = self.sliderTrimLeft.value()
            frame_threshold = cv2.rectangle(frame_threshold, (0, 0), (_trim_left, frame_threshold.shape[0]), False, -1)

        if self.cboxTrimRight.isChecked():
            _trim_right = self.sliderTrimRight.value()
            frame_threshold = cv2.rectangle(frame_threshold, (_trim_right, 0), (frame_threshold.shape[1], frame_threshold.shape[0]), False, -1)

        if self.cboxInverseMask.isChecked():
            frame_threshold = cv2.bitwise_not(frame_threshold, frame_threshold)

        self.updateMaskedRaw(frame_threshold)
        frame_threshold = cv2.cvtColor(frame_threshold, cv2.COLOR_GRAY2RGB)

        _asQImage = QImage(frame_threshold.data, frame_threshold.shape[1], frame_threshold.shape[0], frame_threshold.shape[1]*3,  QtGui.QImage.Format_RGB888)
        _asQImage = _asQImage.rgbSwapped()
        self.previewMask.setPixmap(QPixmap.fromImage(_asQImage).scaledToWidth(self.previewMask.size().width()))


    def updateMaskedRaw(self, masking):
        if self.imgRaw is None:
            return

        frame_threshold = None

        if self.plugin:
            result = self.plugin.process_image(self.imgRaw, masking)

            if result is not None:
                if isinstance(result, (tuple, list)):
                    if len(result) >= 1:
                        frame_threshold = result[0]
                    if len(result) >= 2:
                        self.pluginOutput.setPlainText(f"Plugin {os.path.basename(self.plugin.__file__)} output:\n{json.dumps(result[1], indent=4)}\n")
                else:
                    frame_threshold = result

        if frame_threshold is None:
            frame_threshold = cv2.bitwise_and(self.imgRaw, self.imgRaw, mask=masking)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            edges  = cv2.GaussianBlur(masking, (5, 5), 0)
            edges  = cv2.Canny(edges, 50, 150)
            edges  = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations = 2)

            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for c in sorted(contours, key = cv2.contourArea, reverse = True):
                epsilon = 0.01 * cv2.arcLength(c, True) 
                approx  = cv2.approxPolyDP(c, epsilon, True)
                cv2.drawContours(frame_threshold, [approx], 0, (255, 0, 0), 1)

        _asQImage = QImage(frame_threshold.data, frame_threshold.shape[1], frame_threshold.shape[0], frame_threshold.shape[1]*3,  QtGui.QImage.Format_RGB888)
        _asQImage = _asQImage.rgbSwapped()
        self.previewMaskedRaw.setPixmap(QPixmap.fromImage(_asQImage).scaledToWidth(self.previewMaskedRaw.size().width()))

    # =========== EVENT HANDLER ===========

    def onCBoxModeChanged(self, text):
        if self.cboxSetMode.currentIndex() == 0:
            self.selectedHue = self.upperHSV[0] * 2
            self.selectedSaturation = self.upperHSV[1]
            self.selectedValue = self.upperHSV[2]
        elif self.cboxSetMode.currentIndex() == 1:
            self.selectedHue = self.lowerHSV[0] * 2
            self.selectedSaturation = self.lowerHSV[1]
            self.selectedValue = self.lowerHSV[2]

        self.sliderH.setValue(self.selectedHue)
        self.sliderS.setValue(self.selectedSaturation)
        self.sliderV.setValue(self.selectedValue)

        self.updateHSVPreview()

    def onHChanged(self):
        _v = self.selectedHue = self.sliderH.value()
        self.lblH.setText(str(f"{_v//2}"))
        self.updateHSVPreview()

    def onSChanged(self):
        _v = self.selectedSaturation = self.sliderS.value()
        self.lblS.setText(str(_v))
        self.updateHSVPreview()

    def onVChanged(self):
        _v = self.selectedValue = self.sliderV.value()
        self.lblV.setText(str(_v))
        self.updateHSVPreview()


    def onSliderErodeChanged(self):
        self.cboxErode.setText(f"Erode {self.sliderErosion.value()}")

        if self.sliderErosion.value() > 1 and not self.cboxErode.isChecked():
            self.cboxErode.setChecked(True)
        elif self.sliderErosion.value() <= 1 and self.cboxErode.isChecked():
            self.cboxErode.setChecked(False)

        self.updateMask()


    def onSliderDilateChanged(self):
        self.cboxDilate.setText(f"Dilate {self.sliderDilation.value()}")

        if self.sliderDilation.value() > 1 and not self.cboxDilate.isChecked():
            self.cboxDilate.setChecked(True)
        elif self.sliderDilation.value() <= 1 and self.cboxDilate.isChecked():
            self.cboxDilate.setChecked(False)

        self.updateMask()


    def onSliderErode2Changed(self):
        self.cboxErode2.setText(f"Erode {self.sliderErosion2.value()}")

        if self.sliderErosion2.value() > 1 and not self.cboxErode2.isChecked():
            self.cboxErode2.setChecked(True)
        elif self.sliderErosion2.value() <= 1 and self.cboxErode2.isChecked():
            self.cboxErode2.setChecked(False)

        self.updateMask()


    def onSliderDilate2Changed(self):
        self.cboxDilate2.setText(f"Dilate {self.sliderDilation2.value()}")

        if self.sliderDilation2.value() > 1 and not self.cboxDilate2.isChecked():
            self.cboxDilate2.setChecked(True)
        elif self.sliderDilation2.value() <= 1 and self.cboxDilate2.isChecked():
            self.cboxDilate2.setChecked(False)

        self.updateMask()


    def onSliderTrimHeaderChanged(self):
        self.cboxTrimHeader.setText(f"Trim Header {self.sliderTrimHeader.value()}")

        if self.sliderTrimHeader.value() > 0 and not self.cboxTrimHeader.isChecked():
            self.cboxTrimHeader.setChecked(True)
        elif self.sliderTrimHeader.value() == 0 and self.cboxTrimHeader.isChecked():
            self.cboxTrimHeader.setChecked(False)

        self.updateMask()


    def onSliderTrimFooterChanged(self):
        self.cboxTrimFooter.setText(f"Trim Footer {self.sliderTrimFooter.value()}")

        if self.sliderTrimFooter.value() < self.sliderTrimFooter.maximum() and not self.cboxTrimFooter.isChecked():
            self.cboxTrimFooter.setChecked(True)
        elif self.sliderTrimFooter.value() == self.sliderTrimFooter.maximum() and self.cboxTrimFooter.isChecked():
            self.cboxTrimFooter.setChecked(False)

        self.updateMask()


    def onSliderTrimLeftChanged(self):
        self.cboxTrimLeft.setText(f"Trim Left {self.sliderTrimLeft.value()}")

        if self.sliderTrimLeft.value() > 0 and not self.cboxTrimLeft.isChecked():
            self.cboxTrimLeft.setChecked(True)
        elif self.sliderTrimLeft.value() == 0 and self.cboxTrimLeft.isChecked():
            self.cboxTrimLeft.setChecked(False)

        self.updateMask()


    def onSliderTrimRightChanged(self):
        self.cboxTrimRight.setText(f"Trim Right {self.sliderTrimRight.value()}")

        if self.sliderTrimRight.value() < self.sliderTrimRight.maximum() and not self.cboxTrimRight.isChecked():
            self.cboxTrimRight.setChecked(True)
        elif self.sliderTrimRight.value() == self.sliderTrimRight.maximum() and self.cboxTrimRight.isChecked():
            self.cboxTrimRight.setChecked(False)

        self.updateMask()


    def _loadImageFile(self, fileName):
        self.updateRawImg(cv2.imread(fileName))
        self.fileName = fileName
        self.lblFileName.setText(os.path.basename(fileName))

        path = os.path.dirname(fileName)

        for ndx in range(self.cboxFolderName.count()):
            if self.cboxFolderName.itemData(ndx) == path:
                self.cboxFolderName.setCurrentIndex(ndx)
                return

        folderName = os.path.basename(path)
        ndx = self.cboxFolderName.findText(folderName, Qt.MatchExactly)

        dup = 0
        while ndx >= 0:
            dup += 1
            ndx = self.cboxFolderName.findText(f"{folderName}({dup})", Qt.MatchExactly)

        if dup > 0:
            folderName = f"{folderName}({dup})"

        self.cboxFolderName.insertItem(0, folderName, path)
        self.cboxFolderName.setCurrentIndex(0)

        while self.cboxFolderName.count() > 20:
            self.cboxFolderName.removeItem(self.cboxFolderName.count() - 1)


    def onBtnOpenClicked(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self, "QFileDialog.getOpenFileName()", "", "All Files (*);;Jpeg (*.jpeg);;BMP (*.bmp)", options=options)
        if not fileName:
            return
        self._loadImageFile(fileName)

        # self.srcQimg = QImage(fileName=fileName, format=QImage.Format_RGB32)
        # self.updateRawImg(cv2.imread(fileName))
        # with open(fileName, 'rb') as f:
        #     self.updateRawImg(QImage.fromData(f.read()))


    def onBtnFirstClicked(self):
        if self.fileName:
            files = sorted(glob(os.path.join(os.path.dirname(self.fileName), "*.jp*g")))

            if len(files) > 0:
                self._loadImageFile(files[0])


    def onBtnPrevClicked(self):
        if self.fileName:
            files = sorted(glob(os.path.join(os.path.dirname(self.fileName), "*.jp*g")))

            for i, fileName in enumerate(files):
                if self.fileName == fileName:
                    if i > 0:
                        self._loadImageFile(files[i - 1])
                    return


    def onBtnNextClicked(self):
        if self.fileName:
            files = sorted(glob(os.path.join(os.path.dirname(self.fileName), "*.jp*g")))

            for i, fileName in enumerate(files):
                if self.fileName == fileName:
                    if i + 1 < len(files):
                        self._loadImageFile(files[i + 1])
                    return


    def onBtnLastClicked(self):
        if self.fileName:
            files = sorted(glob(os.path.join(os.path.dirname(self.fileName), "*.jp*g")))

            if len(files) > 0:
                self._loadImageFile(files[-1])


    def onChangeFolder(self):
        ndx = self.cboxFolderName.currentIndex()
        if ndx >= 0:
            path = self.cboxFolderName.itemData(ndx)
            files = sorted(glob(os.path.join(path, "*.jp*g")))

            if len(files) > 0:
                self._loadImageFile(files[0])


    def onBtnDropFolderName(self):
        ndx = self.cboxFolderName.currentIndex()
        if ndx >= 0:
            self.cboxFolderName.removeItem(ndx)


    def loadSettings(self):
        try:
            with open("HsvRangeTool.json") as f:
                self.settings = json.load(f)

        except BaseException as e:
            print("Unable to load settings from HsvRangeTool.json: " + repr(e))
            return

        if "profile" not in self.settings:
            self.settings["profile"] = {}
        if "folders" not in self.settings:
            self.settings["folders"] = []
        if "plugins" not in self.settings:
            self.settings["plugins"] = []

        self.syncProfile(self.settings["profile"].get("default", {}))

        found = False
        for profile in self.settings["profile"]:
            if profile in ("", "default"):
                continue

            ndx = self.cboxProfile.findText(profile, Qt.MatchExactly)
            if ndx < 0:
                self.cboxProfile.insertItem(0, profile)
                ndx = 0

            if self.settings["profile"][profile] == self.settings["profile"].get("default", {}):
                found = True
                self.cboxProfile.setCurrentIndex(ndx)

        if not found:
            self.cboxProfile.setCurrentIndex(-1)

        self.cboxFolderName.clear()
        for path in reversed(self.settings["folders"][:20]):
            folderName = os.path.basename(path)
            ndx = self.cboxFolderName.findText(folderName, Qt.MatchExactly)

            dup = 0
            while ndx >= 0:
                dup += 1
                ndx = self.cboxFolderName.findText(f"{folderName}({dup})", Qt.MatchExactly)

            if dup > 0:
                folderName = f"{folderName}({dup})"

            self.cboxFolderName.insertItem(0, folderName, path)

        self.cboxFolderName.setCurrentIndex(-1)

        self.cboxSwitchPluginFile.clear()
        plugins = sorted(glob(os.path.join(os.path.dirname(__file__), "plugins", "*.py")))
        for path in plugins:
            pluginName = os.path.basename(path)
            ndx = self.cboxSwitchPluginFile.findText(pluginName, Qt.MatchExactly)

            dup = 0
            while ndx >= 0:
                dup += 1
                ndx = self.cboxSwitchPluginFile.findText(f"{pluginName}({dup})", Qt.MatchExactly)

            if dup > 0:
                pluginName = f"{pluginName}({dup})"

            self.cboxSwitchPluginFile.insertItem(0, pluginName, path)
            try:
                self.settings["plugins"].remove(path)
            except:
                pass

        for path in reversed(self.settings["plugins"][:20]):
            if not os.path.exists(path):
                continue

            pluginName = os.path.basename(path)
            ndx = self.cboxSwitchPluginFile.findText(pluginName, Qt.MatchExactly)

            dup = 0
            while ndx >= 0:
                dup += 1
                ndx = self.cboxSwitchPluginFile.findText(f"{pluginName}({dup})", Qt.MatchExactly)

            if dup > 0:
                pluginName = f"{pluginName}({dup})"

            self.cboxSwitchPluginFile.insertItem(0, pluginName, path)

        self.cboxSwitchPluginFile.setCurrentIndex(-1)


    def syncProfile(self, profile):
        try:
            ################################################
            self.upperHSV = tuple(profile.get("upper_hsv", [179, 255, 255]))
            self.lowerHSV = tuple(profile.get("lower_hsv", [0, 0, 0]))
            self.cboxInverseHSV.setChecked(profile.get("inverse_hsv", False))

            if self.cboxSetMode.currentIndex() == 0:
                self.selectedHue        = self.upperHSV[0] * 2
                self.selectedSaturation = self.upperHSV[1]
                self.selectedValue      = self.upperHSV[2]
            elif self.cboxSetMode.currentIndex() == 1:
                self.selectedHue        = self.lowerHSV[0] * 2
                self.selectedSaturation = self.lowerHSV[1]
                self.selectedValue      = self.lowerHSV[2]

            self.sliderH.setValue(self.selectedHue)
            self.sliderS.setValue(self.selectedSaturation)
            self.sliderV.setValue(self.selectedValue)

            ################################################
            erosion1  = profile.get("erosion1", 0)
            dilation1 = profile.get("dilation1", 0)
            erosion2  = profile.get("erosion2", 0)
            dilation2 = profile.get("dilation2", 0)

            if erosion1 > 0:
                self.cboxErode.setChecked(True)
                self.sliderErosion.setValue(erosion1)
            else:
                self.cboxErode.setChecked(False)
                self.sliderErosion.setValue(1)

            if dilation1 > 0:
                self.cboxDilate.setChecked(True)
                self.sliderDilation.setValue(dilation1)
            else:
                self.cboxDilate.setChecked(False)
                self.sliderDilation.setValue(1)

            if erosion2 > 0:
                self.cboxErode2.setChecked(True)
                self.sliderErosion2.setValue(erosion2)
            else:
                self.cboxErode2.setChecked(False)
                self.sliderErosion2.setValue(1)

            if dilation2 > 0:
                self.cboxDilate2.setChecked(True)
                self.sliderDilation2.setValue(dilation2)
            else:
                self.cboxDilate2.setChecked(False)
                self.sliderDilation2.setValue(1)

            ################################################
            trim_header = profile.get("trim_header", 0)
            self.sliderTrimHeader.setValue(trim_header)
            self.cboxTrimHeader.setChecked(trim_header > 0)

            trim_footer = profile.get("trim_footer", self.sliderTrimFooter.maximum())
            if trim_footer > self.sliderTrimFooter.maximum():
                self.sliderTrimFooter.setMaximum(trim_footer)
            self.sliderTrimFooter.setValue(trim_footer)
            self.cboxTrimFooter.setChecked(trim_footer < self.sliderTrimFooter.maximum())

            trim_left = profile.get("trim_left", 0)
            self.sliderTrimLeft.setValue(trim_left)
            self.cboxTrimLeft.setChecked(trim_left > 0)

            trim_right = profile.get("trim_right", self.sliderTrimRight.maximum())
            if trim_right > self.sliderTrimRight.maximum():
                self.sliderTrimRight.setMaximum(trim_right)
            self.sliderTrimRight.setValue(trim_right)
            self.cboxTrimRight.setChecked(trim_right < self.sliderTrimRight.maximum())

            self.cboxInverseMask.setChecked(profile.get("inverse_mask", False))
            ################################################

            self.refreshAllImg()

        except BaseException as e:
            print("Settings in HsvRangeTool.json were likely mismatched: " + repr(e))
            raise


    def snapshotCurrentProfile(self):
        return {
            "lower_hsv"     : list(self.lowerHSV),
            "upper_hsv"     : list(self.upperHSV),
            "inverse_hsv"   : self.cboxInverseHSV.isChecked(),
            "erosion1"      : self.sliderErosion.value()    if self.cboxErode.isChecked()      else 0,
            "dilation1"     : self.sliderDilation.value()   if self.cboxDilate.isChecked()     else 0,
            "erosion2"      : self.sliderErosion2.value()   if self.cboxErode2.isChecked()     else 0,
            "dilation2"     : self.sliderDilation2.value()  if self.cboxDilate2.isChecked()    else 0,
            "trim_header"   : self.sliderTrimHeader.value() if self.cboxTrimHeader.isChecked() else 0,
            "trim_footer"   : self.sliderTrimFooter.value() if self.cboxTrimFooter.isChecked() else self.sliderTrimFooter.maximum(),
            "trim_left"     : self.sliderTrimLeft.value()   if self.cboxTrimLeft.isChecked()   else 0,
            "trim_right"    : self.sliderTrimRight.value()  if self.cboxTrimRight.isChecked()  else self.sliderTrimRight.maximum(),
            "inverse_mask"  : self.cboxInverseMask.isChecked(),
        }


    def saveSettings(self):
        self.settings["profile"]["default"] = self.snapshotCurrentProfile()
        self.settings["folders"] = []
        self.settings["plugins"] = []

        for ndx in range(self.cboxFolderName.count()):
            path = self.cboxFolderName.itemData(ndx)
            self.settings["folders"].append(path)

        plugin_basepath = os.path.join(os.path.dirname(__file__), "plugins")

        for ndx in range(self.cboxSwitchPluginFile.count() - 1, -1, -1):
            path = self.cboxSwitchPluginFile.itemData(ndx)
            if not os.path.exists(path):
                self.cboxSwitchPluginFile.removeItem(ndx)
                continue

            if os.path.dirname(path) != plugin_basepath:
                self.settings["plugins"].insert(0, path)

        try:
            with open("HsvRangeTool.json", "w") as fp:
                json.dump(self.settings, fp, indent=4)
        except BaseException as e:
            print("Unable to save settings to HsvRangeTool.json: " + repr(e))


    def onActivateProfile(self):
        profile = self.cboxProfile.currentText()
        if profile not in ("", "default"):
            if profile in self.settings["profile"]:
                self.syncProfile(self.settings["profile"].get(profile, {}))
            else:
                self.settings["profile"][profile] = self.snapshotCurrentProfile()


    def onSnapshotProfile(self):
        profile = self.cboxProfile.currentText()

        if profile in ("", "default"):
            self.cboxProfile.clearEditText()
        else:
            ndx = self.cboxProfile.findText(profile, Qt.MatchExactly)

            if ndx < 0:
                self.cboxProfile.insertItem(0, profile)
                self.cboxProfile.setCurrentIndex(0)

            self.settings["profile"][profile] = self.snapshotCurrentProfile()


    def onDeleteProfile(self):
        ndx = self.cboxProfile.currentIndex()
        if ndx >= 0:
            profile = self.cboxProfile.currentText()
            self.cboxProfile.setCurrentIndex(-1)
            self.cboxProfile.removeItem(ndx)

            if profile not in ("", "default") and profile in self.settings["profile"]:
                del self.settings["profile"][profile]


    def onResetProfile(self):
        self.syncProfile({})


    def _loadPluginFile(self, filePath):
        self.pluginOutput.setPlainText("")
        self.plugin = None

        if filePath:
            found = False
            for ndx in range(self.cboxSwitchPluginFile.count()):
                if self.cboxSwitchPluginFile.itemData(ndx) == filePath:
                    self.cboxSwitchPluginFile.setCurrentIndex(ndx)
                    found = True
                    break

            if not found:
                fileName = os.path.basename(filePath)
                ndx = self.cboxSwitchPluginFile.findText(fileName, Qt.MatchExactly)

                dup = 0
                while ndx >= 0:
                    dup += 1
                    ndx = self.cboxFolderName.findText(f"{fileName}({dup})", Qt.MatchExactly)

                if dup > 0:
                    fileName = f"{fileName}({dup})"

                self.cboxSwitchPluginFile.insertItem(0, fileName, filePath)
                self.cboxSwitchPluginFile.setCurrentIndex(0)

                while self.cboxSwitchPluginFile.count() > 20:
                    self.cboxSwitchPluginFile.removeItem(self.cboxSwitchPluginFile.count() - 1)

            try:
                _spec   = importlib.util.spec_from_file_location("plugin", filePath)
                _plugin = importlib.util.module_from_spec(_spec)
                _spec.loader.exec_module(_plugin)

                if 'process_image' in _plugin.__dict__:
                    self.plugin = _plugin
                    self.pluginOutput.setPlainText("")
                    self.refreshAllImg()
                else:
                    self.pluginOutput.setPlainText(f"Missing process_image function while loading plugin file {filePath}\n\n"
                        "# example source code:\n"
                        "import cv2\n\n"
                        "def process_image(image, mask):\n"
                        "   output = cv2.bitwise_and(image, image, mask=mask)\n"
                        "   return output, {}\n\n"
                    )

            except BaseException as e:
                import traceback
                self.pluginOutput.setPlainText(f"Exception occurred while loading plugin file {filePath}: {str(e)}\n{traceback.format_exc()}")


    def onOpenPluginFile(self):
        options     = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*);;Python3 Source (*.py)", options=options)

        if not filePath:
            return

        self._loadPluginFile(filePath)


    def onSwitchPluginFile(self):
        ndx = self.cboxSwitchPluginFile.currentIndex()
        if ndx >= 0:
            filePath = self.cboxSwitchPluginFile.itemData(ndx)
            self._loadPluginFile(filePath)


    def onDropPluginFile(self):
        ndx = self.cboxSwitchPluginFile.currentIndex()
        if ndx >= 0:
            plugin_basepath = os.path.join(os.path.dirname(__file__), "plugins")

            if os.path.dirname(self.cboxSwitchPluginFile.itemData(ndx)) != plugin_basepath:
                self.cboxSwitchPluginFile.setCurrentIndex(-1)
                self.cboxSwitchPluginFile.removeItem(ndx)
                self._loadPluginFile(None)


    def onReloadPluginFile(self):
        ndx = self.cboxSwitchPluginFile.currentIndex()
        if ndx >= 0:
            filePath = self.cboxSwitchPluginFile.itemData(ndx)
            self._loadPluginFile(filePath)


    def onUnloadPluginFile(self):
        self.cboxSwitchPluginFile.setCurrentIndex(-1)
        self._loadPluginFile(None)


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
