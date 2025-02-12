from flask import request, jsonify
from flask_restful import Resource

class HistoryResource(Resource):
    def get(self):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            # 获取历史记录列表 (假设 video_service 已经在 app.py 中初始化)
            # 需要在 app.py 中导入 video_service
            from app import video_service  # 避免循环导入 (如果 resources 文件夹独立)

            # 获取ID列表
            start = (page - 1) * per_page
            end = start + per_page - 1
            video_ids = video_service.redis.zrevrange("history:list", start, end)

            # 获取详细信息
            history_list = []
            for video_id in video_ids:
                details = video_service.redis.hgetall(f"history:detail:{video_id}")
                if details:
                    details['id'] = video_id
                    history_list.append(details)

            return jsonify({
                'items': history_list,
                'page': page,
                'per_page': per_page
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500
class RecentHistoryResource(Resource):
    def get(self):
        try:
            # 需要在 app.py 中导入 video_service
            from app import video_service

            # 获取最近的历史记录
            history_list = video_service.get_recent_history(limit=10)

            return jsonify({
                'success': True,
                'history': history_list
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

class HistoryDetailResource(Resource):
    def delete(self, history_id):
        try:
            # 需要在 app.py 中导入 video_service
            from app import video_service

            success, message = video_service.delete_history(history_id)
            if success:
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'error': message
                }), 400

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500