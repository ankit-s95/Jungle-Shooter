import pygame
from pygame import mixer
import os
import math
import random
import csv
import button

mixer.init()
pygame.init()


SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Shooter')

#set framerate
clock = pygame.time.Clock()
FPS = 60

#define game variables
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
start_intro = False

#define player action variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False

#load music and sound
pygame.mixer.music.load('audio/black.mp3')
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1, 0.0, 5000)
jump_fx = pygame.mixer.Sound('audio/jump.mp3')
jump_fx.set_volume(100)
shot_fx = pygame.mixer.Sound('audio/shot.mp3')
jump_fx.set_volume(0.3)
nade_fx = pygame.mixer.Sound('audio/nade.mp3')
nade_fx.set_volume(0.3)
orb_fx = pygame.mixer.Sound('audio/orb.mp3')
orb_fx.set_volume(0.8)
death_fx = pygame.mixer.Sound('audio/death.wav')
#heal_fx = pygame.mixer.Sound('audio/heal.wav')
#ammo_fx = pygame.mixer.Sound('audio/ammo.wav')
#grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
#darius_fx = pygame.mixer.Sound('audio/darius.wav')
#death_fx = pygame.mixer.Sound('audio/death.wav')

#load images
#button images
start_img = pygame.image.load('Img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('Img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('Img/restart_btn.png').convert_alpha()
#bg images
#loading screen
loading_img = pygame.image.load('Img/Background/load.png').convert_alpha()
#main game
back_img = pygame.image.load('Img/Background/back.png').convert_alpha()
tree1_img = pygame.image.load('Img/Background/tree1.png').convert_alpha()
tree2_img = pygame.image.load('Img/Background/tree2.png').convert_alpha()
water_img = pygame.image.load('Img/Background/water.png').convert_alpha()
grass_img = pygame.image.load('Img/Background/grass.png').convert_alpha()
#store tiles in a list
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'Img/Tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
#bullet
bullet_img = pygame.image.load('Img/Icons/bullet.png').convert_alpha()
#grenade
grenade_img = pygame.image.load('Img/Icons/grenade.png').convert_alpha()
#orb
orb_img = pygame.image.load('Img/Icons/orb.png').convert_alpha()
#pickup boxes
health_box_img = pygame.image.load('Img/Icons/brain3.png').convert_alpha()
ammo_box_img = pygame.image.load('Img/Icons/picklebas1.png').convert_alpha()
grenade_box_img = pygame.image.load('Img/Icons/unc1.png').convert_alpha()
item_boxes = {
    'Health'    : health_box_img,
    'Ammo'      : ammo_box_img,
    'Grenade'   : grenade_box_img
}


#define colours
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

#define font
font = pygame.font.Font('Jacquar.ttf', 30)


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_load():
    screen.fill(BLACK)
    screen.blit(loading_img, (100, 0))


def draw_bg():
    screen.fill(BG)
    width = back_img.get_width()
    for x in range(8):
        screen.blit(back_img, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(tree1_img, ((x * width) - bg_scroll * 0.6, 0))
        screen.blit(tree2_img, ((x * width) - bg_scroll * 0.7, 0))
        screen.blit(water_img, ((x * width) - bg_scroll * 0.8, 0))
        screen.blit(grass_img, ((x * width) - bg_scroll * 0.9, 0))


#function to reset level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()
    orb_group.empty()

    #create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    return data


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.scream = False
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        #ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 200, 20)
        self.idling = False
        self.idling_counter = 0        
        
        
        #load all images for players
        animation_types = ['Idle', 'Run', 'Jump', 'Death', 'Attack']
        for animation in animation_types:
            #reset temporary list of imgs
            temp_list = []
            #count number of files in the folder
            num_of_frames = len(os.listdir(f'Img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'Img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()  # Change self.img to self.image
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()



    def update(self):
        self.update_animation()
        self.check_alive()
        #update cooldown#
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1



    def move(self, moving_left, moving_right):
        #reset movement variables
        screen_scroll = 0
        dx = 0
        dy = 0
        
        #assign movement variables if moving left or right
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        
        if self.jump == True and self.in_air == False:
            self.vel_y = -12
            self.jump = False
            self.in_air = True

        #apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y

        #check collision with floor
        for tile in world.obstacle_list:
            #check collision in the x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #if the ai has hit the wall make it turn around
                #if self.char_type == 'enemy':
                #    self.direction *= -1
                #    self.move_counter = 0
            #check collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if below the ground i.e jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top # may need to decrease
                #check if above ground, i.e falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom
        
        #check for collision with water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

         #check for collision with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        #check if fallen off the map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        
        #check if going off the edge of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0





        #update rect position
        self.rect.x += dx
        self.rect.y += dy

        #update scroll based on player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_HEIGHT - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
                or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx
        return screen_scroll, level_complete

    def shoot(self):
            if self.shoot_cooldown == 0 and self.ammo > 0:
                self.shoot_cooldown = 15
                #bullet_ejection_offset = 12
                gun_level_offset = 0  # Adjust this based on how far down the gun is from the sprite's center
                bullet = Bullet(self.rect.centerx + ( 0.75 * player.rect.size[0] * self.direction), self.rect.centery + gun_level_offset, self.direction)
                bullet_group.add(bullet)
                #reduce ammo
                self.ammo -=1
                shot_fx.play()

    def magic(self):
            if self.shoot_cooldown == 0 and self.ammo > 0:
                self.shoot_cooldown = 120
                #bullet_ejection_offset = 12
                gun_level_offset = -5  # Adjust this based on how far down the gun is from the sprite's center
                orb = Magic(self.rect.centerx + ( 0.75 * player.rect.size[0] * self.direction), self.rect.centery + gun_level_offset, self.direction)
                orb_group.add(orb)
                #reduce ammo
                self.ammo -=1
                orb_fx.play()
                

    
    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)#0: idle
                self.idling = True
                self.idling_counter = 200
            #check if ai near player
            if self.vision.colliderect(player.rect):
                #stop running and face player
                self.update_action(4)
                #shoot
                self.magic()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)#1: run
                    self.move_counter += 1
                    #update ai vision as enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    #visualise their vision
                    #pygame.draw.rect(screen, RED, self.vision)
                    
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                        
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling= False
        
        #scroll
        self.rect.x += screen_scroll



    def update_animation(self):
        #update animation
        ANIMATION_COOLDOWN = 125
        #update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]
        #check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #if animation runs out, reset back to start
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) -1
            else:
                self.frame_index = 0


    def update_action(self, new_action):
        #check if new action is different to previous
        if new_action != self.action:
            self.action = new_action
            #update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0 and not self.scream:
            self.health = 0
            self.speed = 0
            death_fx.play()
            self.scream = True
            self.alive = False
            self.update_action(3)


    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        #iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >=0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >=9 and tile <=10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif tile >=11 and tile <=14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:#create player
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1, 9, 30, 5)
                        player_group.add(player)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:#reate enemies
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1, 2, 20, 0)
                        enemy_group.add(enemy)
                    elif tile == 17:#ammo box
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:#grenade box
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:#health box
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:#create exit
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)

        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])


