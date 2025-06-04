
# Simulación por Agentes: Criaturas Buscadoras de Recursos y Evasoras de Peligro

## 1. Introducción y Propósito

Este proyecto presenta una simulación por agentes desarrollada en Python utilizando la biblioteca Pygame. La simulación modela un ecosistema simplificado donde múltiples **Criaturas** (agentes) autónomas interactúan en un entorno 2D con el objetivo principal de sobrevivir y prosperar. Su comportamiento se rige por la búsqueda de **Recursos** (necesarios para su subsistencia, aunque en esta versión no se implementa un sistema de energía que lleve a la muerte) y la evasión de **Peligros** estáticos presentes en el mapa.

El propósito fundamental de esta simulación es observar y analizar el **comportamiento emergente** que surge de reglas locales simples implementadas en cada criatura. No se programa explícitamente un comportamiento colectivo complejo, sino que este surge de las interacciones individuales de los agentes con su entorno y entre ellos. Se busca entender cómo patrones como la formación de rutas, la aglomeración en zonas ricas en recursos o la evitación de áreas peligrosas pueden desarrollarse espontáneamente.

## 2. Motivación de la Temática

La elección de una simulación basada en la búsqueda de recursos y evasión de peligros en un entorno natural se inspira en observaciones fundamentales del comportamiento animal y los principios de la ecología. Estos comportamientos son cruciales para la supervivencia y la dinámica de poblaciones en la naturaleza. Modelar este tipo de interacciones permite:

*   **Explorar conceptos de autoorganización:** Cómo sistemas complejos pueden surgir de componentes simples.
*   **Estudiar la toma de decisiones bajo incertidumbre:** Las criaturas operan con información local y limitada.
*   **Visualizar patrones espaciales dinámicos:** Cómo la distribución de agentes y recursos cambia con el tiempo.
*   **Proporcionar una base intuitiva y relatable:** Los conceptos de buscar comida y evitar el peligro son fácilmente comprensibles.

Esta temática ofrece un rico conjunto de comportamientos emergentes potenciales y se alinea bien con los principios del modelado basado en agentes, como se ve en ejemplos clásicos como "Flock of Birds" (modelo de Boids), pero con un enfoque en objetivos diferentes (recursos y peligros en lugar de solo movimiento coordinado).

## 3. Implementación del Protocolo ODD (Overview, Design Concepts, Details)

El desarrollo de esta simulación siguió el protocolo ODD, un estándar para describir modelos basados en agentes, asegurando claridad y reproducibilidad.

### 3.1. Overview (Visión General)

*   **Propósito:** Modelar el comportamiento de criaturas autónomas buscando recursos y evadiendo peligros para observar patrones emergentes.
*   **Entidades:**
    *   `Criatura`: Agente activo con posición, velocidad y estado (BUSCANDO, EVADIENDO, EXPLORANDO).
    *   `Recurso`: Objeto pasivo con posición, consumible.
    *   `Peligro`: Objeto pasivo estático con posición, que debe ser evitado.
*   **Escalas:**
    *   Espacial: Entorno 2D continuo (800x600 píxeles).
    *   Temporal: Pasos discretos (frames de Pygame). La simulación se ejecuta por un número definido de frames (1000 por defecto).

### 3.2. Design Concepts (Conceptos de Diseño)

*   **Emergencia:** Se esperan patrones como rutas de recolección, zonas de evitación alrededor de peligros y agrupaciones temporales.
*   **Adaptación:** Las criaturas adaptan su movimiento basándose en la percepción local (visión) de recursos, peligros y otras criaturas.
*   **Objetivos:** Implícitamente, sobrevivir al encontrar recursos y evitar peligros. Esto se traduce en las reglas de comportamiento.
*   **Percepción (Sensing):** Las criaturas tienen radios de visión definidos para detectar recursos, peligros y otras criaturas.
*   **Interacción:**
    *   Criatura-Recurso: Consumo de recursos.
    *   Criatura-Peligro: Evasión activa.
    *   Criatura-Criatura: Separación para evitar colisiones y una leve cohesión si no hay otros estímulos fuertes.
