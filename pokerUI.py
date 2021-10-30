import os

import maya.cmds as cmds

from utility._vendor.Qt import QtWidgets, QtCore, QtGui
from utility._vendor.Qt import _loadUi

import util
reload(util)

MODULE_PATH = os.path.dirname(__file__)
UI_FILE = r'ui/pokerSpring.ui'


class PokerUI(QtWidgets.QMainWindow):
    def __init__(self):

        super(PokerUI, self).__init__()

        _loadUi(os.path.join(MODULE_PATH, UI_FILE), self)

        self.numEdit.setText('54')
        self.stackEdit.setText('0.015')
        self.offsetEdit.setText('1.5')

        self.buildButton.clicked.connect(self.build)
        self.ui_suffle_btn.clicked.connect(self.shuffle)
        self.ratioSlider.valueChanged.connect(self.completion_link)
        self.tangentBox.currentIndexChanged.connect(self.tangent_link)

    @staticmethod
    def shuffle(self):
        util.shuffle_cards(util.texture_dir)

    def build(self):
        num = int(self.numEdit.text())
        stack = float(self.stackEdit.text())
        offset = float(self.offsetEdit.text())
        util.delete_node()
        util.build_deck(num=num, stack=stack, hold_value=offset)

    def completion_link(self):
        slider_v = self.ratioSlider.value()
        cmds.setAttr('pokerPath.completion', slider_v)

    def tangent_link(self):
        tangent_v = self.tangentBox.currentIndex()
        util.set_tangent(tangent_v)


def show():
    global window
    window = PokerUI()
    window.show()
    return window


if __name__ == "__main__":
    window = show()



