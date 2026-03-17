import pygame
import threading
import time
import random
import sys

# ------------ setar o fps maior aumenta a quantidade de carros por causa da logica---------------------
CELL_SIZE = 25   
GRID_SIZE = 30   
FPS = 10

COLOR_BG = (20, 20, 20)
COLOR_ROAD = (45, 45, 45)
COLOR_CAR_FAST = (0, 0, 255)
COLOR_CAR_MED = (255, 255, 0)
COLOR_CAR_SLOW = (0, 255, 0)
COLOR_AMBULANCE = (255, 0, 0)
COLOR_RED_LIGHT = (255, 0, 0)
COLOR_GREEN_LIGHT = (0, 255, 0)

ROADS_H = [5, 12, 19, 26]
ROADS_V = [5, 12, 19, 26]

# mutexes para controle das células e renderização
grid_locks = {(x, y): threading.Lock() for x in range(GRID_SIZE) for y in range(GRID_SIZE)}
render_mutex = threading.Lock()

global_tick = 0
def clock_manager():
    global global_tick
    while True:
        time.sleep(0.1)
        global_tick += 1

class TrafficLight:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.horizontal_green = random.choice([True, False])
        self.event_h = threading.Event()
        self.event_v = threading.Event()
        self.active_ambulance_direction = None 
        self._update_events()

    def _update_events(self):
        if self.horizontal_green:
            self.event_h.set()
            self.event_v.clear()
        else:
            self.event_h.clear()
            self.event_v.set()

    def toggle(self):
        if self.active_ambulance_direction is None:
            self.horizontal_green = not self.horizontal_green
            self._update_events()

    def force_green(self, direction):
        self.active_ambulance_direction = direction
        self.horizontal_green = (direction == 'H')
        self._update_events()

    def release_priority(self):
        self.active_ambulance_direction = None

intersections = {(x, y): TrafficLight(x, y) for x in ROADS_V for y in ROADS_H}

class Vehicle(threading.Thread):
    def __init__(self, is_ambulance=False):
        super().__init__()
        self.daemon = True
        self.active = True
        self.is_ambulance = is_ambulance
        self.direction = random.choice(['H', 'V'])
        
        if self.direction == 'H':
            self.y, self.x = random.choice(ROADS_H), 0
            self.dx, self.dy = 1, 0
        else:
            self.x, self.y = random.choice(ROADS_V), 0
            self.dx, self.dy = 0, 1

        if self.is_ambulance:
            self.speed_ticks, self.color = 1, COLOR_AMBULANCE
        else:
            v_type = random.random()
            if v_type < 0.33: self.speed_ticks, self.color = 1, COLOR_CAR_FAST
            elif v_type < 0.66: self.speed_ticks, self.color = 2, COLOR_CAR_MED
            else: self.speed_ticks, self.color = 4, COLOR_CAR_SLOW

    def run(self):
        if not grid_locks[(self.x, self.y)].acquire(blocking=False):
            self.active = False
            return

        current_light = None
        while self.active:
            #prioridade para ambulância
            if self.is_ambulance:
                for i in range(0, 6):
                    tx, ty = self.x + (self.dx * i), self.y + (self.dy * i)
                    if (tx, ty) in intersections:
                        light = intersections[(tx, ty)]
                        if light.active_ambulance_direction in [None, self.direction]:
                            light.force_green(self.direction)
                            current_light = light

            last_t = global_tick
            while global_tick - last_t < self.speed_ticks:
                time.sleep(0.01)

            nx, ny = self.x + self.dx, self.y + self.dy

            if nx >= GRID_SIZE or ny >= GRID_SIZE:
                grid_locks[(self.x, self.y)].release()
                if current_light: current_light.release_priority()
                self.active = False
                break

            if (nx, ny) in intersections:
                light = intersections[(nx, ny)]
                if self.direction == 'H': light.event_h.wait()
                else: light.event_v.wait()
                current_light = light

            if (self.x, self.y) in intersections:
                intersections[(self.x, self.y)].release_priority()

            # sincronização da movimentação
            if grid_locks[(nx, ny)].acquire():
                with render_mutex:
                    grid_locks[(self.x, self.y)].release()
                    self.x, self.y = nx, ny

