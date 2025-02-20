from flask import request, jsonify
from flask_restful import Resource

class HistoryResource(Resource):
    def get(self):
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            from app import video_service  # 延迟导入

            # 从 Supabase 查询历史记录
            start = (page - 1) * per_page
            end = start + per_page - 1

            # 假设你的 Supabase 表名为 'video_history'
            result = video_service.supabase.table('video_history') \
                .select('*') \
                .order('created_at', desc=True) \
                .range(start, end) \
                .execute()

            if result.data:
                return jsonify({
                    'items': result.data,  # 直接返回 Supabase 查询结果
                    'page': page,
                    'per_page': per_page
                })
            else:
                print("获取历史记录失败:", result)
                return jsonify({'error': '获取历史记录失败'}), 500

        except Exception as e:
            print(f"从 Supabase 获取历史记录失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
        

class RecentHistoryResource(Resource):
    def get(self):
        try:
            from app import video_service

            history_list = video_service.get_recent_history(limit=10)
            return jsonify({
                    'success': True,
                    'history': history_list
                })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

class HistoryDetailResource(Resource):
    def get(self, history_id):
        try:
            from app import video_service
            video_data = video_service.get_history_detail(history_id)
            if video_data:
                return jsonify({
                    'success': True,
                    'history_item': video_data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '历史记录未找到'
                }), 404

        except Exception as e:
            print(f"从 Supabase 获取历史记录详情失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    def delete(self, history_id):
        try:
            from app import video_service
            #保证history_id是字符串
            success, message = video_service.delete_history(str(history_id))
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
            print(f"从 Supabase 删除历史记录失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500