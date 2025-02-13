import os
from flask import request, jsonify
from flask_restful import Resource
from werkzeug.utils import secure_filename
from datetime import datetime
from config import Config

class UploadVideoResource(Resource):
    def post(self):
        try:
            if 'file' not in request.files:
                return jsonify({'error': '没有上传文件'}), 400

            video_file = request.files['file']
            if video_file.filename == '':
                return jsonify({'error': '没有选择文件'}), 400

            if not video_file.filename.lower().endswith('.mp4'):
                return jsonify({'error': '只支持MP4格式的视频'}), 400

            filename = secure_filename(video_file.filename)
            file_path = os.path.join(Config.RECORDS_FOLDER, filename)

            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(file_path):
                filename = f"{base}_{counter}{ext}"
                file_path = os.path.join(Config.RECORDS_FOLDER, filename)
                counter += 1

            video_file.save(file_path)
            print(f"文件已保存到: {file_path}")

            video_data = {
                'title': filename,
                'source': 'upload',
                'video_path': filename,
                'duration': '0:00',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            from app import video_service  # 延迟导入
            history_id = video_service.save_to_history(video_data)
            print(f"[DEBUG] 生成的 history_id: {history_id} (类型: {type(history_id)})")

            return jsonify({
                'success': True,
                'message': '文件上传成功',
                'title': filename,
                'history_id': history_id
            })

        except Exception as e:
            print(f"处理上传视频时出错: {str(e)}")
            return jsonify({'error': str(e)}), 500