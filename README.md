# Simulador de Tráfego Urbano com Concorrência
# Urban Traffic Concurrency Simulator

Projeto desenvolvido para a disciplina **Programação Concorrente** do curso de **Ciência da Computação**.

Project developed for the subject **Competing Programming** of the **Computer Science** course.

---

## 🇧🇷 Português

### Descrição
Este projeto implementa uma **simulação de tráfego urbano** utilizando **programação concorrente com memória compartilhada**. O sistema modela uma malha viária onde cada veículo opera como uma **thread independente**, competindo por recursos (espaço físico) e respeitando regras de sincronização para evitar colisões e deadlocks.

### Destaques da Implementação
- **Gerenciamento de Threads**: Cada veículo no mapa é uma thread individual.
- **Exclusão Mútua (Mutex/Locks)**: Controle rigoroso de acesso às coordenadas da via, garantindo que dois veículos nunca ocupem o mesmo espaço simultaneamente.
- **Sincronização de Semáforos**: Uso de variáveis de sinalização para que veículos em sinal vermelho entrem em estado de espera, otimizando o uso de CPU.
- **Prioridade Dinâmica**: Sistema de preempção de sinais para veículos de emergência.
- **Interface Gráfica 2D**: Visualização em tempo real utilizando a biblioteca Pygame.

### Características Técnicas
- **Malha Viária**: Grid de 30x30 células com vias contínuas e cruzamentos.
- **Relógio Global Discreto**: Sincronização de tempo baseada em *ticks* para controle de velocidade.
- **Eficiência de CPU**: Veículos parados no sinal vermelho entram em estado de espera (*waiting*) e não consomem processamento, utilizando `threading.Event`.
- **Impenetrabilidade**: Implementada via **Mutex/Locks** por coordenada, garantindo que dois corpos não ocupem o mesmo espaço.

### Veículos e Velocidades
Os veículos são gerados aleatoriamente com as seguintes propriedades:
- 🔵 **Carro Rápido (Azul)**: Move-se em 1 tick do relógio.
- 🟡 **Carro Médio (Amarelo)**: Move-se em 2 ticks do relógio.
- 🟢 **Carro Lento (Verde)**: Move-se em 4 ticks do relógio.
- 🔴 **Ambulância (Vermelho)**: Veículo de emergência com prioridade máxima.

### Regras de Prioridade da Ambulância
- **Forçar Sinal**: Ao detectar um semáforo (mesmo que não seja o primeiro da fila), a ambulância força o sinal a ficar verde para sua direção.
- **Desempate de Emergência**: Se duas ambulâncias chegarem a cruzamentos conflitantes, a primeira a solicitar a prioridade mantém o sinal aberto, enquanto a segunda aguarda a liberação do cruzamento para evitar sinais verdes simultâneos em sentidos opostos.

### Interface Gráfica (Pygame)
- **Grid de 30x30**: Espaçamento amplo entre vias para melhor visualização.
- **Semáforos**: 
  - 🟢/🔴 Esfera no **canto inferior esquerdo**: Representa o sinal da via **Horizontal**.
  - 🟢/🔴 Esfera no **canto superior direito**: Representa o sinal da via **Vertical**.

## Como Executar

1. Certifique-se de ter o Python 3 e a biblioteca Pygame instalados:
   ```bash
   pip install pygame
2. Execulte traffic_simulator.py ou traffic_simulator_with_car.py
  ```bash
  python traffic_simulator.py
  ou
  ```bash
  python traffic_simulator_with_car.py

---

## 🇺🇸 English

### Description
This project implements an **urban traffic simulation** using **concurrent programming with shared memory**. Each vehicle is an **independent thread** that competes for physical space (shared resources) while following synchronization rules to prevent collisions and deadlocks.

### Implementation Highlights
- **Thread Management**: Each vehicle on the map is an individual thread.
- **Mutual Exclusion (Mutex/Locks)**: Strict control of access to road coordinates, ensuring no two vehicles occupy the same space.
- **Traffic Light Synchronization**: Signaling variables allow vehicles at red lights to enter a wait state, optimizing CPU usage.
- **Dynamic Priority**: Traffic light preemption system for emergency vehicles.
- **2D Graphical Interface**: Real-time visualization using the Pygame library.

### Technical Features
- **Road Network**: A 30x30 grid with continuous roads and multiple intersections.
- **Discrete Global Clock**: Tick-based synchronization for speed control.
- **CPU Efficiency**: Vehicles stopped at red lights enter a wait state using `threading.Event`, ensuring zero CPU consumption while idling.
- **Impenetrability**: Handled via **Mutex/Locks** per coordinate, ensuring no two vehicles occupy the same cell.

### Vehicles and Speeds
Vehicles are spawned randomly with the following color-coded speeds:
- 🔵 **Fast Car (Blue)**: Moves every 1 clock tick.
- 🟡 **Medium Car (Yellow)**: Moves every 2 clock ticks.
- 🟢 **Slow Car (Green)**: Moves every 4 clock ticks.
- 🔴 **Ambulance (Red)**: Emergency vehicle with maximum priority.

### Ambulance Priority Rules
- **Traffic Light Preemption**: Upon detecting an intersection, the ambulance forces the light to turn green for its direction, even if it is not at the front of the queue.
- **Emergency Tie-breaking**: If two ambulances approach conflicting roads, the first one to claim priority holds the green light until it clears the path, preventing simultaneous green lights in perpendicular directions.

### Graphical Interface (Pygame)
- **30x30 Grid**: Larger scale for better traffic flow observation.
- **Traffic Light Indicators**:
  - 🟢/🔴 Sphere at the **bottom-left**: Represents the **Horizontal** flow.
  - 🟢/🔴 Sphere at the **top-right**: Represents the **Vertical** flow.

---

## How to Run

1. Make sure you have Python 3 and the Pygame library installed:
   ```bash
   pip install pygame
2. Run traffic_simulator.py or traffic_simulator_with_car.py
  ```bash
  python traffic_simulator.py
  or
  ```bash
  python traffic_simulator_with_car.py
