from flask import Flask, send_file, abort, jsonify
from config import header_text as image_title
from config import debug as debugStatus
from config import isProduction
import os

app = Flask(__name__)
port = 9999


@app.route("/")
def index():
    file_path = "web_files/index.html"
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="text/html")
    else:
        abort(404, description="File not found")


@app.route("/output/")
@app.route("/output/<filename>")
def get_output_file(filename="weather_forecast.png"):
    file_path = f"output/{filename}"
    if os.path.exists(file_path):
        if filename.endswith(".png"):
            mimetype = "image/png"
        elif filename.endswith(".json"):
            mimetype = "application/json"
        else:
            abort(400, description="Unsupported file type")

        return send_file(file_path, mimetype=mimetype)
    else:
        abort(404, description="File not found")


@app.route("/title/")
def get_title():
    return jsonify({"title": image_title})


@app.route("/index.js")
def get_js():
    file_path = "web_files/index.js"
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="application/javascript")
    else:
        abort(404, description="File not found")


@app.route("/debug/")
def get_debug():
    if debugStatus:
        from config import (
            width_multiplier,
            max_width,
            center_image,
            font,
            header_font,
            footer_font,
            header_text,
            timezone,
            wx_obs_station,
            folder,
            fileName,
            text_color,
            background_color,
            header_color,
            footer_color,
        )

        data = {
            "width_multiplier": width_multiplier,
            "max_width": max_width,
            "center_image": center_image,
            "font": font.getname()[0],
            "header_font": header_font.getname()[0],
            "footer_font": footer_font.getname()[0],
            "header_text": header_text,
            "timezone": timezone,
            "wx_obs_station": wx_obs_station,
            "folder": folder,
            "fileName": fileName,
            "text_color": text_color,
            "background_color": background_color,
            "header_color": header_color,
            "footer_color": footer_color,
        }

        if isProduction:
            data["timezone"] = "[REDACTED]"
            data["wx_obs_station"] = "[REDACTED]"
            data["folder"] = "[REDACTED]"
            data["fileName"] = "[REDACTED]"

        return jsonify(data)

    return jsonify({"debug": False})


if __name__ == "__main__":
    app.run(port=port, debug=False)
