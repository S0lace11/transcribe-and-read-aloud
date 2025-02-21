import os
from flask import render_template, request, send_from_directory, make_response
from flask_restful import Resource
from config import Config

class PlayerResource(Resource):
    def get(self, video_path):
        """视频播放页面"""
        try:
            source = request.args.get('source', 'upload')
            history_id = request.args.get('history_id')

            # 需要在 app.py 中导入 video_service
            from app import video_service


            # 检查文件是否存在 (这部分逻辑保留，因为仍然需要检查本地文件)
            video_file_path = os.path.join(Config.RECORDS_FOLDER, video_path)
            if not os.path.exists(video_file_path):
                return "视频文件不存在", 404

            # 构建视频URL
            video_url = f'/video/{video_path}'

            # 获取转录状态和文本
            transcribed = "0"  # 默认值
            transcription = None  # 默认值

            if history_id:
                # 从 Supabase 获取视频信息
                video_data = video_service.get_history_detail(history_id) # 调用 video_service 的方法
                print("Supabase 数据:", video_data)

                if video_data:
                    transcribed = video_data.get('transcribed', '0')  # 从 Supabase 数据中获取
                    transcription = video_data.get('transcription', '')  # 从 Supabase 数据中获取
                    print("转录状态:", transcribed)
                    print("转录文本:", transcription)

            # 使用 make_response 创建响应对象，并设置 Content-Type
            response = make_response(render_template('player.html',
                                 video_path=video_path,
                                 video_url=video_url,
                                 source=source,
                                 history_id=history_id,
                                 transcribed=transcribed,
                                 transcription=transcription))
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response

        except Exception as e:
            print(f"播放器页面错误: {str(e)}")
            return str(e), 500