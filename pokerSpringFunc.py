import maya.cmds as cmds
import os
import math
import random

advance = True

MODULE_PATH = os.path.dirname(__file__)
TEXTURES = r'cardTexture'

textureDir = os.path.join(MODULE_PATH, TEXTURES)

def deleteNode():
    if (cmds.ls('Deck')):
        cmds.delete('Deck')
    cmds.group(em=True, name='Deck')

    if (cmds.ls('curveLengthNode*', 'influencePmultiplierNode*', 'finalRotationNode*', 'addDoubleLinear*', 'PokerMat*')):
        nodes = cmds.ls('curveLengthNode*', 'influencePmultiplierNode*', 'finalRotationNode*', 'addDoubleLinear*', 'PokerMat*', 'place2dTexture*')
        cmds.delete(nodes)


def buildDeck(num=54, stack=0.015, holdValue=1.5):

    # identify if the hold value needs to decrease
    if (holdValue * num > 100):
        print('the hold value needs to decrease')
    intv = stack / num  # interval between each cards

    # build card and attach to motion path
    for i in range(0, num):
        offsetGroup = cmds.group(em=True, name='car_offsetGrp_'+str(i))
        if not advance:
            card = cmds.polyPlane(height=3.5, width=2.5, sw=1, sh=1, name='card_' + str(i))
        elif advance:
            card = cmds.polyPlane(height= 3.5, width=2.5, sw=1, sh=10,  name='card_'+str(i))
        cmds.parent(card[0], offsetGroup)
        cmds.pathAnimation(offsetGroup, curve='pokerPath', f=True, fm=True, name='mopathtest' + str(i))
        cardPos = i * intv
        cmds.setAttr('mopathtest%s.uValue' % str(i), cardPos)
        cmds.addAttr(at='float', k=True, h=False, ln='pathValue')
        cmds.parent(offsetGroup, 'Deck')

    cards = cmds.ls('card*', transforms=True)

    for i, card in enumerate(cards):
        startPos = i * intv
        endPos = 1 - (stack - startPos)
        cmds.setDrivenKeyframe(card + '.pathValue', currentDriver='pokerPath.completion', dv=0, v=startPos)
        cmds.setDrivenKeyframe(card + '.pathValue', currentDriver='pokerPath.completion', dv=100, v=endPos)
        cmds.setDrivenKeyframe(card + '.pathValue', currentDriver='pokerPath.completion', dv=0 + (num - i) * holdValue, v=startPos)
        cmds.setDrivenKeyframe(card + '.pathValue', currentDriver='pokerPath.completion', dv=100 - i * holdValue, v=endPos)

        cmds.connectAttr(card + '.pathValue', 'mopathtest%s.uValue' % str(i), force=True)
        cmds.keyTangent(card, lock=False, itt='auto', ott='auto', index=[(1, 1), (2, 2)])

    connectNode(cards)
    assignTexture(cards)
    if advance:
        addBlend()
    randomOffest(cards)


def connectNode(cards):
    leftCtrl = cmds.ls('leftc')[0]
    rightCtrl = cmds.ls('rightc')[0]

    cvLengthDiff = cmds.shadingNode('plusMinusAverage', asUtility=True, name='curveLengthNode')
    cmds.connectAttr(rightCtrl+'.rx', cvLengthDiff+'.input1D[0]')
    cmds.connectAttr(leftCtrl+'.rx', cvLengthDiff+'.input1D[1]')
    cmds.setAttr(cvLengthDiff+'.operation', 2)

    for i, card in enumerate(cards):
        # connect the front twist node to the start and end controller
        influenceMult = cmds.shadingNode('multiplyDivide', asUtility=True, name='influencePmultiplierNode')
        cmds.setAttr(influenceMult + '.operation', 1)
        cmds.connectAttr('mopathtest%s.uValue' % str(i), influenceMult + '.input1X')
        cmds.connectAttr(cvLengthDiff + '.output1D', influenceMult + '.input2X')

        rotCal = cmds.shadingNode('plusMinusAverage', asUtility=True, name='finalRotationNode')
        cmds.setAttr(rotCal + '.operation', 1)
        cmds.connectAttr(influenceMult + '.outputX', rotCal + '.input1D[0]')
        cmds.connectAttr(leftCtrl + '.rx', rotCal + '.input1D[1]')

        #reverseNode = cmds.shadingNode('reverse', asUtility=True, name='reverseNode')
        #cmds.connectAttr(rotCal + '.output1D', reverseNode + '.inputX')
        #cmds.connectAttr(reverseNode + '.outputX', 'mopathtest%s.frontTwist' % str(i), f=True)

        cmds.connectAttr(rotCal+'.output1D', 'mopathtest%s.frontTwist' % str(i), f=True)


def addBlend():
    cards = cmds.ls('card*', transforms=True)
    for card in cards:
        bend = cmds.nonLinear(card, type='bend')[1]
        if not cmds.ls('bendHandleLayer'):
            cmds.createDisplayLayer(nr=True, name='bendHandleLayer')
        else:
            cmds.editDisplayLayerMembers('bendHandleLayer', bend )
        cmds.parent(bend, card)
        cmds.setAttr(bend+'.rx', 90)
        cmds.setAttr(bend+'.ry', 0)
        cmds.setAttr(bend+'.rz', 90)


def getCardFront(textureDir):
    files = os.listdir(textureDir)
    cardFront = []
    for file in files:
        if file != 'back.png' and file != 'alpha.png':
            cardFront.append(file)
    return cardFront


