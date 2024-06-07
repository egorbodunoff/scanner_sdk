import sys
import os
from ctypes import *

# Добавляем путь к SDK в sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '../sdk'))

from MVSDK import *

class CameraAPI:
    def __init__(self):
        self.camera = None                  # Инициализация камеры
        self._exposure_time_node = None     # Узел для управления экспозицией
        self._acquisition_mode_node = None  # Узел для управления режимом активации

    def __enter__(self):
        '''Метод контекстного менеджера для открытия камеры'''
        self.camera = self.open_camera()    # Вызываем метод открытия камеры при входе в контекст
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''Метод контекстного менеджера для закрытия камеры'''
        if self.camera:
            self.close_camera(self.camera)  # Закрываем камеру при выходе из контекста

    def open_camera(self):
        '''Метод для открытия камеры'''
        system = self.get_system_instance() # Получаем системный экземпляр камеры
        if not system:
            return None
        
        camera_list, camera_cnt = self.discover_cameras(system)  # Ищем доступные камеры
        if not camera_list or camera_cnt < 1:
            return None

        first_camera = camera_list[0]                            # Подключаемся к первой найденной камере
        if not self.connect_camera(first_camera):       
            return None
        
        self._initialize_exposure_time_node(first_camera)        # Инициализируем узел экспозиции
        self._initialize_acquisition_mode_node(first_camera)     # Инициализируем узел режима активации
    
        return first_camera

    def close_camera(self, camera):
        '''Метод для отключения камеры'''
        nRet = camera.disConnect(byref(camera))
        if nRet != 0:
            print('disconnect camera fail!')
            return -1
        return 0

    def get_system_instance(self):
        '''Метод для получения системного экземпляра камеры'''
        system = pointer(GENICAM_System())
        nRet = GENICAM_getSystemInstance(byref(system))
        if nRet != 0:
            print('getSystemInstance fail!')
            return None
        return system

    def discover_cameras(self, system):
        '''Метод для поиска доступных камер'''
        camera_list = pointer(GENICAM_Camera()) 
        camera_cnt = c_uint()
        nRet = system.contents.discovery(system, byref(camera_list), byref(camera_cnt), c_int(GENICAM_EProtocolType.typeAll))
        if nRet != 0:
            print('discovery fail!')
            return None, None
        return camera_list, camera_cnt.value

    def connect_camera(self, camera):
        '''Метод для подключения камеры'''
        nRet = camera.connect(camera, c_int(GENICAM_ECameraAccessPermission.accessPermissionControl))
        if nRet != 0:
            print('camera connect fail!')
            return False
        print('camera connect success.')
        return True

    def _initialize_exposure_time_node(self, camera):
        '''Инициализация узла экспозиции'''
        self._exposure_time_node = self._create_double_node(camera, 'ExposureTime')
        if not self._exposure_time_node:
            print('Failed to initialize ExposureTime node.')

    def _initialize_acquisition_mode_node(self, camera):
        """Метод для инициализации узла режима активации"""
        self._acquisition_mode_node = self._create_enum_node(camera, 'AcquisitionMode')
        if not self._acquisition_mode_node:
            print('Failed to initialize AcquisitionMode node.')

    def _create_int_node(self, camera, attr_name):
        '''Создание узла для атрибута типа int'''
        node_info = GENICAM_IntNodeInfo()                   # Создаем информацию о узле
        node_info.pCamera = pointer(camera)                 # Указываем камеру, к которой привязан узел
        node_info.attrName = attr_name.encode('utf-8')      # Указываем имя атрибута узла
        node = pointer(GENICAM_IntNode())                   # Создаем указатель на узел типа int
        nRet = GENICAM_createIntNode(byref(node_info), byref(node))  # Создаем узел
        if nRet != 0:
            print(f'create {attr_name} Node fail!')                  # Обработка ошибки
            return None
        return node                                                  # Возвращаем созданный узел


    def _create_double_node(self, camera, attr_name):
        '''Создание узла для атрибута типа double'''
        node_info = GENICAM_DoubleNodeInfo()            # Создаем информацию о узле
        node_info.pCamera = pointer(camera)             # Указываем камеру, к которой привязан узел
        node_info.attrName = attr_name.encode('utf-8')  # Указываем имя атрибута узла
        node = pointer(GENICAM_DoubleNode())            # Создаем указатель на узел типа double
        nRet = GENICAM_createDoubleNode(byref(node_info), byref(node))  # Создаем узел
        if nRet != 0:
            print(f'create {attr_name} Node fail!')                     # Обработка ошибки
            return None
        return node                                                     # Возвращаем созданный узел
    
    def _create_enum_node(self, camera, attr_name):
        '''Создание узла для атрибута типа enum'''
        node_info = GENICAM_EnumNodeInfo()            # Создаем информацию о узле
        node_info.pCamera = pointer(camera)             # Указываем камеру, к которой привязан узел
        node_info.attrName = attr_name.encode('utf-8')  # Указываем имя атрибута узла
        node = pointer(GENICAM_EnumNode())            # Создаем указатель на узел типа double
        nRet = GENICAM_createEnumNode(byref(node_info), byref(node))  # Создаем узел
        if nRet != 0:
            print(f'create {attr_name} Node fail!')                     # Обработка ошибки
            return None
        return node                                                     # Возвращаем созданный узел


    @property
    def ExposureTime(self):
        '''Свойство для получения текущего значения экспозиции'''
        if self._exposure_time_node is None:
            print('ExposureTime node is not initialized.')
            return None
        value = c_double()
        nRet = self._exposure_time_node.contents.getValue(self._exposure_time_node, byref(value))
        if nRet != 0:
            print('get ExposureTime value fail!')
            return None
        return value.value

    @ExposureTime.setter
    def ExposureTime(self, value):
        '''Свойство для установки нового значения экспозиции'''
        nRet = self._set_exposure_time(value)
        if nRet == 0:
            print('ExposureTime set to', value)
        else:
            print('Failed to set ExposureTime')

    def _set_exposure_time(self, dVal):
        '''Внутренний метод для установки значения экспозиции'''
        if self._exposure_time_node is None:
            print('ExposureTime node is not initialized.')
            return -1
        
        nRet = self._exposure_time_node.contents.setValue(self._exposure_time_node, c_double(dVal))
        if nRet != 0:
            print(f'set ExposureTime value [{dVal}]us fail!')
            return -1
        
        return 0
    
    @property
    def AcquisitionMode(self):
        '''Свойство для получения текущего режима активации'''
        if self._acquisition_mode_node is None:
            print('AcquisitionMode node is not initialized.')
            return None
        value = c_ulong()
        nRet = self._acquisition_mode_node.contents.getValue(self._acquisition_mode_node, byref(value))
        if nRet != 0:
            print('get AcquisitionMode value fail!')
            return None
        return value.value

    @AcquisitionMode.setter
    def AcquisitionMode(self, mode):
        '''Свойство для установки нового режима активации'''
        if self._acquisition_mode_node is None:
            print('AcquisitionMode node is not initialized.')
            return
        nRet = self._acquisition_mode_node.contents.setValue(self._acquisition_mode_node, c_ulong(mode))
        if nRet != 0:
            print('Failed to set AcquisitionMode')
        else:
            print('AcquisitionMode set to', mode)

    def setROI(self, nWidth, nHeight, OffsetX, OffsetY):
        '''
        Метод для установки ROI (Region of Interest).
        
        Параметры:
        - nWidth: Ширина области.
        - nHeight: Высота области.
        - OffsetX: Смещение по оси X.
        - OffsetY: Смещение по оси Y.
        
        Последовательность установки:
        1. Установить ширину (Width).
        2. Установить высоту (Height).
        3. Установить смещение по оси X (OffsetX).
        4. Установить смещение по оси Y (OffsetY).
        '''
        if not self._set_int_node_value('Width', nWidth):
            return -1
        if not self._set_int_node_value('Height', nHeight):
            return -1
        if not self._set_int_node_value('OffsetX', OffsetX):
            return -1
        if not self._set_int_node_value('OffsetY', OffsetY):
            return -1
        print('ROI set to OffsetX:', OffsetX, 'OffsetY:', OffsetY, 'Width:', nWidth, 'Height:', nHeight)
        return 0

    def _set_int_node_value(self, node_name, value):
        '''Внутренний метод для установки значения узла типа int'''
        node = self._create_int_node(self.camera, node_name)
        if node is None:
            return False
        nRet = node.contents.setValue(node, c_long(value))
        node.contents.release(node)
        if nRet != 0:
            print(f'{node_name} setValue [{value}] fail!')
            return False
        return True


c = CameraAPI()  
with c as camera:
    if camera.camera:
        print('Camera is connected.')
        camera.ExposureTime = 10000
        print('ExposureTime:', camera.ExposureTime)
        camera.setROI(640, 1900, 100, 100)
        print(camera.AcquisitionMode)
        camera.AcquisitionMode = 1
    else:
        print('Failed to connect to the camera.')