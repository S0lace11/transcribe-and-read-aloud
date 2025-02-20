from flask import Flask, render_template
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
api.add_resource(PlayerResource, '/player/<path:video_path>')

api.add_resource(VideoFileResource, '/video/<path:filename>')
api.add_resource(TranscribeVideoResource, '/transcribe')
api.add_resource(HistoryResource, '/api/history') # 添加 HistoryResource 到 /api/history 路由
    
api.add_resource(RecentHistoryResource, '/api/history/recent')
api.add_resource(HistoryDetailResource, '/api/history/<history_id>')

if __name__ == '__main__':
    # 确保必要的目录存在
    Config.init_folders()
    app.run(debug=True)
