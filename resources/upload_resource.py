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
                return {'error': '没有文件'}, 400
                
            file = request.files['file']
            if file.filename == '':
                return {'error': '没有选择文件'}, 400

            if not file.filename.lower().endswith('.mp4'):
                return jsonify({'error': '只支持MP4格式的视频'}), 415

            # 使用 secure_filename 确保文件名安全
            filename = secure_filename(file.filename)

            # 保存文件
            file_path = os.path.join(Config.RECORDS_FOLDER, filename)
            file.save(file_path)

            # 获取视频信息
            from app import video_service  # 延迟导入
            video_info = video_service.get_video_info(file_path)
            
            # 准备要保存的数据
            video_data = {
                'title': filename,
                'source': 'upload',
                'video_path': filename,
                'duration': str(video_info['duration']) if video_info and 'duration' in video_info else '0:00',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 保存到历史记录
            history_id = video_service.save_to_history(video_data)

            # 确保返回的是可序列化的数据
            return {
                'success': True,
                'message': '上传成功',
                'data': {
                    'filename': filename,
                    'history_id': str(history_id) if history_id else None,
                    'duration': str(video_info['duration']) if video_info and 'duration' in video_info else '0:00'
                }
            }, 201

        except Exception as e:
            print(f"上传处理失败: {str(e)}")
            return {'error': str(e)}, 500