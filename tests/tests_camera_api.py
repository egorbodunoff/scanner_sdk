import sys
import os
from ctypes import *
import unittest
from unittest.mock import MagicMock, patch

api_relative_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../api'))
sys.path.append(api_relative_path)

from camera_api import CameraAPI, CameraConnectionError, NodeInitializationError

class TestCameraAPI(unittest.TestCase):
    def setUp(self):
        self.camera_api = CameraAPI()
        self.camera = MagicMock()

    def test_initialization(self):
        self.assertIsNone(self.camera_api.camera)
        self.assertIsNone(self.camera_api._exposure_time_node)
        self.assertIsNone(self.camera_api._acquisition_frame_count_node)
        self.assertIsNone(self.camera_api._acquisition_frame_rate_enable_node)
        self.assertIsNone(self.camera_api._acquisition_frame_rate_node)
        self.assertIsNone(self.camera_api._acquisition_mode_node)
        self.assertIsNone(self.camera_api._gamma_node)
        self.assertIsNone(self.camera_api._black_level_auto_node)
        self.assertIsNone(self.camera_api._black_level_node)
        self.assertIsNone(self.camera_api._offsetX_node)
        self.assertIsNone(self.camera_api._offsetY_node)
        self.assertIsNone(self.camera_api._width_node)
        self.assertIsNone(self.camera_api._height_node)
        self.assertIsNone(self.camera_api._gain_raw_node)
        self.assertIsNone(self.camera_api._exposure_auto_node)
        self.assertIsNone(self.camera_api._exposure_mode_node)


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

    def test_open_camera_fail(self):
        with patch('camera_api.CameraAPI.get_system_instance') as mock_get_system_instance:
            mock_get_system_instance.return_value = None
            
            with self.assertRaises(CameraConnectionError) as err:
                self.camera_api.open_camera()

            self.assertEqual(CameraConnectionError, type(err.exception))

            mock_get_system_instance.assert_called_once()

    def test_get_system_instance_success(self):
        with patch('camera_api.GENICAM_getSystemInstance') as mock_get_system_instance, \
             patch('camera_api.GENICAM_System') as mock_system:
            
            mock_get_system_instance.return_value = 0
            mock_system.return_value = c_int()

            system = self.camera_api.get_system_instance()
            self.assertIsNotNone(system)

    def test_get_system_instance_fail(self):
        with patch('camera_api.GENICAM_getSystemInstance') as mock_get_system_instance:
            mock_get_system_instance.return_value = -1

            with self.assertRaises(CameraConnectionError) as err:
                system = self.camera_api.get_system_instance()

            self.assertEqual(CameraConnectionError, type(err.exception))

            mock_get_system_instance.assert_called_once()

    def test_discover_cameras_success(self):
        system = MagicMock()
        with patch.object(system.contents, 'discovery') as mock_discovery:
            mock_discovery.return_value = 0

            nRet = self.camera_api.discover_cameras(system)

            self.assertEqual(nRet[1], 0)

    def test_discover_cameras_fail(self):
        system = MagicMock()
        with patch.object(system.contents, 'discovery') as mock_discovery:

            mock_discovery.return_value = 1
            with self.assertRaises(CameraConnectionError) as err:
                self.camera_api.discover_cameras(system)

            self.assertEqual(CameraConnectionError, type(err.exception))

    def test_initialize_nodes(self):
        with patch('camera_api.CameraAPI._create_node') as mock_create_node:
            mock_create_node.return_value = MagicMock()
            self.camera_api._initialize_nodes(self.camera)

        self.assertTrue(hasattr(self.camera_api, '_exposure_mode_node'))
        self.assertTrue(hasattr(self.camera_api, '_offsetX_node'))
        self.assertTrue(hasattr(self.camera_api, '_acquisition_frame_rate_enable_node'))
        self.assertTrue(hasattr(self.camera_api, '_gamma_node'))
        self.assertTrue(hasattr(self.camera_api, '_black_level_node'))
        self.assertTrue(hasattr(self.camera_api, '_acquisition_mode_node'))
        self.assertTrue(hasattr(self.camera_api, '_width_node'))
        self.assertTrue(hasattr(self.camera_api, '_gain_raw_node'))
        
    def test_initialize_nodes_bad_node(self):
        with patch('camera_api.CameraAPI._create_node') as mock_create_node:
            mock_create_node.side_effect = NodeInitializationError('_atr_name')

            with self.assertRaises(NodeInitializationError) as err:
                self.camera_api._initialize_nodes(self.camera)
                self.assertTrue(hasattr(self.camera_api, 'Gamma'))
            
            self.assertEqual(NodeInitializationError, type(err.exception))



if __name__ == '__main__':
    unittest.main()