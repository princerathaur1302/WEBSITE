// script.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize player variables
    let hls;
    const playerOverlay = document.getElementById('playerOverlay');
    const videoPlayer = document.getElementById('videoPlayer');
    const qualitySelect = document.getElementById('qualitySelect');
    const videoTitle = document.getElementById('videoTitle');
    let currentVideoUrl = '';
    let currentVideoTitle = '';

    // Close player when clicking outside
    playerOverlay.addEventListener('click', function(e) {
        if (e.target === playerOverlay) {
            closePlayer();
        }
    });

    // Protection Measures
    document.addEventListener('keydown', function(e) {
        // Block F12, Ctrl+Shift+I, Ctrl+U
        if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I') || (e.ctrlKey && e.key === 'u')) {
            e.preventDefault();
        }
    });
});

// Open Player Function
function openPlayer(videoUrl, title) {
    if (!videoUrl) {
        console.error("No video URL provided");
        alert("Video URL is missing");
        return;
    }

    const playerOverlay = document.getElementById('playerOverlay');
    const videoPlayer = document.getElementById('videoPlayer');
    const qualitySelect = document.getElementById('qualitySelect');
    const videoTitle = document.getElementById('videoTitle');

    // Set current video info
    currentVideoUrl = videoUrl;
    currentVideoTitle = title;

    // Update UI
    videoTitle.textContent = title;
    playerOverlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Create and show loading spinner
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    document.querySelector('.video-container').appendChild(spinner);
    spinner.style.display = 'block';

    // Clear previous video source
    videoPlayer.src = '';
    
    if (Hls.isSupported()) {
        if (window.hls) {
            window.hls.destroy();
        }
        
        window.hls = new Hls({
            maxMaxBufferLength: 600,
            maxBufferSize: 60*1000*1000,
            enableWorker: true,
            startLevel: -1, // Auto quality by default
        });
        
        window.hls.on(Hls.Events.MEDIA_ATTACHED, function() {
            console.log("Media attached");
            window.hls.loadSource(videoUrl);
        });
        
        window.hls.on(Hls.Events.MANIFEST_PARSED, function(event, data) {
            console.log("Manifest parsed");
            spinner.style.display = 'none';
            
            // Populate quality selector
            qualitySelect.innerHTML = '<option value="auto">Auto Quality</option>';
            data.levels.forEach((level, index) => {
                qualitySelect.add(new Option(
                    `${level.height}p (${Math.round(level.bitrate/1000)}kbps)`, 
                    index
                ));
            });
            
            videoPlayer.play().catch(e => {
                console.error("Autoplay prevented:", e);
                showPlayButton();
            });
        });
        
        window.hls.on(Hls.Events.ERROR, function(event, data) {
            console.error("HLS Error:", data);
            spinner.style.display = 'none';
            
            if (data.fatal) {
                switch(data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        console.error("Network Error");
                        showErrorRetry("Network error. Trying to recover...");
                        window.hls.startLoad();
                        break;
                    case Hls.ErrorTypes.MEDIA_ERROR:
                        console.error("Media Error");
                        showErrorRetry("Media error. Trying to recover...");
                        window.hls.recoverMediaError();
                        break;
                    default:
                        console.error("Fatal Error");
                        showErrorRetry("Failed to load video. Please try again.");
                        closePlayer();
                        break;
                }
            }
        });
        
        window.hls.attachMedia(videoPlayer);
        
    } else if (videoPlayer.canPlayType('application/vnd.apple.mpegurl')) {
        // Safari native HLS support
        videoPlayer.src = videoUrl;
        videoPlayer.addEventListener('loadedmetadata', function() {
            spinner.style.display = 'none';
            videoPlayer.play().catch(e => {
                console.error("Safari autoplay prevented:", e);
                showPlayButton();
            });
        });
        
        videoPlayer.addEventListener('error', function() {
            spinner.style.display = 'none';
            console.error("Video Error:", videoPlayer.error);
            showErrorRetry("Error loading video. Please try again.");
        });
    } else {
        spinner.style.display = 'none';
        console.error("HLS not supported in this browser");
        showErrorRetry("Video playback not supported in your browser. Please try Chrome or Firefox.");
    }
}

// Close Player Function
function closePlayer() {
    const videoPlayer = document.getElementById('videoPlayer');
    const playerOverlay = document.getElementById('playerOverlay');

    if (window.hls) {
        window.hls.destroy();
        window.hls = null;
    }
    
    videoPlayer.pause();
    videoPlayer.removeAttribute('src');
    videoPlayer.load();
    
    // Remove any existing UI elements
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) spinner.remove();
    
    const errorDiv = document.querySelector('.player-error');
    if (errorDiv) errorDiv.remove();
    
    const playBtnOverlay = document.querySelector('.play-button-overlay');
    if (playBtnOverlay) playBtnOverlay.remove();
    
    playerOverlay.style.display = 'none';
    document.body.style.overflow = '';
}

// Change Quality Function
function changeQuality() {
    if (!window.hls) return;
    
    const qualitySelect = document.getElementById('qualitySelect');
    const quality = parseInt(qualitySelect.value);
    if (isNaN(quality)) {
        window.hls.currentLevel = -1; // Auto
    } else {
        window.hls.currentLevel = quality;
    }
}

// Show Error with Retry Button
function showErrorRetry(message) {
    // Remove existing error if any
    const existingError = document.querySelector('.player-error');
    if (existingError) existingError.remove();

    const errorDiv = document.createElement('div');
    errorDiv.className = 'player-error';
    errorDiv.innerHTML = `
        <p>${message || 'Error loading video'}</p>
        <button onclick="retryPlayback()">Retry</button>
    `;
    document.querySelector('.video-container').appendChild(errorDiv);
}

// Retry Playback Function
function retryPlayback() {
    const errorDiv = document.querySelector('.player-error');
    if (errorDiv) errorDiv.remove();
    openPlayer(currentVideoUrl, currentVideoTitle);
}

// Show Play Button (when autoplay is blocked)
function showPlayButton() {
    const existingBtn = document.querySelector('.play-button-overlay');
    if (existingBtn) existingBtn.remove();

    const playBtn = document.createElement('div');
    playBtn.className = 'play-button-overlay';
    playBtn.innerHTML = '<i class="fas fa-play"></i>';
    playBtn.onclick = function() {
        document.getElementById('videoPlayer').play();
        playBtn.remove();
    };
    document.querySelector('.video-container').appendChild(playBtn);
}