class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
    
    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll
    



class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        #scroll
        self.rect.x += screen_scroll
        #check if player has picked up box
        if pygame.sprite.collide_rect(self, player):
            #check wht kind of box it was
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
                #print(player.health)
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades += 3
            #delete the item box
            self.kill()
    
class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
       #update with new health
       self.health = health
       ratio = self.health / self.max_health
       pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
       pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
       pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

        




class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
    # move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll

    # check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()


        #check collision with characters
        for enemy in pygame.sprite.spritecollide(self, enemy_group, False):
            if enemy.alive:  # Only apply damage to alive enemies
                enemy.health -= 25
                #print("Enemy health:", enemy.health)
                self.kill()  # Destroy the bullet after it hits one enemy
        
        if player.alive:
            if pygame.sprite.spritecollide(self, player_group, False):
                player.health -= 5
                self.kill()

class Magic(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 3.5
        self.image = orb_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
    # move projectile
        self.rect.x += (self.direction * self.speed) + screen_scroll

    # check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
    #check for collision with level
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
        
        if player.alive:
            if pygame.sprite.spritecollide(self, player_group, False):
                player.health -= 10
                self.kill()


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.vel_y = -11
        self.speed = 10
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y


        #check for collison with level
        for tile in world.obstacle_list:
            # check if collision with walls
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
        
            #check collision in the y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                #check if below the ground i.e thrown up
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                #check if above ground, i.e falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        

        #update grenade position
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        #countdown timer
        self.timer -= 1
        if self.timer<= 0:
            self.kill()
            nade_fx.play()
            explosion = Explosion(self.rect.x + 17, self.rect.y - 18, 1)
            explosion_group.add(explosion)
            #do damage to anyone that is nearby
            
            center_offset = 30  # Adjust this based on your sprites

            if player.alive:
                # Player distance with offset
                distance_to_player = ((self.rect.centerx - player.rect.centerx) ** 2 + 
                                    (self.rect.centery - (player.rect.centery + center_offset)) ** 2) ** 0.5

                if distance_to_player < TILE_SIZE * 1.5:
                    player.health -= 75
                    #print("Close damage:", player.health)
                elif distance_to_player < TILE_SIZE * 3:
                    player.health -= 10
                    #print("Far damage:", player.health)

            # Enemy distance with offset
            for enemy in enemy_group:
                if enemy.alive:
                    distance_to_enemy = ((self.rect.centerx - enemy.rect.centerx) ** 2 + 
                                        (self.rect.centery - (enemy.rect.centery + center_offset)) ** 2) ** 0.5

                    if distance_to_enemy < TILE_SIZE * 2:
                        enemy.health -= 100
                        #print("Close damage to enemy:", enemy.health)
                    elif distance_to_enemy < TILE_SIZE * 3:
                        enemy.health -= 25
                        #print("Far damage to enemy:", enemy.health)
                
                
                
                


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 10):
            img = pygame.image.load(f'Img/explosion/explosion2/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        #scroll
        self.rect.x += screen_scroll
        EXPLOSION_SPEED = 4
        #update explosion animation
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            #if animation complete then delete explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:#whole screen fade
            pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2: #vertical screen fade down
            pygame.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True
        return fade_complete


#create screen fades
intro_fade = ScreenFade(1, BLACK, 4)
death_fade = ScreenFade(2, PINK, 4)



#create buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 120, start_img, 0.2)
exit_button = button.Button(SCREEN_WIDTH // 2 + 80, SCREEN_HEIGHT // 2 + 120, exit_img, 0.2)
restart_button = button.Button(SCREEN_WIDTH // 2 - 210 , SCREEN_HEIGHT // 2 - 230 , restart_img, 0.4)



# create sprite groups
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
orb_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()








#create empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
#load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)

world = World()
player, health_bar = world.process_data(world_data)



run = True
while run:
    
    clock.tick(FPS)

    if start_game == False:
        #draw menu
        draw_load()
        #add buttons
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            run = False

    else:
        #update background
        draw_bg()
        #draw world map
        world.draw()
        #show player health
        health_bar.draw(player.health)
        #show ammo
        draw_text(f'Ammo: {player.ammo}', font, WHITE, 10, 35)
        #show grenades
        draw_text('Grenades: ', font, WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (115 + (x * 15), 55))
        

        player.update()
        player.draw()

        # Draw the collision rectangle for the player in red
        #pygame.draw.rect(screen, (255, 0, 0), player.rect, 2)

        #pygame.draw.rect(screen, (255, 0, 0), enemy.rect, 2)

        #for bullet in bullet_group:
        #    pygame.draw.rect(screen, (0, 255, 0), bullet.rect, 2)

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()


        #update and graw groups
        bullet_group.update()
        grenade_group.update()
        orb_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update()
        water_group.update()
        exit_group.update()

        bullet_group.draw(screen)
        orb_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)

        #show intro
        if start_intro == True:
            if intro_fade.fade():#
                start_intro = False
                intro_fade.fade_counter = 0



        #update player actions
        if player.alive:
            #shoot bullets
            if shoot:
                player.shoot()
            #throw grenades
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (0.2 * player.rect.size[0] * player.direction), player.rect.centery, player.direction)
                grenade_group.add(grenade)
                #reduce grenades
                player.grenades -= 1
                grenade_thrown = True
                #print(player.grenades)
            if player.in_air:
                player.update_action(2)#2: jump
            elif moving_left or moving_right:
                player.update_action(1)#1: Run
            else:
                player.update_action(0)#0: back to idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            #check if player has completed the level
            if level_complete:
                start_intro = True
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVELS:
                        #load in level data and create world
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)

        else:
            screen_scroll = 0
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    bg_scroll = 0
                    world_data = reset_level()
                    #load in level data and create world
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)





    for event in pygame.event.get():
        #quit game

        if event.type == pygame.QUIT:
            run = False
        #keyboard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_LSHIFT:
                shoot = True
            if event.key == pygame.K_q:
                grenade = True
            if event.key == pygame.K_SPACE and player.alive:
                jump_fx.play()
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                run = False






        #keyboard button released
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_LSHIFT:
                shoot = False
            if event.key == pygame.K_q:
                grenade = False
                grenade_thrown = False
    pygame.display.update()



pygame.quit()