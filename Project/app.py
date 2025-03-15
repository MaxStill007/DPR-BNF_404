from flask import Flask, render_template, request, jsonify
import os
import uuid
from transformers import DetrForObjectDetection, DetrImageProcessor
from PIL import Image, ImageDraw
import torch
import sqlite3
from datetime import datetime
from Vision import Scan

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static/output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

#model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-101")
#processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-101")

db_path = "objects_database.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS objects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tags TEXT,
        pathTo TEXT,
        upload_date TEXT,
        processed_image_name TEXT
    )
''')
conn.commit()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Нет файла в запросе'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Нет выбранного файла'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    output_image_path, detected_objects = Scan(file_path, db_path, conn, cursor, UPLOAD_FOLDER, OUTPUT_FOLDER)

    output_image_url = f"/{app.config['OUTPUT_FOLDER']}/{os.path.basename(output_image_path)}" if output_image_path else None

    return jsonify({
        'output_image_url': output_image_url,
        'tags': detected_objects
    }), 200

@app.route('/catalog', methods=['GET', 'POST'])
def gallery():
    cursor.execute("SELECT * FROM objects")
    images = cursor.fetchall()

    image_tags = {}
    for image in images:
        image_id = image[0]
        tags = image[1].split(',')
        tag_count = {}
        for tag in tags:
            tag = tag.strip()
            if tag in tag_count:
                tag_count[tag] += 1
            else:
                tag_count[tag] = 1
        image_tags[image_id] = tag_count

    search_query = request.form.get('search')
    if search_query:
        search_query = search_query.strip().lower()
        filtered_images = []
        for image_id, tags in image_tags.items():
            if any(search_query in tag.lower() for tag in tags.keys()):
                filtered_images.append(next(image for image in images if image[0] == image_id))
        images = filtered_images

    return render_template('catalog.html', images=images, image_tags=image_tags, search_query=search_query)

if __name__ == '__main__':
    app.run(debug=True)