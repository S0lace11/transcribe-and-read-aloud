import dashscope
from http import HTTPStatus
import json
from dotenv import load_dotenv
import os

def test_api_connection():
    # 加载环境变量
    load_dotenv()
    
    # 验证 API KEY 是否正确加载
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("错误: 未找到 API KEY，请检查 .env 文件")
        return False
        
    # 设置 API KEY
    dashscope.api_key = api_key
    
    try:
        # 使用示例音频文件测试
        test_audio_url = 'https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/sensevoice/rich_text_example_1.wav'
        
        # 调用 API
        task_response = dashscope.audio.asr.Transcription.async_call(
            model='sensevoice-v1',
            file_urls=[test_audio_url],
            language_hints=['en'],
        )
        
        # 等待结果
        transcribe_response = dashscope.audio.asr.Transcription.wait(task=task_response.output.task_id)
        
        if transcribe_response.status_code == HTTPStatus.OK:
            print("API 测试成功！")
            print("转写结果：")
            print(json.dumps(transcribe_response.output, indent=4, ensure_ascii=False))
            return True
        else:
            print(f"API 调用失败，状态码：{transcribe_response.status_code}")
            return False
            
    except Exception as e:
        print(f"测试过程中发生错误：{str(e)}")
        return False

if __name__ == "__main__":
    test_api_connection() 