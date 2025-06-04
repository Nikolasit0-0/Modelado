import pygame
import random
import math
import matplotlib.pyplot as plt
import numpy as np

# --- Constantes ---
ANCHO_PANTALLA = 800
ALTO_PANTALLA = 600
FPS = 30
MAX_FRAMES_SIMULACION = 1000 

NUM_CRIATURAS_INICIALES = 30
NUM_RECURSOS_INICIALES = 20
NUM_PELIGROS = 2

BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
GRIS_CLARO = (200, 200, 200)
COLOR_CRIATURA_RGB = (0, 150, 255)
COLOR_PELIGRO_RGB = (255, 0, 0)
COLOR_RECURSO_RGB = (0, 255, 0)
COLOR_EXPLORANDO_RGB = (100, 100, 100)

COLOR_CRIATURA_MPL = tuple(c/255 for c in COLOR_CRIATURA_RGB)
COLOR_PELIGRO_MPL = tuple(c/255 for c in COLOR_PELIGRO_RGB)
COLOR_RECURSO_MPL = tuple(c/255 for c in COLOR_RECURSO_RGB)
COLOR_EXPLORANDO_MPL = tuple(c/255 for c in COLOR_EXPLORANDO_RGB)


RADIO_CRIATURA = 8
RADIO_RECURSO = 5
RADIO_PELIGRO_VISUAL = 15
VELOCIDAD_MAX_CRIATURA = 2.5
FUERZA_MAX_DIRECCION = 0.1 # Steering force limit
RADIO_VISION_RECURSO_CRIATURA = 100
RADIO_VISION_PELIGRO_CRIATURA = 120
RADIO_VISION_OTRA_CRIATURA = 50 # Para cohesión
DISTANCIA_SEPARACION_CRIATURA = 25 # Para separación
UMBRAL_CONSUMO_RECURSO = RADIO_CRIATURA + RADIO_RECURSO

# --- Variables para Estadísticas ---
datos_frames = []
datos_num_criaturas_vivas = []
datos_num_recursos_disponibles = []
datos_recursos_consumidos_total = []
total_recursos_consumidos_acumulado = 0
datos_estado_buscando = []
datos_estado_evadiendo = []
datos_estado_explorando = []
datos_dist_prom_peligro = []
datos_dist_prom_recurso_buscando = []

# --- Clases de Agentes ---
class AgenteBase(pygame.sprite.Sprite):
    def __init__(self, x, y, color_rgb, radio, mundo_ancho, mundo_alto):
        super().__init__()
        self.posicion = pygame.math.Vector2(x, y)
        self.color_rgb = color_rgb
        self.radio = radio
        self.mundo_ancho = mundo_ancho
        self.mundo_alto = mundo_alto
        self.image = pygame.Surface([radio * 2, radio * 2], pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color_rgb, (radio, radio), radio)
        self.rect = self.image.get_rect(center=(int(self.posicion.x), int(self.posicion.y)))

    def update_rect(self):
        self.rect.center = (int(self.posicion.x), int(self.posicion.y))

class Recurso(AgenteBase):
    def __init__(self, x, y, mundo_ancho, mundo_alto):
        super().__init__(x, y, COLOR_RECURSO_RGB, RADIO_RECURSO, mundo_ancho, mundo_alto)
        self.disponible = True

class Peligro(AgenteBase):
    def __init__(self, x, y, mundo_ancho, mundo_alto):
        super().__init__(x, y, COLOR_PELIGRO_RGB, RADIO_PELIGRO_VISUAL, mundo_ancho, mundo_alto)

