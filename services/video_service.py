import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import oss2
import dashscope
from config import Config
from http import HTTPStatus
import json
import uuid
# from redis import Redis  # 移除 Redis 导入
import time
from moviepy.editor import VideoFileClip
import requests
from datetime import datetime, timezone # 导入 timezone
import re
from supabase import create_client, Client  # 导入 Supabase 客户端


class VideoService:

    def __init__(self):
        """初始化视频服务
        - 初始化OSS服务
        - 初始化DashScope服务
        - 初始化 Supabase
        - 创建必要的文件夹
        """
        self._init_oss()
        self._init_dashscope()
        self._init_supabase()  # 初始化 Supabase
        # 初始化文件夹
        Config.init_folders()

    def _init_oss(self):
        """初始化阿里云OSS服务"""
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
        """初始化DashScope服务"""
        try:
            dashscope.api_key = Config.DASHSCOPE_API_KEY
        except Exception as e:
            print(f"DashScope 初始化失败: {str(e)}")
            raise

    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        try:
            # 从配置中获取 Supabase URL 和 API 密钥
            supabase_url: str = Config.SUPABASE_URL
            supabase_key: str = Config.SUPABASE_KEY

            # 创建 Supabase 客户端实例
            self.supabase: Client = create_client(supabase_url, supabase_key)
            print("Supabase 初始化成功")

        except Exception as e:
            print(f"Supabase 初始化失败: {str(e)}")
            raise

    #  移除 _build_history_key 和 _get_recent_history_key 方法，因为不再需要 Redis key

    def check_video(self, video_path):
        """检查视频文件是否有效且可以处理"""
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
        """上传视频到OSS存储"""
        try:
            # 生成唯一文件名
            file_extension = os.path.splitext(video_path)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            print(f"开始上传视频到OSS: {os.path.basename(video_path)}")
            
            # 设置文件元数据，包含原始文件名
            headers = {
                'x-oss-meta-original-name': os.path.basename(video_path)
            }
            
            # 上传文件
            self.bucket.put_object_from_file(
                unique_filename, 
                video_path,
                headers=headers
            )
            
            # 生成文件访问URL（24小时有效）
            url = self.bucket.sign_url('GET', unique_filename, 24*3600)
            
            print(f"视频上传到OSS成功: {url}")
            return url
            
        except Exception as e:
            print(f"视频上传到OSS失败: {str(e)}")
            return None

    def transcribe_video(self, video_url):
        """转写视频音频内容"""
        try:
            print(f"开始转写视频: {video_url}")

            # 调用转写API
            task_response = dashscope.audio.asr.Transcription.async_call(
                model='sensevoice-v1',
                file_urls=[video_url],
                language_hints=['en'],  # 添加 language_hints 参数
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
                transcription_url = transcribe_response.output['results'][0]['transcription_url'] if \
                transcribe_response.output.get('results') and len(transcribe_response.output['results']) > 0 else None
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
                print("详细错误信息：", json.dumps(transcribe_response.output, indent=2, ensure_ascii=False))  # 打印详细错误
                return None

        except Exception as e:
            print(f"转写过程发生错误：{str(e)}")
            return None

    def format_time(self, seconds):
        """将秒数转换为时分秒格式"""
        try:
            # 确保输入是数字
            seconds = float(seconds)

            # 计算小时、分钟和秒
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = int(seconds % 60)

            # 如果有小时，返回 HH:MM:SS 格式
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            # 否则返回 MM:SS 格式
            else:
                return f"{minutes:02d}:{seconds:02d}"

        except (ValueError, TypeError) as e:
            print(f"时间格式化失败: {str(e)}")
            return "00:00"
    def process_video(self, filename, source_type='upload'):
        """处理视频文件，上传到OSS，转录，并将结果保存到 Supabase"""
        try:
            video_path = os.path.join(Config.RECORDS_FOLDER, filename)
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

            # 获取视频信息（用于保存到 Supabase）
            video_info = self.get_video_info(video_path)
            if not video_info:
                video_info = {'duration': '0:00', 'size': 0, 'fps': 0, 'resolution': ''}

            # 格式化转录文本
            plain_text = []
            formatted_text = []
            for sentence in transcription.get('sentences', []):
                start_time = self.format_time(sentence.get('begin_time', 0))
                end_time = self.format_time(sentence.get('end_time', 0))
                text = re.sub(r'<\|[^>]+\|>', '', sentence.get('text', '')).strip()

                plain_text.append(text)
                formatted_text.append(f"[{start_time} - {end_time}] {text}")

            plain_text = '\n\n'.join(plain_text)
            transcription_text = '\n\n'.join(formatted_text)

            # 查找并更新 Supabase 记录
            existing_record = self.supabase.table('video_history') \
                .select('*') \
                .eq('title', filename) \
                .eq('source', source_type) \
                .single() \
                .execute()

            # 准备要更新的数据 - 保持原来的 video_path
            supabase_data = {
                'duration': str(video_info['duration']),
                'file_size': video_info['size'],
                'fps': video_info['fps'],
                'resolution': video_info['resolution'],
                'transcribed': "1",
                'transcription': plain_text,
                'origin': transcription_text,
                'video_url': video_url  # 添加 OSS URL
            }

            if existing_record.data:
                # 更新现有记录
                result = self.supabase.table('video_history') \
                    .update(supabase_data) \
                    .eq('id', existing_record.data['id']) \
                    .execute()
                history_id = existing_record.data['id']
            else:
                # 如果记录不存在，添加必要的字段创建新记录
                supabase_data.update({
                    'title': filename,
                    'source': source_type,
                    'video_path': filename,  # 使用原始文件名
                    'created_at': datetime.utcnow().isoformat() + 'Z',
                })
                result = self.supabase.table('video_history').insert(supabase_data).execute()
                history_id = result.data[0]['id'] if result.data else None

            return {
                'transcription': transcription,
                'video_url': video_url,
                'history_id': str(history_id)
            }

        except Exception as e:
            print(f"视频处理失败: {str(e)}")
            return None

    def get_video_info(self, video_path):
        """获取视频文件信息"""
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

    def save_to_history(self, video_data):
      """保存视频信息到 Supabase"""
      try:
            # 准备要插入到 Supabase 的数据, 添加缺少的字段
            supabase_data = {
              'title': video_data.get('title', '未命名视频'),
              'source': video_data.get('source', 'upload'),
              'video_path': video_data.get('video_path', ''),
              'duration': video_data.get('duration', '0:00'),
              'created_at': datetime.utcnow().isoformat() + 'Z',
              'transcribed': '0',
              'transcription': '',
              'origin': ''
            }

            # 使用 Supabase 客户端插入数据
            result = self.supabase.table('video_history').insert(supabase_data).execute()
            print("Supabase 插入结果:", result)

            # 检查是否成功插入数据, 并返回 Supabase 记录的 ID
            if result.data:
                record_id = result.data[0]['id']
                return str(record_id)
            else:
                print("Supabase 插入失败:", result)
                return None

      except Exception as e:
        print(f"保存历史记录到 Supabase 失败: {str(e)}")
        return None

    def get_recent_history(self, limit=10):
      """从 Supabase 获取最近的历史记录"""
      try:
        # 从 Supabase 查询最近的记录，按 created_at 字段降序排列
        result = self.supabase.table('video_history') \
            .select('*') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        if result.data:
            return result.data  # 返回 Supabase 查询结果
        else:
            print("获取最近历史记录失败:", result)
            return []

      except Exception as e:
        print(f"从 Supabase 获取历史记录失败: {str(e)}")
        return []

    def delete_history(self, history_id):
      """从 Supabase 删除历史记录及相关数据"""
      try:
            # 1. 从 Supabase 获取记录信息
            result = self.supabase.table('video_history') \
                .select('*') \
                .eq('id', history_id) \
                .single() \
                .execute()

            if not result.data:
                return False, "记录不存在"

            history_data = result.data
            
            # 2. 删除本地文件
            video_path = os.path.join(Config.RECORDS_FOLDER, history_data.get('video_path', ''))
            if os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    print(f"已删除本地文件: {video_path}")
                except Exception as e:
                    print(f"删除本地文件失败: {str(e)}")

            # 3. 删除OSS文件
            if history_data.get('video_url'):
                try:
                    # 从 URL 中提取 OSS 对象名
                    oss_url = history_data['video_url']
                    # OSS URL 格式: https://bucket.endpoint/object_key?params
                    object_key = oss_url.split('?')[0].split('/')[-1]
                    
                    if object_key:
                        try:
                            self.bucket.delete_object(object_key)
                            print(f"已删除OSS文件: {object_key}")
                        except Exception as e:
                            print(f"删除OSS文件失败: {str(e)}")
                except Exception as e:
                    print(f"处理OSS文件删除失败: {str(e)}")

            # 4. 从 Supabase 删除记录
            delete_result = self.supabase.table('video_history') \
                .delete() \
                .eq('id', history_id) \
                .execute()

            if not delete_result.data:
                print("Supabase 删除失败:", delete_result)
                return False, "删除失败，记录可能不存在或已被删除"

            print("所有相关数据已删除")
            return True, "删除成功"

      except Exception as e:
            print(f"删除历史记录失败: {str(e)}")
            return False, str(e)
    
    def get_history_detail(self, history_id):
      """根据 Supabase 中的 ID 获取视频记录详情"""
      try:
          # 从 Supabase 查询单个记录
          result = self.supabase.table('video_history') \
              .select('*') \
              .eq('id', history_id) \
              .single() \
              .execute()

          if result.data:
              return result.data  # 返回 Supabase 查询结果
          else:
              print("历史记录未找到:", result)  # Supabase 错误信息更详细
              return None

      except Exception as e:
          print(f"从 Supabase 获取历史记录详情失败: {str(e)}")
          return None