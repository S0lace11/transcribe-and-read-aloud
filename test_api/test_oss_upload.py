import oss2
from config import Config
import os

def test_oss_upload(test_file_path):
    """测试 OSS 上传功能"""
    try:
        # 使用 Config 中的配置创建 Bucket 实例
        auth = oss2.Auth(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, Config.OSS_ENDPOINT, Config.OSS_BUCKET_NAME)
        
        # 获取测试文件名
        test_file_name = os.path.basename(test_file_path)
        
        print(f"开始上传文件: {test_file_name}")
        
        # 上传文件
        bucket.put_object_from_file(test_file_name, test_file_path)
        
        # 生成文件访问URL（1小时有效）
        url = bucket.sign_url('GET', test_file_name, 3600)
        
        print(f"文件上传成功！")
        print(f"文件访问URL: {url}")
        print(f"URL有效期: 1小时")
        
        return True
        
    except oss2.exceptions.OssError as e:
        print(f"OSS错误: {str(e)}")
        print("请检查你的认证信息和网络连接")
        return False
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    # 将这里的路径改为你实际的文件路径
    test_file = "F:\\MyProjects\\graduate project\\downloads\\test.mp4"
    
    if os.path.exists(test_file):
        print("开始测试 OSS 上传...")
        test_oss_upload(test_file)
    else:
        print(f"错误: 测试文件不存在: {test_file}") 