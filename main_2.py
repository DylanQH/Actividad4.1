"""Control manual por teclado con clasificacion CNN de senales en Webots."""

import traceback

import cv2
from controller import Keyboard
from vehicle import Driver

from camera_service import CameraService
from cnn_signals import CNNSignals
from config import (
    ANGLE_INCR,
    CAMERA_NAME,
    CRUISING_SPEED_KMH,
    DISPLAY_NAME,
    MAX_ANGLE,
    MAX_SPEED,
    SIGNAL_CLASSIFICATION_EVERY_N_FRAMES,
    SIGNAL_MIN_CONFIDENCE,
    SPEED_INCR,
)
from display_service import DisplayService


def update_manual_control(key, keyboard, speed, steering_angle):
    """Actualiza velocidad y direccion usando una tecla de Webots."""

    if key == keyboard.UP:
        speed = min(MAX_SPEED, speed + SPEED_INCR)
    elif key == keyboard.DOWN:
        speed = max(0.0, speed - SPEED_INCR)
    elif key == keyboard.RIGHT:
        steering_angle = min(MAX_ANGLE, steering_angle + ANGLE_INCR)
    elif key == keyboard.LEFT:
        steering_angle = max(-MAX_ANGLE, steering_angle - ANGLE_INCR)
    elif key == ord("A"):
        steering_angle = 0.0
    elif key == ord(" "):
        speed = 0.0

    return speed, steering_angle


def create_signal_debug_image(image, signal_classifier, signal_result):
    """Crea una imagen BGR con la ultima prediccion disponible."""

    if image.shape[2] == 4:
        debug_image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    else:
        debug_image = image.copy()

    if signal_result is None:
        return debug_image

    confidence = signal_result["confidence"]
    displayed_signal = (
        signal_result["signal_type"]
        if confidence >= SIGNAL_MIN_CONFIDENCE
        else "No reconocida"
    )
    signal_classifier.draw_prediction(
        image_bgr=debug_image,
        roi_polygon=signal_result["roi_polygon"],
        signal_type=displayed_signal,
        confidence=confidence,
    )
    return debug_image


def main():
    print("==========================================")
    print("Control manual y clasificacion de senales")
    print("Flechas: velocidad y direccion")
    print("A: centrar direccion | Espacio: detener")
    print("==========================================")

    driver = Driver()
    timestep = int(driver.getBasicTimeStep())

    camera_service = CameraService(
        robot=driver,
        camera_name=CAMERA_NAME,
        timestep=timestep,
    )
    display_service = DisplayService(
        robot=driver,
        display_name=DISPLAY_NAME,
    )

    keyboard = Keyboard()
    keyboard.enable(timestep)

    signal_classifier = CNNSignals()
    signal_interval = max(1, SIGNAL_CLASSIFICATION_EVERY_N_FRAMES)
    last_signal_result = None

    speed = CRUISING_SPEED_KMH
    steering_angle = 0.0
    frame_counter = 0

    driver.setCruisingSpeed(speed)
    driver.setSteeringAngle(steering_angle)

    while driver.step() != -1:
        frame_counter += 1

        key = keyboard.getKey()
        previous_speed = speed
        previous_angle = steering_angle
        speed, steering_angle = update_manual_control(
            key,
            keyboard,
            speed,
            steering_angle,
        )

        driver.setCruisingSpeed(speed)
        driver.setSteeringAngle(steering_angle)

        if speed != previous_speed or steering_angle != previous_angle:
            print(f"Velocidad: {speed:.1f} km/h | Direccion: {steering_angle:.2f}")

        image = camera_service.get_image()
        if image is None:
            continue

        if last_signal_result is None or frame_counter % signal_interval == 0:
            last_signal_result = signal_classifier.process(image)

        debug_image = create_signal_debug_image(
            image,
            signal_classifier,
            last_signal_result,
        )
        display_service.show_bgr_image(debug_image)

        if frame_counter % 20 == 0 and last_signal_result is not None:
            signal_type = last_signal_result["signal_type"]
            confidence = last_signal_result["confidence"]
            accepted = confidence >= SIGNAL_MIN_CONFIDENCE
            print(
                f"Frame: {frame_counter} | Senal: {signal_type} | "
                f"Confianza: {confidence:.1%} | Aceptada: {accepted}"
            )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("El controlador termino con una excepcion:")
        traceback.print_exc()
