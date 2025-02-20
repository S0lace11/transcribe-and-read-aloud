import requests

# 你的 Flask 应用的 /upload 路由地址 (根据你的实际情况修改)
upload_url = 'http://127.0.0.1:5000/upload'

# 要上传的本地视频文件路径 (替换成你的实际文件路径)
video_file_path = video_file_path = 'F:/MyProjects/graduate project/tests/test_files/test.mp4'

# 打开文件 (以二进制模式)
with open(video_file_path, 'rb') as video_file:
    # 准备文件上传数据 (multipart/form-data)
    files = {
        'file': (video_file.name, video_file, 'video/mp4') # (filename, file_object, content_type)
    }

    # 发送 POST 请求
    response = requests.post(upload_url, files=files)

    # 检查响应
    print("HTTP Status Code:", response.status_code)
    print("Response Body:", response.text)

    try:
        # 尝试解析 JSON 响应
        response_json = response.json()
        print("Response JSON:", response_json)

        # 如果上传成功，应该能从响应中获取 Supabase 记录的 ID
        if response.status_code == 201:  # 假设上传成功返回 201 Created
            history_id = response_json.get('history_id')
            if history_id:
                print("Supabase 记录 ID:", history_id)
            else:
                print("响应中缺少 history_id")
        else:
            print("上传失败")

    except ValueError:
        print("无法解析 JSON 响应")