class Criatura(AgenteBase):
    def __init__(self, x, y, mundo_ancho, mundo_alto):
        super().__init__(x, y, COLOR_CRIATURA_RGB, RADIO_CRIATURA, mundo_ancho, mundo_alto)
        self.velocidad = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.velocidad.length_squared() > 0: # Usar length_squared para eficiencia
            self.velocidad.scale_to_length(VELOCIDAD_MAX_CRIATURA)
        else:
            self.velocidad = pygame.math.Vector2(random.choice([-1.0,1.0]), random.choice([-1.0,1.0])) 
            self.velocidad.scale_to_length(VELOCIDAD_MAX_CRIATURA)
        self.estado_actual = "EXPLORANDO" # Estado inicial por defecto

    def limitar_fuerza(self, fuerza, max_fuerza):
        if fuerza.length_squared() > max_fuerza**2:
            fuerza.scale_to_length(max_fuerza)
        return fuerza

    def calcular_direccion_deseada(self, objetivo_pos, es_alejarse=False):

        if not isinstance(objetivo_pos, pygame.math.Vector2): 
            objetivo_pos = pygame.math.Vector2(objetivo_pos)

        direccion_deseada = objetivo_pos - self.posicion
        if es_alejarse:
            direccion_deseada *= -1
        
        dist_a_obj = direccion_deseada.length()
        if dist_a_obj == 0: 
            return pygame.math.Vector2(0, 0)

        direccion_deseada.scale_to_length(VELOCIDAD_MAX_CRIATURA)
        fuerza_giro = direccion_deseada - self.velocidad
        return self.limitar_fuerza(fuerza_giro, FUERZA_MAX_DIRECCION)

    def evadir(self, peligros_lista):
        fuerza_acumulada = pygame.math.Vector2(0, 0)
        count = 0
        for p_obj in peligros_lista:
            dist = self.posicion.distance_to(p_obj.posicion)
            if 0 < dist < RADIO_VISION_PELIGRO_CRIATURA:
                fuerza = self.calcular_direccion_deseada(p_obj.posicion, es_alejarse=True)
                fuerza *= (RADIO_VISION_PELIGRO_CRIATURA / dist) if dist > 0 else RADIO_VISION_PELIGRO_CRIATURA
                fuerza_acumulada += fuerza
                count += 1
        if count > 0:
            fuerza_acumulada /= count
            return self.limitar_fuerza(fuerza_acumulada, FUERZA_MAX_DIRECCION * 1.5)
        return pygame.math.Vector2(0, 0)

    def buscar(self, recursos_lista):
        recurso_mas_cercano = None
        dist_min = float('inf')
        for r_obj in recursos_lista:
            if r_obj.disponible:
                dist = self.posicion.distance_to(r_obj.posicion)
                if 0 < dist < RADIO_VISION_RECURSO_CRIATURA and dist < dist_min:
                    dist_min = dist
                    recurso_mas_cercano = r_obj
        if recurso_mas_cercano:
            fuerza = self.calcular_direccion_deseada(recurso_mas_cercano.posicion)
            return fuerza, recurso_mas_cercano
        return pygame.math.Vector2(0, 0), None

    def separar(self, otras_criaturas_lista):
        fuerza_acumulada = pygame.math.Vector2(0,0)
        count = 0
        for otra in otras_criaturas_lista:
            if otra != self:
                dist = self.posicion.distance_to(otra.posicion)
                if 0 < dist < DISTANCIA_SEPARACION_CRIATURA:
                    diff = self.posicion - otra.posicion 
                    if diff.length_squared() > 0: 
                        diff.normalize_ip()
                        diff /= dist 
                        fuerza_acumulada += diff
                        count +=1
        if count > 0:
            fuerza_acumulada /= count
            if fuerza_acumulada.length_squared() > 0:
                fuerza_acumulada.scale_to_length(VELOCIDAD_MAX_CRIATURA)
            fuerza_giro = fuerza_acumulada - self.velocidad
            return self.limitar_fuerza(fuerza_giro, FUERZA_MAX_DIRECCION * 1.2)
        return pygame.math.Vector2(0, 0)

    def cohesionar(self, otras_criaturas_lista):
        centro_masa_vecinos = pygame.math.Vector2(0,0)
        count = 0
        for otra in otras_criaturas_lista:
            if otra != self:
                if self.posicion.distance_to(otra.posicion) < RADIO_VISION_OTRA_CRIATURA:
                    centro_masa_vecinos += otra.posicion
                    count += 1
        if count > 0:
            centro_masa_vecinos /= count
            return self.calcular_direccion_deseada(centro_masa_vecinos)
        return pygame.math.Vector2(0, 0)

    def explorar(self):
        circulo_futuro = self.velocidad.copy()
        if circulo_futuro.length_squared() == 0: 
            circulo_futuro = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1))
        
        circulo_futuro.scale_to_length(20) 
        desplazamiento = pygame.math.Vector2(random.uniform(-1,1), random.uniform(-1,1))
        desplazamiento.scale_to_length(10) 
        
        fuerza_exploracion = circulo_futuro + desplazamiento
        return self.calcular_direccion_deseada(self.posicion + fuerza_exploracion) 

    def actualizar_comportamiento(self, recursos_lista, peligros_lista, otras_criaturas_lista):
        # Pesos para las fuerzas
        PESO_EVASION = 2.5
        PESO_SEPARACION = 1.8
        PESO_BUSQUEDA = 1.0
        PESO_COHESION = 0.5
        PESO_EXPLORACION = 0.3

        f_evasion = self.evadir(peligros_lista)
        f_separacion = self.separar(otras_criaturas_lista)
        f_busqueda, recurso_obj = self.buscar(recursos_lista)
        f_cohesion = self.cohesionar(otras_criaturas_lista)
        f_exploracion = self.explorar() 

        fuerza_final = pygame.math.Vector2(0,0)
        
        if f_evasion.length_squared() > 0:
            self.estado_actual = "EVADIENDO"
            fuerza_final += f_evasion * PESO_EVASION
        elif f_busqueda.length_squared() > 0:
            self.estado_actual = "BUSCANDO"
            fuerza_final += f_busqueda * PESO_BUSQUEDA
        else:
            self.estado_actual = "EXPLORANDO" # Por defecto si no hay evasión ni búsqueda
            # Si explora, la cohesión puede influir
            fuerza_final += f_cohesion * PESO_COHESION
            fuerza_final += f_exploracion * PESO_EXPLORACION # Exploración más activa si no hay otros objetivos
        
        # La separación siempre se aplica, sumada a la fuerza dominante
        fuerza_final += f_separacion * PESO_SEPARACION
        
        # Si ninguna fuerza principal fue fuerte, la exploración base toma más relevancia
        if self.estado_actual == "EXPLORANDO" and f_cohesion.length_squared() == 0 :
             fuerza_final = self.explorar() * PESO_EXPLORACION * 1.5 
             fuerza_final += f_separacion * PESO_SEPARACION 


        self.velocidad += fuerza_final 
        if self.velocidad.length_squared() > VELOCIDAD_MAX_CRIATURA**2:
            self.velocidad.scale_to_length(VELOCIDAD_MAX_CRIATURA)
        
        return recurso_obj 

    def mantener_en_pantalla(self):
        buffer = self.radio
        if self.posicion.x > self.mundo_ancho + buffer: self.posicion.x = -buffer
        elif self.posicion.x < -buffer: self.posicion.x = self.mundo_ancho + buffer
        if self.posicion.y > self.mundo_alto + buffer: self.posicion.y = -buffer
        elif self.posicion.y < -buffer: self.posicion.y = self.mundo_alto + buffer
        
    def update(self, recursos_lista, peligros_lista, otras_criaturas_lista):
        recurso_objetivo_perseguido = self.actualizar_comportamiento(recursos_lista, peligros_lista, otras_criaturas_lista)
        self.posicion += self.velocidad
        self.mantener_en_pantalla()
        self.update_rect()

        recursos_consumidos_ahora = 0
        for r in recursos_lista:
            if r.disponible and self.posicion.distance_to(r.posicion) < UMBRAL_CONSUMO_RECURSO:
                r.disponible = False
                recursos_consumidos_ahora += 1
        return recursos_consumidos_ahora, recurso_objetivo_perseguido