*   **Estocasticidad:** Posiciones iniciales, reaparición de recursos y pequeños componentes aleatorios en el movimiento de exploración.
*   **Observación:** Visualización en tiempo real y recolección de datos para gráficas estadísticas (distribución de estados, distancias promedio a peligros/recursos, recursos consumidos).

### 3.3. Details (Detalles)

*   **Inicialización:** Se crean N criaturas, M recursos y P peligros en posiciones iniciales (algunas aleatorias, otras predefinidas para peligros).
*   **Entrada:** Parámetros de la simulación como número de entidades, dimensiones del mundo, radios de visión, velocidades, etc., están definidos como constantes en el código.
*   **Submodelos (Comportamiento de la Criatura):**
    1.  **Percepción:** Detectar entidades en los radios de visión.
    2.  **Toma de Decisiones (Priorizada):**
        *   **Evasión de Peligro:** Si se detecta un peligro, calcular un vector de huida. (Estado: EVADIENDO)
        *   **Búsqueda de Recurso:** Si no hay peligro y se detecta un recurso, calcular un vector de atracción. (Estado: BUSCANDO)
        *   **Exploración/Cohesión:** Si no hay peligro ni recurso, aplicar una leve cohesión hacia otras criaturas visibles y/o moverse aleatoriamente. (Estado: EXPLORANDO)
        *   **Separación:** Calcular un vector para evitar la superposición con otras criaturas cercanas. Esta fuerza se aplica concurrentemente.
    3.  **Actualización de Estado:** El `estado_actual` de la criatura se actualiza según la regla dominante.
    4.  **Movimiento:** La velocidad se actualiza sumando las fuerzas calculadas (limitadas por `FUERZA_MAX_DIRECCION`), y la posición se actualiza con `posicion += velocidad`. La velocidad se limita a `VELOCIDAD_MAX_CRIATURA`.
    5.  **Límites del Mundo:** Efecto toroidal (las criaturas que salen por un lado aparecen por el opuesto).
    6.  **Consumo de Recursos:** Si una criatura alcanza un recurso, este se marca como no disponible y se crea uno nuevo en una posición aleatoria.

## 4. Elección de Pygame vs. AgentPy

Inicialmente, se consideró el uso de la biblioteca **AgentPy**, un framework especializado para Modelado Basado en Agentes (ABM). Sin embargo, durante las etapas preliminares de desarrollo y prueba, surgieron algunos errores y complejidades en la integración de la lógica de movimiento continuo y la gestión del grid de AgentPy que dificultaron la rápida iteración deseada para este proyecto dentro del tiempo asignado.

Se optó entonces por utilizar **Pygame** por las siguientes razones:

*   **Control Directo y Flexibilidad:** Pygame ofrece un control de bajo nivel sobre el bucle de la simulación, el dibujo y la gestión de eventos, lo cual es muy útil para implementar mecánicas de movimiento vectorial y percepción basadas en distancias en un espacio continuo.
*   **Visualización Integrada:** La capacidad de visualización en tiempo real es nativa en Pygame, facilitando la observación directa del comportamiento emergente y la depuración.
*   **Familiaridad y Rapidez de Desarrollo:** Para este proyecto específico, la familiaridad previa con Pygame permitió un desarrollo más ágil y enfocado en la lógica de los agentes.
*   **Cumplimiento del Protocolo ODD:** A pesar de no usar un framework ABM dedicado, el protocolo ODD pudo ser implementado rigurosamente, definiendo claramente todos sus componentes dentro de la estructura de Pygame.

Aunque AgentPy es una herramienta poderosa para ABM más complejos y análisis de datos robustos, Pygame resultó ser una elección más pragmática para los objetivos y restricciones de este proyecto, permitiendo una implementación funcional y visualmente representativa de la simulación deseada.

## 5. Explicación del Código y Términos Clave

### 5.1. Estructura General del Código

El código se organiza en las siguientes secciones principales:

