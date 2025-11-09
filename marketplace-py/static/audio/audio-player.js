/**
 * Audio player JavaScript module
 * Provides functionality for playing audio snippets and requesting missing audio
 */

(function() {
    'use strict';
    
    // Initialize audio players on page load
    document.addEventListener('DOMContentLoaded', function() {
        initializeAudioPlayers();
    });
    
    function initializeAudioPlayers() {
        // Auto-inject audio players for elements with data-audio-target attribute
        document.querySelectorAll('[data-audio-target]').forEach(function(element) {
            const targetField = element.dataset.audioTarget;
            const languageCode = element.dataset.language || getCurrentLanguage();
            const contentTypeId = element.dataset.contentType;
            const objectId = element.dataset.objectId;
            
            // Skip if required attributes are missing or invalid
            if (!targetField || !contentTypeId || !objectId) {
                return;
            }
            
            // Skip if contentTypeId or objectId is "None" (string) or empty
            if (contentTypeId.toLowerCase() === 'none' || objectId.toLowerCase() === 'none' || 
                contentTypeId.trim() === '' || objectId.trim() === '') {
                return;
            }
            
            // Check if audio player already exists
            if (!element.querySelector('.audio-player-wrapper')) {
                loadAudioPlayer(element, contentTypeId, objectId, targetField, languageCode);
            }
        });
    }
    
    function loadAudioPlayer(container, contentTypeId, objectId, targetField, languageCode) {
        // Fetch audio info from API
        const apiUrl = `/api/audio/snippets/get/${contentTypeId}/${objectId}/${targetField}/${languageCode}/`;
        
        fetch(apiUrl)
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else if (response.status === 404 || response.status === 400) {
                    // 404 = not found, 400 = invalid request (e.g., None values, invalid IDs)
                    // Preserve all data from response, especially fallback_audio_url
                    return response.json().then(data => {
                        return {
                            ...data,  // Preserve all fields from response
                            available: false,  // Ensure available is false
                            error: data.error || 'Audio not available'
                        };
                    }).catch(() => {
                        return { available: false };
                    });
                }
                throw new Error('Failed to fetch audio');
            })
            .then(data => {
                if (data.available !== false && data.audio_url) {
                    // Audio available - inject player
                    injectAudioPlayer(container, data.audio_url, targetField, languageCode);
                } else {
                    // Audio not available - inject request button
                    injectAudioRequestButton(container, contentTypeId, objectId, targetField, languageCode);
                }
            })
            .catch(error => {
                console.error('Error loading audio:', error);
            });
    }
    
    function injectAudioPlayer(container, audioUrl, targetField, languageCode) {
        const playerHtml = `
            <div class="audio-player-wrapper">
                <button class="audio-play-btn" 
                        aria-label="Play audio for ${targetField} in ${languageCode}"
                        onclick="window.audioPlayerModule.playAudio(this)">
                    <span class="audio-icon" aria-hidden="true">??</span>
                    <span class="audio-label">Listen</span>
                </button>
                <div class="audio-player-container" style="display: none;">
                    <audio controls preload="none">
                        <source src="${audioUrl}" type="audio/mpeg">
                        <source src="${audioUrl}" type="audio/ogg">
                        Your browser does not support the audio element.
                    </audio>
                    <button class="audio-close-btn" onclick="window.audioPlayerModule.closeAudioPlayer(this)" aria-label="Close audio player">?</button>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', playerHtml);
    }
    
    function injectAudioRequestButton(container, contentTypeId, objectId, targetField, languageCode) {
        const buttonHtml = `
            <div class="audio-player-wrapper">
                <button class="audio-request-btn" 
                        aria-label="Request audio for ${targetField} in ${languageCode}"
                        onclick="window.audioPlayerModule.requestAudio(this)">
                    <span class="audio-icon" aria-hidden="true">??</span>
                    <span class="audio-label">Request audio</span>
                </button>
                <div class="audio-request-message" style="display: none;" role="alert"></div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', buttonHtml);
        
        // Store data attributes
        const wrapper = container.querySelector('.audio-player-wrapper');
        wrapper.dataset.contentType = contentTypeId;
        wrapper.dataset.objectId = objectId;
        wrapper.dataset.audioTarget = targetField;
        wrapper.dataset.language = languageCode;
    }
    
    function getCurrentLanguage() {
        const docEl = document.documentElement;
        if (docEl && docEl.dataset && docEl.dataset.audioLanguage) {
            return docEl.dataset.audioLanguage;
        }
        const htmlLang = docEl ? docEl.lang : null;
        return htmlLang || 'en';
    }
    
    // Export module functions
    window.audioPlayerModule = {
        playAudio: function(button) {
            const wrapper = button.closest('.audio-player-wrapper');
            const playerContainer = wrapper.querySelector('.audio-player-container');
            const audio = playerContainer.querySelector('audio');
            
            button.style.display = 'none';
            playerContainer.style.display = 'flex';
            
            audio.play().catch(err => {
                console.error('Error playing audio:', err);
                // If main audio fails and it's not already a fallback, try fallback
                if (!audio.dataset.fallback) {
                    const fallbackUrl = audio.dataset.fallbackUrl;
                    if (fallbackUrl) {
                        audio.src = fallbackUrl;
                        audio.play().catch(() => {
                            const errorMsg = document.createElement('div');
                            errorMsg.className = 'audio-error';
                            errorMsg.textContent = 'Error loading audio. Please try again.';
                            playerContainer.appendChild(errorMsg);
                        });
                        return;
                    }
                }
                // Show error message
                const errorMsg = document.createElement('div');
                errorMsg.className = 'audio-error';
                errorMsg.textContent = 'Error loading audio. Please try again.';
                playerContainer.appendChild(errorMsg);
            });
        },
        
        closeAudioPlayer: function(button) {
            const container = button.closest('.audio-player-container');
            const wrapper = container.closest('.audio-player-wrapper');
            const playBtn = wrapper.querySelector('.audio-play-btn');
            const audio = container.querySelector('audio');
            
            audio.pause();
            audio.currentTime = 0;
            
            container.style.display = 'none';
            playBtn.style.display = 'inline-flex';
        },
        
        requestAudio: function(button) {
            const wrapper = button.closest('.audio-player-wrapper');
            const contentTypeId = wrapper.dataset.contentType;
            const objectId = wrapper.dataset.objectId;
            const targetField = wrapper.dataset.audioTarget;
            const languageCode = wrapper.dataset.language;
            const messageDiv = wrapper.querySelector('.audio-request-message');
            
            button.disabled = true;
            button.querySelector('.audio-label').textContent = 'Requesting...';
            
            fetch('/api/audio/requests/request_audio/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    content_type_id: contentTypeId,
                    object_id: objectId,
                    target_field: targetField,
                    language_code: languageCode
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => Promise.reject(data));
                }
                return response.json();
            })
            .then(data => {
                messageDiv.textContent = 'Thank you! Your request has been submitted.';
                messageDiv.className = 'audio-request-message success';
                messageDiv.style.display = 'block';
                button.style.display = 'none';
            })
            .catch(error => {
                messageDiv.textContent = error.error || 'Sorry, there was an error submitting your request. Please try again.';
                messageDiv.className = 'audio-request-message error';
                messageDiv.style.display = 'block';
                button.disabled = false;
                button.querySelector('.audio-label').textContent = 'Request audio';
            });
        }
    };
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
})();
