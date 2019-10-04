import maya.cmds as cmds
import os
import math

class Poker(object):

    def __init__(self, num=54, stack=0.015, holdValue=1.5):
        self.num = num  # number of cards
        self.stack = stack  # the length of the deck
        self.intv = self.stack / self.num  # interval between each cards
        self.cardPos = 0.00  # init position of the card
        self.holdValue = holdValue
        self.deleteNode()
        #self.buildDeck()

    def deleteNode(self):
        if (cmds.ls('curveLengthNode*', 'influencePmultiplierNode*', 'finalRotationNode*', 'addDoubleLinear*', 'PokerMat*')):
            nodes = cmds.ls('curveLengthNode*', 'influencePmultiplierNode*', 'finalRotationNode*', 'addDoubleLinear*', 'PokerMat*', 'place2dTexture*')
            cmds.delete(nodes)

    def buildDeck(self):
        if (cmds.ls('Deck')):
            cmds.delete('Deck')
        group = cmds.group(em=True, name='Deck')

        for i in range(0, self.num):
            offsetGroup = cmds.group(em=True, name='car_offsetGrp_'+str(i))
            card = cmds.polyCube(height=0.01, width=2.5, depth=3.5, name='card_'+str(i))
            cmds.parent(card[0], offsetGroup)
            cmds.pathAnimation(offsetGroup, curve='pokerPath', f=True, fm=True, name='mopathtest' + str(i))
            cardPos = i * self.intv
            cmds.setAttr('mopathtest%s.uValue' % str(i), cardPos)
            cmds.addAttr(at='float', k=True, h=False, ln='pathValue')
            cmds.parent(offsetGroup, group)

        if (self.holdValue * self.num > 100):
            print('the hold value needs to decrease')

        cards = cmds.ls('card*', transforms=True)
        midCtrl = cmds.ls('midc')[0]
        leftCtrl = cmds.ls('leftc')[0]
        rightCtrl = cmds.ls('rightc')[0]

        cvLengthDiff = cmds.shadingNode('plusMinusAverage', asUtility=True, name='curveLengthNode')
        cmds.connectAttr(rightCtrl+'.rz', cvLengthDiff+'.input1D[0]')
        cmds.connectAttr(leftCtrl+'.rz', cvLengthDiff+'.input1D[1]')
        cmds.setAttr(cvLengthDiff+'.operation', 2)

        cmds.shadingNode('phong', asShader=True, name='PokerMatBack')

        for i, card in enumerate(cards):
            startPos = i * self.intv
            endPos = 1 - (self.stack - startPos)
            cmds.setDrivenKeyframe(card + '.pathValue', currentDriver=midCtrl+'.completion', dv=0, v=startPos)
            cmds.setDrivenKeyframe(card + '.pathValue', currentDriver=midCtrl+'.completion', dv=100, v=endPos)
            cmds.setDrivenKeyframe(card + '.pathValue', currentDriver=midCtrl+'.completion', dv=0 + (self.num - i) * self.holdValue, v=startPos)
            cmds.setDrivenKeyframe(card + '.pathValue', currentDriver=midCtrl+'.completion', dv=100 - i * self.holdValue, v=endPos)

            cmds.connectAttr(card + '.pathValue', 'mopathtest%s.uValue' % str(i), force=True)
            cmds.keyTangent(card, lock=False, itt='auto', ott='auto', index=[(1, 1), (2, 2)])

            influenceMult = cmds.shadingNode('multiplyDivide', asUtility=True, name='influencePmultiplierNode')
            cmds.setAttr(influenceMult+'.operation', 1)
            cmds.connectAttr('mopathtest%s.uValue' % str(i), influenceMult+'.input1X')
            cmds.connectAttr(cvLengthDiff+'.output1D', influenceMult+'.input2X')

            rotCal = cmds.shadingNode('plusMinusAverage', asUtility=True, name='finalRotationNode')
            cmds.setAttr(rotCal+'.operation', 1)
            cmds.connectAttr(influenceMult+'.outputX', rotCal+'.input1D[0]')
            cmds.connectAttr(leftCtrl+'.rz', rotCal+'.input1D[1]')

            reverseNode = cmds.shadingNode('reverse', asUtility=True, name='reverseNode')
            cmds.connectAttr(rotCal+'.output1D', reverseNode+'.inputX')
            cmds.connectAttr(reverseNode+'.outputX', 'mopathtest%s.frontTwist' % str(i), f=True)

            #Texture for faces
            frontFace = card+'.f[1]'
            backFace = card+'.f[3]'

            cmds.shadingNode('phong', asShader=True, name='PokerMat_%s' % str(i))
            cmds.select(frontFace)
            cmds.hyperShade(assign='PokerMat_%s' % str(i))

            cmds.select(backFace)
            cmds.hyperShade(assign='PokerMatBack')

        textureDir = 'C:/Users/Lei/Desktop/cardTexture'
        files = os.listdir(textureDir)

        for i in range(len(cmds.ls('card_*', transforms=True))):
            if files[i] != 'back.png':
                self.connectTex(textureDir + '/' + files[i], 'PokerMat_%s' % str(i), 'color')
            else:
                self.connectTex(textureDir + '/' + files[i+1], 'PokerMat_%s' % str(i), 'color')
            cmds.select('card_%s.f[1]' % str(i))
            cmds.polyContourProjection()

        for card in cmds.ls('card_*', transforms=True):
            cmds.select(card+'.f[3]')
            cmds.polyContourProjection()
        self.connectTex(textureDir + '/back.png', 'PokerMatBack', 'color')

        place2ds = cmds.ls('place2dTexture*')
        for place2d in place2ds:
            cmds.setAttr(place2d+'.rotateFrame', 90)

    def setTangnet(self, value):
        # edit tangent
        tan = 1.00 / (100 - self.num * self.holdValue)

        sinAngle = 0  # slow in slow out
        flatAngle = math.atan(tan) * 2  # flat
        cosAngle = 3.14 * flatAngle  # slow in mid

        if value is -1:
            self.setAngle(sinAngle)
        elif value is 0:
            self.setAngle(flatAngle)
        elif value is 1:
            self.setAngle(cosAngle)

    def setAngle(self, angle):
        cubes = cmds.ls('card*', transforms=True)
        for card in cubes:
            # out angle of the first tangent
            cmds.keyTangent(card, index=[(1, 1)], oa=angle)
            # in angle of the second tangent
            cmds.keyTangent(card, index=[(2, 2)], ia=angle)

    def connectTex(self, image, material, input):
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