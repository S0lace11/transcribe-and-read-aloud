import sys
import os
import re
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yt_dlp
from config import Config
import queue
import time

class VideoService:
    """视频下载服务类"""

    def __init__(self):
        """初始化视频下载服务"""
        self.progress_queues = {}

    def _extract_url(self, text):
        """从文本中提取 URL"""
        match = re.search(r'(https?://[^\s]+)', text)
        if match:
            url = match.group(1)
            return url.rstrip('/?.#')
        return None

    def _format_size(self, bytes_size):
        """格式化文件大小"""
        if bytes_size is None:
            return "未知"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f}{unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f}TB"

    def _sanitize_filename(self, title):
        """处理文件名"""
        title = title[:30].strip()
        title = re.sub(r'[\\/*?:"<>|]', "", title)
        title = re.sub(r'[\n\r\t]', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        title = title.replace(" ", "_")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{title}_{timestamp}.mp4"

    def _create_progress_hook(self, task_id):
        """创建下载进度回调函数"""
        progress_queue = self.progress_queues.get(task_id)
        if not progress_queue:
            return None

        def progress_hook(d):
            """下载进度回调"""
            if d['status'] == 'downloading':
                percent = d.get('percent')
                if percent is None:
                    percent = 0

                progress = {
                    'status': 'downloading',
                    'downloaded': self._format_size(d.get('downloaded_bytes', 0)),
                    'total': self._format_size(d.get('total_bytes') or d.get('total_bytes_estimate')),
                    'speed': self._format_size(d.get('speed', 0)) + '/s',
                    'eta': str(d.get('eta', '未知')),
                    'progress': percent
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

    def download_video(self, user_input, task_id):
        """下载视频"""
        try:
            url = self._extract_url(user_input)
            if not url:
                raise ValueError("未找到有效的 URL")

            self.progress_queues[task_id] = queue.Queue()

            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'progress_hooks': [self._create_progress_hook(task_id)],
                'retries': 10,
                'fragment_retries': 10,
                'retry-sleep': '5-10',
            }
            

            if "youtube.com" in url or "youtu.be" in url:
                if Config.YOUTUBE_COOKIES_PATH:
                    ydl_opts['cookiefile'] = Config.YOUTUBE_COOKIES_PATH
                elif Config.YOUTUBE_BROWSER:
                    ydl_opts['cookiesfrombrowser'] = (Config.YOUTUBE_BROWSER,)

            elif "bilibili.com" in url:
                if Config.BILIBILI_COOKIES_PATH:
                    ydl_opts['cookiefile'] = Config.BILIBILI_COOKIES_PATH

            else:
                raise ValueError("不支持的视频 URL")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(url, download=False)
                if not video_info:
                    raise Exception("无法获取视频信息")

                safe_filename = self._sanitize_filename(video_info.get('title', 'video'))
                filepath = os.path.join(Config.RECORDS_FOLDER, safe_filename)
                ydl_opts['outtmpl'] = filepath

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                        ydl_download.download([url])
                except Exception as e:
                    print(f"下载过程中发生错误: {str(e)}")
                    # 删除部分下载的文件
                    if os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                            print(f"已删除部分下载的文件: {filepath}")
                        except OSError as remove_err:
                            print(f"删除文件时出错: {remove_err}")
                    raise

                return {
                    'title': video_info.get('title', '视频'),
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
            if task_id in self.progress_queues:
                self.progress_queues[task_id].put(None)

    def get_progress_queue(self, task_id):
        """获取进度队列"""
        return self.progress_queues.get(task_id)

    def remove_progress_queue(self, task_id):
        """移除进度队列"""
        if task_id in self.progress_queues:
            del self.progress_queues[task_id]

if __name__ == "__main__":
    video_service = VideoService()

    print("视频下载器 (输入 'q' 退出)")
    print("提示：")
    print("1. 此版本使用 yt-dlp，下载更稳定")
    print("2. 自动选择最佳可用格式")
    print("3. 显示实时下载速度和剩余时间\n")

    while True:
        user_input = input("请输入YouTube或Bilibili视频链接: ")
        if user_input.lower() == 'q':
            break

        task_id = str(int(time.time()))
        result = video_service.download_video(user_input, task_id)

        progress_queue = video_service.get_progress_queue(task_id)
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
                    print(f"\r进度: {progress.get('progress'):.1f}%  "
                          f"已下载: {progress.get('downloaded')} / {progress.get('total')}  "
                          f"速度: {progress.get('speed')}  剩余时间: {progress.get('eta')}", end="")
                    sys.stdout.flush()
