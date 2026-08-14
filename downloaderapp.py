import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Lista de instancias públicas y estables de Piped (Proxies de YouTube que no bloquean servidores en la nube)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.privacydev.net",
    "https://pipedapi.palvelu.org",
    "https://piped-api.garudalinux.org"
]

def extraer_video_id(url):
    """ Extrae el ID del video de YouTube de cualquier formato de URL """
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def descargar():
    data = request.json or {}
    url = data.get('url', '').strip()
    opcion = data.get('opcion', '1')

    if not url:
        return jsonify({'success': False, 'message': 'Debes ingresar una URL válida.'}), 400

    video_id = extraer_video_id(url)
    if not video_id:
        return jsonify({'success': False, 'message': 'URL de YouTube no válida.'}), 400

    is_audio = (opcion == '2')
    stream_url = None
    last_error = ""

    # Probamos con los proxies de Piped
    for instance in PIPED_INSTANCES:
        try:
            res = requests.get(f"{instance}/streams/{video_id}", timeout=10)
            if res.status_code == 200:
                data_json = res.json()
                
                if is_audio:
                    # Buscar el stream de audio con mayor bitrate
                    audio_streams = data_json.get('audioStreams', [])
                    if audio_streams:
                        # Ordenamos por bitrate de mayor a menor
                        audio_streams.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                        stream_url = audio_streams[0].get('url')
                else:
                    # Buscar stream de video
                    video_streams = data_json.get('videoStreams', [])
                    if video_streams:
                        # Filtramos los que tienen video y audio juntos (videoOnly == False)
                        combined = [v for v in video_streams if not v.get('videoOnly', False)]
                        if combined:
                            stream_url = combined[0].get('url')
                        else:
                            stream_url = video_streams[0].get('url')

                if stream_url:
                    break
        except Exception as e:
            last_error = str(e)

    if not stream_url:
        return jsonify({
            'success': False, 
            'message': 'No se pudo procesar el video. YouTube requiere verificación en este momento.'
        }), 500

    return jsonify({
        'success': True,
        'message': '¡Procesado exitosamente! Descargando...',
        'file_url': stream_url
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
