document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const urlInput = document.getElementById('video-url');
    const downloadBtn = document.getElementById('download-btn');
    const fileInput = document.getElementById('file-upload');
    const uploadBtn = document.getElementById('upload-btn');
    const youtubeTranscribeBtn = document.getElementById('youtube-transcribe-btn');
    const uploadTranscribeBtn = document.getElementById('upload-transcribe-btn');
    const downloadProgress = document.getElementById('download-progress');
    const downloadStatus = document.getElementById('download-status');
    const info = document.getElementById('info');
    const transcriptionText = document.getElementById('transcription-text');
    const transcriptionContainer = document.getElementById('transcription-container');
    const fileDropArea = document.querySelector('.file-drop-area');
    const fileMessage = document.querySelector('.file-message');
    const videoContainer = document.querySelector('.video-container');

    // 当前处理的视频信息
    let currentVideo = {
        filename: null,
        source: null  // 'youtube' 或 'upload'
    };

    // 视频播放器初始化
    let player = videojs('video-player', {
        controls: true,
        fluid: true,
        playbackRates: [0.5, 1, 1.5, 2]
    });

    // 文件拖放处理
    fileDropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileDropArea.classList.add('dragover');
    });

    fileDropArea.addEventListener('dragleave', () => {
        fileDropArea.classList.remove('dragover');
    });

    fileDropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        fileDropArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'video/mp4') {
            handleFileSelect(file);
        } else {
            showError('请上传MP4格式的视频文件');
        }
    });

    // 文件选择处理
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFileSelect(this.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (file.type !== 'video/mp4') {
            showError('请选择MP4格式的视频文件');
            return;
        }
        fileMessage.textContent = file.name;
        uploadBtn.disabled = false;
    }

    // 处理回车键
    urlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            downloadBtn.click();
        }
    });

    // 处理文件上传
    uploadBtn.addEventListener('click', async function() {
        if (!fileInput.files.length) return;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            showInfo('正在上传文件...');
            disableUI();

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showSuccess('文件上传成功！');
                // 刷新历史记录
                loadRecentHistory();
            } else {
                showError(data.error || '上传失败');
            }
        } catch (error) {
            showError('网络错误，请稍后重试');
        } finally {
            enableUI();
            // 清空文件选择
            fileInput.value = '';
            fileMessage.textContent = '选择或拖放视频文件';
        }
    });

    // 处理YouTube下载
    downloadBtn.addEventListener('click', async function() {
        const url = urlInput.value.trim();
        if (!url) {
            showError('请输入视频链接');
            return;
        }

        try {
            showInfo('正在获取视频信息...');
            disableUI();
            downloadProgress.classList.remove('d-none');
            const progressBar = downloadProgress.querySelector('.progress-bar');
            progressBar.style.width = '0%';

            // 创建任务ID
            const taskId = Date.now().toString();
            
            // 设置SSE连接
            const eventSource = new EventSource(`/progress/${taskId}`);
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.status === 'downloading') {
                    updateDownloadProgress(data);
                } else if (data.status === 'completed') {
                    eventSource.close();
                    currentVideo = {
                        filename: data.video_path,
                        source: 'youtube'
                    };
                    showVideo(data.video_path);
                    youtubeTranscribeBtn.classList.remove('d-none');
                    showSuccess('下载完成！');
                } else if (data.status === 'error') {
                    showError(data.message);
                    eventSource.close();
                }
            };
            
            eventSource.onerror = function() {
                eventSource.close();
                showError('下载过程中断');
                enableUI();
            };

            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    url: url,
                    task_id: taskId
                })
            });

            if (!response.ok) {
                const data = await response.json();
                showError(data.error || '下载失败');
                eventSource.close();
            }
        } catch (error) {
            showError('网络错误，请稍后重试');
        }
    });

    // 处理视频转录
    async function transcribeVideo(filename, source) {
        try {
            showInfo('正在转录视频...');
            disableUI();

            const response = await fetch('/transcribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
                    source: source
                })
            });

            const data = await response.json();
            console.log('转录响应:', data); // 添加调试日志

            if (response.ok) {
                if (data.transcription && data.transcription.sentences) {
                    showSuccess('转录完成！');
                    updateTranscription(data);
                } else {
                    showError('转录结果格式不正确');
                    console.log('错误的转录结果格式:', data);
                }
            } else {
                showError(data.error || '转录失败');
                console.log('转录请求失败:', data);
            }
        } catch (error) {
            console.error('转录请求出错:', error);
            showError('网络错误，请稍后重试');
        } finally {
            enableUI();
        }
    }

    // YouTube视频转录按钮
    youtubeTranscribeBtn.addEventListener('click', function() {
        if (currentVideo.source === 'youtube' && currentVideo.filename) {
            transcribeVideo(currentVideo.filename, 'youtube');
        }
    });

    // 上传视频转录按钮
    uploadTranscribeBtn.addEventListener('click', function() {
        if (currentVideo.source === 'upload' && currentVideo.filename) {
            transcribeVideo(currentVideo.filename, 'upload');
        }
    });

    function updateDownloadProgress(progress) {
        const progressBar = downloadProgress.querySelector('.progress-bar');
        if (!progress.downloaded || !progress.total) {
            progressBar.style.width = '100%';
            progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
            downloadStatus.textContent = '正在下载...';
            return;
        }

        const percent = (progress.progress || 0).toFixed(1);
        progressBar.style.width = `${percent}%`;
        downloadStatus.textContent = `下载中: ${progress.downloaded}/${progress.total} | 速度: ${progress.speed} | 剩余时间: ${progress.eta}`;
    }

    function showVideo(filename) {
        player.src({
            type: 'video/mp4',
            src: `/video/${filename}`
        });
        
        videoContainer.classList.remove('d-none');
        player.load();
    }

    function updateTranscription(data) {
        console.log('收到转录数据:', data); // 添加调试日志
        
        if (data && data.transcription && Array.isArray(data.transcription.sentences)) {
            const sentences = data.transcription.sentences;
            // 按时间排序
            sentences.sort((a, b) => a.begin_time - b.begin_time);
            
            const formattedText = sentences.map(sentence => {
                const startTime = formatTime(sentence.begin_time);
                const endTime = formatTime(sentence.end_time);
                // 移除所有标签，只保留实际文本
                const cleanText = sentence.text.replace(/<\|[^>]+\|>/g, '').trim();
                return `[${startTime} - ${endTime}] ${cleanText}`;
            }).join('\n\n');
            
            transcriptionText.value = formattedText;
            transcriptionContainer.classList.remove('d-none');
        } else {
            console.log('转录数据格式不正确:', data); // 添加调试日志
            transcriptionText.value = '无法解析转录结果';
            transcriptionContainer.classList.remove('d-none');
        }
    }

    function formatTime(milliseconds) {
        const totalSeconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        const ms = Math.floor((milliseconds % 1000) / 10); // 只显示两位毫秒
        return `${padZero(minutes)}:${padZero(seconds)}.${padZero(ms, 2)}`;
    }

    function padZero(num, length = 2) {
        return num.toString().padStart(length, '0');
    }

    function showError(message) {
        info.className = 'alert alert-danger';
        info.textContent = message;
        info.classList.remove('d-none');
    }

    function showSuccess(message) {
        info.className = 'alert alert-success';
        info.textContent = message;
        info.classList.remove('d-none');
    }

    function showInfo(message) {
        info.className = 'alert alert-info';
        info.textContent = message;
        info.classList.remove('d-none');
    }

    function disableUI() {
        downloadBtn.disabled = true;
        uploadBtn.disabled = true;
        youtubeTranscribeBtn.disabled = true;
        uploadTranscribeBtn.disabled = true;
    }

    function enableUI() {
        downloadBtn.disabled = false;
        uploadBtn.disabled = !fileInput.files.length;
        youtubeTranscribeBtn.disabled = false;
        uploadTranscribeBtn.disabled = false;
    }

    async function loadRecentHistory() {
        try {
            const response = await fetch('/api/history/recent');
            const data = await response.json();
            
            if (data.success) {
                updateHistoryList(data.history);
            } else {
                console.error('加载历史记录失败:', data.error);
            }
        } catch (error) {
            console.error('加载历史记录失败:', error);
        }
    }

    function updateHistoryList(historyList) {
        const historyContainer = document.querySelector('#history-records');
        if (!historyList || historyList.length === 0) {
            historyContainer.innerHTML = '<div class="history-empty">暂无历史记录</div>';
            return;
        }
        
        historyContainer.innerHTML = '';
        historyList.forEach(item => {
            const card = createHistoryCard(item);
            historyContainer.appendChild(card);
        });
    }

    function createHistoryCard(item) {
        const card = document.createElement('div');
        card.className = 'history-card';
        card.dataset.id = item.id;
        
        // 格式化时长
        const duration = item.duration || '0:00';
        
        card.innerHTML = `
            <div class="history-card-header">
                <span class="source-badge ${item.source.toLowerCase()}">${item.source === 'youtube' ? 'YouTube' : '本地上传'}</span>
                <span class="process-time">${item.created_at}</span>
            </div>
            <div class="history-card-body">
                <h3 class="video-title">${item.title}</h3>
                ${item.text_preview ? `<p class="text-preview">${item.text_preview}</p>` : ''}
            </div>
            <div class="history-card-footer">
                <span class="video-duration"><i class="far fa-clock"></i> ${duration}</span>
                <div class="history-card-actions">
                    <button class="btn btn-sm btn-primary view-btn" data-video="${item.video_path}" data-source="${item.source}">
                        <i class="fas fa-play"></i> 查看
                    </button>
                    <button class="btn btn-sm delete-btn" data-id="${item.id}">
                        <i class="fas fa-trash"></i> 删除
                    </button>
                </div>
            </div>
        `;
        
        // 添加查看按钮点击事件
        const viewBtn = card.querySelector('.view-btn');
        viewBtn.addEventListener('click', () => {
            const video = viewBtn.dataset.video;
            const source = viewBtn.dataset.source;
            // 修改跳转URL格式
            window.location.href = `/player/${encodeURIComponent(video)}?source=${encodeURIComponent(source)}`;
        });
        
        // 添加删除按钮点击事件
        const deleteBtn = card.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', async () => {
            if (confirm('确定要删除这条历史记录吗？')) {
                await deleteHistoryItem(item.id);
            }
        });
        
        return card;
    }

    async function deleteHistoryItem(historyId) {
        try {
            const response = await fetch(`/api/history/${historyId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 从DOM中移除卡片
                const card = document.querySelector(`.history-card[data-id="${historyId}"]`);
                if (card) {
                    card.remove();
                }
                showSuccess('删除成功');
                
                // 检查是否还有历史记录
                const historyContainer = document.querySelector('#history-records');
                if (!historyContainer.children.length) {
                    historyContainer.innerHTML = '<div class="history-empty">暂无历史记录</div>';
                }
            } else {
                showError(data.error || '删除失败');
            }
        } catch (error) {
            console.error('删除历史记录失败:', error);
            showError('网络错误，请稍后重试');
        }
    }

    // 定时刷新历史记录
    setInterval(loadRecentHistory, 5000);  // 每5秒刷新一次

    // 页面加载时获取历史记录
    loadRecentHistory();
}); 