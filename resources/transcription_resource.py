from flask import request, jsonify
from flask_restful import Resource

class TranscribeVideoResource(Resource):
    def post(self):
        try:
            data = request.json
            # 接收 history_id (Supabase 记录 ID)
            if not data or 'history_id' not in data:
                return {'error': '缺少必要的参数 history_id'}, 400

            history_id = data['history_id']

            from app import video_service, current_user # 延迟导入

            # 获取当前登录用户的 ID
            user_id = current_user.id

            # 调用 video_service 的 process_video 方法，传入 history_id 和 user_id
            result = video_service.process_video(history_id, user_id)
            if result:
                return {
                    'success': True,
                    'message': '转录成功',
                    'transcription': result['transcription'],
                    'video_url': result.get('video_url', '')  # OSS URL
                }
            else:
                return {'error': '视频转录失败'}, 500

        except Exception as e:
            print(f"处理视频转录时出错: {str(e)}")
            return {'error': str(e)}, 500