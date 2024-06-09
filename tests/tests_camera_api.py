import sys
import os
import unittest
from unittest.mock import MagicMock, patch

api_relative_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../api'))
sys.path.append(api_relative_path)

from camera_api import CameraAPI


class TestCameraAPI(unittest.TestCase):
    def setUp(self):
        self.camera_api = CameraAPI()

    def tearDown(self):
        pass

    def test_initialization(self):
        self.assertIsNone(self.camera_api.camera)
        self.assertIsNone(self.camera_api._exposure_time_node)

    def test_open_camera_success(self):
        with patch('camera_api.CameraAPI.get_system_instance') as mock_get_system_instance, \
             patch('camera_api.CameraAPI.discover_cameras') as mock_discover_cameras, \
             patch('camera_api.CameraAPI.connect_camera') as mock_connect_camera, \
             patch('camera_api.CameraAPI._initialize_nodes') as mock_initialize_nodes:
            # Устанавливаем моки для всех необходимых методов, чтобы имитировать успешное открытие камеры
            mock_get_system_instance.return_value = MagicMock()
            mock_discover_cameras.return_value = (MagicMock(), 1)  # Предполагаем, что найдена одна камера
            mock_connect_camera.return_value = True  # Предполагаем, что подключение к камере успешно
            # Запускаем метод open_camera
            self.camera_api.open_camera()
            # Проверяем, что все необходимые методы были вызваны
            mock_get_system_instance.assert_called_once()
            mock_discover_cameras.assert_called_once()
            mock_connect_camera.assert_called_once()
            mock_initialize_nodes.assert_called_once()


if __name__ == '__main__':
    unittest.main()
