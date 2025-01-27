// Import delle funzioni di Tauri
const { invoke } = window.__TAURI__.tauri;
const { listen } = window.__TAURI__.event;

// Gestione della navigazione
const pages = ['home', 'search', 'watchlist', 'downloads'];
const navLinks = document.querySelectorAll('nav a');

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.getAttribute('data-page');
        showPage(page);
    });
});

function showPage(pageId) {
    pages.forEach(page => {
        const element = document.getElementById(`${page}-page`);
        if (element) {
            element.classList.toggle('hidden', page !== pageId);
            element.classList.toggle('active', page === pageId);
        }
    });
}

// Gestione della ricerca
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');

let searchTimeout;
searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        const query = e.target.value.trim();
        if (query.length > 2) {
            const results = await invoke('search_titles', { query });
            displaySearchResults(results);
        } else {
            searchResults.innerHTML = '';
        }
    }, 300);
});

function displaySearchResults(results) {
    searchResults.innerHTML = results.map(item => `
        <div class="content-card">
            <img src="${item.poster_path || 'default-poster.jpg'}" alt="${item.title}">
            <div class="content-info">
                <h3 class="text-lg font-semibold">${item.title}</h3>
                <p class="text-sm text-gray-400">${item.year || ''}</p>
                <div class="mt-2 flex space-x-2">
                    <button class="btn btn-primary" onclick="playContent('${item.id}')">
                        <i class="fas fa-play mr-2"></i>Play
                    </button>
                    <button class="btn btn-secondary" onclick="addToWatchlist('${item.id}')">
                        <i class="fas fa-plus mr-2"></i>Watchlist
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Gestione della watchlist
async function loadWatchlist() {
    const watchlist = await invoke('get_watchlist');
    const watchlistContent = document.getElementById('watchlist-content');
    
    watchlistContent.innerHTML = watchlist.map(item => `
        <div class="watchlist-item">
            <div class="flex items-center">
                <img src="${item.poster_path || 'default-poster.jpg'}" 
                     alt="${item.title}" 
                     class="w-16 h-24 object-cover rounded mr-4">
                <div>
                    <h3 class="font-semibold">${item.title}</h3>
                    ${item.media_type === 'series' ? `
                        <p class="text-sm text-gray-400">
                            S${item.current_season} E${item.current_episode}
                        </p>
                    ` : ''}
                </div>
            </div>
            <div class="flex space-x-2">
                <button class="btn btn-primary" onclick="playContent('${item.id}')">
                    <i class="fas fa-play"></i>
                </button>
                <button class="btn btn-danger" onclick="removeFromWatchlist('${item.id}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Gestione dei download
async function loadDownloads() {
    const downloads = await invoke('get_download_status');
    const downloadsList = document.getElementById('downloads-list');
    
    downloadsList.innerHTML = downloads.map(([id, info]) => `
        <div class="download-item">
            <div class="download-info">
                <div>
                    <h3 class="font-semibold">${info.title}</h3>
                    ${info.season ? `
                        <p class="text-sm text-gray-400">
                            S${info.season} E${info.episode}
                        </p>
                    ` : ''}
                </div>
                <div class="flex items-center space-x-2">
                    ${info.status === 'downloading' ? `
                        <button class="btn btn-danger" onclick="cancelDownload('${id}')">
                            <i class="fas fa-stop"></i>
                        </button>
                    ` : info.status === 'error' ? `
                        <button class="btn btn-primary" onclick="retryDownload('${id}')">
                            <i class="fas fa-redo"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress" style="width: ${info.progress}%"></div>
            </div>
            <p class="download-progress">
                ${info.status === 'completed' ? 'Completato' : 
                  info.status === 'error' ? `Errore: ${info.error}` :
                  `${Math.round(info.progress)}%`}
            </p>
        </div>
    `).join('');
}

// Gestione del player video
const videoPlayerModal = document.getElementById('video-player-modal');
const videoPlayer = document.getElementById('video-player');
const closePlayer = document.getElementById('close-player');

async function playContent(id) {
    const source = await invoke('get_video_source', { id });
    videoPlayer.src = source.url;
    videoPlayerModal.classList.remove('hidden');
    videoPlayer.play();
}

closePlayer.addEventListener('click', () => {
    videoPlayer.pause();
    videoPlayer.src = '';
    videoPlayerModal.classList.add('hidden');
});

// Gestione delle notifiche
function showNotification(title, message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="flex-1">
            <h4 class="font-semibold">${title}</h4>
            <p class="text-sm">${message}</p>
        </div>
        <button class="ml-4" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    container.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}

// Ascolta gli eventi dal backend
listen('notification', (event) => {
    const { title, body, type } = event.payload;
    showNotification(title, body, type);
});

// Inizializzazione
document.addEventListener('DOMContentLoaded', () => {
    showPage('home');
    loadWatchlist();
    loadDownloads();
    
    // Aggiorna la lista dei download ogni secondo
    setInterval(loadDownloads, 1000);
});
