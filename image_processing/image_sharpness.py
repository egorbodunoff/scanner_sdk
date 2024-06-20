import cv2

def calculate_sharpness(image, width=None, height=None):
    """
    Вычисляет резкость изображения и опционально обрезает его.

    Параметры:
    - image: Входное изображение (numpy array).
    - width: Ширина для обрезки (опционально).
    - height: Высота для обрезки (опционально).

    Возвращает:
    - sharpness: Значение резкости изображения.
    - cropped_image: Обрезанное изображение (numpy array).
    """
    if width is None or height is None:
        crop_width = image.shape[1]
        crop_height = image.shape[0]
        cropped_image = image
    else:
        crop_width = min(width, image.shape[1])
        crop_height = min(height, image.shape[0])
        cropped_image = crop_center(image, crop_width, crop_height)

    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness = laplacian.var()

    return sharpness, cropped_image

def save_image(image, output_path):
    """
    Сохраняет изображение в файл.

    Параметры:
    - image: Изображение для сохранения (numpy array).
    - output_path: Путь для сохранения изображения.
    """
    try:
        cv2.imwrite(output_path, image)
        print(f"Изображение успешно сохранено в {output_path}")
    except Exception as e:
        print(f"Не удалось сохранить изображение в {output_path}: {e}")

def crop_center(image, crop_width, crop_height):
    """
    Обрезает центр изображения.

    Параметры:
    - image: Входное изображение (numpy array).
    - crop_width: Ширина обрезаемой области.
    - crop_height: Высота обрезаемой области.

    Возвращает:
    - cropped_image: Обрезанное изображение (numpy array).
    """
    height, width = image.shape[:2]
    start_x = (width - crop_width) // 2
    start_y = (height - crop_height) // 2
    cropped_image = image[start_y:start_y + crop_height, start_x:start_x + crop_width]
    return cropped_image

def blur_image(image, kernel_size=(3, 3)):
    """
    Применяет гауссово размытие к изображению.

    Параметры:
    - image: Входное изображение (numpy array).
    - kernel_size: Размер гауссова ядра (по умолчанию (25, 25)).

    Возвращает:
    - blurred_image: Размытое изображение (numpy array).
    """
    blurred_image = cv2.GaussianBlur(image, kernel_size, 0)
    return blurred_image

if __name__ == "__main__":
    image_path = "../image/Образец №4/4_1.bmp"
    output_folder = "../output_images/"

    try:
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Не удалось открыть файл {image_path}")

        blurred_image = blur_image(image)

        # Сохраняем исходное изображение
        save_image(image, output_folder + "original_image.bmp")
        save_image(blurred_image, output_folder + "original_blurred_image.bmp")

        # Посчитаем резкость изображения без обрезки
        sharpness_full, cropped_image = calculate_sharpness(image)
        sharpness_full_blurred, cropped_image_blurred = calculate_sharpness(blurred_image)
        print(f"Резкость полного изображения: {sharpness_full}")
        print(f"Резкость полного размытого изображения: {sharpness_full_blurred}")

        # Задаем параметры обрезки и считаем резкость обрезанного изображения
        crop_width = 640
        crop_height = 1848

        sharpness_cropped, cropped_image = calculate_sharpness(image, crop_width, crop_height)
        sharpness_cropped_blurred, cropped_image_blurred = calculate_sharpness(blurred_image, crop_width, crop_height)

        print(f"Резкость обрезанного изображения: {sharpness_cropped}")
        print(f"Резкость обрезанного размытого изображения: {sharpness_cropped_blurred}")

        # Сохраняем обрезанное изображение с рассчитанной резкостью
        save_image(cropped_image, output_folder + "cropped_image.bmp")
        save_image(cropped_image_blurred, output_folder + "cropped_blurred_image.bmp")

    except Exception as e:
        print(f"Ошибка: {e}")
