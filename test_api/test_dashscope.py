import dashscope
from config import Config
from http import HTTPStatus
import json

def test_transcribe(video_url):
    """测试 DashScope 转写功能"""
    try:
        # 设置 API Key
        dashscope.api_key = Config.DASHSCOPE_API_KEY
        
        print(f"开始转写视频: {video_url}")
        
        # 调用转写API
        task_response = dashscope.audio.asr.Transcription.async_call(
            model='sensevoice-v1',
            file_urls=[video_url],
            language_hints=['en'],  # 可以根据需要修改语言
        )
        
        print("等待转写结果...")
        
        # 等待并获取结果
        transcribe_response = dashscope.audio.asr.Transcription.wait(
            task=task_response.output.task_id
        )
        
        if transcribe_response.status_code == HTTPStatus.OK:
            print("转写成功！")
            print("转写结果：")
            print(json.dumps(transcribe_response.output, indent=4, ensure_ascii=False))
            return transcribe_response.output
        else:
            print(f"转写失败，状态码：{transcribe_response.status_code}")
            return None
            
    except Exception as e:
        print(f"转写过程发生错误：{str(e)}")
        return None

if __name__ == "__main__":
    # 使用之前 OSS 上传后得到的 URL
    video_url = "http://video-s0lace.oss-cn-hangzhou.aliyuncs.com/test.mp4?OSSAccessKeyId=LTAI5tEc6zbnoBjrf38rtEPG&Expires=1736066098&Signature=1nQwNJenyFnyKDRoDArKisUXm6U%3D"
    test_transcribe(video_url) 