# --- Inicialización de Pygame y Entidades ---
pygame.init()
pantalla = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
pygame.display.set_caption("Simulación ODD con Gráficas Detalladas")
reloj = pygame.time.Clock()
fuente_debug = pygame.font.Font(None, 22) 
fuente_frames = pygame.font.Font(None, 30)

todas_las_sprites = pygame.sprite.Group()
criaturas_grupo = pygame.sprite.Group()
recursos_grupo = pygame.sprite.Group()
peligros_grupo = pygame.sprite.Group()

def crear_nuevo_recurso():
    # Intenta no poner recursos encima de peligros
    for _ in range(10): 
        x = random.randrange(RADIO_RECURSO, ANCHO_PANTALLA - RADIO_RECURSO)
        y = random.randrange(RADIO_RECURSO, ALTO_PANTALLA - RADIO_RECURSO)
        nueva_pos = pygame.math.Vector2(x,y)
        muy_cerca_de_peligro = False
        for p in peligros_grupo:
            if nueva_pos.distance_to(p.posicion) < RADIO_PELIGRO_VISUAL * 2:
                muy_cerca_de_peligro = True
                break
        if not muy_cerca_de_peligro:
            recurso = Recurso(x, y, ANCHO_PANTALLA, ALTO_PANTALLA)
            todas_las_sprites.add(recurso)
            recursos_grupo.add(recurso)
            return recurso
    # Si falla, ponerlo en cualquier lado
    recurso = Recurso(random.randrange(RADIO_RECURSO, ANCHO_PANTALLA - RADIO_RECURSO), 
                      random.randrange(RADIO_RECURSO, ALTO_PANTALLA - RADIO_RECURSO), 
                      ANCHO_PANTALLA, ALTO_PANTALLA)
    todas_las_sprites.add(recurso)
    recursos_grupo.add(recurso)
    return recurso