*   **Constantes:** Definen parámetros globales de la simulación (tamaño de pantalla, FPS, número de entidades, colores, radios de visión, velocidades, etc.).
*   **Variables para Estadísticas:** Listas para almacenar datos recolectados durante la simulación para su posterior graficación.
*   **Clases de Agentes:**
    *   `AgenteBase(pygame.sprite.Sprite)`: Clase padre para todas las entidades, maneja la posición, el dibujo básico y la pertenencia a grupos de sprites de Pygame.
    *   `Recurso(AgenteBase)`: Representa los recursos consumibles.
    *   `Peligro(AgenteBase)`: Representa los peligros estáticos.
    *   `Criatura(AgenteBase)`: Clase principal de los agentes activos. Contiene toda la lógica de percepción, toma de decisiones y movimiento.
        *   Métodos clave: `evadir()`, `buscar()`, `separar()`, `cohesionar()`, `explorar()`, `actualizar_comportamiento()`, `update()`.
*   **Inicialización de Pygame y Entidades:** Configura la pantalla, el reloj y crea las instancias iniciales de criaturas, recursos y peligros.
*   **Bucle Principal de Simulación:**
    *   Manejo de eventos (teclado, cierre de ventana).
    *   Actualización de la lógica de cada agente.
    *   Actualización de recursos (consumo y reposición).
    *   Recolección de datos para estadísticas.
    *   Dibujo de todas las entidades en pantalla.
    *   Control de FPS.
*   **Generación de Gráficas:** Después de que el bucle de Pygame termina, se utiliza `matplotlib` para visualizar los datos recolectados.

### 5.2. Términos y Datos Clave

*   **Frames (Cuadros):** La simulación avanza en pasos discretos de tiempo. Cada paso corresponde a un "frame" o cuadro dibujado en la pantalla. `FPS` (Frames Per Second) determina cuántos de estos pasos ocurren por segundo. Las estadísticas se recolectan en cada frame. `MAX_FRAMES_SIMULACION` (establecido en 1000) es el número total de pasos de tiempo que durará la simulación antes de detenerse automáticamente para mostrar las gráficas.

*   **Comportamientos de Criaturas (Fuerzas):**
    *   **Evasión:** Alejarse de los peligros detectados. Tiene la máxima prioridad.
    *   **Búsqueda:** Moverse hacia el recurso visible más cercano si no hay peligro.
    *   **Separación:** Mantener una pequeña distancia con otras criaturas para evitar la superposición.
    *   **Cohesión:** Una leve tendencia a moverse hacia el centro de otras criaturas visibles si no hay objetivos más importantes (peligro o recurso).
    *   **Exploración:** Movimiento con un componente aleatorio para cubrir el espacio cuando no hay otros estímulos.

*   **Estado de la Criatura (`estado_actual`):**
    *   `EVADIENDO`: La criatura está activamente huyendo de un peligro.
    *   `BUSCANDO`: La criatura se dirige hacia un recurso.
    *   `EXPLORANDO`: La criatura no tiene un objetivo inmediato de evasión o búsqueda y se mueve explorando (puede estar influenciada por cohesión).
    Este estado se utiliza para contar cuántas criaturas están en cada actividad principal y para la depuración visual.

*   **Datos Recolectados para Gráficas:**
    *   `datos_frames`: El número de frame actual (eje X para la mayoría de las gráficas).
    *   `datos_num_criaturas_vivas`: Número de criaturas activas (en este modelo, es constante ya que no mueren).
    *   `datos_num_recursos_disponibles`: Cuántos recursos hay en el mapa en cada frame.
    *   `datos_recursos_consumidos_total`: El total acumulado de recursos consumidos desde el inicio.
    *   `datos_estado_buscando / evadiendo / explorando`: Número de criaturas en cada uno de estos estados principales por frame.
    *   `datos_dist_prom_peligro`: La distancia promedio de todas las criaturas al peligro más cercano a ellas en cada frame. Un valor más alto indica mejor evasión general.
    *   `datos_dist_prom_recurso_buscando`: Para las criaturas que están en estado "BUSCANDO", la distancia promedio a su recurso objetivo. Un valor bajo podría indicar eficiencia en la búsqueda o que los recursos están cerca.

## 6. Análisis de Resultados y Conclusiones (Basado en las Estadísticas)

