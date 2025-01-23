"""
YouTube视频下载服务模块
处理YouTube视频的下载和进度跟踪
"""

import sys
import os
import re  # 添加 re 模块导入
from datetime import datetime  # 添加 datetime 导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yt_dlp
from config import Config
import queue
import time

class YouTubeService:
    """YouTube视频下载服务类
    提供YouTube视频下载和进度跟踪功能
    """
    
    def __init__(self):
        """
        初始化YouTube下载服务
        创建进度队列字典，用于存储不同下载任务的进度信息
        """
        self.progress_queues = {}
        
    def _format_size(self, bytes):
        """格式化文件大小
        
        Args:
            bytes: 字节数
            
        Returns:
            str: 格式化后的大小字符串（如：1.5MB）
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024
        return f"{bytes:.1f}GB"
        
    def _sanitize_filename(self, title):
        """处理文件名，使其安全且易读
        
        Args:
            title: 原始标题
            
        Returns:
            str: 处理后的文件名
        """
        # 截取前30个字符
        title = title[:30].strip()
        
        # 移除特殊字符，只保留字母、数字、空格和中文字符
        title = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)
        
        # 将空格替换为下划线
        title = title.replace(' ', '_')
        
        # 添加时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"{title}_{timestamp}.mp4"
        
    def _create_progress_hook(self, task_id):
        """创建下载进度回调函数
        
        Args:
            task_id: 下载任务ID
            
        Returns:
            function: 进度回调函数
        """
        progress_queue = self.progress_queues.get(task_id)
        if not progress_queue:
            return None
            
        def progress_hook(d):
            """下载进度回调
            处理下载状态更新，包括下载进度、速度等信息
            """
            if d['status'] == 'downloading':
                progress = {
                    'status': 'downloading',
                    'downloaded': self._format_size(d.get('downloaded_bytes', 0)),
                    'total': self._format_size(d.get('total_bytes', 0)),
                    'speed': self._format_size(d.get('speed', 0)) + '/s',
                    'eta': str(d.get('eta', '未知')),
                    'progress': d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100 if d.get('total_bytes') else 0
                }
                progress_queue.put(progress)
            elif d['status'] == 'finished':
                video_path = d.get('filename', '').replace('\\', '/')
                filename = os.path.basename(video_path)
                progress_queue.put({
                    'status': 'completed',
                    'video_path': filename
                })
                
        return progress_hook
        
    def download_video(self, url, task_id):
        """下载YouTube视频
        
        Args:
            url: YouTube视频URL
            task_id: 下载任务ID
            
        Note:
            下载进度通过progress_queue通知调用者
        """
        try:
            # 创建进度队列
            self.progress_queues[task_id] = queue.Queue()
            
            # 基础下载选项
            ydl_opts = {
                'format': 'mp4',
                'progress_hooks': [self._create_progress_hook(task_id)],
            }
            
            # 添加cookies配置
            if Config.YOUTUBE_COOKIES_PATH:
                ydl_opts['cookiefile'] = Config.YOUTUBE_COOKIES_PATH
            elif Config.YOUTUBE_BROWSER:
                ydl_opts['cookiesfrombrowser'] = (Config.YOUTUBE_BROWSER,)
            
            # 先获取视频信息
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(url, download=False)
                if not video_info:
                    raise Exception("无法获取视频信息")
                
                # 生成安全的文件名
                safe_filename = self._sanitize_filename(video_info.get('title', 'video'))
                
                # 更新下载选项，设置输出路径
                ydl_opts['outtmpl'] = os.path.join(Config.RECORDS_FOLDER, safe_filename)
                
                # 使用更新后的选项下载视频
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                    ydl_download.download([url])
                
                return {
                    'title': video_info.get('title', 'YouTube视频'),
                    'filename': safe_filename,
                    'duration': video_info.get('duration', 0)
                }
                
        except Exception as e:
            print(f"下载视频失败: {str(e)}")
            if task_id in self.progress_queues:
                self.progress_queues[task_id].put({
                    'status': 'error',
                    'message': str(e)
                })
            return None
        finally:
            # 结束进度队列
            if task_id in self.progress_queues:
                self.progress_queues[task_id].put(None)
                
    def get_progress_queue(self, task_id):
        """获取指定任务的进度队列
        
        Args:
            task_id: 下载任务ID
            
        Returns:
            Queue: 进度队列对象
        """
        return self.progress_queues.get(task_id)
        
    def remove_progress_queue(self, task_id):
        """移除指定任务的进度队列
        
        Args:
            task_id: 下载任务ID
        """
        if task_id in self.progress_queues:
            del self.progress_queues[task_id]

if __name__ == "__main__":
    # 测试代码
    youtube_service = YouTubeService()
    
    print("YouTube视频下载器 (输入 'q' 退出)")
    print("提示：")
    print("1. 此版本使用 yt-dlp，下载更稳定")
    print("2. 自动选择720p或最接近的分辨率")
    print("3. 显示实时下载速度和剩余时间\n")
    
    while True:
        video_url = input("请输入YouTube视频链接: ")
        if video_url.lower() == 'q':
            break
            
        # 尝试修正常见的YouTube短链接
        if 'youtu.be' in video_url:
            video_id = video_url.split('/')[-1].split('?')[0]
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            
        task_id = str(int(time.time()))
        result = youtube_service.download_video(video_url, task_id)
        
        # 显示下载进度
        progress_queue = youtube_service.get_progress_queue(task_id)
        if progress_queue:
            while True:
                progress = progress_queue.get()
                if progress is None:
                    break
                if progress.get('status') == 'error':
                    print(f"\n{progress['message']}")
                    break
                elif progress.get('status') == 'completed':
                    print(f"\n下载完成：{progress.get('video_path')}")
                    break
                else:
                    print(f"\r{progress.get('message', '')}", end="")
