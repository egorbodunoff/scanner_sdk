import os
from api.camera_api import *
from api.qr_api import *


def create_directory_from_qr(port):
    try:
        qr_data = read_from_port(port)
        print(qr_data)

        directory_name = qr_data.strip()

        os.makedirs(directory_name, exist_ok=True)
        print(f"Дирректория '{directory_name}' создана!")

        return directory_name
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def handle_camera_operations(path):
    c = CameraAPI()
    with c as camera:
        if camera.camera:
            print('Camera is connected.')
            camera.ExposureTime = 9900
            camera.setROI(1900, 2000, 100, 100)
            print('Current ROI:', camera.getROI())
            print('Current GainRaw:', camera.GainRaw)
            camera.capture_frame(directory_name)
        else:
            print('Failed to connect to the camera.')

if __name__ == "__main__":
    port = "/dev/ttyS0"
    directory_name = create_directory_from_qr(port)

    handle_camera_operations("../" + directory_name + "1.bmp")

    