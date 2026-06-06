"""Clasificacion de senales de transito con el modelo CNN de GTSRB."""

from pathlib import Path

import cv2
import numpy as np

try:
    import keras
except ImportError:
    from tensorflow import keras


DEFAULT_MODEL_PATH = Path(__file__).with_name("gtsrb_cnn_keras.keras")
MODEL_IMAGE_SIZE = (32, 32)


class CNNSignals:
    """Preprocesa una imagen y predice su clase GTSRB."""

    def __init__(
        self,
        model_path=DEFAULT_MODEL_PATH,
        roi_left_bottom_x=0.0,
        roi_left_bottom_y=1.0,
        roi_left_middle_x=0.0,
        roi_left_middle_y=0.5,
        roi_left_top_x=0.0,
        roi_left_top_y=0.0,
        roi_right_top_x=1.0,
        roi_right_top_y=0.0,
        roi_right_middle_x=1.0,
        roi_right_middle_y=0.5,
        roi_right_bottom_x=1.0,
        roi_right_bottom_y=1.0,
    ):
        model_path = Path(model_path)
        if not model_path.is_file():
            raise FileNotFoundError(f"No se encontro el modelo CNN: {model_path}")

        self.model = keras.models.load_model(model_path, compile=False)

        self.roi_left_bottom_x = roi_left_bottom_x
        self.roi_left_bottom_y = roi_left_bottom_y
        self.roi_left_middle_x = roi_left_middle_x
        self.roi_left_middle_y = roi_left_middle_y
        self.roi_left_top_x = roi_left_top_x
        self.roi_left_top_y = roi_left_top_y
        self.roi_right_top_x = roi_right_top_x
        self.roi_right_top_y = roi_right_top_y
        self.roi_right_middle_x = roi_right_middle_x
        self.roi_right_middle_y = roi_right_middle_y
        self.roi_right_bottom_x = roi_right_bottom_x
        self.roi_right_bottom_y = roi_right_bottom_y

        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))

    def get_roi_polygon(self, width, height):
        """Devuelve el poligono de la ROI limitado al tamano de la imagen."""

        points = [
            (self.roi_left_bottom_x, self.roi_left_bottom_y),
            (self.roi_left_middle_x, self.roi_left_middle_y),
            (self.roi_left_top_x, self.roi_left_top_y),
            (self.roi_right_top_x, self.roi_right_top_y),
            (self.roi_right_middle_x, self.roi_right_middle_y),
            (self.roi_right_bottom_x, self.roi_right_bottom_y),
        ]

        polygon = [
            (
                int(np.clip(x, 0.0, 1.0) * (width - 1)),
                int(np.clip(y, 0.0, 1.0) * (height - 1)),
            )
            for x, y in points
        ]
        return np.array([polygon], dtype=np.int32)

    @staticmethod
    def _to_rgb(image):
        if image is None or not isinstance(image, np.ndarray):
            raise ValueError("image debe ser un arreglo NumPy valido")
        if image.ndim != 3:
            raise ValueError(f"Se esperaba una imagen HxWxC, se recibio {image.shape}")

        channels = image.shape[2]
        if channels == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        if channels == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        raise ValueError(f"Se esperaban 3 o 4 canales, se recibieron {channels}")

    def apply_clahe(self, image_rgb):
        """Aplica CLAHE a una sola imagen RGB y devuelve float32 en [0, 1]."""

        if np.issubdtype(image_rgb.dtype, np.floating):
            image_uint8 = (np.clip(image_rgb, 0.0, 1.0) * 255).astype(np.uint8)
        else:
            image_uint8 = np.clip(image_rgb, 0, 255).astype(np.uint8)

        ycrcb = cv2.cvtColor(image_uint8, cv2.COLOR_RGB2YCrCb)
        channels = list(cv2.split(ycrcb))
        channels[0] = self.clahe.apply(channels[0])
        enhanced = cv2.cvtColor(cv2.merge(channels), cv2.COLOR_YCrCb2RGB)

        return enhanced.astype(np.float32) / 255.0

    def apply_roi(self, image_rgb):
        """Aplica la ROI y devuelve solamente su rectangulo envolvente."""

        height, width = image_rgb.shape[:2]
        roi_polygon = self.get_roi_polygon(width, height)

        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, roi_polygon, 255)
        masked_image = cv2.bitwise_and(image_rgb, image_rgb, mask=mask)

        x, y, roi_width, roi_height = cv2.boundingRect(roi_polygon)
        roi_image = masked_image[y : y + roi_height, x : x + roi_width]
        if roi_image.size == 0:
            raise ValueError("La ROI configurada esta vacia")

        return roi_image, roi_polygon

    @staticmethod
    def draw_prediction(image_bgr, roi_polygon, signal_type, confidence):
        """Dibuja la ROI y la prediccion sobre una imagen BGR."""

        cv2.polylines(image_bgr, roi_polygon, True, (255, 0, 0), 2)
        text = f"Senal: {signal_type}  Confianza: {confidence:.1%}"
        cv2.putText(
            image_bgr,
            text,
            (5, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
        return image_bgr

    @classmethod
    def create_debug_image(cls, original_image, roi_polygon, signal_type, confidence):
        """Dibuja la ROI y la prediccion sobre una copia BGR de la imagen."""

        if original_image.shape[2] == 4:
            debug_image = cv2.cvtColor(original_image, cv2.COLOR_BGRA2BGR)
        else:
            debug_image = original_image.copy()

        cls.draw_prediction(debug_image, roi_polygon, signal_type, confidence)
        return debug_image

    def process(self, image):
        """Clasifica una imagen individual, sin procesarla como batch externo."""

        image_rgb = self._to_rgb(image)
        roi_image, roi_polygon = self.apply_roi(image_rgb)
        resized_image = cv2.resize(roi_image, MODEL_IMAGE_SIZE, interpolation=cv2.INTER_AREA)
        model_image = self.apply_clahe(resized_image)

        # Keras siempre requiere una dimension batch, aunque se prediga una imagen.
        probabilities = self.model.predict(np.expand_dims(model_image, axis=0), verbose=0)[0]
        signal_type = int(np.argmax(probabilities))
        confidence = float(probabilities[signal_type])

        debug_image = self.create_debug_image(
            original_image=image,
            roi_polygon=roi_polygon,
            signal_type=signal_type,
            confidence=confidence,
        )

        return {
            "roi_image": roi_image,
            "model_image": model_image,
            "roi_polygon": roi_polygon,
            "debug_image": debug_image,
            "probabilities": probabilities,
            "signal_type": signal_type,
            "confidence": confidence,
        }


# Alias legible para codigo nuevo.
TrafficSignClassifier = CNNSignals
