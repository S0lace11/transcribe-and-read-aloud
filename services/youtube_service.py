import sys
import os
import re
from datetime import datetime
import yt_dlp
from config import Config

class VideoDownLoadService:
    """视频下载服务类"""

    def __init__(self):
        """初始化视频下载服务"""
        pass

    def _extract_url(self, text):
        """从文本中提取 URL"""
        match = re.search(r'(https?://[^\s]+)', text)
        if match:
            url = match.group(1)
            return url.rstrip('/?.#')
        return None

    def _sanitize_filename(self, title):
        """处理文件名"""
        title = title[:30].strip()
        title = re.sub(r'[\\/*?:"<>|]', "", title)
        title = re.sub(r'[\n\r\t]', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        title = title.replace(" ", "_")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{title}_{timestamp}.mp4"

    def download_video(self, user_input, task_id=None):
        """下载视频"""
        try:
            url = self._extract_url(user_input)
            if not url:
                raise ValueError("未找到有效的 URL")

            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
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
            return None

if __name__ == "__main__":
    video_download_service = VideoDownLoadService()

    print("视频下载器 (输入 'q' 退出)")
    print("提示：")
    print("1. 此版本使用 yt-dlp，下载更稳定")
    print("2. 自动选择最佳可用格式")
    print("3. 下载完成后自动保存\n")

    while True:
        user_input = input("请输入YouTube或Bilibili视频链接: ")
        if user_input.lower() == 'q':
            break

        result = video_download_service.download_video(user_input)
        if result:
            print(f"\n下载完成：{result['filename']}")
        else:
            print("\n下载失败")