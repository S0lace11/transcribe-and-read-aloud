from flask import Flask, render_template, request, jsonify, send_from_directory, Response, redirect, send_file
from services.video_service import VideoService
from services.youtube_service import YouTubeService
from config import Config
import os
import uuid
import time
import json
import threading
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
video_service = VideoService()
youtube_service = YouTubeService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def process_upload():
    """处理上传的视频文件，只保存到本地"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
            
        video_file = request.files['file']
        if video_file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
            
        # 检查文件类型
        if not video_file.filename.lower().endswith('.mp4'):
            return jsonify({'error': '只支持MP4格式的视频'}), 400
            
        # 直接使用原始文件名，但确保安全
        filename = secure_filename(video_file.filename)
        file_path = os.path.join(Config.RECORDS_FOLDER, filename)
        
        # 如果文件已存在，添加数字后缀
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{base}_{counter}{ext}"
            file_path = os.path.join(Config.RECORDS_FOLDER, filename)
            counter += 1
        
        video_file.save(file_path)
        print(f"文件已保存到: {file_path}")
        
        # 保存到历史记录
        video_data = {
            'title': filename,
            'source': 'upload',
            'video_path': filename,
            'duration': '0:00',  # 这里先设置默认值，后续可以通过视频元数据更新
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        history_id = video_service.save_to_history(video_data)
        
        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'title': filename,
            'history_id': history_id
        })
        
    except Exception as e:
        print(f"处理上传视频时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download_youtube():
    """处理YouTube视频下载，保存到records文件夹并记录历史"""
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'error': '请提供YouTube视频链接'}), 400
            
        # 生成任务ID
        task_id = str(int(time.time()))
        
        # 在新线程中启动下载
        def download_and_save_history():
            try:
                # 下载视频
                video_info = youtube_service.download_video(url, task_id)
                
                if video_info:
                    # 保存到历史记录
                    video_data = {
                        'title': video_info['title'],
                        'source': 'youtube',
                        'video_path': video_info['filename'],
                        'duration': video_info['duration'],
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    video_service.save_to_history(video_data)
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

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """获取YouTube下载进度"""
    def generate():
        progress_queue = youtube_service.get_progress_queue(task_id)
        if not progress_queue:
            yield f"data: {json.dumps({'error': '任务不存在'})}\n\n"
            return
            
        try:
            while True:
                progress = progress_queue.get()
                if progress is None:  # 下载完成
                    break
                yield f"data: {json.dumps(progress)}\n\n"
        finally:
            youtube_service.remove_progress_queue(task_id)
            
    return Response(generate(), mimetype='text/event-stream')

@app.route('/player/<path:video_path>')
def player(video_path):
    """视频播放页面"""
    try:
        source = request.args.get('source', 'upload')
        # 检查文件是否存在
        video_file_path = os.path.join(Config.RECORDS_FOLDER, video_path)
        if not os.path.exists(video_file_path):
            return "视频文件不存在", 404
            
        # 构建视频URL
        video_url = f'/video/{video_path}'
        
        return render_template('player.html', 
                             video_path=video_path,
                             video_url=video_url,
                             source=source)
    except Exception as e:
        print(f"播放器页面错误: {str(e)}")
        return str(e), 500

@app.route('/video/<path:filename>')
def serve_video(filename):
    """提供视频文件服务"""
    try:
        return send_from_directory(Config.RECORDS_FOLDER, filename)
    except Exception as e:
        print(f"视频服务出错: {str(e)}")
        return str(e), 500

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """处理视频转录请求"""
    try:
        data = request.json
        if not data or 'filename' not in data or 'source' not in data:
            return jsonify({'error': '缺少必要的参数'}), 400
            
        filename = data['filename']
        source = data['source']
        
        # 处理视频转录
        result = video_service.process_video(filename, source_type=source)
        if not result:
            return jsonify({'error': '视频转录失败'}), 500
        
        return jsonify({
            'success': True,
            'message': '转录成功',
            'transcription': result['transcription']
        })
        
    except Exception as e:
        print(f"处理视频转录时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取历史记录列表
        start = (page - 1) * per_page
        end = start + per_page - 1
        
        # 获取ID列表
        video_ids = video_service.redis.zrevrange("history:list", start, end)
        
        # 获取详细信息
        history_list = []
        for video_id in video_ids:
            details = video_service.redis.hgetall(f"history:detail:{video_id}")
            if details:
                details['id'] = video_id
                history_list.append(details)
        
        return jsonify({
            'items': history_list,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/recent')
def get_recent_history():
    """获取最近的历史记录"""
    try:
        # 获取最近10条历史记录
        history_list = video_service.get_recent_history(limit=10)
        
        return jsonify({
            'success': True,
            'history': history_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
