import sys
import os
from ctypes import *

# Добавляем путь к SDK в sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))

from MVSDK import *

class CameraAPI:
    def __init__(self):
        self.camera = None                                  # Инициализация камеры
        self._exposure_time_node = None                     # Узел для управления экспозицией
        self._acquisition_mode_node = None                  # Узел для управления режимом активации
        self._acquisition_frame_count_node = None           # Узел для управления количеством кадров
        self._acquisition_frame_rate_node = None            # Узел для управления частотой кадров
        self._acquisition_frame_rate_enable_node = None     # Узел для управления включением частоты кадров
        self._exposure_auto_node = None                     # Узел для управления автоматической экспозицией
        self._exposure_mode_node = None                     # Узел для управления режимом экспозиции
        self._gain_raw_node = None                          # Узел для управления усилением (GainRaw)
        self._black_level_node = None                       # Узел для управления черным уровнем (BlackLevel)
        self._black_level_auto_node = None                  # Узел для управления автоматическим определением BlackLevel
        self._gamma_node = None                             # Узел для управления гаммой (Gamma)
        self._width_node = None                             # Узел для управления шириной области (ROI)
        self._height_node = None                            # Узел для управления высотой области (ROI)
        self._offsetX_node = None                           # Узел для управления смещением по оси X (ROI)
        self._offsetY_node = None                           # Узел для управления смещением по оси Y (ROI)

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
        
        self._initialize_nodes(first_camera)
    
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

    def _initialize_nodes(self, camera):
        '''Инициализация всех узлов камеры'''
        self._initialize_node(camera, '_exposure_time_node', 'ExposureTime', self._create_double_node)
        self._initialize_node(camera, '_acquisition_mode_node', 'AcquisitionMode', self._create_enum_node)
        self._initialize_node(camera, '_acquisition_frame_count_node', 'AcquisitionFrameCount', self._create_int_node)
        self._initialize_node(camera, '_acquisition_frame_rate_node', 'AcquisitionFrameRate', self._create_double_node)
        self._initialize_node(camera, '_acquisition_frame_rate_enable_node', 'AcquisitionFrameRateEnable', self._create_bool_node)
        self._initialize_node(camera, '_exposure_auto_node', 'ExposureAuto', self._create_enum_node)
        self._initialize_node(camera, '_exposure_mode_node', 'ExposureMode', self._create_enum_node)
        self._initialize_node(camera, '_gain_raw_node', 'GainRaw', self._create_double_node)
        self._initialize_node(camera, '_black_level_node', 'BlackLevel', self._create_int_node)
        self._initialize_node(camera, '_black_level_auto_node', 'BlackLevelAuto', self._create_enum_node)
        self._initialize_node(camera, '_gamma_node', 'Gamma', self._create_double_node)

        # Добавляем узлы для ROI
        self._width_node = self._create_int_node(camera, 'Width')
        self._height_node = self._create_int_node(camera, 'Height')
        self._offsetX_node = self._create_int_node(camera, 'OffsetX')
        self._offsetY_node = self._create_int_node(camera, 'OffsetY')


    def _initialize_node(self, camera, node_attr, node_name, create_node_func):
        '''Инициализация конкретного узла'''
        setattr(self, node_attr, create_node_func(camera, node_name))
        if not getattr(self, node_attr):
            print(f'Failed to initialize {node_name} node.')

    def _create_node(self, camera, attr_name, node_type):
        '''Универсальный метод для создания узла'''
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
        return self._create_node(camera, attr_name, {
            'info': GENICAM_IntNodeInfo,
            'node': GENICAM_IntNode,
            'create': GENICAM_createIntNode
        })

    def _create_double_node(self, camera, attr_name):
        return self._create_node(camera, attr_name, {
            'info': GENICAM_DoubleNodeInfo,
            'node': GENICAM_DoubleNode,
            'create': GENICAM_createDoubleNode
        })
    
    def _create_enum_node(self, camera, attr_name):
        return self._create_node(camera, attr_name, {
            'info': GENICAM_EnumNodeInfo,
            'node': GENICAM_EnumNode,
            'create': GENICAM_createEnumNode
        })
    
    def _create_bool_node(self, camera, attr_name):
        return self._create_node(camera, attr_name, {
            'info': GENICAM_BoolNodeInfo,
            'node': GENICAM_BoolNode,
            'create': GENICAM_createBoolNode
        })

    @property
    def ExposureTime(self):
        '''Свойство для получения текущего значения экспозиции'''
        return self._get_node_value(self._exposure_time_node, c_double)

    @ExposureTime.setter
    def ExposureTime(self, value):
        '''Свойство для установки нового значения экспозиции'''
        self._set_node_value(self._exposure_time_node, c_double(value))

    @property
    def AcquisitionMode(self):
        '''Свойство для получения текущего режима активации'''
        return self._get_node_value(self._acquisition_mode_node, c_ulong)

    @AcquisitionMode.setter
    def AcquisitionMode(self, mode):
        '''Свойство для установки нового режима активации'''
        self._set_node_value(self._acquisition_mode_node, c_ulong(mode))

    @property
    def AcquisitionFrameCount(self):
        '''Свойство для получения текущего количества кадров'''
        return self._get_node_value(self._acquisition_frame_count_node, c_long)
    
    @AcquisitionFrameCount.setter
    def AcquisitionFrameCount(self, count):
        '''Свойство для установки нового значения количества кадров'''
        self._set_node_value(self._acquisition_frame_count_node, c_int64(count))

    @property
    def AcquisitionFrameRate(self):
        '''Свойство для получения текущей частоты кадров'''
        return self._get_node_value(self._acquisition_frame_rate_node, c_double)

    @AcquisitionFrameRate.setter
    def AcquisitionFrameRate(self, rate):
        '''Свойство для установки новой частоты кадров'''
        self._set_node_value(self._acquisition_frame_rate_node, c_double(rate))

    @property
    def AcquisitionFrameRateEnable(self):
        '''Свойство для получения текущего значения включения частоты кадров'''
        return bool(self._get_node_value(self._acquisition_frame_rate_enable_node, c_uint))

    @AcquisitionFrameRateEnable.setter
    def AcquisitionFrameRateEnable(self, enable):
        '''Свойство для установки нового значения включения частоты кадров'''
        self._set_node_value(self._acquisition_frame_rate_enable_node, c_uint(1 if enable else 0))

    @property
    def ExposureAuto(self):
        '''Свойство для получения текущего значения автоматической экспозиции'''
        return self._get_node_value(self._exposure_auto_node, c_ulong)

    @ExposureAuto.setter
    def ExposureAuto(self, mode):
        '''Свойство для установки нового значения автоматической экспозиции'''
        self._set_node_value(self._exposure_auto_node, c_ulong(mode))

    @property
    def ExposureMode(self):
        '''Свойство для получения текущего значения режима экспозиции'''
        return self._get_node_value(self._exposure_mode_node, c_ulong)

    @ExposureMode.setter
    def ExposureMode(self, mode):
        '''Свойство для установки нового значения режима экспозиции'''
        self._set_node_value(self._exposure_mode_node, c_ulong(mode))

    @property
    def GainRaw(self):
        '''Свойство для получения текущего значения усиления (GainRaw)'''
        return self._get_node_value(self._gain_raw_node, c_double)

    @GainRaw.setter
    def GainRaw(self, value):
        '''Свойство для установки нового значения усиления (GainRaw)'''
        self._set_node_value(self._gain_raw_node, c_double(value))

    @property
    def BlackLevel(self):
        '''Свойство для получения текущего значения черного уровня (BlackLevel)'''
        return self._get_node_value(self._black_level_node, c_long)

    @BlackLevel.setter
    def BlackLevel(self, value):
        '''Свойство для установки нового значения черного уровня (BlackLevel)'''
        self._set_node_value(self._black_level_node, c_long(value))

    @property
    def BlackLevelAuto(self):
        '''Свойство для получения текущего значения автоматического определения черного уровня (BlackLevelAuto)'''
        return self._get_node_value(self._black_level_auto_node, c_ulong)

    @BlackLevelAuto.setter
    def BlackLevelAuto(self, mode):
        '''Свойство для установки нового значения автоматического определения черного уровня (BlackLevelAuto)'''
        self._set_node_value(self._black_level_auto_node, c_ulong(mode))

    @property
    def Gamma(self):
        '''Свойство для получения текущего значения гаммы (Gamma)'''
        return self._get_node_value(self._gamma_node, c_double)

    @Gamma.setter
    def Gamma(self, value):
        '''Свойство для установки нового значения гаммы (Gamma)'''
        self._set_node_value(self._gamma_node, c_double(value))

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
        '''
        Метод для получения параметров ROI (Region of Interest).
        
        Возвращает кортеж из четырех значений: (Width, Height, OffsetX, OffsetY)
        '''
        width = self._get_node_value(self._width_node, c_long)
        height = self._get_node_value(self._height_node, c_long)
        offsetX = self._get_node_value(self._offsetX_node, c_long)
        offsetY = self._get_node_value(self._offsetY_node, c_long)
        
        if None in (width, height, offsetX, offsetY):
            return None
        
        return width, height, offsetX, offsetY

    def _get_node_value(self, node, value_type):
        '''Внутренний метод для получения значения узла'''
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
        '''Внутренний метод для установки значения узла'''
        if node is None:
            print(f'{type(value).__name__} node is not initialized.')
            return False
        nRet = node.contents.setValue(node, value)
        if nRet != 0:
            print(f'set {type(value).__name__} value [{value}] fail!')
            return False
        return True


c = CameraAPI()  
with c as camera:
    if camera.camera:
        print('Camera is connected.')
        camera.Gamma = 1
        print(camera.Gamma)
        # camera.setROI(640, 1900, 100, 100)
        # camera.setROI(5472, 3648, 0, 0)
        # print(camera.getROI())
    else:
        print('Failed to connect to the camera.')