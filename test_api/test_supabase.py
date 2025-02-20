import pytest
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的环境变量

# 从环境变量获取 Supabase URL 和 Anon Key
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # 使用 Anon Key


# 使用 pytest.fixture 创建一个 Supabase 客户端实例，供测试函数使用
@pytest.fixture(scope="module")
def supabase_client():
    # 确保 URL 和 Key 已设置
    if not SUPABASE_URL or not SUPABASE_KEY:
        pytest.fail("请设置 SUPABASE_URL 和 SUPABASE_ANON_KEY 环境变量")

    # 创建客户端
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        yield client
    except Exception as e:
        pytest.fail(f"创建 Supabase 客户端失败: {e}")


# 测试连接是否成功
def test_supabase_connection(supabase_client):
    # 尝试执行一个非常简单的查询 (只获取少量数据，提高效率)
    try:
        # 使用 head=True 只获取元数据，不获取实际数据，更快
        response = supabase_client.from_('video_history').select('id').limit(1).execute()
        assert response.data is not None  # 检查是否成功获取到响应 (即使 data 为空列表)
        # 也可以检查 count, 如果你确定表中有数据
        # assert response.count is not None

    except Exception as e:
        pytest.fail(f"连接到 Supabase 失败: {e}")