from flask import Flask, render_template, request, jsonify, send_file
import os
import glob
import shutil
import yt_dlp

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

    # Crear una carpeta temporal única por petición para evitar conflictos de nombres entre usuarios
    import uuid
    session_id = str(uuid.uuid4())
    temp_dir = os.path.join(DOWNLOAD_DIR, session_id)
    os.makedirs(temp_dir, exist_ok=True)

    plantilla_salida = os.path.join(temp_dir, '%(title)s.%(ext)s')

    # Si ffmpeg está en el sistema (como en servidores de la nube) o localmente
    ydl_opts = {
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'cookiefile': os.path.join(BASE_DIR, 'cookies.txt'),
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'ios']
            }
        }
    }

    if opcion == '1':
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })
    elif opcion == '2':
        ydl_opts.update({
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        })
    else:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({'success': False, 'message': 'Opción no válida.'}), 400

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Buscar el archivo generado dentro de la carpeta temporal
        archivos = glob.glob(os.path.join(temp_dir, '*'))
        if not archivos:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({'success': False, 'message': 'No se pudo generar el archivo.'}), 500

        archivo_descargado = archivos[0]
        nombre_archivo = os.path.basename(archivo_descargado)

        # Retornamos la ruta donde el frontend puede ir a solicitar la descarga del archivo directo
        return jsonify({
            'success': True,
            'message': '¡Procesado exitosamente! Descargando archivo...',
            'file_url': f'/get-file/{session_id}/{nombre_archivo}'
        })

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({'success': False, 'message': f'Ocurrió un error :( {str(e)}'}), 500

@app.route('/get-file/<session_id>/<filename>')
def get_file(session_id, filename):
    temp_dir = os.path.join(DOWNLOAD_DIR, session_id)
    file_path = os.path.join(temp_dir, filename)

    if os.path.exists(file_path):
        # send_file envía el archivo al navegador/celular del usuario
        response = send_file(file_path, as_attachment=True, download_name=filename)
        
        # Eliminar la carpeta temporal después de enviar el archivo para no llenar el servidor
        @response.call_on_close
        def cleanup():
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        return response
    else:
        return "El archivo no existe o ya expiró.", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
