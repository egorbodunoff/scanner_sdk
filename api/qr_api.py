import time
import serial

def read_from_port(port, baudrate=115200, timeout=1):
    ser = None
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f"Подключен к {port} на скорости {baudrate}")

        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').rstrip()
                print(data)
                return data
            else:
                time.sleep(0.1)

    except serial.SerialException as e:
        print(f"Ошибка: {e}")
    except KeyboardInterrupt:
        print("Прерывание программы.")
    finally:
        if ser is not None and ser.is_open:
            ser.close()
            print(f"Порт {port} закрыт.")

if __name__ == "__main__":
    port = "/dev/ttyS0"
    read_from_port(port)
