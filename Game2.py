import pygame as pg
import sys
import math
import random
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

win_width = 600
win_height = 550


def check_border(rect: pg.Rect) -> tuple[bool, bool]:
    """
    Rectオブジェクトを渡すとオブジェクトが
    ウィンドウの外にあるかどうかをタプルで返す関数
    """
    horizontal, vertical = True, True
    if rect.left < 0 or win_width < rect.right:
        horizontal = False
    if rect.top < 0 or win_height < rect.bottom:
        vertical = False
    return horizontal, vertical


class Player(pg.sprite.Sprite):
    """
    プレイヤーのクラス
    """
    def __init__(self, path: str, pos: tuple, angle: int, 
                 size: int, speed: int, frame_len: int, frame_rate: int):
        super().__init__()
        anime_di = ["flont", "back", "right", "left"]
        self.anime = []
        for di in anime_di:
            frame = []
            for i in range(frame_len):
                frame.append(f"{path}{di}-{str(i)}.png")
            self.anime.append(frame)
        self.pos = pos
        self.angle = angle
        self.size = size
        self.counter = 0
        self.rate = frame_rate
        self.direction = 0
        self.frame_counter = 0
        self.frame_len = frame_len
        self.move = 0
        self.speed = speed
        self.place = [self.pos[0], self.pos[1]]
    
    def update(self):
        key_list = pg.key.get_pressed()
        move_lst={pg.K_UP:(0,-self.speed), pg.K_DOWN:(0,self.speed), 
                pg.K_RIGHT:(self.speed,0), pg.K_LEFT:(-self.speed,0)}
        sum_move=[0,0]
        for key, item in move_lst.items():
            if key_list[key]:
                sum_move[0]+=item[0]
                sum_move[1]+=item[1]
        self.sum_move = sum_move
        self.place[0] += sum_move[0]
        self.place[1] += sum_move[1]

        if (key_list[pg.K_DOWN] or key_list[pg.K_UP] or key_list[pg.K_RIGHT] or key_list[pg.K_LEFT] or
           key_list[pg.K_s] or key_list[pg.K_w] or key_list[pg.K_a] or key_list[pg.K_d]):
            self.move = 1
        else:
            self.move = 0
        
        if self.move == 1:
            if self.counter % self.rate == 0:
                self.frame_counter +=1
                if key_list[pg.K_DOWN] or key_list[pg.K_s]:
                    self.direction = 0
                if key_list[pg.K_UP] or key_list[pg.K_w]:
                    self.direction = 1
                if key_list[pg.K_RIGHT] or key_list[pg.K_a]:
                    self.direction = 2
                if key_list[pg.K_LEFT] or key_list[pg.K_d]:
                    self.direction = 3
                self.image = pg.transform.rotozoom(pg.image.load(self.anime[self.direction][self.frame_counter%self.frame_len]).convert_alpha()
                                                    , self.angle, self.size)
                self.rect = self.image.get_rect()
        else:
            self.image = pg.transform.rotozoom(pg.image.load(self.anime[self.direction][0]).convert_alpha()
                                                , self.angle, self.size)
            self.rect = self.image.get_rect()
        
        self.rect.center = self.pos
        self.counter += 1
    
    def draw(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)


class Map_Tile(pg.sprite.Sprite):
    """
    マップタイルを表示するクラス
    """
    def __init__(self, path: str, pos: tuple, player: Player, 
                 size: int, angle: int, flip: bool):
        super().__init__()
        self.path = path
        self.pos = pos
        self.player = player
        self.size = size
        self.angle = angle 
        self.flip = flip
        self.image = pg.transform.rotozoom(pg.image.load(path).convert_alpha(), self.angle, self.size)
        if self.flip:
            self.image = pg.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
    
    def update(self):
        self.rect.center = (-(self.rect.width * -self.pos[0] + self.player.place[0]),
                            -(self.rect.height * -self.pos[1] + self.player.place[1]))
    
    def draw(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)


def random_mapping(map_group: pg.sprite.Group, map_tile: pg.sprite.Sprite,
                   map_size: tuple, player: Player):
    for i in range(map_size[0]):
        for j in range(map_size[1]):
            map_random = random.randint(0, 8)
            map_flip = random.randint(0, 1)
            Tile = map_tile("image/map/map_tile2/pixil-frame-"+str(map_random)+".png", (i, j), player, 1, 0, map_flip)
            map_group.add(Tile)
    return map_group

def main():
    clock = pg.time.Clock()
    counter = 0
    screen = pg.display.set_mode((win_width, win_height))
    player = Player("image/Animation/player/", (win_width/2, win_height/2), 0, 0.3, 5, 4, 6)
    # tile = Map_Tile("image/map/red_stone.png", (0, 0), player, 0.5, 0, False)
    map_group = pg.sprite.Group()
    player_group = pg.sprite.Group()
    game_group = pg.sprite.Group()

    player_group.add(player)
    game_group.add(random_mapping(map_group, Map_Tile, (6, 6), player), player_group)

    while(True):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
        screen.fill((0, 0, 0))
        game_group.update()
        game_group.draw(screen)
        pg.display.update()
        clock.tick(50)
        counter += 1

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()