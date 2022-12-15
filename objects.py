from pygame.math import Vector2
from pygame.transform import rotozoom
import sounds
import random
import sprites
from math import sqrt
UP = Vector2(0,-1)

def wrapPos(pos,surface):
    x,y = pos
    w,h = surface.get_size()
    return Vector2(x%w, y%h)

def getRandomVelocity(minSpeed,maxSpeed):
    speed = random.randint(minSpeed,maxSpeed)
    angle = random.randrange(0,360)
    return Vector2(speed,0).rotate(angle)
class GameObject:
    def __init__(self, position, sprite, velocity):
        self.position = Vector2(position)
        self.sprite = sprite
        self.radius = sprite.get_width() / 2
        self.velocity = Vector2(velocity)

    def draw(self, surface):
        blit_position = self.position - Vector2(self.radius)
        surface.blit(self.sprite, blit_position)

    def move(self,surface):
        self.position = wrapPos(self.position + self.velocity,surface)

    def countCollision(self, otherObj):
        distance = self.position.distance_to(otherObj.position)
        return distance < self.radius + otherObj.radius

class Spaceship(GameObject):
    
    def __init__(self,position,bulletGen):
        self.bulletGen = bulletGen
        self.direction = Vector2(UP)
        self.turnspeed = 4
        self.accelspeed = 0.05
        self.bulletspeed = 6
        self.cooldown = 200
        self.hyperspaceCooldown = 10000
        self.hyperspaceTime = 2400
        self.lastHyperSpace = 0
        self.attackSound = sounds.loadSound("fire")
        self.thrustSound = sounds.loadSound("thrust")
        self.deathSound = sounds.loadSound("bangm")
        self.invuln = False
        self.defaultSprite = sprites.loadSprite("spaceshipidle")
        super().__init__(position,self.defaultSprite,Vector2(0))
    
    def rotate(self,clockWise=True):
        mul = 1 if clockWise else -1
        angle = self.turnspeed*mul
        self.direction.rotate_ip(angle)

    def accelerate(self):
        self.sprite = sprites.loadSprite("spaceshipmove")
        compareVelo = self.direction*self.accelspeed
        if abs(compareVelo[0]+self.velocity[0]) < 1.5:
            self.velocity[0] += compareVelo[0]
        if abs(compareVelo[1]+self.velocity[1]) < 1.5:
            self.velocity[1] += compareVelo[1]
        
    def hyperspace(self,curTime):
        if curTime - self.lastHyperSpace >= self.hyperspaceCooldown:
            self.invuln = True
            self.lastHyperSpace = curTime

    def draw(self, surface):
        angle = self.direction.angle_to(UP)
        rotation = rotozoom(self.sprite,angle,1.0)
        rotationSize = Vector2(rotation.get_size())
        blitPos = self.position - rotationSize*0.5
        surface.blit(rotation,blitPos)

    def shoot(self,time):
        bulletVelocity = self.direction*self.bulletspeed+self.velocity
        bullet = Bullet(self.position, self.bulletGen,bulletVelocity,time)
        self.bulletGen(bullet)

class Asteroid(GameObject):
    def __init__(self,pos,asteroidGen,size=3):
        self.asteroidGen = asteroidGen
        self.size = size        
        if self.size == 3:
            rnd = random.choice(["asteroidl","asteroidl1","asteroidl2"])
            sprite = sprites.loadSprite(rnd)
            self.sound = sounds.loadSound("bangl")
        if self.size == 2:
            rnd = random.choice(["asteroidm","asteroidm1","asteroidm2"])
            sprite = sprites.loadSprite(rnd)
            self.sound = sounds.loadSound("bangm")
        if self.size == 1:
            rnd = random.choice(["asteroids","asteroids1","asteroids2"])
            sprite = sprites.loadSprite(rnd)
            self.sound = sounds.loadSound("bangs")
    
        super().__init__(pos,sprite,getRandomVelocity(1,3))
    def split(self):
        if self.size > 1:
            for _ in range(2):
                newAster = Asteroid(self.position,self.asteroidGen,self.size -1)
                self.asteroidGen(newAster)

class Bullet(GameObject):
    def __init__(self,position,bulletGen,velocity,time):
        self.bulletGen = bulletGen
        self.time = time
        self.direction = Vector2(UP)
        super().__init__(position,sprites.loadSprite("bullet"),velocity)

class UFOBullet(GameObject):
    def __init__(self,position,bulletGen,velocity,time):
        self.bulletGen = bulletGen
        self.time = time
        self.direction = Vector2(UP)
        super().__init__(position,sprites.loadSprite("bullet2"),velocity)

class UFO(GameObject):
    def __init__(self,position,size,bulletGen):
        self.bulletGen = bulletGen
        self.bulletspeed = 3
        self.cooldown = 450
        self.size = size
        self.verticalStop = random.randint(1200,3600)
        self.velocityCooldown = 4200
        self.deathsound = sounds.loadSound("bangm")
        self.lastShot = 1
        self.lastMove = 1
        self.vertical = False
        self.velocity = Vector2((random.choice([-1.75,-1.5,1.5,1.75]),0))
        if self.size == 0:
            super().__init__(position,sprites.loadSprite("ufo"),self.velocity)
        if self.size == 1:
            sprite = rotozoom(sprites.loadSprite("ufo"),0,1.25)
            super().__init__(position,sprite,self.velocity)

    def shoot(self,time,target=None):
        if target:
            dx = target.position[0] - self.position[0]
            dy = target.position[1] - self.position[1]
            mg = sqrt(abs(dx*dx-dy*dy))
            self.direction = Vector2(dx/mg,dy/mg)
        else:
            self.direction = Vector2(random.choice([-1,1]),random.choice([-1,1]))
        bulletVelocity = self.direction*self.bulletspeed+self.velocity
        bullet = UFOBullet(self.position, self.bulletGen,bulletVelocity,time)
        self.bulletGen(bullet)
    
    def moveVertical(self):
        if self.velocity[0] < 0:
            self.velocity = Vector2((self.velocity[0]-1,random.choice([-1,1])))
        else:
            self.velocity = Vector2((self.velocity[0]+1,random.choice([-1,1])))
        self.vertical = True
    
    def stopVertical(self):
        if self.velocity[0] < 0:
            self.velocity = Vector2((self.velocity[0]+1,random.choice([-1,1])))
        else:
            self.velocity = Vector2((self.velocity[0]-1,random.choice([-1,1])))
        self.vertical = False

class Debris(GameObject):
    def __init__(self, position,time):
        self.ttl = 360
        self.speed = 1.25
        self.time = time
        velocity = Vector2(random.uniform(-1.5,1.5),random.uniform(-1.5,1.5)) * self.speed
        super().__init__(position,sprites.loadSprite("debris"),velocity)

class Explosion:
    def __init__(self,position,time):
        self.debrisList = []
        self.time = time
        self.position = position

    def explode(self):
        for _ in range(25):
            debris = Debris(self.position,self.time)
            self.debrisList.append(debris)
        return self.debrisList




