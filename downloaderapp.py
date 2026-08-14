from flask import Flask, render_template, request, jsonify, send_file
import os
import glob
import shutil
import requests

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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

    import uuid
    session_id = str(uuid.uuid4())
    temp_dir = os.path.join(DOWNLOAD_DIR, session_id)
    os.makedirs(temp_dir, exist_ok=True)

    is_audio = (opcion == '2')

    # Instancias actuales de la API pública de Cobalt
    instances = [
        "https://api.cobalt.tools",
        "https://cobalt-api.koyeb.app"
    ]

    payload = {
        "url": url,
        "downloadMode": "audio" if is_audio else "auto",
        "audioFormat": "mp3" if is_audio else "best",
        "videoQuality": "1080"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    media_url = None
    last_error = ""

    # Probamos las instancias activas si una falla
    for instance in instances:
        try:
            response = requests.post(instance, json=payload, headers=headers, timeout=12)
            res_data = response.json()
            
            if response.status_code == 200 and res_data.get('status') != 'error':
                media_url = res_data.get('url') or (res_data.get('picker', [{}])[0].get('url') if res_data.get('picker') else None)
                if media_url:
                    break
            else:
                last_error = res_data.get('text', 'Error en el servidor de descarga.')
        except Exception as e:
            last_error = str(e)

    if not media_url:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({'success': False, 'message': f'No se pudo obtener el archivo: {last_error}'}), 400

    try:
        ext = 'mp3' if is_audio else 'mp4'
        nombre_archivo = f"descarga_{session_id[:8]}.{ext}"
        archivo_path = os.path.join(temp_dir, nombre_archivo)

        file_res = requests.get(media_url, stream=True, timeout=30)
        with open(archivo_path, 'wb') as f:
            for chunk in file_res.iter_content(chunk_size=8192):
                f.write(chunk)

        return jsonify({
            'success': True,
            'message': '¡Procesado exitosamente! Descargando archivo...',
            'file_url': f'/get-file/{session_id}/{nombre_archivo}'
        })

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({'success': False, 'message': f'Error al guardar el archivo: {str(e)}'}), 500

@app.route('/get-file/<session_id>/<filename>')
def get_file(session_id, filename):
    temp_dir = os.path.join(DOWNLOAD_DIR, session_id)
    file_path = os.path.join(temp_dir, filename)

    if os.path.exists(file_path):
        response = send_file(file_path, as_attachment=True, download_name=filename)
        
        @response.call_on_close
        def cleanup():
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        return response
    else:
        return "El archivo no existe o ya expiró.", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
