from flask import Flask, render_template, request, jsonify, send_from_directory, Response, redirect, send_file
from flask_restful import Api
from services.video_service import VideoService
from services.youtube_service import YouTubeService
from config import Config
import os
from resources.history_resource import HistoryResource, RecentHistoryResource, HistoryDetailResource
from resources.transcription_resource import TranscribeVideoResource
from resources.upload_resource import UploadVideoResource
from resources.youtube_resource import YoutubeDownloadResource
from resources.progress_resource import ProgressResource
from resources.video_file_resource import VideoFileResource
from resources.player_resource import PlayerResource


app = Flask(__name__)
video_service = VideoService()
youtube_service = YouTubeService()
api = Api(app)



@app.route('/')
def index():
    return render_template('index.html')


api.add_resource(UploadVideoResource, '/upload') 
api.add_resource(YoutubeDownloadResource, '/download')
api.add_resource(ProgressResource, '/progress/<task_id>')

# @app.route('/player/<path:video_path>')
# def player(video_path):
#     """视频播放页面"""
#     try:
#         source = request.args.get('source', 'upload')
#         history_id = request.args.get('history_id')
        
#         # 如果收到纯数字ID，添加前缀用于Redis查询
#         if history_id and history_id.isdigit():
#             redis_key = f"history:{history_id}"
#             video_data = video_service.redis.hgetall(redis_key)
        
#         # 检查文件是否存在
#         video_file_path = os.path.join(Config.RECORDS_FOLDER, video_path)
#         if not os.path.exists(video_file_path):
#             return "视频文件不存在", 404
            
#         # 构建视频URL
#         video_url = f'/video/{video_path}'
        
#         # 获取转录状态和文本
#         transcribed = "0"
#         transcription = None
        
#         if history_id:
#             # 获取视频信息
#             video_data = video_service.redis.hgetall(history_id)
#             print("Redis数据:", video_data)  # 添加调试日志
            
#             if video_data:
#                 transcribed = video_data.get('transcribed', '0')
#                 # 直接获取纯文本转录结果
#                 transcription = video_data.get('transcription', '')
#                 print("转录状态:", transcribed)   # 添加调试日志
#                 print("转录文本:", transcription) # 添加调试日志
        
#         return render_template('player.html',
#                              video_path=video_path,
#                              video_url=video_url,
#                              source=source,
#                              history_id=history_id,
#                              transcribed=transcribed,
#                              transcription=transcription)
#     except Exception as e:
#         print(f"播放器页面错误: {str(e)}")
#         return str(e), 500
    
api.add_resource(PlayerResource, '/player/<path:video_path>')

# @app.route('/video/<path:filename>')
# def serve_video(filename):
#     """提供视频文件服务"""
#     try:
#         return send_from_directory(Config.RECORDS_FOLDER, filename)
#     except Exception as e:
#         print(f"视频服务出错: {str(e)}")
#         return str(e), 500
    
api.add_resource(VideoFileResource, '/video/<path:filename>')

# @app.route('/transcribe', methods=['POST'])
# def transcribe():
#     """处理视频转录请求"""
#     try:
#         data = request.json
#         if not data or 'filename' not in data or 'source' not in data:
#             return jsonify({'error': '缺少必要的参数'}), 400
            
#         filename = data['filename']
#         source = data['source']
        
#         # 处理视频转录
#         result = video_service.process_video(filename, source_type=source)
#         if not result:
#             return jsonify({'error': '视频转录失败'}), 500
        
#         return jsonify({
#             'success': True,
#             'message': '转录成功',
#             'transcription': result['transcription']
#         })
        
#     except Exception as e:
#         print(f"处理视频转录时出错: {str(e)}")
#         return jsonify({'error': str(e)}), 500

api.add_resource(TranscribeVideoResource, '/transcribe')
    
api.add_resource(HistoryResource, '/api/history') # 添加 HistoryResource 到 /api/history 路由


    
api.add_resource(RecentHistoryResource, '/api/history/recent')

@app.route('/api/history/<history_id>', methods=['DELETE'])
def delete_history(history_id):
    """删除历史记录"""
    try:
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # 确保必要的目录存在
    Config.init_folders()
    app.run(debug=True)
