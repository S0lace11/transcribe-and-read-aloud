"""
视频服务模块
处理视频文件的上传、转录和OSS存储相关功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import oss2
import dashscope
from config import Config
from http import HTTPStatus
import json
import uuid
from redis import Redis
import time
from moviepy.editor import VideoFileClip
import requests
from datetime import datetime

class VideoService:
    """视频服务类
    提供视频文件的处理、上传和转录功能
    """
    
    def __init__(self):
        """初始化视频服务
        - 初始化OSS服务
        - 初始化DashScope服务
        - 创建必要的文件夹
        """
        self._init_oss()
        self._init_dashscope()
        self._init_redis()
        # 初始化文件夹
        Config.init_folders()
        
    def _init_oss(self):
        """初始化阿里云OSS服务
        - 确保endpoint格式正确
        - 创建Bucket实例
        """
        try:
            # 确保endpoint格式正确
            self.endpoint = Config.OSS_ENDPOINT
            if not self.endpoint.startswith('http'):
                self.endpoint = f'https://{self.endpoint}'
                
            # 创建 Bucket 实例
            auth = oss2.Auth(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET)
            self.bucket = oss2.Bucket(auth, self.endpoint, Config.OSS_BUCKET_NAME)
            
        except Exception as e:
            print(f"OSS 初始化失败: {str(e)}")
            raise
            
    def _init_dashscope(self):
        """初始化DashScope服务
        设置API密钥
        """
        try:
            dashscope.api_key = Config.DASHSCOPE_API_KEY
        except Exception as e:
            print(f"DashScope 初始化失败: {str(e)}")
            raise
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis = Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=10,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis.ping()
            print("Redis连接成功")
        except Exception as e:
            print(f"Redis连接失败: {str(e)}")
            raise
            
    def _get_cache(self, key):
        """获取缓存数据"""
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"获取缓存失败: {str(e)}")
            return None
            
    def _set_cache(self, key, data, expire=None):
        """设置缓存数据"""
        try:
            if expire is None:
                expire = Config.REDIS_CACHE_TTL
                
            self.redis.setex(
                key,
                expire,
                json.dumps(data)
            )
            return True
        except Exception as e:
            print(f"设置缓存失败: {str(e)}")
            return False
            
    def check_video(self, video_path):
        """检查视频文件是否有效且可以处理
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        try:
            if not os.path.exists(video_path):
                return False, "视频文件不存在"
                
            # 检查文件大小
            file_size = os.path.getsize(video_path)
            if file_size > Config.MAX_VIDEO_SIZE:
                return False, f"视频文件过大，最大允许 {Config.MAX_VIDEO_SIZE/(1024*1024)}MB"
                
            # 检查视频时长
            with VideoFileClip(video_path) as video:
                duration = video.duration
                if duration > Config.MAX_VIDEO_DURATION:
                    return False, f"视频时长过长，最大允许 {Config.MAX_VIDEO_DURATION/60}分钟"
                    
            return True, None
            
        except Exception as e:
            return False, f"视频文件检查失败: {str(e)}"

    def upload_to_oss(self, video_path):
        """上传视频到OSS存储
        
        Args:
            video_path: 本地视频文件路径
            
        Returns:
            str: OSS文件访问URL，失败返回None
        """
        try:
            # 生成唯一文件名
            file_extension = os.path.splitext(video_path)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            print(f"开始上传视频到OSS: {os.path.basename(video_path)}")
            
            # 上传文件
            self.bucket.put_object_from_file(unique_filename, video_path)
            
            # 生成文件访问URL（24小时有效）
            url = self.bucket.sign_url('GET', unique_filename, 24*3600)
            
            print(f"视频上传到OSS成功: {url}")
            return url
            
        except Exception as e:
            print(f"视频上传到OSS失败: {str(e)}")
            return None

    def transcribe_video(self, video_url):
        """转写视频音频内容
        
        Args:
            video_url: 视频文件的URL
            
        Returns:
            dict: 转写结果，失败返回None
        """
        try:
            print(f"开始转写视频: {video_url}")
            
            # 调用转写API
            task_response = dashscope.audio.asr.Transcription.async_call(
                model='sensevoice-v1',
                file_urls=[video_url],
                language_hints=['en'],
            )
            print("转写任务创建响应：", json.dumps(task_response.output, indent=2, ensure_ascii=False))
            
            print("等待转写结果...")
            
            # 等待并获取结果
            transcribe_response = dashscope.audio.asr.Transcription.wait(
                task=task_response.output.task_id
            )
            print("转写完成响应：", json.dumps(transcribe_response.output, indent=2, ensure_ascii=False))
            
            if transcribe_response.status_code == HTTPStatus.OK:
                print("转写成功！")
                # 获取转录URL
                transcription_url = transcribe_response.output['results'][0]['transcription_url'] if transcribe_response.output.get('results') and len(transcribe_response.output['results']) > 0 else None
                if not transcription_url:
                    print("未找到转录URL")
                    return None
                    
                # 获取转录内容
                response = requests.get(transcription_url)
                if response.status_code != 200:
                    print(f"获取转录内容失败: {response.status_code}")
                    return None
                    
                transcription_data = response.json()
                # 提取sentences
                if transcription_data.get('transcripts') and len(transcription_data['transcripts']) > 0:
                    return {
                        'sentences': transcription_data['transcripts'][0].get('sentences', [])
                    }
                return None
            else:
                print(f"转写失败，状态码：{transcribe_response.status_code}")
                return None
                
        except Exception as e:
            print(f"转写过程发生错误：{str(e)}")
            return None

    def process_video(self, filename, source_type='upload'):
        """处理视频文件
        
        Args:
            filename: 视频文件名
            source_type: 'upload' 或 'download' 表示视频来源
            
        Returns:
            dict: 处理结果，包含视频URL和转写结果，失败返回None
        """
        try:
            # 1. 检查缓存
            cache_key = f"video:transcription:{filename}"
            cached_result = self._get_cache(cache_key)
            if cached_result:
                print("从缓存获取转录结果")
                return cached_result
                
            # 2. 获取正确的文件路径
            base_folder = Config.UPLOAD_FOLDER if source_type == 'upload' else Config.DOWNLOAD_FOLDER
            video_path = os.path.join(base_folder, filename)
            
            # 检查视频文件
            is_valid, error_msg = self.check_video(video_path)
            if not is_valid:
                print(error_msg)
                return None
            
            # 上传到OSS
            video_url = self.upload_to_oss(video_path)
            if not video_url:
                return None
                
            # 转写视频
            transcription = self.transcribe_video(video_url)
            if not transcription:
                return None
                
            # 3. 构建结果
            result = {
                'video_url': video_url,
                'transcription': transcription,
                'filename': filename
            }
            
            # 4. 保存到缓存
            self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"视频处理失败: {str(e)}")
            return None

    def get_video_info(self, video_path):
        """获取视频文件信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            dict: 视频信息，包含时长、大小、帧率和分辨率
        """
        try:
            with VideoFileClip(video_path) as video:
                return {
                    'duration': video.duration,
                    'size': os.path.getsize(video_path),
                    'fps': video.fps,
                    'resolution': f"{video.size[0]}x{video.size[1]}"
                }
        except Exception as e:
            print(f"获取视频信息失败: {str(e)}")
            return None

    def clear_cache(self, filename):
        """清除指定视频的缓存"""
        try:
            cache_key = f"video:transcription:{filename}"
            self.redis.delete(cache_key)
            return True
        except Exception as e:
            print(f"清除缓存失败: {str(e)}")
            return False
            
    def clear_all_cache(self):
        """清除所有视频转录缓存"""
        try:
            pattern = "video:transcription:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception as e:
            print(f"清除所有缓存失败: {str(e)}")
            return False

    def save_to_history(self, video_data):
        """保存视频到历史记录"""
        try:
            # 生成历史记录ID
            history_id = f"history:{int(time.time())}"
            
            # 准备历史记录数据
            history_data = {
                "id": history_id,
                "title": video_data.get('title', '未命名视频'),
                "source": video_data.get('source', 'upload'),
                "video_path": video_data.get('video_path', ''),
                "duration": video_data.get('duration', '0:00'),
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "transcribed": "0"  # 使用字符串"0"代表False
            }
            
            # 将所有值转换为字符串
            history_data = {k: str(v) for k, v in history_data.items()}
            
            # 保存到Redis
            self.redis.hmset(history_id, history_data)
            # 添加到最近记录列表
            self.redis.zadd('recent_history', {history_id: time.time()})
            
            return history_id
        except Exception as e:
            print(f"保存历史记录失败: {str(e)}")
            return None

    def get_recent_history(self, limit=10):
        """获取最近的历史记录"""
        try:
            # 获取最近的历史记录ID
            history_ids = self.redis.zrevrange('recent_history', 0, limit-1)
            
            # 获取详细信息
            history_list = []
            for history_id in history_ids:
                data = self.redis.hgetall(history_id)
                if data:
                    history_list.append(data)
                    
            return history_list
        except Exception as e:
            print(f"获取历史记录失败: {str(e)}")
            return []

    def delete_history(self, history_id):
        """删除历史记录"""
        try:
            # 获取视频路径
            video_data = self.redis.hgetall(history_id)
            if not video_data:
                return False, "历史记录不存在"
                
            # 从Redis中删除历史记录
            self.redis.delete(history_id)
            # 从最近记录列表中删除
            self.redis.zrem('recent_history', history_id)
            
            return True, "删除成功"
        except Exception as e:
            print(f"删除历史记录失败: {str(e)}")
            return False, str(e)

# 测试代码
if __name__ == "__main__":
    # 创建服务实例
    video_service = VideoService()
    
    # 测试视频处理
    video_path = "F:\\MyProjects\\graduate project\\downloads\\test.mp4"  # 替换为实际的视频路径
    
    if os.path.exists(video_path):
        result = video_service.process_video(video_path)
        if result:
            print("视频处理完成！")
            print("处理结果：")
            print(json.dumps(result, indent=4, ensure_ascii=False))
        else:
            print("视频处理失败！")
    else:
        print(f"错误: 视频文件不存在: {video_path}") 