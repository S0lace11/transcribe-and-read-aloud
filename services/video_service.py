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
import time
from moviepy.editor import VideoFileClip
import requests
from datetime import datetime
import re
from supabase import create_client, Client

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
        self._init_supabase()
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
        
    def format_time(self, seconds):
        """将秒数转换为时分秒格式
    
        Args:
        seconds: 秒数（可以是整数或浮点数）
        
        Returns:
            str: 格式化后的时间字符串 (HH:MM:SS)
        """
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

            video_url = self.upload_to_oss(video_path)
            if not video_url:
                return None

            transcription = self.transcribe_video(video_url)
            if not transcription:
                return None

            # 获取视频信息（用于保存到 Supabase）
            video_info = self.get_video_info(video_path)
            if not video_info:
                video_info = {'duration': '0:00', 'size': 0, 'fps': 0, 'resolution': ''}


            # 格式化转录文本 (与之前一样，但现在将文本保存到 Supabase)
            plain_text = []
            formatted_text = []
            for sentence in transcription.get('sentences', []):
                start_time = self.format_time(sentence.get('begin_time', 0))
                end_time = self.format_time(sentence.get('end_time', 0))
                text = re.sub(r'<\|[^>]+\|>', '', sentence.get('text', '')).strip()

                plain_text.append(text)
                formatted_text.append(f"[{start_time} - {end_time}] {text}")

            plain_text = '\n\n'.join(plain_text) #纯文本
            transcription_text = '\n\n'.join(formatted_text) #带时间戳的文本

            # 准备要插入到 Supabase 的数据, 添加缺少的字段
            supabase_data = {
              'title': filename,
              'source': source_type,
              'video_path': video_url,  # 存储 OSS URL
              'duration': str(video_info['duration']), #转为字符串
              'file_size': video_info['size'],  # 新增：文件大小
              'fps': video_info['fps'],  # 新增：帧率
              'resolution': video_info['resolution'],  # 新增：分辨率
              'created_at': datetime.utcnow().isoformat() + 'Z',  # UTC 时间, ISO 8601 格式
              'transcribed': "1", #直接改为字符串
              'transcription': plain_text,  # 纯文本
              'origin': transcription_text # 原始转录文本（带时间戳）
            }


            # 使用 Supabase 客户端插入数据 或 更新数据
            # 假设你的 Supabase 表名为 'video_records'
            # 先尝试根据 title 和 source 查找是否已有记录
            existing_record = self.supabase.table('video_history') \
                .select('id') \
                .eq('title', filename) \
                .eq('source', source_type) \
                .single() \
                .execute()
            
            if existing_record.data: #如果存在
               # 更新现有记录
               result = self.supabase.table('video_history') \
                   .update(supabase_data) \
                   .eq('id', existing_record.data['id']) \
                   .execute()
               print("Supabase 更新结果:", result)
               history_id = existing_record.data['id']
            else:
                #创建新纪录
                result = self.supabase.table('video_history').insert(supabase_data).execute()
                print("Supabase 插入结果:", result)
                history_id = result.data[0]['id'] if result.data else None


            #检查是否成功插入数据
            if result.data:
              return {
                'transcription': transcription,
                'video_url': video_url,
                'history_id': str(history_id)
              }

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



    def save_to_history(self, video_data):
        """保存视频信息到 Supabase (仅保存本地文件信息，不上传 OSS)"""
        try:
            # 准备要插入到 Supabase 的数据
            supabase_data = {
                'title': video_data.get('title', '未命名视频'),
                'source': video_data.get('source', 'upload'),
                'video_path': video_data.get('video_path', ''),  # 保存本地文件路径
                'duration': video_data.get('duration', '0:00'),
                'created_at': datetime.now().isoformat() + 'Z',
                'transcribed': False,  # 初始状态为未转录
                'transcription': '',
                'origin': ''
            }

            # 使用 Supabase 客户端插入数据
            result = self.supabase.table('video_history').insert(supabase_data).execute()
            print("Supabase 插入结果:", result)

            # 检查是否成功插入数据
            if result.data:
                record_id = result.data[0]['id']
                return str(record_id)  # 返回 Supabase 记录的 ID
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
            # 1. 从 Supabase 删除记录
            # 这里 history_id 是 Supabase 表中的主键 (文本类型)
            delete_result = self.supabase.table('video_history').delete().eq('id', history_id).execute()

            if not delete_result.data:
                print("Supabase 删除失败:", delete_result)
                return False, "删除失败，记录可能不存在或已被删除"

            print("supabase数据已删除")
            return True, "删除成功"

      except Exception as e:
            print(f"从 Supabase 删除历史记录失败: {str(e)}")
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

    def delete_history(self, history_id):
        """从 Supabase 删除历史记录及相关数据，并删除 OSS 上的视频文件"""
        try:
            # 1. 查询 Supabase 记录，获取 video_path (OSS 上的文件名)
            select_result = self.supabase.table('video_history') \
                .select('video_path') \
                .eq('id', history_id) \
                .single() \
                .execute()

            if not select_result.data:
                print("Supabase 记录未找到:", select_result)
                return False, "删除失败，记录可能不存在或已被删除"

            video_path_oss = select_result.data['video_path']  # 获取 OSS 上的完整 URL

            # 2. 从 Supabase 删除记录
            delete_result = self.supabase.table('video_history').delete().eq('id', history_id).execute()

            if not delete_result.data:
                print("Supabase 删除失败:", delete_result)
                return False, "删除失败，记录可能不存在或已被删除"

            # 3. 从 OSS 删除视频文件
            if video_path_oss:
                try:
                    # 从 video_path_oss 中提取文件名
                    #  假设 video_path_oss 的格式是： https://your-bucket.oss-cn-region.aliyuncs.com/your-file-name.mp4
                    filename_oss = video_path_oss.split('/')[-1]  # 获取 URL 中的文件名部分
                    self.bucket.delete_object(filename_oss)  # 使用 OSS 文件名删除
                    print(f"已从 OSS 删除视频文件: {filename_oss}")
                except Exception as e:
                    print(f"从 OSS 删除视频文件失败: {str(e)}")
                    #  这里可以选择是否继续删除 Supabase 记录。
                    #  如果 OSS 文件删除失败，但 Supabase 记录已删除，可能会导致数据不一致。
                    #  一种处理方式是：如果 OSS 删除失败，就回滚 Supabase 的删除操作 (但这需要事务支持，Supabase 免费版不支持事务)
                    #  另一种处理方式是：即使 OSS 删除失败，也继续删除 Supabase 记录，并在日志中记录 OSS 删除失败的情况，稍后手动处理。
                    #  这里选择继续删除 Supabase 记录。
                    return False, f"从 OSS 删除视频文件失败: {str(e)}，但 Supabase 记录已删除"

            print("Supabase 数据已删除")
            return True, "删除成功"

        except Exception as e:
            print(f"从 Supabase 删除历史记录失败: {str(e)}")
            return False, str(e)

