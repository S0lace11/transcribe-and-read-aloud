import oss2
from dotenv import load_dotenv
import os
from moviepy.editor import VideoFileClip
import uuid

def process_video(video_path):
    """处理视频文件：上传到OSS并返回URL"""
    try:
        # 直接上传视频文件到OSS
        video_url = upload_to_oss(video_path)
        if not video_url:
            raise Exception("视频上传失败")
            
        return video_url
        
    except Exception as e:
        print(f"处理视频失败：{str(e)}")
        return None

def upload_to_oss(local_file_path):
    """上传文件到OSS并返回可访问的URL"""
    # 加载环境变量
    load_dotenv()
    
    # 从环境变量获取 OSS 配置
    access_key_id = os.getenv('OSS_ACCESS_KEY_ID')
    access_key_secret = os.getenv('OSS_ACCESS_KEY_SECRET')
    endpoint = os.getenv('OSS_ENDPOINT')
    bucket_name = os.getenv('OSS_BUCKET_NAME')
    
    if not all([access_key_id, access_key_secret, endpoint, bucket_name]):
        raise ValueError("OSS 配置信息不完整，请检查 .env 文件")
    
    # 创建 Bucket 实例
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    
    # 生成唯一的文件名（使用UUID避免重名）
    file_extension = os.path.splitext(local_file_path)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    try:
        # 上传文件
        bucket.put_object_from_file(unique_filename, local_file_path)
        
        # 生成文件的公网访问URL（默认有效期24小时）
        url = bucket.sign_url('GET', unique_filename, 24*3600)
        
        print(f"文件上传成功：{url}")
        return url
        
    except Exception as e:
        print(f"上传文件失败：{str(e)}")
        return None

# 使用示例
if __name__ == "__main__":
    video_path = "path/to/your/video.mp4"  # 替换为你的视频文件路径
    video_url = process_video(video_path)
    if video_url:
        print(f"视频处理成功，URL: {video_url}") 