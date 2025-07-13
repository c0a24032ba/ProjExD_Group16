import pygame as pg
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

map_width, map_height = 800, 650


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or map_width < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or map_height < obj_rct.bottom:
        tate = False
    return yoko, tate


class player(pg.sprite.Sprite):
    """
    プレイヤーのスプライト
    """
    def __init__(self, path="", image_tag="", pos=(0, 0), vxy=(0, 0), 
        angle=0, size=0, speed=5, animation=True, frame_len=0, frame_fps=3):
          
        super(player, self).__init__()
        if path!="":
            if animation:
                self.anime=[]
                self.base_anime=[]
                self.base_frame=frame_len
                self.base_size=size
                self.base_speed=speed
                for i in range(frame_len):
                    self.anime.append(path+str(i)+image_tag)
                    self.base_anime.append(path+str(i)+image_tag)
                self.image=pg.transform.rotozoom(pg.image.load(self.anime[0]).convert_alpha(), angle, size)
                self.rect=self.image.get_rect()
            else:
                self.image=pg.transform.rotozoom(pg.image.load(path).convert_alpha(), angle, size)
                self.rect=self.image.get_rect()
        else:
            self.image=pg.Surface((20, 20))
            self.rect=self.image.get_rect()
            pg.draw.rect(self.image, (0, 255, 0), self.rct)
        self.size=size
        self.set_x, self.set_y=pos
        self.vx, self.vy=vxy
        self.rect.center=(pos)
        self.speed=speed
        self.counter=0
        self.frame=frame_len
        self.frame_fps=frame_fps
        self.frame_counter=0
        self.direction=0
        self.frag=False

    def animetion(self, path="", image_tag="", frame_len=0):
        self.anime=[]
        self.frag = True
        self.frame = frame_len
        for i in range(frame_len):
            self.anime.append(path+str(i)+image_tag)

    def update(self):
        key_lst=pg.key.get_pressed()
        move_lst={pg.K_UP:(0,-self.speed), pg.K_DOWN:(0,self.speed), 
                pg.K_RIGHT:(self.speed,0), pg.K_LEFT:(-self.speed,0)}
        sum_move=[0,0]
        if key_lst[pg.K_LEFT]:
            self.direction=0
        if key_lst[pg.K_RIGHT]:
            self.direction=1
        for key, item in move_lst.items():
            if key_lst[key]:
                sum_move[0]+=item[0]
                sum_move[1]+=item[1]
        self.rect.move_ip(sum_move)
        if check_bound(self.rect)!=(True, True):
            self.rect.move_ip(-sum_move[0], -sum_move[1])
        if (sum_move!=[0, 0]) and (not self.frag):
            if self.counter%self.frame_fps==0:
                self.frame_counter+=1
                self.image=pg.transform.rotozoom(pg.image.load(self.anime[self.frame_counter%self.frame]).convert_alpha(), 0, self.size)
                if self.direction==1:
                    self.image=pg.transform.flip(pg.transform.rotozoom(pg.image.load(self.anime[self.frame_counter%self.frame]).convert_alpha(), 0, self.size),
                                                       True, False)
        else:
            if not self.frag:
                if self.direction==1:
                    self.image=pg.transform.flip(pg.transform.rotozoom(pg.image.load(self.anime[0]).convert_alpha(), 0, self.size),
                                                    True, False)
                else:
                    self.image=pg.transform.rotozoom(pg.image.load(self.anime[0]).convert_alpha(), 0, self.size)
            else:
                self.speed*=0.5
                if self.counter%self.frame_fps==0:
                    self.frame_counter+=1
                    self.image=pg.transform.rotozoom(pg.image.load(self.anime[self.frame_counter%self.frame]).convert_alpha(), 0, self.size)
                    if self.direction==1:
                        self.image=pg.transform.flip(pg.transform.rotozoom(pg.image.load(self.anime[self.frame_counter%self.frame]).convert_alpha(), 0, self.size),
                                                       True, False)
                    if self.frame_counter>self.frame:
                        self.frag = False
                        self.anime = []
                        self.size = self.base_size
                        self.speed = self.base_speed
        self.counter+=1
        if self.anime==[]:
            self.anime = self.base_anime
            self.frame =  self.base_frame
            
    def draw(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)


class Map_tile(pg.sprite.Sprite):
    """
    マップタイルを表示するクラス
    """
    def __init__(self, path: str, pos: tuple, angle: int, size: int, collide: bool):
        super().__init__()
        self.path = path
        self.angle = angle
        self.size = size
        self.collide = collide
        self.image = pg.transform.rotozoom(pg.image.load(path), self.angle, self.size)
        self.rect = self.image.get_rect()
        self.image.set_colorkey((0, 0, 0))
        self.rect.centerx = pos[0]
        self.rect.centery = pos[1]

    def update(self, base_rect: pg.Rect):
        self.rect.centerx = base_rect.centerx      
        self.rect.centery = base_rect.centery
          
    def draw(self, screen: pg.Surface):
        screen.blit(self.image, self.rect)

def main():
    screen = pg.display.set_mode((map_width, map_height))
    size=1
    speed=5
    frame=6
    zombie=player("image/Animation/zombie_walk2/pixil-frame-", ".png", 
                   (map_width/2, map_height/2), (0, 0), 0, size, speed, True, frame, 3)
    clock = pg.time.Clock()
    player_group = pg.sprite.Group()
    game_group = pg.sprite.Group()
    player_group.add(zombie)
    game_group.add(player_group)
    counter = 0
    while(True):
        for event in pg.event.get():
            if event.type==pg.QUIT:
                return
            if event.type==pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    zombie.animetion("image/Animation/zombie_attack/pixil-frame-", ".png", 9)
                    zombie.frame_counter=0
                    zombie.size=1
        screen.fill((50, 50, 50))
        game_group.update()
        game_group.draw(screen)
        pg.display.update()
        clock.tick(30)
        counter += 1


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
