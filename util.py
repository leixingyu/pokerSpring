import logging
import math
import random
import os

import maya.cmds as cmds

MODULE_PATH = os.path.dirname(__file__)
TEXTURE_FOLDER = r'cards'

TEXTURE_DIR = os.path.join(MODULE_PATH, TEXTURE_FOLDER)

DECK_GROUP = r'Deck'


def delete_previous():
    nodes = cmds.ls(
        'curveLengthNode*',
        'influencePmultiplierNode*',
        'finalRotationNode*',
        'addDoubleLinear*',
        'PokerMat*',
        'place2dTexture*'
    )
    group = cmds.ls(DECK_GROUP)

    cmds.delete(nodes, group)


# TODO: find out what is hold value doing
def build_deck(num=54, stack=0.015, hold_value=1.5):

    cmds.group(em=1, name=DECK_GROUP)

    # identify if the hold value needs to decrease
    if hold_value * num > 100:
        logging.error('the hold value needs to decrease')
    intv = stack / num  # interval between each cards

    # build card and attach to motion path
    for i in range(0, num):
        offset_group = cmds.group(em=1, name='offsetGrp_{}'.format(i))
        card = cmds.polyPlane(height=3.5, width=2.5, sw=1, sh=10, name='card_{}'.format(i))
        cmds.parent(card[0], offset_group)
        cmds.pathAnimation(offset_group, curve='pokerPath', f=1, fm=1, name='motion_path{}'.format(i))
        card_pos = i * intv
        cmds.setAttr('motion_path%s.uValue' % str(i), card_pos)
        cmds.addAttr(at='float', k=1, h=0, ln='pathValue')
        cmds.parent(offset_group, DECK_GROUP)

    cards = cmds.ls('card*', transforms=1)

    for i, card in enumerate(cards):
        start_pos = i * intv
        end_pos = 1 - (stack - start_pos)
        cmds.setDrivenKeyframe('{}.pathValue'.format(card), currentDriver='pokerPath.completion', dv=0, v=start_pos)
        cmds.setDrivenKeyframe('{}.pathValue'.format(card), currentDriver='pokerPath.completion', dv=100, v=end_pos)
        cmds.setDrivenKeyframe('{}.pathValue'.format(card), currentDriver='pokerPath.completion', dv=0+(num - i) * hold_value, v=start_pos)
        cmds.setDrivenKeyframe('{}.pathValue'.format(card), currentDriver='pokerPath.completion', dv=100-i * hold_value, v=end_pos)

        cmds.connectAttr('{}.pathValue'.format(card), 'motion_path{}.uValue'.format(i), force=1)
        cmds.keyTangent(card, lock=0, itt='auto', ott='auto', index=[(1, 1), (2, 2)])

    connect_node(cards)
    assign_texture(cards)
    add_bend()
    randomize_offset(cards)


def connect_node(cards):
    left_ctrl = cmds.ls('leftc')[0]
    right_ctrl = cmds.ls('rightc')[0]

    cv_length_diff = cmds.shadingNode('plusMinusAverage', asUtility=1, name='curveLengthNode')
    cmds.connectAttr('{}.rx'.format(right_ctrl), '{}.input1D[0]'.format(cv_length_diff))
    cmds.connectAttr('{}.rx'.format(left_ctrl), '{}.input1D[1]'.format(cv_length_diff))
    cmds.setAttr('{}.operation'.format(cv_length_diff), 2)

    for i, card in enumerate(cards):
        # connect the front twist node to the start and end controller
        influence_mult = cmds.shadingNode('multiplyDivide', asUtility=1, name='influencePmultiplierNode')
        cmds.setAttr('{}.operation'.format(influence_mult), 1)
        cmds.connectAttr('motion_path{}.uValue'.format(i), influence_mult + '.input1X')
        cmds.connectAttr('{}.output1D'.format(cv_length_diff), influence_mult + '.input2X')

        rot_cal = cmds.shadingNode('plusMinusAverage', asUtility=1, name='finalRotationNode')
        cmds.setAttr('{}.operation'.format(rot_cal), 1)
        cmds.connectAttr('{}.outputX'.format(influence_mult), '{}.input1D[0]'.format(rot_cal))
        cmds.connectAttr('{}.rx'.format(left_ctrl), '{}.input1D[1]'.format(rot_cal))

        cmds.connectAttr('{}.output1D'.format(rot_cal), 'motion_path{}.frontTwist'.format(i), f=1)


def add_bend():
    cards = cmds.ls('card*', transforms=1)
    for card in cards:
        bend = cmds.nonLinear(card, type='bend')[1]
        if not cmds.ls('bendHandleLayer'):
            cmds.createDisplayLayer(nr=1, name='bendHandleLayer')
        else:
            cmds.editDisplayLayerMembers('bendHandleLayer', bend)
        cmds.parent(bend, card)
        cmds.setAttr(bend+'.rx', 90)
        cmds.setAttr(bend+'.ry', 0)
        cmds.setAttr(bend+'.rz', 90)


def get_card_front(directory):
    files = os.listdir(directory)
    card_front = []
    for f in files:
        if f != 'back.png' and f != 'alpha.png':
            card_front.append(f)
    return card_front


