import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(override=True)

class Config:
    # 基础路径配置
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    RECORDS_FOLDER = os.path.join(BASE_DIR, 'records')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')
    
    # 视频文件限制
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_VIDEO_DURATION = 1800  # 30分钟
    ALLOWED_EXTENSIONS = {'mp4'}
    
    # OSS配置
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
    OSS_ENDPOINT = os.getenv('OSS_ENDPOINT')
    OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME')
    
    # DashScope配置
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
    
    # YouTube下载配置
    YOUTUBE_DEFAULT_FORMAT = 'mp4'
    YOUTUBE_DEFAULT_RESOLUTION = '720'
    
    # Redis配置
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = int(os.getenv('REDIS_PORT'))
    REDIS_DB = int(os.getenv('REDIS_DB'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    REDIS_CACHE_TTL = 24 * 60 * 60  # 缓存24小时
    
    # YouTube配置
    YOUTUBE_COOKIES_PATH = os.getenv('YOUTUBE_COOKIES_PATH')
    YOUTUBE_BROWSER = os.getenv('YOUTUBE_BROWSER', 'chrome')
    
    @classmethod
    def init_folders(cls):
        """初始化必要的文件夹"""
        if not os.path.exists(cls.RECORDS_FOLDER):
            os.makedirs(cls.RECORDS_FOLDER)
        
    @classmethod
    def allowed_file(cls, filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in cls.ALLOWED_EXTENSIONS
            
    @classmethod
    def get_video_path(cls, filename, source_type='upload'):
        """获取视频文件路径"""
        base_folder = cls.UPLOAD_FOLDER if source_type == 'upload' else cls.DOWNLOAD_FOLDER
        return os.path.join(base_folder, filename)
        
    @classmethod
    def clean_old_files(cls, max_age_days=7):
        """清理旧文件"""
        import time
        current_time = time.time()
        
        for folder in [cls.UPLOAD_FOLDER, cls.DOWNLOAD_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                # 如果文件超过指定天数
                if os.path.isfile(file_path) and \
                   current_time - os.path.getmtime(file_path) > max_age_days * 86400:
                    try:
                        os.remove(file_path)
                        print(f"已删除旧文件: {file_path}")
                    except Exception as e:
                        print(f"删除文件失败 {file_path}: {str(e)}") 