import os

import maya.cmds as cmds
from Qt import QtWidgets
from Qt import _loadUi

import util

MODULE_PATH = os.path.dirname(__file__)
UI_FILE = r'ui/pokerSpring.ui'


class PokerUI(QtWidgets.QMainWindow):
    def __init__(self):
        super(PokerUI, self).__init__()

        _loadUi(os.path.join(MODULE_PATH, UI_FILE), self)

        self.ui_num_edit.setText('54')
        self.ui_stack_edit.setText('0.015')
        self.ui_offset_edit.setText('1.5')

        self.ui_build_btn.clicked.connect(self.build)
        self.ui_suffle_btn.clicked.connect(self.shuffle)
        self.ui_ratio_slider.valueChanged.connect(self.completion_link)
        self.ui_tangent_cbox.currentIndexChanged.connect(self.tangent_link)

    @staticmethod
    def shuffle():
        util.shuffle_cards(util.TEXTURE_DIR)

    def build(self):
        num = int(self.ui_num_edit.text())
        stack = float(self.ui_stack_edit.text())
        offset = float(self.ui_offset_edit.text())

        util.delete_previous()
        cards = util.build_deck(num=num, stack=stack, hold_value=offset)
        util.connect_node(cards)
        util.assign_texture(cards)
        #util.shuffle_cards(cards)
        util.add_bend(cards)
        util.randomize_offset(cards)

    def completion_link(self):
        slider_v = self.ui_ratio_slider.value()
        cmds.setAttr('pokerPath.completion', slider_v)

    def tangent_link(self):
        tangent_v = self.ui_tangent_cbox.currentIndex()
        util.set_tangent(tangent_v)


def show():
    global window
    window = PokerUI()
    window.show()
    return window


if __name__ == "__main__":
    window = show()



