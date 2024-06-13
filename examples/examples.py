import sys
import os

api_relative_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../api'))
sys.path.append(api_relative_path)

from camera_api import CameraAPI
from camera_exceptions import *

def main():
    try:
        with CameraAPI() as camera:
            print('Camera is connected.')
            camera.ExposureTime = 5000
            print(camera.ExposureTime)

    except CameraConnectionError:
        print('Failed to connect to the camera.')

    try:
        with CameraAPI() as camera:
            print('Camera is connected.')
            camera.setROI(1920, 2000, 100, 100)
            print(camera.getROI())  

    except CameraConnectionError:
        print('Failed to connect to the camera.')

    except NodeValueError as ex:
        print(ex.args[0])

if __name__ == '__main__':
    main()