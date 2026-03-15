import pygame
import threading
import time
import random
import sys

# ================= CONFIGURAÇÕES DO PROJETO =================
CELL_SIZE = 25   
GRID_SIZE = 30   
FPS = 60

# Cores
COLOR_BG = (20, 20, 20)
COLOR_ROAD = (45, 45, 45)
COLOR_CAR_FAST = (0, 0, 255)     # Azul
COLOR_CAR_MED = (255, 255, 0)    # Amarelo
COLOR_CAR_SLOW = (0, 255, 0)     # Verde
COLOR_AMBULANCE = (255, 0, 0)    # Vermelho
COLOR_RED_LIGHT = (255, 0, 0)
COLOR_GREEN_LIGHT = (0, 255, 0)

ROADS_H = [5, 12, 19, 26]
ROADS_V = [5, 12, 19, 26]

# [CONCORRÊNCIA] Locks: Garante que cada célula do grid seja um recurso compartilhado único. Isso impede que dois carros ocupem a mesma coordenada ao mesmo tempo.
grid_locks = {(x, y): threading.Lock() for x in range(GRID_SIZE) for y in range(GRID_SIZE)}

# [SINCRONIZAÇÃO] Relógio Global: Thread separada que dita o tempo discreto da simulação.
global_tick = 0
def clock_manager():
    global global_tick
    while True:
        time.sleep(0.1)
        global_tick += 1

# ================= CLASSES DE SINCRONIZAÇÃO =================

class TrafficLight:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.horizontal_green = random.choice([True, False])
        # [THREADS EM ESPERA] Events: Fazem as threads dormirem para não consumir CPU.
        self.event_h = threading.Event()
        self.event_v = threading.Event()
        self.active_ambulance_direction = None 
        self._update_events()

    def _update_events(self):
        #Atualiza quais threads podem prosseguir e quais devem dormir.
        if self.horizontal_green:
            self.event_h.set()   # Sinal Verde: Libera threads no sentido horizontal
            self.event_v.clear() # Sinal Vermelho: Bloqueia threads no sentido vertical
        else:
            self.event_h.clear()
            self.event_v.set()

    def toggle(self):
        #Alterna o sinal, a menos que uma ambulância tenha prioridade ativa.
        if self.active_ambulance_direction is None:
            self.horizontal_green = not self.horizontal_green
            self._update_events()

    def force_green(self, direction):
        #Mecanismo de Preempção: Força a abertura para a ambulância.
        self.active_ambulance_direction = direction
        self.horizontal_green = (direction == 'H')
        self._update_events()

    def release_priority(self):
        #Libera o semáforo para o ciclo automático normal.
        self.active_ambulance_direction = None

# Criação dos objetos de cruzamento
intersections = {(x, y): TrafficLight(x, y) for x in ROADS_V for y in ROADS_H}

# ================= VEÍCULO (THREAD) =================

