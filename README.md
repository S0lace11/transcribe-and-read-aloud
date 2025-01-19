# 视频文本同步工具

一个基于 Flask 的 Web 应用，可以将视频内容转换为文本，并实现视频播放与文本实时同步高亮显示。

## 核心功能

### 1. 视频输入
- 支持 YouTube 链接输入
- 支持本地 MP4 文件上传

### 2. 语音转文字
- 调用 SenseVoice API 进行语音识别
- 生成带时间戳的文本内容

### 3. 视频文本同步
- 视频播放时文本实时高亮
- 根据音频进度自动滚动文本
- 点击文本片段可跳转到视频相应位置

### 4. 历史记录
- 记录用户的视频处理历史
- 支持按时间顺序查看历史记录
- 提供快速访问之前处理过的视频
- 历史记录包含：
  - 视频标题和来源（上传/YouTube）
  - 处理时间
  - 视频时长和大小
  - 转写文本预览
  - 一键重新播放功能

## 用户使用流程

### 1. 主界面
- 显示所有历史记录（按时间倒序排列）
- 提供视频处理入口：
  - 上传本地视频
  - 下载YouTube视频
- 历史记录展示内容：
  - 视频标题
  - 来源（本地上传/YouTube）
  - 处理时间
  - 视频时长
  - 转录状态（未转录/已转录）
  - 操作按钮（播放/转录）

### 2. 视频下载流程
1. 用户输入YouTube链接
2. 点击下载按钮
3. 系统下载视频到downloads文件夹
4. 在历史记录中显示下载的视频
5. 用户可选择是否进行转录
6. 转录完成后更新历史记录状态

### 3. 视频上传流程
1. 用户选择本地视频文件
2. 系统将视频保存到uploads文件夹
3. 在历史记录中显示上传的视频
4. 用户可选择是否进行转录
5. 转录完成后更新历史记录状态

### 4. 历史记录管理
- 支持查看所有处理过的视频
- 可以重新播放任意历史视频
- 未转录的视频可以启动转录
- 已转录的视频可以直接查看文本
- 支持删除历史记录
- 支持导出历史记录

## 技术栈

### 后端
- Flask (Python Web 框架)
- Redis (数据存储与缓存)
  - 存储历史记录
  - 缓存转录结果
  - 支持多用户数据隔离
- OSS (对象存储)
- DashScope (语音转写)

### 存储方案设计

#### 1. Redis 键值设计
- 转录结果缓存：`video:transcription:{filename}`
- 用户历史记录：`user:{user_id}:history:page:{page}`
- 最近处理记录：`user:{user_id}:recent:{limit}`

#### 2. 数据结构
- 历史记录存储格式：
  ```json
  {
    "title": "视频标题",
    "source": "upload/youtube",
    "video_path": "存储路径",
    "duration": "视频时长",
    "text_preview": "转写文本预览",
    "created_at": "处理时间"
  }
  ```

#### 3. 主要功能
- 多用户数据隔离
- 自动过期清理
- 分页加载支持
- 按时间排序

### 前端
- HTML5 (视频播放器)
- CSS3 (样式和动画)
- JavaScript (视频文本同步)

## 项目结构
graduate_project/ # 项目根目录
│
├── app.py # Flask主应用程序
│ ├── process_upload() # 处理上传视频
│ ├── process_youtube() # 处理YouTube视频
│ ├── get_progress() # 获取下载进度
│ ├── serve_video() # 提供视频文件服务
│ └── get_history() # 获取历史记录
│
├── config.py # 配置文件
│ ├── BASE_DIR # 项目根目录
│ ├── UPLOAD_FOLDER # 上传文件目录
│ ├── DOWNLOAD_FOLDER # 下载文件目录
│ ├── OSS配置 # 阿里云OSS配置
│ ├── DashScope配置 # 阿里云转写服务配置
│ └── HISTORY_LIMIT # 历史记录保存数量限制
│
├── services/ # 服务层目录
│ ├── init.py
│ ├── video_service.py # 视频处理服务
│ │ ├── upload_video() # 上传视频到OSS
│ │ ├── transcribe_video() # 视频转写
│ │ ├── process_video() # 完整视频处理流程
│ │ ├── save_history() # 保存历史记录
│ │ └── get_history() # 获取历史记录
│ │
│ └── youtube_service.py # YouTube下载服务
│
├── static/ # 静态文件目录
│ ├── css/
│ │ ├── styles.css # 主样式表
│ │ ├── player.css # 播放器样式
│ │ └── history.css # 历史记录样式
│ │
│ └── js/
│ ├── main.js # 主页面脚本
│ ├── player.js # 播放器脚本
│ └── history.js # 历史记录处理脚本
│
├── templates/ # 模板目录
│ ├── index.html # 主页面
│ ├── player.html # 播放器页面
│ └── history.html # 历史记录页面
│
├── uploads/ # 上传文件临时存储目录
├── downloads/ # YouTube下载文件存储目录
│
├── .env # 环境变量配置
└── requirements.txt # 项目依赖