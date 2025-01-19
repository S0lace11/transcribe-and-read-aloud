from redis import Redis
from config import Config
from dotenv import load_dotenv
import os

def test_redis_connection():
    try:
        # 确保环境变量已加载
        load_dotenv(override=True)
        
        # 打印环境变量值进行检查
        print("环境变量检查:")
        print(f"REDIS_HOST: {os.getenv('REDIS_HOST')}")
        print(f"REDIS_PORT: {os.getenv('REDIS_PORT')}")
        print(f"REDIS_PASSWORD: {os.getenv('REDIS_PASSWORD')}")
        
        # 打印配置值
        print("\nConfig值检查:")
        print(f"Config.REDIS_HOST: {Config.REDIS_HOST}")
        print(f"Config.REDIS_PORT: {Config.REDIS_PORT}")
        print(f"Config.REDIS_PASSWORD: {Config.REDIS_PASSWORD}")
        
        # 创建Redis连接
        redis_client = Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            password=Config.REDIS_PASSWORD,
            decode_responses=True
        )
        
        # 测试连接
        redis_client.ping()
        print("\nRedis连接成功！")
        return True
        
    except Exception as e:
        print(f"\nRedis连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_redis_connection() 