for _ in range(NUM_CRIATURAS_INICIALES):
    criatura = Criatura(random.randrange(ANCHO_PANTALLA), random.randrange(ALTO_PANTALLA), ANCHO_PANTALLA, ALTO_PANTALLA)
    todas_las_sprites.add(criatura)
    criaturas_grupo.add(criatura)

# Crear peligros primero para que los recursos no caigan encima fácilmente
for i in range(NUM_PELIGROS):
    if i == 0: x, y = ANCHO_PANTALLA * 0.25, ALTO_PANTALLA * 0.25
    elif i == 1: x, y = ANCHO_PANTALLA * 0.75, ALTO_PANTALLA * 0.75
    else:
        x = random.randrange(RADIO_PELIGRO_VISUAL, ANCHO_PANTALLA - RADIO_PELIGRO_VISUAL)
        y = random.randrange(RADIO_PELIGRO_VISUAL, ALTO_PANTALLA - RADIO_PELIGRO_VISUAL)
    peligro = Peligro(x, y, ANCHO_PANTALLA, ALTO_PANTALLA)
    todas_las_sprites.add(peligro)
    peligros_grupo.add(peligro)

for _ in range(NUM_RECURSOS_INICIALES):
    crear_nuevo_recurso()

# --- Bucle Principal de Simulación ---
ejecutando = True
mostrar_debug_info = True # Por defecto activado
frame_actual = 0

print("Iniciando simulación Pygame...")

