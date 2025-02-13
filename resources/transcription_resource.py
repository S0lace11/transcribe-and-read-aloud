from flask import request, jsonify
from flask_restful import Resource

class TranscribeVideoResource(Resource):
    def post(self):
        try:
            data = request.json
            if not data or 'filename' not in data or 'source' not in data:
                return jsonify({'error': '缺少必要的参数'}), 400

            filename = data['filename']
            source = data['source']

            from app import video_service  # 延迟导入
            result = video_service.process_video(filename, source_type=source)
            if not result:
                return jsonify({'error': '视频转录失败'}), 500

            return jsonify({
                'success': True,
                'message': '转录成功',
                'transcription': result['transcription']
            })

        except Exception as e:
            print(f"处理视频转录时出错: {str(e)}")
            return jsonify({'error': str(e)}), 500