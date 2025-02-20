from flask import request, jsonify
from flask_restful import Resource
import threading
import time
from datetime import datetime

class YoutubeDownloadResource(Resource):
    def post(self):
        try:
            url = request.json.get('url')
            if not url:
                return jsonify({'error': '请提供YouTube视频链接'}), 400

            task_id = str(int(time.time()))

            def download_and_save_history():
                try:
                    from app import youtube_service, video_service, current_user  # 延迟导入

                    video_info = youtube_service.download_video(url, task_id)

                    if video_info:
                        video_data = {
                            'title': video_info['title'],
                            'source': 'youtube',
                            'video_path': video_info['filename'],  # 保存本地文件名
                            'duration': video_info['duration'],
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        # 获取当前登录用户的 ID
                        user_id = current_user.id
                        video_service.save_to_history(video_data, user_id)  # 传入 user_id
                except Exception as e:
                    print(f"下载和保存历史记录失败: {str(e)}")

            thread = threading.Thread(target=download_and_save_history)
            thread.daemon = True
            thread.start()

            return jsonify({
                'success': True,
                'message': '开始下载视频',
                'task_id': task_id
            })

        except Exception as e:
            print(f"处理YouTube视频时出错: {str(e)}")
            return jsonify({'error': str(e)}), 500