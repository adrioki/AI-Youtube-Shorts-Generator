from flask import Flask, request, jsonify
import os
from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight
from Components.FaceCrop import crop_to_vertical, combine_videos

app = Flask(__name__)
OUTPUT_DIR = "outputs/shorts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/generate", methods=["POST"])
def generate_short():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        # 1️⃣ Télécharger la vidéo
        Vid = download_youtube_video(url)
        if not Vid:
            return jsonify({"error": "Unable to download video"}), 500

        Vid = Vid.replace(".webm", ".mp4")
        
        # 2️⃣ Extraire l'audio
        Audio = extractAudio(Vid)
        if not Audio:
            return jsonify({"error": "No audio file found"}), 500

        # 3️⃣ Transcrire
        transcriptions = transcribeAudio(Audio)
        if not transcriptions:
            return jsonify({"error": "No transcriptions found"}), 500

        # 4️⃣ Générer Highlights
        TransText = "".join([f"{start}-{end}:{text}" for text, start, end in transcriptions])
        start, stop = GetHighlight(TransText)

        if start <= 0 or stop <= 0 or stop <= start:
            return jsonify({"error": "Error in getting highlight"}), 500

        # 5️⃣ Créer le short
        Output = os.path.join(OUTPUT_DIR, "Out.mp4")
        crop_video(Vid, Output, start, stop)

        croped = os.path.join(OUTPUT_DIR, "croped.mp4")
        crop_to_vertical(Output, croped)

        Final = os.path.join(OUTPUT_DIR, "Final.mp4")
        combine_videos(Output, croped, Final)

        return jsonify({"status": "success", "short_path": Final}), 200

    except Exception as e:
        return jsonify({"status": "error", "details": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "✅ YouTube Shorts Generator API is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