while ejecutando and frame_actual < MAX_FRAMES_SIMULACION:
    frame_actual += 1
    recursos_consumidos_en_este_frame = 0
    
    # Contadores de estados y listas para distancias (resetear cada frame)
    count_buscando, count_evadiendo, count_explorando = 0, 0, 0
    distancias_a_peligros_frame = []
    distancias_a_recursos_buscando_frame = []

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_r: 
                for _ in range(5): crear_nuevo_recurso()
            if evento.key == pygame.K_d: 
                mostrar_debug_info = not mostrar_debug_info
            if evento.key == pygame.K_ESCAPE or evento.key == pygame.K_q: 
                ejecutando = False
    
    if not ejecutando: break # Salir si el evento cambió la bandera

    # --- Lógica de Actualización ---
    lista_recursos_actuales = list(recursos_grupo)
    lista_peligros_actuales = list(peligros_grupo)
    lista_criaturas_actuales = list(criaturas_grupo)

    if not lista_criaturas_actuales: # Si todas las criaturas mueren (si se implementa)
        print(f"Frame {frame_actual}: No quedan criaturas. Terminando.")
        ejecutando = False
        break

    for criatura in lista_criaturas_actuales:
        consumidos_ahora, recurso_perseguido = criatura.update(
            lista_recursos_actuales, 
            lista_peligros_actuales, 
            lista_criaturas_actuales
        )
        recursos_consumidos_en_este_frame += consumidos_ahora

        # Recolectar estado
        if criatura.estado_actual == "BUSCANDO":
            count_buscando += 1
            if recurso_perseguido and recurso_perseguido.disponible: # Solo si el recurso aún existe y está disponible
                try:
                    dist = criatura.posicion.distance_to(recurso_perseguido.posicion)
                    distancias_a_recursos_buscando_frame.append(dist)
                except AttributeError: # Si recurso_perseguido no tiene .posicion (ya no existe, etc.)
                    pass # No añadir a la lista
        elif criatura.estado_actual == "EVADIENDO":
            count_evadiendo += 1
        elif criatura.estado_actual == "EXPLORANDO":
            count_explorando += 1
        
        # Distancia al peligro más cercano
        if lista_peligros_actuales:
            dist_min_p = min(criatura.posicion.distance_to(p.posicion) for p in lista_peligros_actuales)
            distancias_a_peligros_frame.append(dist_min_p)

    # Reponer recursos consumidos
    recursos_a_reponer = [r for r in recursos_grupo if not r.disponible]
    for _ in recursos_a_reponer:
        crear_nuevo_recurso()
    for r_removido in recursos_a_reponer: # Eliminar después de iterar sobre ellos
        r_removido.kill()
    
    total_recursos_consumidos_acumulado += recursos_consumidos_en_este_frame

    # Almacenar datos para gráficas
    datos_frames.append(frame_actual)
    datos_num_criaturas_vivas.append(len(lista_criaturas_actuales)) # Asumiendo que no mueren
    datos_num_recursos_disponibles.append(len(recursos_grupo))
    datos_recursos_consumidos_total.append(total_recursos_consumidos_acumulado)
    datos_estado_buscando.append(count_buscando)
    datos_estado_evadiendo.append(count_evadiendo)
    datos_estado_explorando.append(count_explorando)
    
    datos_dist_prom_peligro.append(np.mean(distancias_a_peligros_frame) if distancias_a_peligros_frame else np.nan)
    datos_dist_prom_recurso_buscando.append(np.mean(distancias_a_recursos_buscando_frame) if distancias_a_recursos_buscando_frame else np.nan)

    # --- Dibujo ---
    pantalla.fill(GRIS_CLARO)
    recursos_grupo.draw(pantalla) # Dibujar recursos primero
    peligros_grupo.draw(pantalla)
    criaturas_grupo.draw(pantalla) # Criaturas encima

    # Info en pantalla
    texto_frame_render = fuente_frames.render(f"Frame: {frame_actual}/{MAX_FRAMES_SIMULACION}", True, NEGRO)
    pantalla.blit(texto_frame_render, (ANCHO_PANTALLA - texto_frame_render.get_width() - 10, 10))

    if mostrar_debug_info:
        info_text_lines = [
            f"Criaturas: {len(lista_criaturas_actuales)}",
            f"  Buscando: {count_buscando}",
            f"  Evadiendo: {count_evadiendo}",
            f"  Explorando: {count_explorando}",
            f"Recursos Disp: {len(recursos_grupo)}",
            f"Consumidos (Frame): {recursos_consumidos_en_este_frame}",
            f"Consumidos (Total): {total_recursos_consumidos_acumulado}",
            f"Dist. Prom. Peligro: {datos_dist_prom_peligro[-1]:.1f}" if datos_dist_prom_peligro and not np.isnan(datos_dist_prom_peligro[-1]) else "Dist. Prom. Peligro: N/A",
            f"Dist. Prom. Recurso: {datos_dist_prom_recurso_buscando[-1]:.1f}" if datos_dist_prom_recurso_buscando and not np.isnan(datos_dist_prom_recurso_buscando[-1]) else "Dist. Prom. Recurso: N/A"
        ]
        for i, line in enumerate(info_text_lines):
            pantalla.blit(fuente_debug.render(line, True, NEGRO), (10, 10 + i * 18))

    pygame.display.flip()
    reloj.tick(FPS)