class Vehicle(threading.Thread):
    def __init__(self, is_ambulance=False):
        super().__init__()
        self.daemon = True # Garante que a thread feche ao encerrar o programa
        self.active = True
        self.is_ambulance = is_ambulance
        
        # Escolha aleatória de rota
        self.direction = random.choice(['H', 'V'])
        if self.direction == 'H':
            self.y = random.choice(ROADS_H); self.x = 0
            self.dx, self.dy = 1, 0
        else:
            self.x = random.choice(ROADS_V); self.y = 0
            self.dx, self.dy = 0, 1

        # Definição de velocidade baseada em Ticks do Relógio
        if self.is_ambulance:
            self.speed_ticks = 1
            self.color = COLOR_AMBULANCE
        else:
            v_type = random.random()
            if v_type < 0.33: self.speed_ticks = 1; self.color = COLOR_CAR_FAST
            elif v_type < 0.66: self.speed_ticks = 2; self.color = COLOR_CAR_MED
            else: self.speed_ticks = 4; self.color = COLOR_CAR_SLOW

    def run(self):
        # [EXCLUSÃO MÚTUA] Tenta spawnar: Só entra se a posição inicial não estiver ocupada.
        if not grid_locks[(self.x, self.y)].acquire(blocking=False):
            self.active = False
            return

        current_light = None

        while self.active:
            # [PRIORIDADE] Lógica da Ambulância: Verifica até 5 casas à frente para abrir semáforos.
            if self.is_ambulance:
                for i in range(0, 6):
                    tx, ty = self.x + (self.dx * i), self.y + (self.dy * i)
                    if (tx, ty) in intersections:
                        light = intersections[(tx, ty)]
                        if light.active_ambulance_direction in [None, self.direction]:
                            light.force_green(self.direction)
                            current_light = light

            # [TEMPO DISCRETO] Espera o número de ticks correspondente à sua velocidade.
            last_t = global_tick
            while global_tick - last_t < self.speed_ticks:
                time.sleep(0.01)

            nx, ny = self.x + self.dx, self.y + self.dy

            # Verificação de saída do mapa
            if nx >= GRID_SIZE or ny >= GRID_SIZE:
                grid_locks[(self.x, self.y)].release()
                if current_light: current_light.release_priority()
                self.active = False
                break

            # [SINCRONIZAÇÃO] Semáforo: Se estiver vermelho, a thread dorme no .wait()
            if (nx, ny) in intersections:
                light = intersections[(nx, ny)]
                if self.direction == 'H': light.event_h.wait()
                else: light.event_v.wait()
                current_light = light

            # Libera prioridade do semáforo anterior após atravessar
            if (self.x, self.y) in intersections:
                intersections[(self.x, self.y)].release_priority()

            # [EXCLUSÃO MÚTUA] Movimentação: Bloqueia a próxima célula e libera a atual.
            if grid_locks[(nx, ny)].acquire():
                grid_locks[(self.x, self.y)].release()
                self.x, self.y = nx, ny

# ================= LOOP PRINCIPAL =================