def assignTexture(cards):
    # assign card back textures
    cmds.shadingNode('phong', asShader=True, name='PokerMatBack')
    connectTex(textureDir + '/back.png', 'PokerMatBack', 'color')
    cmds.shadingNode('samplerInfo', asUtility=True, name='flippedNormalDetectNode')

    # shuffle card front texture
    for i, card in enumerate(cards):
        material = cmds.shadingNode('phong', asShader=True, name='PokerMat_%s' % str(i))
        connectTex(textureDir + '/alpha.png', material, 'transparency')

        cmds.shadingNode('phong', asShader=True, name='PokerMatFront_%s' % str(i))

        condition = cmds.shadingNode('condition', asUtility=True, name='conditionNode_%s' % str(i))
        cmds.connectAttr('PokerMatFront_%s.outColor' % str(i), condition + '.colorIfTrue', force=True)
        cmds.connectAttr('PokerMatBack.outColor', condition + '.colorIfFalse', force=True)
        cmds.connectAttr('flippedNormalDetectNode.flippedNormal', condition + '.firstTerm')
        cmds.connectAttr(condition + '.outColor', 'PokerMat_%s.color' % str(i))

        cmds.select(card)
        cmds.hyperShade(assign=material)
        cmds.polyContourProjection()

    shuffleCards(cards, textureDir)

    place2ds = cmds.ls('place2dTexture*')
    for place2d in place2ds:
        if advance:
            cmds.setAttr(place2d+'.rotateFrame', 90)


def shuffleCards(cards = cmds.ls('card*', transforms=True), textureDir=textureDir):
    print('shuffle')
    cardFront = getCardFront(textureDir)
    random.shuffle(cardFront)
    for i in range(len(cards)):
        connectTex(textureDir + '/' + cardFront[i], 'PokerMatFront_%s' % str(i), 'color')


def randomOffest(cards):
    for i, card in enumerate(cards):
        bend = cmds.ls('bend%s' % str(i + 1))[0]
        osX = random.randint(-40, 40)
        osY = random.randint(-60, 60)
        osZ = random.randint(-40, 40)
        cmds.setDrivenKeyframe(card + '.rx', currentDriver=card + '.pathValue', dv=0.5, v=osX)
        cmds.setDrivenKeyframe(card + '.ry', currentDriver=card + '.pathValue', dv=0.5, v=osY)
        cmds.setDrivenKeyframe(card + '.rz', currentDriver=card + '.pathValue', dv=0.5, v=osZ)
        cmds.setDrivenKeyframe(bend+'.curvature', currentDriver=card + '.pathValue', dv=0.5, v=random.randint(20, 30))
        cmds.setDrivenKeyframe(bend + '.curvature', currentDriver=card + '.pathValue', dv=0.1, v=0)
        cmds.setDrivenKeyframe(bend + '.curvature', currentDriver=card + '.pathValue', dv=0.9, v=0)
        for axis in 'xyz':
            cmds.setDrivenKeyframe(card + '.r'+axis, currentDriver=card + '.pathValue', dv=0.1, v=0)
            cmds.setDrivenKeyframe(card + '.r' + axis, currentDriver=card + '.pathValue', dv=0.9, v=0)


def setTangent(value, num=54, holdValue=1.5):
    # edit tangent
    tan = 1.00 / (100 - num * holdValue)

    # calculate the corresponding angle for different tangent
    sinAngle = 0  # slow in slow out
    flatAngle = math.atan(tan) * 2  # flat
    cosAngle = 3.14 * flatAngle  # slow in mid

    if value is 2:
        setAngle(sinAngle)
    elif value is 0:
        setAngle(flatAngle)
    elif value is 1:
        setAngle(cosAngle)


def setAngle(angle):
    cards = cmds.ls('card*', transforms=True)
    for card in cards:
        # out angle of the first tangent
        cmds.keyTangent(card+'.pathValue', index=[(1, 1)], oa=angle)
        # in angle of the second tangent
        cmds.keyTangent(card+'.pathValue', index=[(2, 2)], ia=angle)


def connectTex(image,material,input):
    # if a file texture is already connected to this input, update it
    # otherwise, delete it
    conn = cmds.listConnections(material+'.'+input, type='file')
    if conn:
        # there is a file texture connected. replace it
        cmds.setAttr(conn[0]+'.fileTextureName', image, type='string')
    else:
        # no connected file texture, so make a new one
        newFile = cmds.shadingNode('file', asTexture=1)
        newPlacer = cmds.shadingNode('place2dTexture', asUtility=1)
        # make common connections between place2dTexture and file texture
        connections = ['rotateUV', 'offset', 'noiseUV', 'vertexCameraOne', 'vertexUvThree', 'vertexUvTwo', 'vertexUvOne', 'repeatUV', 'wrapV', 'wrapU', 'stagger', 'mirrorU', 'mirrorV', 'rotateFrame', 'translateFrame', 'coverage']
        cmds.connectAttr(newPlacer+'.outUV', newFile+'.uvCoord')
        cmds.connectAttr(newPlacer+'.outUvFilterSize', newFile+'.uvFilterSize')
        for i in connections:
            cmds.connectAttr(newPlacer+'.'+i, newFile+'.'+i)
        # now connect the file texture output to the material input
        cmds.connectAttr(newFile+'.outColor', material+'.'+input, f=1)
        # now set attributes on the file node.
        cmds.setAttr(newFile+'.fileTextureName', image, type='string')
        cmds.setAttr(newFile+'.filterType', 0)
