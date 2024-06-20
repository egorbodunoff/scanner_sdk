import sys
import os
import logging
from ctypes import *
import time
import struct

# exceptions_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'exceptions'))
# sdk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils'))

# sys.path.append(exceptions_path)
# sys.path.append(sdk_path)


from exceptions.camera_exceptions import *
from api.nodes import * 
from utils.MVSDK import *
from utils.ImageConvert import *


# Функция для создания базового логгера
def get_base_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler('cache.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    file_formatter = '\t%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s'
    file_handler.setFormatter(logging.Formatter(file_formatter))

    return logger

# Функция для создания обработчика потока
def get_stream_handler():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    stdout_formatter = 'stdout_log\t%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s'
    stream_handler.setFormatter(logging.Formatter(stdout_formatter))

    return stream_handler

# Настройка логгера
logger = get_base_logger()
# logger.addHandler(get_stream_handler())

# Определение структур для работы с изображениями
class BITMAPFILEHEADER(Structure):
    _fields_ = [
                ('bfType', c_ushort),
                ('bfSize', c_uint),
                ('bfReserved1', c_ushort),
                ('bfReserved2', c_ushort),
                ('bfOffBits', c_uint),
                ]
 
class BITMAPINFOHEADER(Structure):
    _fields_ = [
                ('biSize', c_uint),
                ('biWidth', c_int),
                ('biHeight', c_int),
                ('biPlanes', c_ushort),
                ('biBitCount', c_ushort),
                ('biCompression', c_uint),
                ('biSizeImage', c_uint),
                ('biXPelsPerMeter', c_int),
                ('biYPelsPerMeter', c_int),
                ('biClrUsed', c_uint),
                ('biClrImportant', c_uint),
                ] 

class RGBQUAD(Structure):
    _fields_ = [
                ('rgbBlue', c_ubyte),
                ('rgbGreen', c_ubyte),
                ('rgbRed', c_ubyte),
                ('rgbReserved', c_ubyte),
                ]


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
        logger.info("Opening camera")
        system = self.get_system_instance()
        if not system:
            logger.error("Не удалось получить экземпляр системы")
            raise CameraConnectionError()

        camera_list, camera_cnt = self.discover_cameras(system)
        if not camera_list or camera_cnt < 1:
            logger.error("Камеры не обнаружены")
            raise CameraConnectionError()

        first_camera = camera_list[0]
        if not self.connect_camera(first_camera):
            logger.error("Не удалось подключиться к первой камере")
            raise CameraConnectionError()

        self._initialize_nodes(first_camera)
        logger.info("Камера успешно открыта")

        return first_camera

    def close_camera(self, camera):
        """
        Закрытие соединения с камерой.

        :param camera: Объект камеры.
        :return: 0 при успешном отключении, -1 при ошибке.
        """
        nRet = camera.disConnect(byref(camera))
        if nRet != 0:
            raise CameraConnectionError('Не удалось отключить камеру!')
        return 0

    def get_system_instance(self):
        """
        Получение экземпляра системы.

        :return: Экземпляр системы или None при ошибке.
        """
        system = pointer(GENICAM_System())
        nRet = GENICAM_getSystemInstance(byref(system))
        if nRet != 0:
            raise CameraConnectionError('Не удалось получить экземпляр системы!')
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
            raise CameraConnectionError('Не удалось обнаружить камеры!')
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
        
        logger.info('Успешное подключение камеры.')
        return True

    def _initialize_nodes(self, camera):
        """
        Инициализация узлов камеры.

        :param camera: Объект камеры.
        """
        logger.info("Инициализация узлов камеры")
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
            logger.debug(f'Инициализирован узел: {node_name}')

            if not getattr(self, node_attr):
                logger.error(f"Не удалось инициализировать узел: {node_name}")
                raise NodeInitializationError(node_name)
            
        logger.info("Узлы камеры успешно инициализированы")

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
            logger.error(f"Не удалось создать ноду {attr_name}")
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
    
    def capture_frame(self, path):
        """
        Захват одного кадра с камеры.

        :return: 0 при успешном выполнении, -1 при ошибке.
        """
        logger.info("Начат захват кадра")
        
        # Создание источника потока
        streamSourceInfo = GENICAM_StreamSourceInfo()
        streamSourceInfo.channelId = 0
        streamSourceInfo.pCamera = pointer(self.camera)
        
        streamSource = pointer(GENICAM_StreamSource())
        nRet = GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource))
        if nRet != 0:
            logger.error("Ошибка создания источника потока")
            return -1
        
        # Отключение режима триггера
        if not self._set_trigger_mode("Off"):
            streamSource.contents.release(streamSource)
            return -1
        
        # Начало захвата
        nRet = streamSource.contents.startGrabbing(streamSource, c_ulonglong(0), c_int(GENICAM_EGrabStrategy.grabStrartegySequential))
        if nRet != 0:
            logger.error("Ошибка начала захвата кадра")
            streamSource.contents.release(streamSource)
            return -1
        
        time.sleep(1)  # Задержка на 1 секунду
        
        # Получение кадра
        frame = pointer(GENICAM_Frame())
        nRet = streamSource.contents.getFrame(streamSource, byref(frame), c_uint(1000))
        if nRet != 0:
            logger.error("Ошибка получения кадра")
            streamSource.contents.release(streamSource)
            return -1
        
        if not self._validate_frame(frame):
            streamSource.contents.release(streamSource)
            return -1
        
        # Копирование данных изображения
        imageSize = frame.contents.getImageSize(frame)
        frameBuff = self._copy_image_data(frame, imageSize)
        if frameBuff is None:
            streamSource.contents.release(streamSource)
            return -1
        
        convertParams = self._fill_conversion_params(frame, imageSize)
        frame.contents.release(frame)
        
        if not self._save_image_as_bmp(convertParams, frameBuff, path):
            streamSource.contents.release(streamSource)
            return -1
        
        # Остановка захвата
        nRet = streamSource.contents.stopGrabbing(streamSource)
        if nRet != 0:
            logger.error("Ошибка остановки захвата кадра")
            streamSource.contents.release(streamSource)
            return -1
        
        streamSource.contents.release(streamSource)
        logger.info("Захват кадра завершен успешно")
        return 0

    def _set_trigger_mode(self, mode):
        """
        Установка режима триггера.

        :param mode: Режим триггера ("Off", "On" и т.д.).
        :return: True при успешной установке, False при ошибке.
        """
        logger.info(f"Установка режима триггера: {mode}")

        trigModeEnumNode = pointer(GENICAM_EnumNode())
        trigModeEnumNodeInfo = GENICAM_EnumNodeInfo()
        trigModeEnumNodeInfo.pCamera = pointer(self.camera)
        trigModeEnumNodeInfo.attrName = b"TriggerMode"
        
        nRet = GENICAM_createEnumNode(byref(trigModeEnumNodeInfo), byref(trigModeEnumNode))
        if nRet != 0:
            logger.error("Ошибка создания узла TriggerMode")
            return False
        
        nRet = trigModeEnumNode.contents.setValueBySymbol(trigModeEnumNode, mode.encode('utf-8'))
        if nRet != 0:
            logger.error(f"Ошибка установки значения TriggerMode на {mode}")
            trigModeEnumNode.contents.release(trigModeEnumNode)
            return False
        
        trigModeEnumNode.contents.release(trigModeEnumNode)
        logger.info("Режим триггера установлен успешно")
        return True

    def _validate_frame(self, frame):
        """
        Проверка корректности кадра.

        :param frame: Объект кадра.
        :return: True при корректности кадра, False при ошибке.
        """
        logger.info("Проверка корректности кадра")

        nRet = frame.contents.valid(frame)
        if nRet != 0:
            logger.error("Invalid frame")
            frame.contents.release(frame)
            return False
        
        logger.info("Кадр проверен на корректность")
        return True

    def _copy_image_data(self, frame, imageSize):
        """
        Копирование данных изображения из кадра.

        :param frame: Объект кадра.
        :param imageSize: Размер изображения.
        :return: Буфер с данными изображения или None при ошибке.
        """
        logger.info("Копирование данных изображения")

        buffAddr = frame.contents.getImage(frame)
        frameBuff = c_buffer(b'\0', imageSize)
        memmove(frameBuff, c_char_p(buffAddr), imageSize)

        logger.info("Данные изображения скопированы успешно")
        return frameBuff

    def _fill_conversion_params(self, frame, imageSize):
        """
        Заполнение параметров для конвертации изображения.

        :param frame: Объект кадра.
        :param imageSize: Размер изображения.
        :return: Параметры для конвертации.
        """
        logger.info("Заполнение параметров для конвертации изображения")

        convertParams = IMGCNV_SOpenParam()
        convertParams.dataSize = imageSize
        convertParams.height = frame.contents.getImageHeight(frame)
        convertParams.width = frame.contents.getImageWidth(frame)
        convertParams.paddingX = frame.contents.getImagePaddingX(frame)
        convertParams.paddingY = frame.contents.getImagePaddingY(frame)
        convertParams.pixelForamt = frame.contents.getImagePixelFormat(frame)

        logger.info("Параметры для конвертации изображения заполнены успешно")
        return convertParams

    def _save_image_as_bmp(self, convertParams, frameBuff, path):
        """
        Сохранение изображения в формате BMP.

        :param convertParams: Параметры для конвертации.
        :param frameBuff: Буфер с данными изображения.
        :return: True при успешном сохранении, False при ошибке.
        """
        logger.info("Сохранение изображения в формате BMP")

        bmpInfoHeader = BITMAPINFOHEADER() 
        bmpFileHeader = BITMAPFILEHEADER()
        uRgbQuadLen = 0
        rgbQuad = (RGBQUAD * 256)() 
        rgbBuff = c_buffer(b'\0', convertParams.height * convertParams.width * 3)
        
        if convertParams.pixelForamt == EPixelType.gvspPixelMono8:
            for i in range(256):
                rgbQuad[i].rgbBlue = rgbQuad[i].rgbGreen = rgbQuad[i].rgbRed = i
            uRgbQuadLen = sizeof(RGBQUAD) * 256    
            bmpFileHeader.bfSize = sizeof(bmpFileHeader) + sizeof(bmpInfoHeader) + uRgbQuadLen + convertParams.dataSize
            bmpInfoHeader.biBitCount = 8
        else:
            rgbSize = c_int()
            nRet = IMGCNV_ConvertToBGR24(cast(frameBuff, c_void_p), byref(convertParams), cast(rgbBuff, c_void_p), byref(rgbSize))
            if nRet != 0:
                logger.error("Ошибка конвертации изображения")
                return False
            bmpFileHeader.bfSize = sizeof(bmpFileHeader) + sizeof(bmpInfoHeader) + rgbSize.value
            bmpInfoHeader.biBitCount = 24
        
        bmpFileHeader.bfType = 0x4D42 
        bmpFileHeader.bfReserved1 = 0 
        bmpFileHeader.bfReserved2 = 0 
        bmpFileHeader.bfOffBits = 54 + uRgbQuadLen 
        bmpInfoHeader.biSize = 40     
        bmpInfoHeader.biWidth = convertParams.width
        bmpInfoHeader.biHeight = -convertParams.height
        bmpInfoHeader.biPlanes = 1    
        bmpInfoHeader.biCompression = 0 
        bmpInfoHeader.biSizeImage = 0
        bmpInfoHeader.biXPelsPerMeter = 0
        bmpInfoHeader.biYPelsPerMeter = 0
        bmpInfoHeader.biClrUsed = 0
        bmpInfoHeader.biClrImportant = 0
        
        fileName = path
        try:
            with open(fileName, 'wb+') as imageFile:
                imageFile.write(struct.pack('H', bmpFileHeader.bfType))
                imageFile.write(struct.pack('I', bmpFileHeader.bfSize))
                imageFile.write(struct.pack('H', bmpFileHeader.bfReserved1))
                imageFile.write(struct.pack('H', bmpFileHeader.bfReserved2))
                imageFile.write(struct.pack('I', bmpFileHeader.bfOffBits))
                imageFile.write(struct.pack('I', bmpInfoHeader.biSize))
                imageFile.write(struct.pack('i', bmpInfoHeader.biWidth))
                imageFile.write(struct.pack('i', bmpInfoHeader.biHeight))
                imageFile.write(struct.pack('H', bmpInfoHeader.biPlanes))
                imageFile.write(struct.pack('H', bmpInfoHeader.biBitCount))
                imageFile.write(struct.pack('I', bmpInfoHeader.biCompression))
                imageFile.write(struct.pack('I', bmpInfoHeader.biSizeImage))
                imageFile.write(struct.pack('i', bmpInfoHeader.biXPelsPerMeter))
                imageFile.write(struct.pack('i', bmpInfoHeader.biYPelsPerMeter))
                imageFile.write(struct.pack('I', bmpInfoHeader.biClrUsed))
                imageFile.write(struct.pack('I', bmpInfoHeader.biClrImportant))
                
                if convertParams.pixelForamt == EPixelType.gvspPixelMono8:
                    for i in range(256):
                        imageFile.write(struct.pack('B', rgbQuad[i].rgbBlue)) 
                        imageFile.write(struct.pack('B', rgbQuad[i].rgbGreen))   
                        imageFile.write(struct.pack('B', rgbQuad[i].rgbRed))           
                        imageFile.write(struct.pack('B', rgbQuad[i].rgbReserved))
                    imageFile.write(frameBuff)
                else:
                    imageFile.write(rgbBuff)
        except Exception as e:
            logger.error(f"Ошибка сохранения в BMP: {e}")
            return False

        logger.info(f"Изображение сохранено в BMP {fileName}")
        return True


if __name__ == '__main__':
    c = CameraAPI()
    with c as camera:
        if camera.camera:
            print('Camera is connected.')
            camera.ExposureTime = 9900
            camera.setROI(1900, 2000, 100, 100)
            print(camera.getROI())
            print(camera.GainRaw)
            camera.capture_frame('../image/1.bmp')
        else:
            print('Failed to connect to the camera.')