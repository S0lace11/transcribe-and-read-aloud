from flask_restful import Resource
from flask import jsonify

class ProgressResource(Resource):
    def get(self, task_id):
        from app import video_download_service
        progress = video_download_service.get_progress(task_id)
        return jsonify(progress)