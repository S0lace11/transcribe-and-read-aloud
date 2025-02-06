// 历史记录处理
class HistoryManager {
    constructor() {
        this.page = 1;
        this.pageSize = 10;
        this.loading = false;
        this.hasMore = true;
        
        this.initElements();
        this.bindEvents();
        this.loadHistory();
    }
    
    initElements() {
        this.historyList = document.querySelector('.history-list');
        this.emptyState = document.querySelector('.history-empty');
        this.loadMoreBtn = document.getElementById('loadMoreHistory');
        this.refreshBtn = document.getElementById('refreshHistory');
        this.template = document.querySelector('.history-item-template');
    }
    
    bindEvents() {
        this.refreshBtn.addEventListener('click', () => this.refresh());
        this.loadMoreBtn.addEventListener('click', () => this.loadMore());
        
        // 委托事件处理
        this.historyList.addEventListener('click', (e) => {
            const target = e.target;
            if (target.classList.contains('replay-btn')) {
                this.replayVideo(target.closest('.history-item'));
            } else if (target.classList.contains('delete-btn')) {
                this.deleteHistory(target.closest('.history-item'));
            }
        });
    }
    
    async loadHistory(append = false) {
        if (this.loading) return;
        
        try {
            this.loading = true;
            this.updateLoadingState(true);
            
            const response = await fetch(`/api/history?page=${this.page}&size=${this.pageSize}`);
            const data = await response.json();
            
            if (!append) {
                this.historyList.innerHTML = '';
            }
            
            this.renderHistory(data.items);
            this.hasMore = data.has_more;
            this.updateLoadMoreButton();
            
        } catch (error) {
            console.error('加载历史记录失败:', error);
        } finally {
            this.loading = false;
            this.updateLoadingState(false);
        }
    }
    
    renderHistory(items) {
        if (items.length === 0 && this.page === 1) {
            this.emptyState.classList.remove('d-none');
            return;
        }
        
        this.emptyState.classList.add('d-none');
        
        items.forEach(item => {
            const historyItem = this.createHistoryItem(item);
            this.historyList.appendChild(historyItem);
        });
    }
    
    createHistoryItem(item) {
        const template = this.template.cloneNode(true);
        template.classList.remove('d-none', 'history-item-template');
        
        // 填充数据
        template.querySelector('.video-title').textContent = item.title;
        template.querySelector('.video-source').textContent = item.source;
        template.querySelector('.video-time').textContent = this.formatTime(item.created_at);
        template.querySelector('.text-preview').textContent = item.text_preview || '暂无转录文本';
        
        // 设置转录状态
        const transcribed = item.transcribed === '1';
        template.querySelector('.transcribe-status').textContent = transcribed ? '已转录' : '未转录';
        template.querySelector('.transcribe-status').classList.toggle('text-success', transcribed);
        
        return template;
    }
    
    // ... 其他辅助方法
}

