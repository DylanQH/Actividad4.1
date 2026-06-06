# config.py
# Archivo de configuración general para el controlador autónomo en Webots.
#
# Este módulo centraliza todos los parámetros usados por el sistema:
#   - nombres de dispositivos de Webots,
#   - velocidad y límites del vehículo,
#   - parámetros de procesamiento de imagen,
#   - región de interés,
#   - filtro de líneas,
#   - ganancias del PID,
#   - opciones de guardado para depuración.
#
# Mantener estos valores en un archivo separado facilita realizar pruebas,
# ajustar parámetros y documentar el comportamiento del sistema.

import math


# ============================================================
# DISPOSITIVOS WEBOTS
# ============================================================
# Estos nombres deben coincidir exactamente con los nombres definidos
# en el mundo de Webots para la cámara y el display.

CAMERA_NAME = "camera"
DISPLAY_NAME = "display_image"
KEYBOARD_NAME = "keyboard"


# ============================================================
# VEHÍCULO
# ============================================================
# CRUISING_SPEED_KMH define la velocidad constante del vehículo.
# La actividad solicita validar el funcionamiento a una velocidad mínima
# de 50 km/h.
#
# MAX_STEERING_ANGLE limita el ángulo máximo de dirección para evitar
# giros demasiado bruscos.
#
# DEFAULT_STEERING_ANGLE se usa cuando no se detecta ninguna línea válida;
# en ese caso, el vehículo intenta continuar recto.

CRUISING_SPEED_KMH = 10.0
MAX_STEERING_ANGLE = 0.25
DEFAULT_STEERING_ANGLE = 0.0
DEBOUNCE_TIME = 0.1
MAX_ANGLE = 0.5
MAX_SPEED = 250
SPEED_INCR = 5
ANGLE_INCR = 0.05



# ============================================================
# CANNY
# ============================================================
# Parámetros para la detección de bordes mediante el algoritmo de Canny.
#
# La imagen de la cámara primero se convierte a escala de grises y después
# se aplica Canny para obtener los bordes principales de la carretera y de
# la línea amarilla.
#
# CANNY_LOW_THRESHOLD:
#   umbral inferior para la detección de bordes.
#
# CANNY_HIGH_THRESHOLD:
#   umbral superior para la detección de bordes.

CANNY_LOW_THRESHOLD = 20
CANNY_HIGH_THRESHOLD = 120


# ============================================================
# HOUGHLINESP
# ============================================================
# Parámetros para la Transformada Probabilística de Hough.
#
# HoughLinesP toma como entrada la imagen de bordes después de aplicar
# la región de interés y devuelve segmentos de líneas rectas.
#
# HOUGH_RHO:
#   resolución en pixeles para la distancia rho.
#
# HOUGH_THETA:
#   resolución angular. math.pi / 180 equivale a 1 grado.
#
# HOUGH_THRESHOLD:
#   número mínimo de votos requerido para aceptar una línea.
#
# HOUGH_MIN_LINE_LENGTH:
#   longitud mínima en pixeles para aceptar un segmento de línea.
#
# HOUGH_MAX_LINE_GAP:
#   separación máxima permitida entre segmentos para unirlos como una línea.

HOUGH_RHO = 1
HOUGH_THETA = math.pi / 180

HOUGH_THRESHOLD = 12
HOUGH_MIN_LINE_LENGTH = 7
HOUGH_MAX_LINE_GAP = 3


# ============================================================
# ROI CON 6 PUNTOS CONFIGURABLES
# ============================================================
# Región de Interés, ROI.
#
# La ROI limita la zona de la imagen donde se buscan líneas. Esto ayuda a
# ignorar regiones no relevantes como cielo, edificios, sombras lejanas,
# banquetas o zonas superiores de la imagen.
#
# La ROI se define con seis puntos:
#   1. inferior izquierdo
#   2. medio izquierdo
#   3. superior izquierdo
#   4. superior derecho
#   5. medio derecho
#   6. inferior derecho
#
# Cada coordenada está expresada como proporción del ancho o alto de la imagen.
#
# Ejemplo:
#   ROI_LEFT_TOP_X = 0.24 significa:
#       x = 0.24 * image_width
#
#   ROI_LEFT_TOP_Y = 0.55 significa:
#       y = 0.55 * image_height
#
# En imágenes digitales:
#   - (0, 0) está en la esquina superior izquierda.
#   - X aumenta hacia la derecha.
#   - Y aumenta hacia abajo.
#
# Esta ROI se utiliza posteriormente con cv2.fillPoly() para crear una máscara.

