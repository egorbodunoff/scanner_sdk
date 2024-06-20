class CameraError(Exception):
    """Базовый класс для всех исключений, связанных с камерой."""
    pass

class NodeInitializationError(CameraError):
    """Исключение для ошибок инициализации узлов камеры."""
    def __init__(self, node_name):
        self.node_name = node_name
        super().__init__(f'Failed to initialize {node_name} node.')

class CameraConnectionError(CameraError):
    """Исключение для ошибок подключения камеры."""
    def __init__(self, message='Failed to connect to the camera.'):
        super().__init__(message)

class NodeValueError(CameraError):
    """Исключение для ошибок получения или установки значения узла."""
    def __init__(self, node_name, value=None):
        self.node_name = node_name
        self.value = value
        if value is not None:
            super().__init__(f'Failed to set value {value} for node {node_name}.')
        else:
            super().__init__(f'Failed to get value for node {node_name}.')

class FrameCaptureError(CameraError):
    """Исключение для ошибок захвата кадра."""
    def __init__(self, message='Failed to capture frame.'):
        super().__init__(message)
