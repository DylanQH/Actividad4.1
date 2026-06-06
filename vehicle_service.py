# vehicle_service.py
# Servicio para controlar el vehículo de Webots.
#
# Este módulo encapsula las acciones principales sobre el vehículo:
#   - establecer velocidad de crucero,
#   - aplicar ángulo de dirección,
#   - limitar el ángulo máximo permitido.
#
# Se usa como una capa intermedia entre main.py y el Driver de Webots,
# para mantener el código principal más limpio y organizado.


class VehicleService:
    """
    Servicio para controlar velocidad y dirección del vehículo.

    Responsabilidades:
        - Mantener una velocidad constante.
        - Aplicar el ángulo calculado por el PID.
        - Evitar que el ángulo exceda los límites configurados.

    En Webots, el vehículo se controla usando la clase Driver, que permite:
        driver.setCruisingSpeed(...)
        driver.setSteeringAngle(...)
    """

    def __init__(self, driver, cruising_speed, max_steering_angle):
        """
        Inicializa el servicio del vehículo.

        Args:
            driver:
                Instancia de vehicle.Driver de Webots.

            cruising_speed:
                Velocidad constante deseada para el vehículo.
                En esta actividad se usa para validar el sistema a una
                velocidad mínima de 50 km/h.

            max_steering_angle:
                Límite máximo permitido para el ángulo de dirección.
                Este valor evita giros demasiado agresivos.
        """

        self.driver = driver
        self.cruising_speed = cruising_speed
        self.max_steering_angle = max_steering_angle

        # Ángulo inicial de dirección.
        # Se inicia en 0.0 para que el vehículo comience recto.
        self.current_steering_angle = 0.0

        # Aplicar velocidad y dirección iniciales.
        self.driver.setCruisingSpeed(self.cruising_speed)
        self.driver.setSteeringAngle(self.current_steering_angle)

    def set_steering_angle(self, angle):
        """
        Aplica el ángulo de dirección al vehículo.

        Antes de enviarlo a Webots, el ángulo se limita al rango:

            -max_steering_angle <= angle <= max_steering_angle

        Esto es importante porque el PID puede generar valores grandes
        cuando el error es alto, especialmente en curvas o cuando se recupera
        la línea después de una intersección.

        Args:
            angle:
                Ángulo de dirección calculado, normalmente por el controlador PID.
        """

        # Limitar el ángulo superior.
        if angle > self.max_steering_angle:
            angle = self.max_steering_angle

        # Limitar el ángulo inferior.
        elif angle < -self.max_steering_angle:
            angle = -self.max_steering_angle

        # Guardar el ángulo aplicado.
        self.current_steering_angle = angle

        # Enviar el comando de dirección al vehículo en Webots.
        self.driver.setSteeringAngle(self.current_steering_angle)

    def keep_constant_speed(self):
        """
        Mantiene la velocidad constante del vehículo.

        Se llama dentro del loop principal para asegurar que el vehículo
        continúe avanzando a la velocidad configurada, mientras el PID se
        encarga únicamente de modificar el ángulo de dirección.
        """

        self.driver.setCruisingSpeed(self.cruising_speed)