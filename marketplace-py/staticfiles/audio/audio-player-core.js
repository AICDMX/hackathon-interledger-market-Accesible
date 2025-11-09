/**
 * Centralized Audio Player Module
 * Provides reusable functions for audio playback with icon state management
 * Configuration is injected from Django via window.AUDIO_CONFIG
 */

(function() {
    'use strict';
    
    // Configuration - will be set from Django context
    const AudioPlayerConfig = {
        iconInactive: '/media/listen-inactive.png',
        iconActive: '/media/listen-active.png',
        fallbackAudio: {},
        staticUrl: '/static/'
    };
    
    // Override with Django config if available
    if (window.AUDIO_CONFIG) {
        // Parse fallbackAudio if it's a JSON string
        if (typeof window.AUDIO_CONFIG.fallbackAudio === 'string') {
            try {
                window.AUDIO_CONFIG.fallbackAudio = JSON.parse(window.AUDIO_CONFIG.fallbackAudio);
            } catch (e) {
                console.warn('Failed to parse fallbackAudio config:', e);
                window.AUDIO_CONFIG.fallbackAudio = {};
            }
        }
        Object.assign(AudioPlayerConfig, window.AUDIO_CONFIG);
    }
    
    /**
     * Get fallback audio path for a language
     */
    function getFallbackAudioPath(languageCode) {
        if (AudioPlayerConfig.fallbackAudio && AudioPlayerConfig.fallbackAudio[languageCode]) {
            return AudioPlayerConfig.staticUrl + AudioPlayerConfig.fallbackAudio[languageCode];
        }
        return AudioPlayerConfig.staticUrl + (AudioPlayerConfig.fallbackFile || 'audio/fallback.mp3');
    }
    
    /**
     * Set icon state (inactive or active)
     */
    function setIconState(icon, state) {
        if (!icon) return;
        icon.src = state === 'active' ? AudioPlayerConfig.iconActive : AudioPlayerConfig.iconInactive;
    }
    
    /**
     * Play audio with icon state management
     */
    function playAudioWithIcon(audio, icon) {
        if (!audio) return Promise.reject(new Error('No audio element'));
        
        // Set to active before playing
        setIconState(icon, 'active');
        
        // Set up event listeners
        const handleEnded = function() {
            setIconState(icon, 'inactive');
        };
        
        audio.addEventListener('ended', handleEnded, { once: true });
        
        // Play audio
        return audio.play().catch(err => {
            setIconState(icon, 'inactive');
            throw err;
        });
    }
    
    /**
     * Play fallback audio for a language
     */
    function playFallbackAudio(languageCode, icon) {
        const fallbackPath = getFallbackAudioPath(languageCode);
        const audio = new Audio(fallbackPath);
        
        return playAudioWithIcon(audio, icon).catch(err => {
            console.error('Error playing fallback audio:', err);
            // Try generic fallback if language-specific fails
            if (languageCode !== 'es' && languageCode !== 'en') {
                const genericPath = AudioPlayerConfig.staticUrl + (AudioPlayerConfig.fallbackFile || 'audio/fallback.mp3');
                const genericFallback = new Audio(genericPath);
                return playAudioWithIcon(genericFallback, icon);
            }
            throw err;
        });
    }
    
    // Export module
    window.AudioPlayerModule = {
        config: AudioPlayerConfig,
        setIconState: setIconState,
        playAudioWithIcon: playAudioWithIcon,
        playFallbackAudio: playFallbackAudio,
        getFallbackAudioPath: getFallbackAudioPath
    };
})();
