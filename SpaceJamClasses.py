from direct.task import Task
from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from CollideObjectBase import *
from direct.task.Task import TaskManager
from typing import Callable
import DefensePaths as defensePaths

class Planet(SphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str,
        texPath: str, posVec: Vec3, scaleVec: float):
        super(Planet, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 1.5)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

class Universe(InverseSphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str,
        texPath: str, posVec: Vec3, scaleVec: float):
        super(Universe, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 0.9)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)


class SpaceStation(CapsuleCollidableObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str,
        posVec: Vec3, scaleVec: float):
        super(SpaceStation, self).__init__(loader, modelPath, parentNode, nodeName, 1, -1, 5, 1, -1, -5, 10)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)

class Drone(SphereCollideObject):
    droneCount = 0
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str,
        texPath: str, posVec: Vec3, scaleVec: float):
        super(Drone, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3)
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)

class XYZDrone(SphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str,
        posVec: Vec3, RGB: tuple):
        super(XYZDrone, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3)
        self.modelNode.setPos(posVec)
        tex = self.modelNode.setColor(RGB)
        self.modelNode.setName(nodeName)

class Missile(SphereCollideObject):
    missileCount = 0
    fireModels = {}
    cNodes = {}
    collisionSolids = {}
    intervals = {}
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, 
        posVec: Vec3, scaleVec: float = 1.0):
        super(Missile, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3.0)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setPos(posVec)

        Missile.missileCount += 1
        Missile.fireModels[nodeName] = self.modelNode
        Missile.cNodes[nodeName] = self.collisionNode

        # We retrieve the solid for our collisionNode
        Missile.collisionSolids[nodeName] = self.collisionNode.node().getSolid(0)
        Missile.cNodes[nodeName].show()

        print("Fire missle #" + str(Missile.missileCount))

class Orbiter(SphereCollideObject):
    numOrbits = 0
    velocity = 0.005
    cloudTimer = 240
    droneATKCount = 0
    droneCloudCount = 0
    def __init__(self, loader: Loader, taskMgr: TaskManager, modelPath: str, parentNode: NodePath, nodeName: str,
        scaleVec: Vec3, texPath: str, centralObject: PlacedObject, orbitRadius: float, orbitType: str, staringAt: Vec3):
        super(Orbiter, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0, 0, 0), 3.2)
        self.taskMgr = taskMgr
        self.render = parentNode
        self.loader = loader
        self.orbitType = orbitType
        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.orbitObject = centralObject
        self.orbitRadius = orbitRadius
        self.staringAt = staringAt
        Orbiter.numOrbits += 1
        self.shipName = nodeName

        self.cloudClock = 0
        self.taskFlag = "Traveler-" + str(Orbiter.numOrbits)
        taskMgr.add(self.Orbit, self.taskFlag)
        
        self.attack = 0
        self.droneDistance = 3500
        self.droneBay = 5
        self.droneReload = 1
        self.droneDoor = 5
        self.cloud = 0

        #self.accept("o", self.Fire)

    def Orbit(self, task):
        if self.orbitType == "MLB":
            positionVec = defensePaths.BaseballSeams(task.time * Orbiter.velocity, self.numOrbits, 2.0)
            self.modelNode.setPos(positionVec * self.orbitRadius + self.orbitObject.modelNode.getPos())
            if self.attack:
                self.attack -= 1
                self.Fire()
            else:
                if not self.taskMgr.hasTaskNamed("DroneAttack"):
                    self.taskMgr.doMethodLater(0, self.DroneCool, "DroneAttack")
                    return Task.cont
        elif self.orbitType == "Cloud":
            if self.cloudClock < Orbiter.cloudTimer:
                self.cloudClock += 1
                if self.cloud:
                    self.cloud -= 1
                    self.FireATK()
                else:
                    if not self.taskMgr.hasTaskNamed("DroneCloud"):
                        self.taskMgr.doMethodLater(0, self.DroneCloud, "DroneCloud")
                        return Task.cont
            else:
                self.cloudClock = 0
                positionVec = defensePaths.Cloud()
                self.modelNode.setPos(positionVec * self.orbitRadius + self.orbitObject.modelNode.getPos())

        self.modelNode.lookAt(self.staringAt.modelNode)
        return Task.cont

    def DroneCool(self, task):
        if task.time > self.droneReload:
            self.attack += 1
            if self.attack > 1:
                self.attack = 1
            return Task.done
        elif task.time <= self.droneReload:
            return Task.cont

    def DroneCloud(self, task):
            if task.time > self.droneReload:
                self.cloud += 1
                if self.cloud > 1:
                    self.cloud = 1
                return Task.done
            elif task.time <= self.droneReload:
                return Task.cont

    def Fire(self):
        if self.droneBay:
            travRate = self.droneDistance
            aim = self.render.getRelativeVector(self.modelNode, Vec3.forward())
            aim.normalize()
            fireSolution = aim * travRate
            inFront = aim * 150
            travVec = fireSolution + self.modelNode.getPos()
            self.droneBay -= 1
            tag = self.shipName + str(Orbiter.droneATKCount)

            posVec = self.modelNode.getPos() + inFront
            currentATK = Missile(self.loader, "./Assets/Spaceships/Phaser/Phaser/phaser.egg", self.render, tag, posVec, 4.0)

            Missile.intervals[tag] = currentATK.modelNode.posInterval(2.0, travVec, startPos = posVec, fluid = 1)
            Missile.intervals[tag].start()
        else:
            if not self.taskMgr.hasTaskNamed("reload_drone"):
                self.taskMgr.doMethodLater(0, self.Reload_Drone, "reload_drone")
                return Task.cont

    def FireATK(self):
        if self.droneDoor:
            travRate = self.droneDistance
            aim = self.render.getRelativeVector(self.modelNode, Vec3.forward())
            aim.normalize()
            fireSolution = aim * travRate
            inFront = aim * 150
            travVec = fireSolution + self.modelNode.getPos()
            self.droneDoor -= 1
            tag = self.shipName + str(Orbiter.droneCloudCount)

            posVec = self.modelNode.getPos() + inFront
            currentATK = Missile(self.loader, "./Assets/Spaceships/Phaser/Phaser/phaser.egg", self.render, tag, posVec, 4.0)

            Missile.intervals[tag] = currentATK.modelNode.posInterval(2.0, travVec, startPos = posVec, fluid = 1)
            Missile.intervals[tag].start()
        else:
            if not self.taskMgr.hasTaskNamed("reload_cloud"):
                self.taskMgr.doMethodLater(0, self.Reload_Cloud, "reload_cloud")
                return Task.cont

    def Reload_Drone(self, task):
        if task.time > self.droneReload:
            self.droneBay += 1
            if self.droneBay > 1:
                self.droneBay = 1
            return Task.done
        elif task.time <= self.droneReload:
            return Task.cont

    def Reload_Cloud(self, task):
            if task.time > self.droneReload:
                self.droneDoor += 1
                if self.droneDoor > 1:
                    self.droneDoor = 1
                return Task.done
            elif task.time <= self.droneReload:
                return Task.cont

    