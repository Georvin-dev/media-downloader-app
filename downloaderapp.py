import os
from flask import Flask, render_template, request, jsonify
import yt_dlp

app = Flask(__name__)

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

    is_audio = (opcion == '2')

    # Configuración ligera para extraer solo el enlace de streaming
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'format': 'bestaudio/best' if is_audio else 'best[ext=mp4]/best',
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'ios']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                info = info['entries'][0]

            direct_url = info.get('url')

            if not direct_url:
                return jsonify({'success': False, 'message': 'No se pudo obtener el enlace de transmisión.'}), 500

            return jsonify({
                'success': True,
                'message': '¡Procesado exitosamente! Descargando...',
                'file_url': direct_url
            })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al procesar el enlace: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
