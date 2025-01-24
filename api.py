from flask import Flask, send_file, abort, jsonify
from config import header_text as image_title
import os

app = Flask(__name__)
port = 9999

@app.route('/')
def index():
    file_path = 'web_files/index.html'
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='text/html')
    else:
        abort(404, description="File not found")

@app.route('/output/')
@app.route('/output/<filename>')
def get_output_file(filename='weather_forecast.png'):
    file_path = f'output/{filename}'
    if os.path.exists(file_path):
        if filename.endswith('.png'):
            mimetype = 'image/png'
        elif filename.endswith('.json'):
            mimetype = 'application/json'
        else:
            abort(400, description="Unsupported file type")
        
        return send_file(file_path, mimetype=mimetype)
    else:
        abort(404, description="File not found")

@app.route('/title/')
def get_title():
    return jsonify({"title": image_title})

@app.route('/index.js')
def get_js():
    file_path = 'web_files/index.js'
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/javascript')
    else:
        abort(404, description="File not found")

if __name__ == '__main__':
    app.run(port=port, debug=False)