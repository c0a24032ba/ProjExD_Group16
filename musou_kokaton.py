import math
import os
import random
import sys
import time
import pygame as pg 


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  #右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  #右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  #上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  #左上
            (-1, 0): img0,
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  #左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  #下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  #右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"
        self.hyper_life = -1

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life -= 1
            if self.hyper_life < 0:
                self.state = "normal"
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)   # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, cross_hairs: pg.Rect):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        base_angle = math.degrees(math.atan2(-(cross_hairs.centery-bird.rect.center[1]), 
                                             (cross_hairs.centerx-bird.rect.center[0])))
        total_angle = base_angle
        self.vx = math.cos(math.radians(total_angle))
        self.vy = -math.sin(math.radians(total_angle))
        self.image = pg.transform.rotozoom(pg.image.load(f"image/bullet.png"), total_angle-90, 0.8)
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 50

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy"):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        self.anime = []
        for i in range(5):
            self.anime.append("image/Animation/explotion/pixil-frame-"+str(i)+".png")
        self.image = pg.transform.rotozoom(pg.image.load(self.anime[0]), 0, 1)
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = 0
        self.counter = 0

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        if self.counter % 3 == 0:
            self.image = pg.transform.rotozoom(pg.image.load(self.anime[self.life]), 0, 1)
            self.life += 1
        self.counter += 1
        if self.life > 4:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """:
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Cross_hairs(pg.sprite.Sprite):
    """
    マウスに追従する照準のクラス
    """
    def __init__(self, pos: tuple):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load("fig/cross_hairs.png").convert_alpha(), 0, 0.3)
        self.rect = self.image.get_rect()
        self.rect.centerx = pos[0]
        self.rect.centery = pos[1]

    def update(self, screen: pg.Surface):
        mouse_pos = pg.mouse.get_pos()
        self.rect.center = mouse_pos
        screen.blit(self.image, self.rect)


class Cartridge(pg.sprite.Sprite):

    def __init__(self, pos: tuple, angle: int, 
                max_x: int, min_x: int, 
                accelerate: int):
        super().__init__()
        self.vx = random.randint(min_x, max_x)
        self.vy = 0
        self.acc = accelerate
        self.angle = angle
        self.image = pg.transform.rotozoom(pg.image.load("image/cartridge.png"), angle, 0.5)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.life = 20
        self.sound1 = pg.mixer.Sound("sounds/drop_1.mp3")
        self.sound1.set_volume(0.1)
        self.sound2 = pg.mixer.Sound("sounds/drop_2.mp3")
        self.sound2.set_volume(0.1)
        self.sound3 = pg.mixer.Sound("sounds/drop_3.mp3")
        self.sound3.set_volume(0.1)
        self.sounds = [self.sound1, self.sound2, self.sound3]
        self.random = random.randint(0, 2)

    def update(self):
        self.image = pg.transform.rotate(self.image, self.angle)
        self.angle += self.angle
        self.rect.move_ip(self.vx, self.vy)
        self.vy += self.acc
        self.life -= 1
        if (check_bound(self.rect) != (True, True)) or (self.life < 0):
            if self.random == 0:
                self.sound1.play()
            elif self.random == 1:
                self.sound2.play()
            else:
                self.sound3.play()
            self.kill()


class Gun(pg.sprite.Sprite):
    """
    機関銃のクラス
    """
    def __init__(self, bird: Bird, target_rect: pg.Rect, 
                 frame_rate: int, frame_len: int,
                 sprite_lst: list, group_lst: list):
        super().__init__()
        self.anime = []
        self.counter = 0
        self.frag = False
        self.size = 0.8
        self.frame_rate = frame_rate
        self.frame_len = frame_len
        self.frame_counter = 0
        self.sound1 = pg.mixer.Sound("sounds/fire.wav")
        self.sound1.set_volume(0.7)
        self.sound2 = pg.mixer.Sound("sounds/fire2.mp3")
        self.sound2.set_volume(0.1)
        self.sprite = sprite_lst
        self.group = group_lst
        for i in range(frame_len):
            self.anime.append("image/Animation/Gun_fire/pixil-frame-" + str(i) + ".png")
        self.angle = math.degrees(math.atan2(-(target_rect.centery-bird.rect.center[1]), 
                                             (target_rect.centerx-bird.rect.center[0])))
        self.image = pg.transform.rotozoom(pg.image.load(self.anime[0]).convert_alpha(), self.angle, self.size)
        self.rect = self.image.get_rect()
    
    def update(self, screen: pg.Surface, bird: Bird, target_rect: pg.Rect):
        self.angle = math.degrees(math.atan2(-(target_rect.centery-bird.rect.center[1]), 
                                             (target_rect.centerx-bird.rect.center[0]))) - 90
        key_lst = pg.mouse.get_pressed()
        if key_lst[0]:
            self.frag = True
        else:
            self.frag = False
            self.frame_counter = 0
        if self.frag:
            if self.counter%self.frame_rate == 0:
                self.frame_counter += 1
                if self.frame_counter%self.frame_len == 1:
                    self.group[0].add(self.sprite[0](bird, target_rect))
                    self.sound1.play(0)
                    self.sound2.play(0)
                if self.frame_counter%self.frame_len == 3:
                    self.group[1].add(self.sprite[1]((self.rect.centerx + math.cos(math.radians(-self.angle)) * 50,
                                                      self.rect.centery + math.sin(math.radians(-self.angle)) * 50), 2, -1, -4, 2))
                    self.group[1].add(self.sprite[1]((self.rect.centerx + math.cos(math.radians(-self.angle)) * -50,
                                                      self.rect.centery + math.sin(math.radians(-self.angle)) * -50), -2, 4, 1, 2))
                self.image = pg.transform.rotozoom(pg.image.load(self.anime[self.frame_counter%self.frame_len]), 
                                                self.angle, self.size)
                self.rect = self.image.get_rect()
        else:
            self.image = pg.transform.rotozoom(pg.image.load(self.anime[0]), self.angle, self.size)
            self.rect = self.image.get_rect()
        self.rect.center = bird.rect.center
        self.counter += 1
        screen.blit(self.image, self.rect)


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()
    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    cartridges = pg.sprite.Group()
    aim = Cross_hairs(pg.mouse.get_pos())
    cartridges.add(Cartridge((WIDTH/2, HEIGHT/2), 90, -1, -4, -0.5))
    gun = Gun(bird, aim.rect, 1, 4, [Beam, Cartridge], [beams, cartridges])
    pg.mouse.set_visible(False)
    tmr = 0
    clock = pg.time.Clock()
    score.value=100
    while True:
        key_lst = pg.key.get_pressed()
        mouse_lst = pg.mouse.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            
        if mouse_lst[0]:
            mouse_pressed = True
        else:
            mouse_pressed = False
        screen.blit(bg_img, [0, 0])
        

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
            if emy.state == "stop" and tmr % emy.interval == 0:
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            if hasattr(bomb, "inactive") and bomb.inactive:
                continue
            if bird.state == "hyper":
                exps.add(Explosion(bomb))
                score.value += 1
            else:
                bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return

        bird.update(key_lst, screen)
        aim.update(screen)
        gun.update(screen, bird, aim.rect)
        beams.update()
        beams.draw(screen)
        emys.update() 
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        cartridges.update()
        cartridges.draw(screen)
        
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    pg.mixer.init()
    pg.mixer.set_num_channels(100)
    main()
    pg.quit()
    sys.exit()
    