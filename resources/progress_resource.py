from flask import Response
from flask_restful import Resource
import json

class ProgressResource(Resource):
    def get(self, task_id):
        def generate():
            from app import youtube_service  # 延迟导入
            progress_queue = youtube_service.get_progress_queue(task_id)
            if not progress_queue:
                yield f"data: {json.dumps({'error': '任务不存在'})}\n\n"
                return

            try:
                while True:
                    progress = progress_queue.get()
                    if progress is None:
                        break
                    yield f"data: {json.dumps(progress)}\n\n"
            finally:
                youtube_service.remove_progress_queue(task_id)

        return Response(generate(), mimetype='text/event-stream')