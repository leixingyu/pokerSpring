import os

import maya.cmds as cmds

from utility._vendor.Qt import QtWidgets, QtCore, QtGui
from utility._vendor.Qt import _loadUi

import pokerSpringFunc
reload(pokerSpringFunc)

MODULE_PATH = os.path.dirname(__file__)
UI_FILE = r'ui/pokerSpring.ui'


class PokerUI(QtWidgets.QMainWindow):
    def __init__(self):

        super(PokerUI, self).__init__()

        _loadUi(os.path.join(MODULE_PATH, UI_FILE), self)

        self.linkFunc()

    def linkFunc(self):
        self.numEdit.setText('54')
        self.stackEdit.setText('0.015')
        self.offsetEdit.setText('1.5')

        self.buildButton.clicked.connect(self.build)
        self.ui_suffle_btn.clicked.connect(self.shuffle)
        self.ratioSlider.valueChanged.connect(self.completionLink)
        self.tangentBox.currentIndexChanged.connect(self.tangentLink)

    def shuffle(self):
        pokerSpringFunc.shuffleCards(textureDir=pokerSpringFunc.textureDir)

    def build(self):
        num = int(self.numEdit.text())
        stack = float(self.stackEdit.text())
        offset = float(self.offsetEdit.text())
        pokerSpringFunc.deleteNode()
        pokerSpringFunc.buildDeck(num=num, stack=stack, holdValue=offset)

    def completionLink(self):
        sliderV = self.ratioSlider.value()
        cmds.setAttr('pokerPath.completion', sliderV)

    def tangentLink(self):
        tangentV = self.tangentBox.currentIndex()
        pokerSpringFunc.setTangent(tangentV)


def show():
    global window
    window = PokerUI()
    window.show()
    return window


if __name__ == "__main__":
    window = show()



