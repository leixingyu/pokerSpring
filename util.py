import logging
import math
import random
import os

import maya.cmds as cmds

advance = 1

MODULE_PATH = os.path.dirname(__file__)
TEXTURES = r'cards'

texture_dir = os.path.join(MODULE_PATH, TEXTURES)


def delete_node():
    if (cmds.ls('Deck')):
        cmds.delete('Deck')
    cmds.group(em=1, name='Deck')

    if (cmds.ls('curveLengthNode*', 'influencePmultiplierNode*', 'finalRotationNode*', 'addDoubleLinear*', 'PokerMat*')):
        nodes = cmds.ls('curveLengthNode*', 'influencePmultiplierNode*', 'finalRotationNode*', 'addDoubleLinear*', 'PokerMat*', 'place2dTexture*')
        cmds.delete(nodes)


# TODO: find out what is hold value doing
def build_deck(num=54, stack=0.015, hold_value=1.5):

    # identify if the hold value needs to decrease
    if (hold_value * num > 100):
        logging.error('the hold value needs to decrease')
    intv = stack / num  # interval between each cards

    # build card and attach to motion path
    for i in range(0, num):
        offset_group = cmds.group(em=1, name='car_offsetGrp_'+str(i))
        if not advance:
            card = cmds.polyPlane(height=3.5, width=2.5, sw=1, sh=1, name='card_' + str(i))
        elif advance:
            card = cmds.polyPlane(height= 3.5, width=2.5, sw=1, sh=10,  name='card_'+str(i))
        cmds.parent(card[0], offset_group)
        cmds.pathAnimation(offset_group, curve='pokerPath', f=1, fm=1, name='mopathtest' + str(i))
        card_pos = i * intv
        cmds.setAttr('mopathtest%s.uValue' % str(i), card_pos)
        cmds.addAttr(at='float', k=1, h=0, ln='pathValue')
        cmds.parent(offset_group, 'Deck')

    cards = cmds.ls('card*', transforms=1)

    for i, card in enumerate(cards):
        start_pos = i * intv
        end_pos = 1 - (stack - start_pos)
        cmds.setDrivenKeyframe(card + '.pathValue', currentDriver='pokerPath.completion', dv=0, v=start_pos)
        cmds.setDrivenKeyframe(card + '.pathValue', currentDriver='pokerPath.completion', dv=100, v=end_pos)
        cmds.setDrivenKeyframe(card+ '.pathValue', currentDriver='pokerPath.completion', dv=0+(num - i) * hold_value, v=start_pos)
        cmds.setDrivenKeyframe(card+ '.pathValue', currentDriver='pokerPath.completion', dv=100-i * hold_value, v=end_pos)

        cmds.connectAttr(card + '.pathValue', 'mopathtest%s.uValue' % str(i), force=1)
        cmds.keyTangent(card, lock=0, itt='auto', ott='auto', index=[(1, 1), (2, 2)])

    connect_node(cards)
    assign_texture(cards)
    if advance:
        add_bend()
    randomize_offset(cards)


def connect_node(cards):
    left_ctrl = cmds.ls('leftc')[0]
    right_ctrl = cmds.ls('rightc')[0]

    cv_length_diff = cmds.shadingNode('plusMinusAverage', asUtility=1, name='curveLengthNode')
    cmds.connectAttr(right_ctrl+'.rx', cv_length_diff+'.input1D[0]')
    cmds.connectAttr(left_ctrl+'.rx', cv_length_diff+'.input1D[1]')
    cmds.setAttr(cv_length_diff+'.operation', 2)

    for i, card in enumerate(cards):
        # connect the front twist node to the start and end controller
        influence_mult = cmds.shadingNode('multiplyDivide', asUtility=1, name='influencePmultiplierNode')
        cmds.setAttr(influence_mult + '.operation', 1)
        cmds.connectAttr('mopathtest%s.uValue' % str(i), influence_mult + '.input1X')
        cmds.connectAttr(cv_length_diff + '.output1D', influence_mult + '.input2X')

        rot_cal = cmds.shadingNode('plusMinusAverage', asUtility=1, name='finalRotationNode')
        cmds.setAttr(rot_cal + '.operation', 1)
        cmds.connectAttr(influence_mult + '.outputX', rot_cal + '.input1D[0]')
        cmds.connectAttr(left_ctrl + '.rx', rot_cal + '.input1D[1]')

        cmds.connectAttr(rot_cal+'.output1D', 'mopathtest%s.frontTwist' % str(i), f=1)