La simulación, a través de sus gráficas, permite observar diversas dinámicas:

*   **Distribución de Estados de Criaturas:**
    *   La gráfica de "Distribución de Estados" (stackplot) muestra cómo la población de criaturas cambia su actividad principal a lo largo del tiempo.
    *   **Observación Típica:** Al inicio, puede haber más criaturas "EXPLORANDO". Cuando los recursos son abundantes y fáciles de encontrar, el número de "BUSCANDO" aumenta. Si los peligros son significativos o las criaturas se acercan a ellos, se observará un pico en el estado "EVADIENDO".
    *   **Conclusión:** Esta gráfica ilustra el equilibrio dinámico entre las diferentes prioridades de las criaturas. La aparición de nuevos recursos o la proximidad a peligros puede cambiar drásticamente la distribución de estos estados, mostrando la reactividad de los agentes a su entorno.

*   **Distancia Promedio al Peligro:**
    *   Esta métrica refleja la efectividad general de la regla de evasión.
    *   **Observación Típica:** Si la regla de evasión es efectiva y los peligros están bien definidos, esta distancia debería tender a mantenerse por encima de un cierto umbral o incluso aumentar si las criaturas aprenden (aunque no hay aprendizaje aquí) o si se alejan colectivamente. Fluctuaciones pueden indicar que algunas criaturas se acercan demasiado antes de evadir.
    *   **Conclusión:** Un valor consistentemente alto sugiere un comportamiento de evitación exitoso. Si el promedio es bajo, podría indicar que el radio de visión del peligro es muy pequeño, la fuerza de evasión es insuficiente, o los peligros están ubicados de tal manera que es difícil evitarlos sin comprometer la búsqueda de recursos.

*   **Eficiencia de Búsqueda (Distancia Promedio al Recurso Buscado):**
    *   Esta gráfica se enfoca en las criaturas que están activamente buscando un recurso.
    *   **Observación Típica:** Idealmente, esta distancia disminuiría a medida que las criaturas se acercan a su objetivo. Sin embargo, como los recursos se consumen y reaparecen, y otras criaturas compiten, esta línea puede fluctuar. Picos altos podrían indicar que los recursos cercanos se han agotado y las criaturas deben viajar más lejos.
    *   **Conclusión:** Esta métrica da una idea de la "presión" por los recursos. Si la distancia promedio es consistentemente alta, puede significar que los recursos son escasos o están muy dispersos en relación con el número de criaturas. Si es baja, los recursos son abundantes o las criaturas son eficientes localizándolos. El valor `np.nan` (representado como un hueco en la gráfica) aparece si ninguna criatura está en estado "BUSCANDO" en un frame particular.

*   **Total de Recursos Consumidos (Acumulado):**
    *   Esta es una medida general del "rendimiento" o "actividad" de la población.
    *   **Observación Típica:** Esta línea siempre debe aumentar o mantenerse plana (si no se consumen recursos). La pendiente de la curva indica la tasa de consumo. Una pendiente pronunciada significa alto consumo.
    *   **Conclusión:** La tasa de consumo está influenciada por la cantidad de criaturas, la disponibilidad de recursos, y qué tan ocupadas están las criaturas evadiendo peligros (lo que reduce el tiempo dedicado a buscar). Una tasa de consumo alta y sostenida podría indicar un ecosistema "saludable" dentro de los parámetros de la simulación.

**Conclusiones Generales:**

La simulación demuestra cómo reglas individuales sencillas (ver, decidir, moverse basado en prioridades) pueden llevar a comportamientos colectivos observables y medibles. Las gráficas estadísticas proporcionan una herramienta cuantitativa para analizar estas dinámicas emergentes, permitiendo ir más allá de la simple observación visual. Por ejemplo, se puede ver cómo la introducción de más peligros podría disminuir la tasa de consumo de recursos al aumentar el tiempo que las criaturas pasan "EVADIENDO".

Este modelo sirve como una base que podría expandirse con mecánicas más complejas como energía, reproducción, muerte, aprendizaje o diferentes tipos de agentes y recursos para explorar dinámicas ecológicas aún más ricas.