def main():
    pygame.init()
    screen = pygame.display.set_mode((GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE))
    pygame.display.set_caption("Simulador de Tráfego")
    
    try:
        car_img = pygame.image.load("prog_concorrente/carro_tex.png").convert_alpha()
        car_img = pygame.transform.smoothscale(car_img, (CELL_SIZE, CELL_SIZE))
    except:
        car_img = None
    
    threading.Thread(target=clock_manager, daemon=True).start()
    
    def auto_lights():
        while True:
            time.sleep(4)
            for l in intersections.values(): l.toggle()
    threading.Thread(target=auto_lights, daemon=True).start()

    vehicles, spawn_counter, clock = [], 0, pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        # Num de carros etc.
        active_v = [v for v in vehicles if v.active]
        if len(active_v) < 30 and spawn_counter > 5:
            new_v = Vehicle(is_ambulance=(random.random() < 0.05))
            new_v.start()
            if new_v.active: vehicles.append(new_v)
            spawn_counter = 0
        spawn_counter += 1

        # --- RENDERIZAÇÃO ---
        with render_mutex:
            screen.fill(COLOR_BG)
            for h in ROADS_H: pygame.draw.rect(screen, COLOR_ROAD, (0, h*CELL_SIZE, GRID_SIZE*CELL_SIZE, CELL_SIZE))
            for v in ROADS_V: pygame.draw.rect(screen, COLOR_ROAD, (v*CELL_SIZE, 0, CELL_SIZE, GRID_SIZE*CELL_SIZE))

            for (x, y), l in intersections.items():
                c_h = COLOR_GREEN_LIGHT if l.horizontal_green else COLOR_RED_LIGHT
                c_v = COLOR_RED_LIGHT if l.horizontal_green else COLOR_GREEN_LIGHT
                pygame.draw.circle(screen, c_h, (x*CELL_SIZE + 6, (y+1)*CELL_SIZE - 6), 6)
                pygame.draw.circle(screen, c_v, ((x+1)*CELL_SIZE - 6, y*CELL_SIZE + 6), 6)

            for v in active_v:
                if not car_img: continue
                
                #se for ambulancia desenha o giroflex
                if v.is_ambulance:
                    b_col = (0, 0, 255, 80) if global_tick % 2 == 0 else (255, 0, 0, 80)
                    b_surf = pygame.Surface((CELL_SIZE * 2, CELL_SIZE * 2), pygame.SRCALPHA)
                    pygame.draw.circle(b_surf, b_col, (CELL_SIZE, CELL_SIZE), CELL_SIZE)
                    screen.blit(b_surf, (v.x * CELL_SIZE - CELL_SIZE // 2, v.y * CELL_SIZE - CELL_SIZE // 2))
                
                car_draw = car_img.copy()
                colored = pygame.Surface(car_draw.get_size(), pygame.SRCALPHA)
                colored.fill(v.color + (255,))
                car_draw.blit(colored, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                #faróis
                cx, cy = v.x * CELL_SIZE + CELL_SIZE // 2, v.y * CELL_SIZE + CELL_SIZE // 2
                f_surf = pygame.Surface((GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE), pygame.SRCALPHA)
                if v.direction == 'H':
                    pts = [(cx, cy), (cx + 60, cy - 24), (cx + 60, cy + 24)]
                    car_draw = pygame.transform.rotate(car_draw, 270)
                else:
                    pts = [(cx, cy), (cx - 24, cy + 60), (cx + 24, cy + 60)]
                    car_draw = pygame.transform.rotate(car_draw, 180)

                pygame.draw.polygon(f_surf, (255, 255, 0, 20), pts)
                screen.blit(f_surf, (0, 0))
                screen.blit(car_draw, (v.x * CELL_SIZE, v.y * CELL_SIZE))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
