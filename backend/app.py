from flask import Flask, request, render_template, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import logging
import subprocess
from psd_tools import PSDImage
from PIL import Image

# ログの設定
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.template_folder = "../frontend/templates"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'ai', 'psd'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """ ファイル名が許可された拡張子かどうかをチェック """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_psd_file(filepath):
    """ ファイルがPSDフォーマットかどうかをチェック """
    try:
        with open(filepath, 'rb') as file:
            return file.read(4) == b'8BPS'
    except Exception:
        return False

def process_psd_file(filepath):
    """ PSDファイルをPNGに変換 """
    psd = PSDImage.open(filepath)
    image = psd.composite()
    if image.mode == 'CMYK':
        image = image.convert('RGB')

    base_filename = os.path.splitext(os.path.basename(filepath))[0]
    png_filename = base_filename + '.png'
    png_filepath = os.path.join(app.config['UPLOAD_FOLDER'], png_filename)
    image.save(png_filepath, format='PNG')
    
    return png_filename  # ファイル名のみを返す
    
def process_ai_file(filepath):
    """ AIファイルをPNGに変換 """
    base_filename = os.path.splitext(os.path.basename(filepath))[0]
    png_filename = base_filename + '.png'
    png_filepath = os.path.join(app.config['UPLOAD_FOLDER'], png_filename)
    subprocess.run(["convert", filepath, png_filepath])
    return png_filename  # ファイル名のみを返す

@app.route('/')
def index():
    """ メインページのルート """
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """ ファイルアップロードと処理のルート """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        file_ext = filename.rsplit('.', 1)[1].lower()
        
        if file_ext == 'psd' and is_psd_file(filepath):
            png_filename = process_psd_file(filepath)
            return jsonify({'uploaded_file_path': url_for('uploaded_file', filename=png_filename)})

        elif file_ext == 'ai':
            png_filename = process_ai_file(filepath)
            return jsonify({'uploaded_file_path': url_for('uploaded_file', filename=png_filename)})

        elif file_ext in ['jpg', 'png', 'jpeg', 'gif']:
            return jsonify({'uploaded_file_path': url_for('uploaded_file', filename=filename)})

        else:
            return jsonify({'message': 'Unsupported file format'})

    return jsonify({'error': 'Invalid file format'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """ アップロードされたファイルを提供するルート """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
