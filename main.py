from flask import Flask, request, jsonify
from pytube import YouTube
import re
import io

app = Flask(__name__)

def on_progress(chunk, bytes_remaining):
    yield chunk

@app.route('/download_video/<resolution>/<path:url>')
def download_video(resolution, url):
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=resolution).first()
        if stream:
            response = Response(stream.stream(), content_type='video/mp4')
            response.headers['Content-Disposition'] = f'attachment; filename="{yt.title}.mp4"'
            return response
        else:
            return "Video with the specified resolution not found.", 404
    except Exception as e:
        return str(e), 500

def get_video_info(url):
    try:
        yt = YouTube(url)
        stream = yt.streams.first()
        video_info = {
            "title": yt.title,
            "author": yt.author,
            "length": yt.length,
            "views": yt.views,
            "description": yt.description,
            "publish_date": yt.publish_date,
        }
        return video_info, None
    except Exception as e:
        return None, str(e)

def is_valid_youtube_url(url):
    pattern = r"^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+(&\S*)?$"
    return re.match(pattern, url) is not None

@app.route('/download/<resolution>', methods=['GET'])
def download_by_resolution(resolution):
    youtube_link = request.args.get('link')

    if not youtube_link:
        return jsonify({"error": "Missing 'link' query parameter."}), 400

    if not YouTube.validate_url(youtube_link):
        return jsonify({"error": "Invalid YouTube URL."}), 400

    success, error_message = download_video(youtube_link, resolution)

    if success:
        return jsonify({"message": f"Video with resolution {resolution} downloaded successfully."}), 200
    else:
        return jsonify({"error": error_message}), 500

@app.route('/video_info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "Missing 'url' parameter in the request body."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400
    
    video_info, error_message = get_video_info(url)
    
    if video_info:
        return jsonify(video_info), 200
    else:
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    app.run(debug=True)