def main():
  pygame.init()
  screen = pygame.display.set_mode((GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE))
  pygame.display.set_caption("Simulador de Tráfego")
  
  # Inicia a thread do relógio
  threading.Thread(target=clock_manager, daemon=True).start()
  
  # Thread Controladora dos Semáforos (Muda o estado a cada 4 segundos)
  def auto_traffic_lights():
    while True:
      time.sleep(4)
      for l in intersections.values(): l.toggle()
  threading.Thread(target=auto_traffic_lights, daemon=True).start()

  vehicles = []
  spawn_counter = 0
  
  while True:
    for event in pygame.event.get():
      if event.type == pygame.QUIT: pygame.quit(); sys.exit()

    # [DINÂMICA] Controle de fluxo: Mantém até 30 veículos ativos no grid.
    active_v = [v for v in vehicles if v.active]
    if len(active_v) < 30 and spawn_counter > 5:
      # Probabilidade de vir ambulância
      is_amb = random.random() < 0.15
      new_v = Vehicle(is_ambulance=is_amb)
      new_v.start() # Inicia a execução da Thread do veículo
      if new_v.active: vehicles.append(new_v)
      spawn_counter = 0
    spawn_counter += 1

    # --- RENDERIZAÇÃO ---
    screen.fill(COLOR_BG)
    # Desenha as estradas
    for h in ROADS_H: pygame.draw.rect(screen, COLOR_ROAD, (0, h*CELL_SIZE, GRID_SIZE*CELL_SIZE, CELL_SIZE))
    for v in ROADS_V: pygame.draw.rect(screen, COLOR_ROAD, (v*CELL_SIZE, 0, CELL_SIZE, GRID_SIZE*CELL_SIZE))

    # Desenha os sinais
    for (x, y), l in intersections.items():
      ch = COLOR_GREEN_LIGHT if l.horizontal_green else COLOR_RED_LIGHT
      cv = COLOR_RED_LIGHT if l.horizontal_green else COLOR_GREEN_LIGHT
      # Horizontal (Baixo-Esquerda) | Vertical (Cima-Direita)
      pygame.draw.circle(screen, ch, (x*CELL_SIZE + 6, (y+1)*CELL_SIZE - 6), 6)
      pygame.draw.circle(screen, cv, ((x+1)*CELL_SIZE - 6, y*CELL_SIZE + 6), 6)

    # Desenha os veículos
    for v in active_v:
      try:
        car_image = pygame.image.load("prog_concorrente/carro_tex.png").convert_alpha()
        car_image = pygame.transform.smoothscale(car_image, (int(CELL_SIZE), int(CELL_SIZE)))

        # Define a cor do farol com base no tipo de veículo
        headlight_color = (255, 255, 0, 20)  # Amarelo com alpha baixo para outros veículos

        # Desenha o farol (triângulo com alpha mais baixo)
        headlight = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        if v.is_ambulance:
          
          blink_color = (0, 0, 255, 80) if global_tick % 2 == 0 else (255, 0, 0, 80)
          blink_surface = pygame.Surface((CELL_SIZE * 2, CELL_SIZE * 2), pygame.SRCALPHA)
          pygame.draw.circle(blink_surface, blink_color, (CELL_SIZE, CELL_SIZE), CELL_SIZE)
          screen.blit(blink_surface, (v.x * CELL_SIZE - CELL_SIZE // 2, v.y * CELL_SIZE - CELL_SIZE // 2))
        
        # Aplica a cor do veículo à textura
        colored_car = pygame.Surface(car_image.get_size(), pygame.SRCALPHA)
        colored_car.fill(v.color + (255,))  # Ensure alpha is set to 255 for visibility
        car_image.blit(colored_car, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        
      
      # Desenha um triângulo equilátero gigantesco que ocupa a tela inteira com a origem na posição do carro
        giant_headlight = pygame.Surface((GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE), pygame.SRCALPHA)
        center_x = v.x * CELL_SIZE + CELL_SIZE // 2
        center_y = v.y * CELL_SIZE + CELL_SIZE // 2
        size = 30

        if v.direction == 'H':  # Carros vindo de lado
          
          points = [
          (center_x, center_y),  # Right vertex
          (center_x + size + 30, center_y - size * 0.8),  # Top vertex
          (center_x + size + 30, center_y + size * 0.8)   # Bottom vertex
        ]
        else:  # Carros vindo de cima ou de baixo
          points = [
        (center_x, center_y),  # Top vertex
        (center_x - size * 0.8, center_y + size + 30),  # Bottom-left vertex
        (center_x + size * 0.8, center_y + size + 30)   # Bottom-right vertex
          ]

        pygame.draw.polygon(giant_headlight, headlight_color, points)
        screen.blit(giant_headlight, (0, 0))
        # Rotaciona o carro conforme a direção
        if v.direction == 'H' and v.dx > 0:  # Indo para a direita
          car_image = pygame.transform.rotate(car_image, 270)
        elif v.direction == 'H' and v.dx < 0:  # Indo para a esquerda
          car_image = pygame.transform.rotate(car_image, 90)
        elif v.direction == 'V' and v.dy > 0:  # Indo para baixo
          car_image = pygame.transform.rotate(car_image, 180)
        elif v.direction == 'V' and v.dy < 0:  # Indo para cima
          car_image = pygame.transform.rotate(car_image, 0)

        
        
        # Renderiza o carro na posição correta
        screen.blit(car_image, (v.x * CELL_SIZE , v.y * CELL_SIZE ))

      except pygame.error as e:
        print(f"Error loading or rendering car image: {e}")

    pygame.display.flip()
    pygame.time.Clock().tick(FPS)

if __name__ == "__main__":
  main()