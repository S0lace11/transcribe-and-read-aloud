from flask import send_from_directory
from flask_restful import Resource
from config import Config

class VideoFileResource(Resource):
    def get(self, filename):
        """提供视频文件服务"""
        try:
            return send_from_directory(Config.RECORDS_FOLDER, filename)
        except Exception as e:
            print(f"视频服务出错: {str(e)}")
            return str(e), 500