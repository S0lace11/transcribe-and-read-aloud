from flask_restful import Resource
from flask import jsonify

class ProgressResource(Resource):
    def get(self, task_id):
        from app import VideoDownloadService
        progress = VideoDownloadService.get_progress(task_id)
        return jsonify(progress)