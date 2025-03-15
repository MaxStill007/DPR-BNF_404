from transformers import DetrForObjectDetection, DetrImageProcessor
from PIL import Image, ImageDraw
import torch
from datetime import datetime
import uuid
import sqlite3
import os
from collections import Counter

# Загрузка предобученной модели DETR и процессора
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")



def Scan(image_path, db_path, conn, cursor, inputFolder, outputFolder):
    # Загрузка изображения
    image = Image.open(image_path)

    # Подготовка изображения для модели
    inputs = processor(images=image, return_tensors="pt")

    # Обнаружение объектов
    with torch.no_grad():
        outputs = model(**inputs)

    # Преобразование результатов в читаемый формат
    target_sizes = torch.tensor([image.size[::-1]])  # Размеры изображения (высота, ширина)
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.5)[0]

    # Получение обнаруженных объектов
    detected_objects = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        if score > 0.5:  # Фильтрация по уверенности модели
            class_name = model.config.id2label[label.item()]  # Название класса
            detected_objects.append(class_name)

    # Генерация описания
    if detected_objects:
        tags_string = ', '.join(detected_objects)
        upload_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        unique_code = str(uuid.uuid4())
        output_image_name = f"output_image_{unique_code}.jpg"

        cursor.execute('INSERT INTO objects (tags, pathTo, upload_date, processed_image_name) VALUES (?, ?, ?, ?)',
                       (tags_string, image_path, upload_date, output_image_name))
        conn.commit()
        output_image_path = os.path.join(outputFolder,  output_image_name)
    else:
        output_image_path = None

    if output_image_path:
        draw = ImageDraw.Draw(image)
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            if score > 0.55 and score <= 0.75:  # Фильтрация по уверенности модели
                class_name = model.config.id2label[label.item()]  # Название класса
                box = [round(i, 2) for i in box.tolist()]  # Координаты bounding box
                draw.rectangle(box, outline="red", width=3)  # Рисуем прямоугольник
                draw.text((box[0], box[1]), class_name, fill="black")  # Подписываем класс
            elif score > 0.75 and score <= 0.89:
                class_name = model.config.id2label[label.item()]  # Название класса
                box = [round(i, 2) for i in box.tolist()]  # Координаты bounding box
                draw.rectangle(box, outline="yellow", width=3)  # Рисуем прямоугольник
                draw.text((box[0], box[1]), class_name, fill="black")  # Подписываем класс
            elif score > 0.89:
                class_name = model.config.id2label[label.item()]  # Название класса
                box = [round(i, 2) for i in box.tolist()]  # Координаты bounding box
                draw.rectangle(box, outline="green", width=3)  # Рисуем прямоугольник
                draw.text((box[0], box[1]), class_name, fill="black")  # Подписываем класс

        image.save(output_image_path)
        #conn.close()

        object_counts = Counter(detected_objects)
        description = "На фотографии изображены: " + ", ".join(
            [f"{count} {obj}" for obj, count in object_counts.items()])
        print(description)

    return output_image_path, detected_objects