def assign_texture(cards):
    # assign card back textures
    cmds.shadingNode('phong', asShader=1, name='PokerMatBack')
    connect_texture(os.path.join(TEXTURE_DIR, 'back.png'), 'PokerMatBack', 'color')
    cmds.shadingNode('samplerInfo', asUtility=1, name='flippedNormalDetectNode')

    # shuffle card front texture
    for i, card in enumerate(cards):
        material = cmds.shadingNode('phong', asShader=1, name='PokerMat_%s' % str(i))
        connect_texture(os.path.join(TEXTURE_DIR, 'alpha.png'), material, 'transparency')

        cmds.shadingNode('phong', asShader=1, name='PokerMatFront_%s' % str(i))

        condition = cmds.shadingNode('condition', asUtility=1, name='conditionNode_{}'.format(i))
        cmds.connectAttr('PokerMatFront_{}.outColor'.format(i), '{}.colorIfTrue'.format(condition), force=1)
        cmds.connectAttr('PokerMatBack.outColor', '{}.colorIfFalse'.format(condition), force=1)
        cmds.connectAttr('flippedNormalDetectNode.flippedNormal', '{}.firstTerm'.format(condition))
        cmds.connectAttr('{}.outColor'.format(condition), 'PokerMat_{}.color'.format(i))

        cmds.select(card)
        cmds.hyperShade(assign=material)
        cmds.polyContourProjection()

    shuffle_cards(cards, TEXTURE_DIR)

    place2ds = cmds.ls('place2dTexture*')
    for place2d in place2ds:
        cmds.setAttr(place2d+'.rotateFrame', 90)


def shuffle_cards(cards=cmds.ls('card*', transforms=1), directory=TEXTURE_DIR):
    card_front = get_card_front(directory)
    random.shuffle(card_front)
    for i in range(len(cards)):
        connect_texture(os.path.join(directory, card_front[i]), 'PokerMatFront_{}'.format(i), 'color')
    logging.info('shuffled')


def randomize_offset(cards):
    for i, card in enumerate(cards):
        bend = cmds.ls('bend{}'.format(i + 1))[0]
        offset_x = random.randint(-40, 40)
        offset_y = random.randint(-60, 60)
        offset_z = random.randint(-40, 40)

        cmds.setDrivenKeyframe('{}.rx'.format(card), currentDriver='{}.pathValue'.format(card), dv=0.5, v=offset_x)
        cmds.setDrivenKeyframe('{}.ry'.format(card), currentDriver='{}.pathValue'.format(card), dv=0.5, v=offset_y)
        cmds.setDrivenKeyframe('{}.rz'.format(card), currentDriver='{}.pathValue'.format(card), dv=0.5, v=offset_z)
        cmds.setDrivenKeyframe('{}.curvature'.format(bend), currentDriver='{}.pathValue'.format(card), dv=0.5, v=random.randint(20, 30))
        cmds.setDrivenKeyframe('{}.curvature'.format(bend), currentDriver='{}.pathValue'.format(card), dv=0.1, v=0)
        cmds.setDrivenKeyframe('{}.curvature'.format(bend), currentDriver='{}.pathValue'.format(card), dv=0.9, v=0)
        for axis in 'xyz':
            cmds.setDrivenKeyframe('{}.r{}'.format(card, axis), currentDriver='{}.pathValue'.format(card), dv=0.1, v=0)
            cmds.setDrivenKeyframe('{}.r{}'.format(card, axis), currentDriver='{}.pathValue'.format(card), dv=0.9, v=0)


def set_tangent(value, num=54, hold_value=1.5):
    # edit tangent
    tan = 1.00 / (100-num * hold_value)

    # calculate the corresponding angle for different tangent
    sin_angle = 0  # slow in slow out
    flat_angle = math.atan(tan) * 2  # flat
    cos_angle = 3.14 * flat_angle  # slow in mid

    if value is 2:
        set_angle(sin_angle)
    elif value is 0:
        set_angle(flat_angle)
    elif value is 1:
        set_angle(cos_angle)


def set_angle(angle):
    cards = cmds.ls('card*', transforms=1)
    for card in cards:
        # out angle of the first tangent
        cmds.keyTangent('{}.pathValue'.format(card), index=[(1, 1)], oa=angle)
        # in angle of the second tangent
        cmds.keyTangent('{}.pathValue'.format(card), index=[(2, 2)], ia=angle)


def connect_texture(image, material, input_node):
    # if a file texture is already connected to this input, update it
    # otherwise, delete it
    conn = cmds.listConnections('{}.{}'.format(material, input_node), type='file')
    if conn:
        # there is a file texture connected. replace it
        cmds.setAttr('{}.fileTextureName'.format(conn[0]), image, type='string')
    else:
        # no connected file texture, so make a new one
        new_file = cmds.shadingNode('file', asTexture=1)
        new_placer = cmds.shadingNode('place2dTexture', asUtility=1)

        # make common connections between place2dTexture and file texture
        connections = ['rotateUV',
                       'offset',
                       'noiseUV',
                       'vertexCameraOne',
                       'vertexUvThree',
                       'vertexUvTwo',
                       'vertexUvOne',
                       'repeatUV',
                       'wrapV',
                       'wrapU',
                       'stagger',
                       'mirrorU',
                       'mirrorV',
                       'rotateFrame',
                       'translateFrame',
                       'coverage'
                       ]

        cmds.connectAttr('{}.outUV'.format(new_placer), '{}.uvCoord'.format(new_file))
        cmds.connectAttr('{}.outUvFilterSize'.format(new_placer), '{}.uvFilterSize'.format(new_file))
        for i in connections:
            cmds.connectAttr('{}.{}'.format(new_placer, i), '{}.{}'.format(new_file, i))

        # now connect the file texture output to the material input
        cmds.connectAttr('{}.outColor'.format(new_file), '{}.{}'.format(material, input_node), f=1)

        # now set attributes on the file node.
        cmds.setAttr('{}.fileTextureName'.format(new_file), image, type='string')
        cmds.setAttr('{}.filterType'.format(new_file), 0)
