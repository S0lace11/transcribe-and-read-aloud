from flask import request, jsonify
from flask_restful import Resource
import threading
import time
from datetime import datetime


class YoutubeDownloadResource(Resource):

    def post(self):
        try:
            user_input = request.json.get('url')  # 获取原始用户输入
            if not user_input:
                return jsonify({'error': '请提供视频链接'}), 400

            task_id = str(int(time.time()))

            def download_and_save_history():
                try:
                    # 延迟导入
                    from app import video_download_service, video_service

                    video_info = video_download_service.download_video(user_input, task_id)

                    if video_info:

                        video_data = {
                            'title': video_info['title'],
                            'source': 'youtube',  #  'youtube' or 'bilibili'
                            'video_path': video_info['filename'],
                            'duration': video_info['duration'],
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        video_service.save_to_history(video_data)

                except Exception as e:
                    print(f"下载和保存历史记录失败: {str(e)}")
                    # 可选：向客户端发送错误消息（通过进度队列）
                    progress_queue = video_download_service.get_progress_queue(task_id)
                    if progress_queue:
                        progress_queue.put({
                            'status': 'error',
                            'message': str(e)
                        })

            thread = threading.Thread(target=download_and_save_history)
            thread.daemon = True
            thread.start()

            return jsonify({
                'success': True,
                'message': '开始下载视频',
                'task_id': task_id
            })

        except Exception as e:
            print(f"处理视频时出错: {str(e)}")
            return jsonify({'error': str(e)}), 500
