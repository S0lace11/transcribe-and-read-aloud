# For prerequisites running the following sample, visit https://help.aliyun.com/document_detail/611472.html

from http import HTTPStatus
import dashscope
import json

# 如您未将API Key配置到环境变量中，可带上下面这行代码并将your-dashscope-api-key替换成您自己的API Key
dashscope.api_key = 'sk-xxxxxx'

task_response = dashscope.audio.asr.Transcription.async_call(
    model='sensevoice-v1',
    file_urls=['https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/sensevoice/rich_text_example_1.wav'],
    language_hints=['en'],
)

transcribe_response = dashscope.audio.asr.Transcription.wait(task=task_response.output.task_id)
if transcribe_response.status_code == HTTPStatus.OK:
    print(json.dumps(transcribe_response.output, indent=4, ensure_ascii=False))
    print('transcription done!')