print("Bucle de Pygame finalizado.")
pygame.quit()
print("Pygame cerrado.")

# --- Generación de Gráficas ---
if datos_frames and len(datos_frames) > 1 : # Necesitamos al menos 2 puntos para una línea
    print("Generando gráficas de resultados...")
    
    try:
        fig, axs = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True) # constrained_layout ayuda con superposiciones
        fig.suptitle('Estadísticas de Comportamiento de la Simulación', fontsize=16)

        # Gráfica 1: Distribución de Estados
        axs[0, 0].stackplot(datos_frames, 
                            datos_estado_buscando, 
                            datos_estado_evadiendo, 
                            datos_estado_explorando, 
                            labels=['Buscando', 'Evadiendo', 'Explorando'],
                            colors=[COLOR_RECURSO_MPL, COLOR_PELIGRO_MPL, COLOR_EXPLORANDO_MPL],
                            alpha=0.8)
        axs[0, 0].set_xlabel('Frame')
        axs[0, 0].set_ylabel('Número de Criaturas')
        axs[0, 0].set_title('Distribución de Estados')
        axs[0, 0].legend(loc='best')
        axs[0, 0].grid(True, linestyle=':', alpha=0.7)
        axs[0, 0].set_xlim(min(datos_frames), max(datos_frames))

        # Gráfica 2: Distancia Promedio al Peligro
        axs[0, 1].plot(datos_frames, datos_dist_prom_peligro, label='Dist. Prom. a Peligro', color='magenta', marker='.', markersize=2, linestyle='-')
        axs[0, 1].set_xlabel('Frame')
        axs[0, 1].set_ylabel('Distancia Promedio')
        axs[0, 1].set_title('Distancia Promedio al Peligro Más Cercano')
        axs[0, 1].legend(loc='best')
        axs[0, 1].grid(True, linestyle=':', alpha=0.7)
        axs[0, 1].set_xlim(min(datos_frames), max(datos_frames))


        # Gráfica 3: Distancia Promedio al Recurso (buscando)
        axs[1, 0].plot(datos_frames, datos_dist_prom_recurso_buscando, label='Dist. Prom. a Recurso (buscando)', color='darkcyan', marker='.', markersize=2, linestyle='-')
        axs[1, 0].set_xlabel('Frame')
        axs[1, 0].set_ylabel('Distancia Promedio')
        axs[1, 0].set_title('Eficiencia de Búsqueda (Dist. a Recurso)')
        axs[1, 0].legend(loc='best')
        axs[1, 0].grid(True, linestyle=':', alpha=0.7)
        axs[1, 0].set_xlim(min(datos_frames), max(datos_frames))


        # Gráfica 4: Total Recursos Consumidos
        axs[1, 1].plot(datos_frames, datos_recursos_consumidos_total, label='Total Recursos Consumidos', color='darkorchid', linewidth=2)
        axs[1, 1].set_xlabel('Frame')
        axs[1, 1].set_ylabel('Cantidad Acumulada')
        axs[1, 1].set_title('Recursos Consumidos (Acumulado)')
        axs[1, 1].legend(loc='best')
        axs[1, 1].grid(True, linestyle=':', alpha=0.7)
        axs[1, 1].set_xlim(min(datos_frames), max(datos_frames))

        print("Mostrando gráficas...")
        plt.show()
        print("Ventana de gráficas cerrada.")

    except Exception as e_graph:
        print(f"ERROR al generar o mostrar las gráficas: {e_graph}")
        import traceback
        traceback.print_exc()
else:
    print("No se recolectaron datos suficientes para graficar (simulación no corrió o muy pocos frames).")

print("Script Python finalizado.")