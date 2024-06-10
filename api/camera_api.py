import sys
import os
from ctypes import *

# Определяем путь к папке с исключениями
exceptions_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'exceptions'))
sdk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils'))
# Добавляем путь к папке с исключениями в sys.path
sys.path.append(exceptions_path)
sys.path.append(sdk_path)

from camera_exceptions import CameraConnectionError, NodeInitializationError
from nodes import * 
from MVSDK import *


class CameraAPI:
    """
    Класс для работы с камерой с использованием SDK MVSDK.
    """
    # Использование дескриптора CameraNode для узлов
    ExposureTime = DoubleNode('_exposure_time_node')
    AcquisitionMode = EnumNode('_acquisition_mode_node', (0, 1, 2))
    AcquisitionFrameCount = IntNode('_acquisition_frame_count_node')
    AcquisitionFrameRate = DoubleNode('_acquisition_frame_rate_node')
    AcquisitionFrameRateEnable = BoolNode('_acquisition_frame_rate_enable_node')
    ExposureAuto = EnumNode('_exposure_auto_node', (0, 1, 2))
    ExposureMode = EnumNode('_exposure_mode_node', (0,))
    GainRaw = DoubleNode('_gain_raw_node')
    BlackLevel = IntNode('_black_level_node')
    BlackLevelAuto = EnumNode('_black_level_auto_node', (0, 1, 2))
    Gamma = DoubleNode('_gamma_node')
    Width = IntNode('_width_node')
    Height = IntNode('_height_node')
    OffsetX = IntNode('_offsetX_node')
    OffsetY = IntNode('_offsetY_node')
    

    def __init__(self):
        self.camera = None
        self._exposure_time_node = None
        self._acquisition_mode_node = None
        self._acquisition_frame_count_node = None
        self._acquisition_frame_rate_node = None
        self._acquisition_frame_rate_enable_node = None
        self._exposure_auto_node = None
        self._exposure_mode_node = None
        self._black_level_auto_node = None
        self._gamma_node = None
        self._gain_raw_node =None
        self._black_level_node = None
        self._width_node = None
        self._height_node = None
        self._offsetX_node = None
        self._offsetY_node = None

    def __enter__(self):
        """
        Вход в контекстный менеджер. Открывает камеру.
        """
        self.camera = self.open_camera()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Выход из контекстного менеджера. Закрывает камеру.
        """
        if self.camera:
            self.close_camera(self.camera)

    def open_camera(self):
        """
        Открытие камеры.

        :return: Первый найденный объект камеры или None при ошибке.
        """
        system = self.get_system_instance()
        if not system:
            raise CameraConnectionError()

        camera_list, camera_cnt = self.discover_cameras(system)
        if not camera_list or camera_cnt < 1:
            raise CameraConnectionError()

        first_camera = camera_list[0]
        if not self.connect_camera(first_camera):
            raise CameraConnectionError()

        self._initialize_nodes(first_camera)

        return first_camera

    def close_camera(self, camera):
        """
        Закрытие соединения с камерой.

        :param camera: Объект камеры.
        :return: 0 при успешном отключении, -1 при ошибке.
        """
        nRet = camera.disConnect(byref(camera))
        if nRet != 0:
            raise CameraConnectionError('Failed to disconnect camera!')
        return 0

    def get_system_instance(self):
        """
        Получение экземпляра системы.

        :return: Экземпляр системы или None при ошибке.
        """
        system = pointer(GENICAM_System())
        nRet = GENICAM_getSystemInstance(byref(system))
        if nRet != 0:
            raise CameraConnectionError('Failed to get system instance!')
        return system

    def discover_cameras(self, system):
        """
        Обнаружение камер в системе.

        :param system: Экземпляр системы.
        :return: Список камер и количество камер.
        """
        camera_list = pointer(GENICAM_Camera())
        camera_cnt = c_uint()
        nRet = system.contents.discovery(system, byref(camera_list), byref(camera_cnt), c_int(GENICAM_EProtocolType.typeAll))
        if nRet != 0:
            raise CameraConnectionError('Failed to discover cameras!')
        return camera_list, camera_cnt.value

    def connect_camera(self, camera):
        """
        Подключение к камере.

        :param camera: Объект камеры.
        :return: True при успешном подключении, False при ошибке.
        """
        nRet = camera.connect(camera, c_int(GENICAM_ECameraAccessPermission.accessPermissionControl))
        if nRet != 0:
            raise CameraConnectionError()
        
        print('camera connect success.')
        return True

    def _initialize_nodes(self, camera):
        """
        Инициализация узлов камеры.

        :param camera: Объект камеры.
        """
        nodes = {
            '_exposure_time_node': ('ExposureTime', self._create_double_node),
            '_acquisition_mode_node': ('AcquisitionMode', self._create_enum_node),
            '_acquisition_frame_count_node': ('AcquisitionFrameCount', self._create_int_node),
            '_acquisition_frame_rate_node': ('AcquisitionFrameRate', self._create_double_node),
            '_acquisition_frame_rate_enable_node': ('AcquisitionFrameRateEnable', self._create_bool_node),
            '_exposure_auto_node': ('ExposureAuto', self._create_enum_node),
            '_exposure_mode_node': ('ExposureMode', self._create_enum_node),
            '_gain_raw_node': ('GainRaw', self._create_double_node),
            '_black_level_node': ('BlackLevel', self._create_int_node),
            '_black_level_auto_node': ('BlackLevelAuto', self._create_enum_node),
            '_gamma_node': ('Gamma', self._create_double_node),
            '_width_node': ('Width', self._create_int_node),
            '_height_node': ('Height', self._create_int_node),
            '_offsetX_node': ('OffsetX', self._create_int_node),
            '_offsetY_node': ('OffsetY', self._create_int_node),
        }

        for node_attr, (node_name, create_node_func) in nodes.items():
            setattr(self, node_attr, create_node_func(camera, node_name))

            if not getattr(self, node_attr):
                raise NodeInitializationError(node_name)

    def _create_node(self, camera, attr_name, node_type):
        """
        Создание узла.

        :param camera: Объект камеры.
        :param attr_name: Имя узла.
        :param node_type: Тип узла.
        :return: Созданный узел или None при ошибке.
        """
        node_info = node_type['info']()
        node_info.pCamera = pointer(camera)
        node_info.attrName = attr_name.encode('utf-8')

        node = pointer(node_type['node']())
        nRet = node_type['create'](byref(node_info), byref(node))
        if nRet != 0:
            raise NodeInitializationError(attr_name)
        return node

    def _create_int_node(self, camera, attr_name):
        """
        Создание узла типа int.

        :param camera: Объект камеры.
        :param attr_name: Имя узла.
        :return: Созданный узел или None при ошибке.
        """
        return self._create_node(camera, attr_name, {
            'info': GENICAM_IntNodeInfo,
            'node': GENICAM_IntNode,
            'create': GENICAM_createIntNode
        })

    def _create_double_node(self, camera, attr_name):
        """
        Создание узла типа double.

        :param camera: Объект камеры.
        :param attr_name: Имя узла.
        :return: Созданный узел или None при ошибке.
        """
        return self._create_node(camera, attr_name, {
            'info': GENICAM_DoubleNodeInfo,
            'node': GENICAM_DoubleNode,
            'create': GENICAM_createDoubleNode
        })

    def _create_enum_node(self, camera, attr_name):
        """
        Создание узла типа enum.

        :param camera: Объект камеры.
        :param attr_name: Имя узла.
        :return: Созданный узел или None при ошибке.
        """
        return self._create_node(camera, attr_name, {
            'info': GENICAM_EnumNodeInfo,
            'node': GENICAM_EnumNode,
            'create': GENICAM_createEnumNode
        })

    def _create_bool_node(self, camera, attr_name):
        """
        Создание узла типа bool.

        :param camera: Объект камеры.
        :param attr_name: Имя узла.
        :return: Созданный узел или None при ошибке.
        """
        return self._create_node(camera, attr_name, {
            'info': GENICAM_BoolNodeInfo,
            'node': GENICAM_BoolNode,
            'create': GENICAM_createBoolNode
        })

    def setROI(self, nWidth, nHeight, OffsetX, OffsetY):
        """
        Установка области интереса (ROI) камеры.

        :param nWidth: Ширина области.
        :param nHeight: Высота области.
        :param OffsetX: Смещение по оси X.
        :param OffsetY: Смещение по оси Y.
        :return: 0 при успешной установке, -1 при ошибке.
        """
        self.Width = nWidth
        self.Height = nHeight
        self.OffsetX = OffsetX
        self.OffsetY = OffsetY
        
        print('ROI set to OffsetX:', OffsetX, 'OffsetY:', OffsetY, 'Width:', nWidth, 'Height:', nHeight)
        return 0

    def getROI(self):
        """
        Получение текущей области интереса (ROI) камеры.

        :return: Кортеж с шириной, высотой, смещением по оси X и смещением по оси Y или None при ошибке.
        """
        width = self.Width
        height = self.Height
        offsetX = self.OffsetX
        offsetY = self.OffsetY

        if None in (width, height, offsetX, offsetY):
            return None

        return width, height, offsetX, offsetY


if __name__ == '__main__':
    c = CameraAPI()
    with c as camera:
        if camera.camera:
            print('Camera is connected.')
            camera.ExposureTime = 9900
            camera.setROI(1900, 2000, 100, 100)
            print(camera.getROI())
            print(camera.GainRaw)
        else:
            print('Failed to connect to the camera.')