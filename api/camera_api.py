import sys
import os
from ctypes import *

# Добавляем путь к SDK в sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))

from MVSDK import *

class CameraNode:
    """
    Дескриптор для узлов камеры. Обеспечивает централизованное управление получением и установкой значений узлов.
    """
    def __init__(self, node_attr, value_type):
        """
        Инициализация дескриптора.

        :param node_attr: Атрибут узла в классе CameraAPI.
        :param value_type: Тип значения узла.
        """
        self.node_attr = node_attr
        self.value_type = value_type

    def __get__(self, instance, owner):
        """
        Получение значения узла.

        :param instance: Экземпляр класса CameraAPI.
        :param owner: Класс-владелец.
        :return: Значение узла.
        """
        node = getattr(instance, self.node_attr)
        return self._get_node_value(node, self.value_type)

    def __set__(self, instance, value):
        """
        Установка значения узла.

        :param instance: Экземпляр класса CameraAPI.
        :param value: Новое значение узла.
        """
        node = getattr(instance, self.node_attr)
        self._set_node_value(node, self.value_type(value))

    def _get_node_value(self, node, value_type):
        """
        Получение значения узла.

        :param node: Узел.
        :param value_type: Тип значения.
        :return: Значение узла или None при ошибке.
        """
        if node is None:
            print(f'{value_type.__name__} node is not initialized.')
            return None
        value = value_type()
        nRet = node.contents.getValue(node, byref(value))
        if nRet != 0:
            print(f'get {value_type.__name__} value fail!')
            return None
        return value.value

    def _set_node_value(self, node, value):
        """
        Установка значения узла.

        :param node: Узел.
        :param value: Новое значение.
        :return: True при успешной установке, False при ошибке.
        """
        if node is None:
            print(f'{type(value).__name__} node is not initialized.')
            return False
        nRet = node.contents.setValue(node, value)
        if nRet != 0:
            print(f'set {type(value).__name__} value [{value}] fail!')
            return False
        return True


class CameraAPI:
    """
    Класс для работы с камерой с использованием SDK MVSDK.
    """
    def __init__(self):
        self.camera = None
        self._exposure_time_node = None
        self._acquisition_mode_node = None
        self._acquisition_frame_count_node = None
        self._acquisition_frame_rate_node = None
        self._acquisition_frame_rate_enable_node = None
        self._exposure_auto_node = None
        self._exposure_mode_node = None
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
            return None

        camera_list, camera_cnt = self.discover_cameras(system)
        if not camera_list or camera_cnt < 1:
            return None

        first_camera = camera_list[0]
        if not self.connect_camera(first_camera):
            return None

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
            print('disconnect camera fail!')
            return -1
        return 0

    def get_system_instance(self):
        """
        Получение экземпляра системы.

        :return: Экземпляр системы или None при ошибке.
        """
        system = pointer(GENICAM_System())
        nRet = GENICAM_getSystemInstance(byref(system))
        if nRet != 0:
            print('getSystemInstance fail!')
            return None
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
            print('discovery fail!')
            return None, None
        return camera_list, camera_cnt.value

    def connect_camera(self, camera):
        """
        Подключение к камере.

        :param camera: Объект камеры.
        :return: True при успешном подключении, False при ошибке.
        """
        nRet = camera.connect(camera, c_int(GENICAM_ECameraAccessPermission.accessPermissionControl))
        if nRet != 0:
            print('camera connect fail!')
            return False
        print('camera connect success.')
        return True

    def _initialize_nodes(self, camera):
        """
        Инициализация узлов камеры.

        :param camera: Объект камеры.
        """
        self._initialize_node(camera, '_exposure_time_node', 'ExposureTime', self._create_double_node)
        self._initialize_node(camera, '_acquisition_mode_node', 'AcquisitionMode', self._create_enum_node)
        self._initialize_node(camera, '_acquisition_frame_count_node', 'AcquisitionFrameCount', self._create_int_node)
        self._initialize_node(camera, '_acquisition_frame_rate_node', 'AcquisitionFrameRate', self._create_double_node)
        self._initialize_node(camera, '_acquisition_frame_rate_enable_node', 'AcquisitionFrameRateEnable', self._create_bool_node)
        self._initialize_node(camera, '_exposure_auto_node', 'ExposureAuto', self._create_enum_node)
        self._initialize_node(camera, '_exposure_mode_node', 'ExposureMode', self._create_enum_node)
        self._width_node = self._create_int_node(camera, 'Width')
        self._height_node = self._create_int_node(camera, 'Height')
        self._offsetX_node = self._create_int_node(camera, 'OffsetX')
        self._offsetY_node = self._create_int_node(camera, 'OffsetY')

    def _initialize_node(self, camera, node_attr, node_name, create_node_func):
        """
        Инициализация конкретного узла.

        :param camera: Объект камеры.
        :param node_attr: Атрибут узла в классе.
        :param node_name: Имя узла.
        :param create_node_func: Функция для создания узла.
        """
        setattr(self, node_attr, create_node_func(camera, node_name))
        if not getattr(self, node_attr):
            print(f'Failed to initialize {node_name} node.')

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
            print(f'create {attr_name} Node fail!')
            return None
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

    # Использование дескриптора CameraNode для узлов
    ExposureTime = CameraNode('_exposure_time_node', c_double)
    AcquisitionMode = CameraNode('_acquisition_mode_node', c_ulong)
    AcquisitionFrameCount = CameraNode('_acquisition_frame_count_node', c_long)
    AcquisitionFrameRate = CameraNode('_acquisition_frame_rate_node', c_double)
    AcquisitionFrameRateEnable = CameraNode('_acquisition_frame_rate_enable_node', c_uint)
    ExposureAuto = CameraNode('_exposure_auto_node', c_ulong)
    ExposureMode = CameraNode('_exposure_mode_node', c_ulong)

    def setROI(self, nWidth, nHeight, OffsetX, OffsetY):
        """
        Установка области интереса (ROI) камеры.

        :param nWidth: Ширина области.
        :param nHeight: Высота области.
        :param OffsetX: Смещение по оси X.
        :param OffsetY: Смещение по оси Y.
        :return: 0 при успешной установке, -1 при ошибке.
        """
        if (
            not self._set_node_value(self._create_int_node(self.camera, 'Width'), nWidth) or
            not self._set_node_value(self._create_int_node(self.camera, 'Height'), nHeight) or
            not self._set_node_value(self._create_int_node(self.camera, 'OffsetX'), OffsetX) or
            not self._set_node_value(self._create_int_node(self.camera, 'OffsetY'), OffsetY)
        ):
            return -1
        print('ROI set to OffsetX:', OffsetX, 'OffsetY:', OffsetY, 'Width:', nWidth, 'Height:', nHeight)
        return 0

    def getROI(self):
        """
        Получение текущей области интереса (ROI) камеры.

        :return: Кортеж с шириной, высотой, смещением по оси X и смещением по оси Y или None при ошибке.
        """
        width = self._get_node_value(self._width_node, c_long)
        height = self._get_node_value(self._height_node, c_long)
        offsetX = self._get_node_value(self._offsetX_node, c_long)
        offsetY = self._get_node_value(self._offsetY_node, c_long)

        if None in (width, height, offsetX, offsetY):
            return None

        return width, height, offsetX, offsetY

# Пример использования
c = CameraAPI()
with c as camera:
    if camera.camera:
        print('Camera is connected.')
        print(camera.ExposureTime)
        print(camera.AcquisitionFrameCount)
    else:
        print('Failed to connect to the camera.')
