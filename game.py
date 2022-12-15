import pygame
from pygame import Vector2
import random
import sprites
import objects
import sounds
def getRandomPosition(surface):
    return Vector2(random.randrange(surface.get_width()),random.randrange(surface.get_height()))
class Asteroids:
    def __init__(self):
        pygame.init()
        pygame.mixer.set_num_channels(20)
        pygame.display.set_caption("ASTEROIDS")
        self.spawnDistance = 200
        self.screen = pygame.display.set_mode((800,600))
        self.clock  = pygame.time.Clock()
        self.background = sprites.loadSprite("void")
        self.bullets = []
        self.ufobullets = []
        self.asteroids = []
        self.ufos = []
        self.debris = []
        self.spaceship = None
        self.getLifeSound = sounds.loadSound("extra")
        self.font = pygame.font.Font('vectorbattle.ttf',14)
        self.menufont = pygame.font.Font('vectorbattle.ttf',32)
        self.minAsteroids = 4
        self.maxAsteroids = 6
        self.stage = 99
        self.score = 0
        self.scoreCap = 10000
        self.ufoTimer = 2000
        self.genAsteroids()
        self.musicChannel = pygame.mixer.Channel(19)
        self.beepList = [sounds.loadSound("beat1"),sounds.loadSound("beat2")]

    def getGameplayOptions(self):
        self.minAsteroids = 4
        self.maxAsteroids = 6
        self.bullets = []
        self.ufos = []
        self.debris = []
        self.spaceship = objects.Spaceship((400,300),self.bullets.append)
        self.lastShot =  0
        self.accelSound = 0
        self.score = 0
        self.lives = 3
        self.stage = 0
        self.respawnShield = 800
        self.spawnTime = 0
        self.scoreCap = 10000
        self.bulletTTL = 3600
        self.ufobulletTTL = 1600
        self.gameOver = False
        self.ufoWarning = False
        self.lastBeep = 0
        self.minBeep = 125
        self.maxBeep = 1000
        self.curBeep = self.maxBeep
        self.smallUfoChance = 0.2
        self.beep = 0

    def genAsteroids(self):
        self.asteroids = []
        self.minAsteroids += self.stage // 3
        self.maxAsteroids += self.stage // 3
        for _ in range(random.randint(self.minAsteroids,self.maxAsteroids)):
            while True:
                pos = getRandomPosition(self.screen)
                if not self.spaceship or pos.distance_to(self.spaceship.position) > self.spawnDistance:
                    break
            self.asteroids.append(objects.Asteroid(pos, self.asteroids.append))


    def explode(self,target):
        explosion = objects.Explosion(target.position,self.now)
        self.debris.extend(explosion.explode())

    def genUFO(self):
        if len(self.ufos) > 1:
            return
        while True:
            pos = getRandomPosition(self.screen)
            if not self.spaceship or pos.distance_to(self.spaceship.position) > self.spawnDistance//4:
                for asteroid in self.asteroids:
                    if pos.distance_to(asteroid.position) < self.spawnDistance*0.75:
                        continue
                break
        if random.random() < self.smallUfoChance:
            self.ufos.append(objects.UFO(pos, 0, self.ufobullets.append))
            self.ufos[-1].lastMove = self.now
            self.ufos[-1].lastShot = self.now
        else:
            self.ufos.append(objects.UFO(pos,1,self.ufobullets.append))
            self.ufos[-1].lastMove = self.now
            self.ufos[-1].lastShot = self.now

    def playMusic(self):
        self.curBeep = 100*len(self.asteroids)
        if self.curBeep > self.maxBeep:
            self.curBeep = self.maxBeep
        if self.curBeep < self.minBeep:
            self.curBeep = self.minBeep
        if self.now - self.lastBeep >= self.curBeep:
            self.musicChannel.play(self.beepList[self.beep])
            self.beep = 1 if self.beep == 0 else 0
            self.lastBeep = self.now

    def mainMenu(self):
        self.inMenu = True
        while self.inMenu:
            self.processLogic()
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    quit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.inMenu = False
                    self.gameplay()

    def gameplay(self):
        self.getGameplayOptions()
        self.genAsteroids()
        running = True
        playing = False
        pygame.mixer.stop()
        while running:
            self.now = pygame.time.get_ticks()
            if self.now % self.ufoTimer == 0 and self.asteroids and self.spaceship:
                    self.genUFO()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    quit()
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_r]:
                self.gameplay()
            if self.spaceship:
                if pressed[pygame.K_SPACE] and not self.spaceship.invuln:
                    if self.now - self.lastShot >= self.spaceship.cooldown:
                        self.spaceship.shoot(self.now)
                        channelShoot = pygame.mixer.find_channel()
                        channelShoot.set_volume(0.2)
                        channelShoot.play(self.spaceship.attackSound)
                        self.lastShot = pygame.time.get_ticks()
                if pressed[pygame.K_LSHIFT]:
                    self.spaceship.hyperspace(self.now)
                if pressed[pygame.K_RIGHT]:
                    self.spaceship.rotate(clockWise=True)
                elif pressed[pygame.K_LEFT]:
                    self.spaceship.rotate(clockWise=False) 
                if pressed[pygame.K_UP]:
                    if playing == False:
                        playing = True
                        self.spaceship.thrustSound.play(-1)
                    if self.spaceship.invuln:
                        playing = False
                        self.spaceship.thrustSound.stop()
                    self.spaceship.accelerate()
                if not pressed[pygame.K_UP]:
                    self.spaceship.sprite = sprites.loadSprite('spaceshipidle')
                    playing = False
                    self.spaceship.thrustSound.stop()
            self.processLogic()
            self.draw()

    def handleObjects(self):
        objects = [*self.asteroids,*self.bullets, *self.ufos, *self.ufobullets,*self.debris]
        if self.spaceship and not self.inMenu and not self.spaceship.invuln:
            objects.append(self.spaceship)
        return objects

    def processLogic(self):
        for asteroid in self.asteroids:
            asteroid.move(self.screen)
        for debris in self.debris:
            debris.move(self.screen)
            if self.now - debris.time >= debris.ttl:
                self.debris.remove(debris)
        
        for ufo in self.ufos:
                shot = 0
                ufo.move(self.screen)
                if self.now - ufo.lastShot >= ufo.cooldown:
                    if ufo.size == 1:
                        ufo.shoot(self.now)
                    if ufo.size == 0:
                        for asteroid in self.asteroids:
                            if not self.spaceship or ufo.position.distance_to(asteroid.position) > ufo.position.distance_to(self.spaceship.position):
                                ufo.shoot(self.now,asteroid)
                                shot = 1
                                break
                        if not shot:
                            ufo.shoot(self.now,self.spaceship)
                    ufo.lastShot = self.now
                        
                    ufo.lastShot = self.now
                if self.now - ufo.lastMove >= ufo.velocityCooldown:
                    ufo.moveVertical()
                    ufo.lastMove = self.now
                if self.now - ufo.lastMove >= ufo.verticalStop and ufo.vertical == True:
                    ufo.stopVertical()
            
        if not self.inMenu:
            if self.spaceship:
                if self.now - self.spaceship.lastHyperSpace >= self.spaceship.hyperspaceTime and self.spaceship.invuln:
                    self.spaceship.invuln = False
                if self.ufos and not self.ufoWarning:
                    self.musicChannel.play(sounds.loadSound("ufo"),-1)
                    self.ufoWarning = True
                if not self.ufos:
                    if self.ufoWarning:
                        self.musicChannel.stop()
                        self.ufoWarning = False
                self.spaceship.move(self.screen)
                for asteroid in self.asteroids:
                    if asteroid.countCollision(self.spaceship):
                        if self.now - self.spawnTime > self.respawnShield and not self.spaceship.invuln:
                            pygame.mixer.stop()
                            pygame.mixer.find_channel().play(self.spaceship.deathSound)
                            self.dieTime = self.now
                            self.explode(self.spaceship)
                            self.spaceship = None
                            break
                    for ufo in self.ufos:
                        if asteroid.countCollision(ufo):
                            if self.spaceship:
                                ufochannel = pygame.mixer.find_channel()
                                ufochannel.set_volume(0.2)
                                ufochannel.play(ufo.deathsound,fade_ms=30)
                            self.explode(ufo)
                            self.ufos.remove(ufo)
            else:
                self.bullets = []
                self.ufoWarning = False
                if self.lives > 0:
                    if self.now - self.dieTime >= 1800:
                        for ufo in self.ufos:
                            self.ufos.remove(ufo)
                        self.lives -= 1
                        self.spaceship = objects.Spaceship((400,300),self.bullets.append)
                        self.spawnTime = self.now
                else:
                    self.gameOver = True
                    self.bullets = []
        for ufobullet in self.ufobullets[:]:
            if self.now - ufobullet.time >= self.ufobulletTTL:
                self.ufobullets.remove(ufobullet)
            ufobullet.move(self.screen)
            for asteroid in self.asteroids[:]:
                if asteroid.countCollision(ufobullet):
                    if self.spaceship:
                        channel = pygame.mixer.find_channel()
                        channel.set_volume(0.2)
                        channel.play(asteroid.sound,fade_ms = 30)
                    self.asteroids.remove(asteroid)
                    if ufobullet in self.ufobullets:
                        self.ufobullets.remove(ufobullet)
                    self.explode(asteroid)
                    asteroid.split()
            if self.spaceship:
                if ufobullet.countCollision(self.spaceship):
                    if self.now - self.spawnTime > self.respawnShield and not self.spaceship.invuln:
                            pygame.mixer.stop()
                            pygame.mixer.find_channel().play(self.spaceship.deathSound)
                            self.dieTime = self.now
                            if ufobullet in self.ufobullets:
                                self.ufobullets.remove(ufobullet)
                            self.explode(self.spaceship)
                            self.spaceship = None
        
        for bullet in self.bullets[:]:
            if self.now - bullet.time > self.bulletTTL:
                self.bullets.remove(bullet)
            bullet.move(self.screen)
            for ufo in self.ufos[:]:
                if ufo.countCollision(bullet):
                    if self.spaceship:
                        ufochannel = pygame.mixer.find_channel()
                        ufochannel.set_volume(0.2)
                        ufochannel.play(ufo.deathsound,fade_ms=30)
                        self.explode(ufo)
                        self.ufos.remove(ufo)
                        self.lastShot = self.now
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        if ufo.size == 0:
                            self.score += 2000
                        if ufo.size == 1:
                            self.score += 750
                            
            for ufo in self.ufos[:]:
                if self.spaceship:
                    if ufo.countCollision(self.spaceship):
                        if self.now - self.spawnTime > self.respawnShield and not self.spaceship.invuln:
                            pygame.mixer.stop()
                            pygame.mixer.find_channel().play(self.spaceship.deathSound)
                            self.dieTime = self.now
                            self.explode(self.spaceship)
                            self.spaceship = None
                        break
            for asteroid in self.asteroids[:]:
                if asteroid.countCollision(bullet):
                    if self.spaceship:
                        channel = pygame.mixer.find_channel()
                        channel.set_volume(0.2)
                        channel.play(asteroid.sound,fade_ms = 30)
                    self.asteroids.remove(asteroid)
                    self.lastShot = self.now
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    self.explode(asteroid)
                    asteroid.split()
                    self.score += 50*asteroid.size
                    break
            
        for ufobullet in self.ufobullets[:]:
            if not self.screen.get_rect().collidepoint(ufobullet.position):
                self.ufobullets.remove(ufobullet)
        
        for bullet in self.bullets[:]:
            if not self.screen.get_rect().collidepoint(bullet.position):
                self.bullets.remove(bullet)
        if self.spaceship and not self.ufos and self.asteroids:
            self.playMusic()
        if not self.asteroids and not self.ufos and self.spaceship:
            if self.now - self.lastShot >= 6000:
                self.stage += 1
                self.ufoTimer -= 100
                self.score += 500 * self.lives
                self.genAsteroids()
        if self.score >= self.scoreCap:
                self.scoreCap += 10000
                self.lives += 1
                pygame.mixer.find_channel().play(self.getLifeSound)
    def draw(self):
        self.screen.blit(self.background,(0,0))
        if self.inMenu:
            text1 = self.menufont.render("ASTEROIDS",False,pygame.Color("white"))
            self.screen.blit(text1,(self.screen.get_width()/2-100,0))
            text2 = self.font.render("PRESS SPACE TO PLAY",False,pygame.Color("white"))
            self.screen.blit(text2,(self.screen.get_width()/2-92,self.screen.get_height()-48))
            text3 = self.font.render("BY ALEXANDER SMIRNOV",False, pygame.Color("white"))
            self.screen.blit(text3,(self.screen.get_width()-232,self.screen.get_height()-18))
        if not self.inMenu:
            self.scoreText = self.font.render("SCORE "+str(self.score),False,pygame.Color("white"))
            self.screen.blit(self.scoreText,(0,0))
            self.stageText = self.font.render("STAGE " + str(self.stage),False,pygame.Color("white"))
            self.screen.blit(self.stageText,(self.screen.get_width()-90,0))
            if self.gameOver:
                self.liveText = self.font.render("GAME OVER",False,pygame.Color("White"))
                self.gameOverText = self.font.render("PRESS R TO RESTART",False,pygame.Color("White"))
                self.screen.blit(self.gameOverText,(0,self.screen.get_height()-18))
            else:
                self.liveText = self.font.render("LIVES "+str(self.lives%100),False,pygame.Color("white"))
            self.screen.blit(self.liveText,(0,20))
        for obj in self.handleObjects():
            obj.draw(self.screen)
        pygame.display.flip()
        self.clock.tick(60)


if __name__ == "__main__":
    game = Asteroids()
    game.mainMenu()