def add_bend():
    cards = cmds.ls('card*', transforms=1)
    for card in cards:
        bend = cmds.nonLinear(card, type='bend')[1]
        if not cmds.ls('bendHandleLayer'):
            cmds.createDisplayLayer(nr=1, name='bendHandleLayer')
        else:
            cmds.editDisplayLayerMembers('bendHandleLayer', bend )
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
    connect_texture(texture_dir+'/back.png', 'PokerMatBack', 'color')
    cmds.shadingNode('samplerInfo', asUtility=1, name='flippedNormalDetectNode')

    # shuffle card front texture
    for i, card in enumerate(cards):
        material = cmds.shadingNode('phong', asShader=1, name='PokerMat_%s' % str(i))
        connect_texture(texture_dir+'/alpha.png', material, 'transparency')

        cmds.shadingNode('phong', asShader=1, name='PokerMatFront_%s' % str(i))

        condition = cmds.shadingNode('condition', asUtility=1, name='conditionNode_%s' % str(i))
        cmds.connectAttr('PokerMatFront_%s.outColor' % str(i), condition + '.colorIfTrue', force=1)
        cmds.connectAttr('PokerMatBack.outColor', condition + '.colorIfFalse', force=1)
        cmds.connectAttr('flippedNormalDetectNode.flippedNormal', condition + '.firstTerm')
        cmds.connectAttr(condition + '.outColor', 'PokerMat_%s.color' % str(i))

        cmds.select(card)
        cmds.hyperShade(assign=material)
        cmds.polyContourProjection()

    shuffle_cards(cards, texture_dir)

    place2ds = cmds.ls('place2dTexture*')
    for place2d in place2ds:
        if advance:
            cmds.setAttr(place2d+'.rotateFrame', 90)


def shuffle_cards(cards=cmds.ls('card*', transforms=1), directory=texture_dir):
    card_front = get_card_front(directory)
    random.shuffle(card_front)
    for i in range(len(cards)):
        connect_texture(os.path.join(directory, card_front[i]), 'PokerMatFront_%s' % str(i), 'color')
    logging.info('shuffled')


def randomize_offset(cards):
    for i, card in enumerate(cards):
        bend = cmds.ls('bend%s' % str(i + 1))[0]
        offset_x = random.randint(-40, 40)
        offset_y = random.randint(-60, 60)
        offset_z = random.randint(-40, 40)

        cmds.setDrivenKeyframe(card + '.rx', currentDriver=card + '.pathValue', dv=0.5, v=offset_x)
        cmds.setDrivenKeyframe(card + '.ry', currentDriver=card + '.pathValue', dv=0.5, v=offset_y)
        cmds.setDrivenKeyframe(card + '.rz', currentDriver=card + '.pathValue', dv=0.5, v=offset_z)
        cmds.setDrivenKeyframe(bend + '.curvature', currentDriver=card + '.pathValue', dv=0.5, v=random.randint(20, 30))
        cmds.setDrivenKeyframe(bend + '.curvature', currentDriver=card + '.pathValue', dv=0.1, v=0)
        cmds.setDrivenKeyframe(bend + '.curvature', currentDriver=card + '.pathValue', dv=0.9, v=0)
        for axis in 'xyz':
            cmds.setDrivenKeyframe(card + '.r'+axis, currentDriver=card + '.pathValue', dv=0.1, v=0)
            cmds.setDrivenKeyframe(card + '.r' + axis, currentDriver=card + '.pathValue', dv=0.9, v=0)


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
        cmds.keyTangent(card+'.pathValue', index=[(1, 1)], oa=angle)
        # in angle of the second tangent
        cmds.keyTangent(card+'.pathValue', index=[(2, 2)], ia=angle)


def connect_texture(image, material, input_node):
    # if a file texture is already connected to this input, update it
    # otherwise, delete it
    conn = cmds.listConnections(material+'.'+input_node, type='file')
    if conn:
        # there is a file texture connected. replace it
        cmds.setAttr(conn[0]+'.fileTextureName', image, type='string')
    else:
        # no connected file texture, so make a new one
        new_file = cmds.shadingNode('file', asTexture=1)
        new_placer = cmds.shadingNode('place2dTexture', asUtility=1)

        # make common connections between place2dTexture and file texture
        connections = ['rotateUV', 'offset', 'noiseUV', 'vertexCameraOne', 'vertexUvThree', 'vertexUvTwo', 'vertexUvOne', 'repeatUV', 'wrapV', 'wrapU', 'stagger', 'mirrorU', 'mirrorV', 'rotateFrame', 'translateFrame', 'coverage']
        cmds.connectAttr(new_placer+'.outUV', new_file+'.uvCoord')
        cmds.connectAttr(new_placer+'.outUvFilterSize', new_file+'.uvFilterSize')
        for i in connections:
            cmds.connectAttr(new_placer+'.'+i, new_file+'.'+i)

        # now connect the file texture output to the material input
        cmds.connectAttr(new_file+'.outColor', material+'.'+input_node, f=1)

        # now set attributes on the file node.
        cmds.setAttr(new_file+'.fileTextureName', image, type='string')
        cmds.setAttr(new_file+'.filterType', 0)