ROI_LEFT_BOTTOM_X = 0.09
ROI_LEFT_BOTTOM_Y = 1.00

ROI_LEFT_MIDDLE_X = 0.15
ROI_LEFT_MIDDLE_Y = 0.82

ROI_LEFT_TOP_X = 0.24
ROI_LEFT_TOP_Y = 0.55

ROI_RIGHT_TOP_X = 0.65
ROI_RIGHT_TOP_Y = 0.55

ROI_RIGHT_MIDDLE_X = 0.74
ROI_RIGHT_MIDDLE_Y = 0.82

ROI_RIGHT_BOTTOM_X = 0.8
ROI_RIGHT_BOTTOM_Y = 1.00


# ============================================================
# FILTRO DE LÍNEAS
# ============================================================
# Después de HoughLinesP, se filtran líneas mayormente horizontales.
#
# Esto es importante porque en intersecciones, sombras o bordes de carretera
# pueden aparecer líneas que no representan la línea amarilla central.
#
# La pendiente se calcula como:
#   slope = dy / dx
#
# MIN_ABS_SLOPE define la pendiente mínima absoluta para considerar válida
# una línea. Si abs(slope) es menor que este valor, la línea se descarta
# por ser demasiado horizontal.

MIN_ABS_SLOPE = 0.03


# ============================================================
# BLUR
# ============================================================
# Nivel de desenfoque aplicado antes de Canny.
#
# El blur ayuda a reducir ruido en la imagen antes de detectar bordes.
#
# En el módulo de detección:
#   0 = sin blur
#   1 = kernel 3x3
#   2 = kernel 5x5
#   3 = kernel 7x7

BLUR_LEVEL = 3


# ============================================================
# PID
# ============================================================
# Ganancias del controlador PID.
#
# El controlador recibe como entrada el error horizontal entre:
#   - el centro de la imagen, usado como setpoint,
#   - el centro de la línea seleccionada por el detector.
#
# El error se calcula en pixeles y la salida del PID se usa como ángulo
# de dirección del vehículo.
#
# PID_KP:
#   término proporcional. Corrige en función del error actual.
#
# PID_KI:
#   término integral. Corrige errores acumulados en el tiempo.
#   En esta configuración se mantiene en cero para evitar acumulación
#   excesiva cuando se pierde la línea en intersecciones.
#
# PID_KD:
#   término derivativo. Ayuda a suavizar cambios bruscos en el error
#   y reduce oscilaciones.

PID_KP = 0.008
PID_KI = 0.00
PID_KD = 0.0015


# ============================================================
# DEBUG IMAGES
# ============================================================
# Parámetros para guardar imágenes de depuración.
#
# Estas imágenes sirven para revisar visualmente las etapas del pipeline:
#   - imagen original,
#   - escala de grises,
#   - bordes Canny,
#   - bordes dentro de la ROI,
#   - overlay con ROI y líneas detectadas.
#
# SAVE_DEBUG_IMAGES:
#   activa o desactiva el guardado.
#
# DEBUG_MAX_IMAGES:
#   si es None, no hay límite de imágenes guardadas.
#
# DEBUG_SAVE_EVERY_N_FRAMES:
#   define cada cuántos frames se guarda una imagen.
#
# SAVE_DEBUG_OVERLAY_IMAGE:
#   guarda la imagen final con ROI, líneas de Hough, líneas válidas,
#   línea seleccionada y centro de imagen.

SAVE_DEBUG_IMAGES = True

DEBUG_MAX_IMAGES = 100
DEBUG_SAVE_EVERY_N_FRAMES = 50
DEBUG_OUTPUT_DIR = "debug_outputs"

SAVE_GRAY_IMAGE = False
SAVE_EDGES_IMAGE = True
SAVE_ROI_EDGES_IMAGE = True
SAVE_DEBUG_OVERLAY_IMAGE = True


# ============================================================
# CLASIFICACION CNN DE SENALES
# ============================================================
# Ejecutar TensorFlow en cada frame puede reducir la velocidad de Webots.
# Este valor controla cada cuantos frames se actualiza la prediccion.

SIGNAL_CLASSIFICATION_EVERY_N_FRAMES = 10
SIGNAL_MIN_CONFIDENCE = 0.70
