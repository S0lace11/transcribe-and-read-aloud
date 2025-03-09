from flask import request
from flask_restful import Resource

class TranscribeVideoResource(Resource):
    def post(self):
        try:
            data = request.json
            if not data or 'filename' not in data or 'source' not in data:
                return {'error': '缺少必要的参数'}, 400

            filename = data['filename']
            source = data['source']

            from app import video_service  # 延迟导入
            result = video_service.process_video(filename, source_type=source)
            if result:
                # 确保返回的数据是可 JSON 序列化的
                transcription_data = {
                    'sentences': [
                        {
                            'begin_time': sentence.get('begin_time', 0),
                            'end_time': sentence.get('end_time', 0),
                            'text': sentence.get('text', '')
                        }
                        for sentence in result['transcription'].get('sentences', [])
                    ]
                }
                
                return {
                    'success': True,
                    'message': '转录成功',
                    'transcription': transcription_data,
                    'video_url': result.get('video_url', ''),
                    'history_id': result.get('history_id', '')
                }
            else:
                return {'error': '视频转录失败'}, 500

        except Exception as e:
            print(f"处理视频转录时出错: {str(e)}")
            return {'error': str(e)}, 500