/**
 * Mobile-first audio recorder with compression and background uploads
 * Handles permissions, recording, compression, and uploads
 */

class AudioRecorder {
    constructor(options = {}) {
        this.options = {
            maxDuration: options.maxDuration || 30000, // 30 seconds default
            compressionBitrate: options.compressionBitrate || 192000, // 192 kbps for high quality
            uploadUrl: options.uploadUrl || '/api/audio/contributions/upload/',
            onProgress: options.onProgress || null,
            onComplete: options.onComplete || null,
            onError: options.onError || null,
            ...options
        };
        
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
        this.startTime = null;
        this.duration = 0;
        this.uploadController = null;
    }

    /**
     * Check if browser supports MediaRecorder API
     */
    static isSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
    }

    /**
     * Request microphone permission and initialize recorder
     */
    async requestPermission() {
        try {
            // Request microphone access with high-quality settings
            // Try for best quality first, fallback to device defaults
            const audioConstraints = {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                // Request high sample rate (48kHz is ideal, 44.1kHz is standard)
                sampleRate: 48000,
                channelCount: 1, // Mono is fine for voice, reduces file size
                // Request specific audio quality constraints
                latency: 0.01, // Low latency for real-time feel
                googEchoCancellation: true,
                googNoiseSuppression: true,
                googAutoGainControl: true,
                googHighpassFilter: true,
                googTypingNoiseDetection: true,
            };

            // Try high quality first
            try {
                this.stream = await navigator.mediaDevices.getUserMedia({
                    audio: audioConstraints
                });
            } catch (e) {
                // Fallback to standard quality if high quality fails
                this.stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: false, // Disable AGC to prevent initial spikes
                        sampleRate: 44100, // Standard CD quality
                        volume: 0.9, // Reduce volume to prevent clipping
                    }
                });
            }
            
            // Check for MediaRecorder support with preferred codec (prioritize high quality)
            // Opus codec provides excellent quality at lower bitrates
            const mimeTypes = [
                'audio/webm;codecs=opus',  // Best quality, best compression
                'audio/webm',
                'audio/ogg;codecs=opus',   // Good quality
                'audio/mp4;codecs=mp4a.40.2', // AAC codec for Safari
                'audio/mp4',
                'audio/wav'  // Uncompressed fallback (large files)
            ];
            
            let selectedMimeType = null;
            for (const mimeType of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mimeType)) {
                    selectedMimeType = mimeType;
                    break;
                }
            }
            
            if (!selectedMimeType) {
                throw new Error('No supported audio codec found');
            }

            // Create MediaRecorder with high-quality compression settings
            const options = {
                mimeType: selectedMimeType,
                audioBitsPerSecond: this.options.compressionBitrate,
                // For Opus codec, we can specify additional quality parameters
                // Note: These may not be supported in all browsers
            };

            // For Opus, try to set quality if supported (Chrome/Edge)
            if (selectedMimeType.includes('opus')) {
                // Opus quality is excellent even at lower bitrates, but higher is better
                // 192 kbps gives near-transparent quality for voice
            }

            this.mediaRecorder = new MediaRecorder(this.stream, options);
            
            // Handle data available events
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this._handleRecordingStop();
            };

            this.mediaRecorder.onerror = (event) => {
                this._handleError('Recording error: ' + event.error);
            };

            return { success: true, mimeType: selectedMimeType };
        } catch (error) {
            let errorMessage = 'No se pudo acceder al micr?fono.';
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                errorMessage = 'Se necesita permiso para usar el micr?fono. Por favor, permite el acceso en la configuraci?n del navegador.';
            } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                errorMessage = 'No se encontr? ning?n micr?fono.';
            } else if (error.name === 'NotSupportedError') {
                errorMessage = 'Tu navegador no soporta grabaci?n de audio.';
            }
            
            this._handleError(errorMessage);
            return { success: false, error: errorMessage };
        }
    }

    /**
     * Start recording
     */
    async startRecording() {
        if (!this.mediaRecorder) {
            const permissionResult = await this.requestPermission();
            if (!permissionResult.success) {
                return false;
            }
        }

        if (this.isRecording) {
            return false;
        }

        try {
            this.audioChunks = [];
            this.isRecording = true;
            this.startTime = Date.now();
            this.duration = 0;
            
            // Small delay before starting to let AGC settle and prevent initial spike
            await new Promise(resolve => setTimeout(resolve, 50)); // 50ms delay
            
            // Start recording with timeslice for chunked data
            this.mediaRecorder.start(1000); // Collect data every second
            
            return true;
        } catch (error) {
            this._handleError('Error al iniciar la grabaci?n: ' + error.message);
            return false;
        }
    }

    /**
     * Stop recording
     */
    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) {
            return false;
        }

        try {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.duration = Date.now() - this.startTime;
            
            // Stop all tracks to release microphone
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
                this.stream = null;
            }
            
            return true;
        } catch (error) {
            this._handleError('Error al detener la grabaci?n: ' + error.message);
            return false;
        }
    }

    /**
     * Cancel recording
     */
    cancelRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
        }
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        this.audioChunks = [];
        this.isRecording = false;
        this.duration = 0;
    }

    /**
     * Get current recording duration
     */
    getDuration() {
        if (this.isRecording && this.startTime) {
            return Date.now() - this.startTime;
        }
        return this.duration;
    }

    /**
     * Get formatted duration string
     */
    getFormattedDuration() {
        const ms = this.getDuration();
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    /**
     * Process and enhance audio quality using Web Audio API
     * Applies normalization, filtering, fade-in, and high-quality compression
     * Prevents clipping and "blown out" audio at the beginning
     * Always processes audio to add fade-in and prevent clipping
     */
    async compressAudio(blob) {
        // Always process audio to add fade-in and prevent clipping, even if already compressed
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 48000 // Use high sample rate for processing
            });
            
            const arrayBuffer = await blob.arrayBuffer();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            
            // Apply fade-in to prevent "blown out" start (0.2 seconds fade-in)
            const fadeInDuration = 0.2; // 200ms fade-in to prevent initial spike
            const fadeInSamples = Math.floor(fadeInDuration * audioBuffer.sampleRate);
            const channelData = audioBuffer.getChannelData(0); // Process first channel
            
            // Apply fade-in to prevent initial clipping
            for (let i = 0; i < Math.min(fadeInSamples, channelData.length); i++) {
                const fadeValue = i / fadeInSamples;
                channelData[i] *= fadeValue;
            }
            
            // Also apply fade-in to other channels if they exist
            if (audioBuffer.numberOfChannels > 1) {
                for (let channel = 1; channel < audioBuffer.numberOfChannels; channel++) {
                    const channelDataMulti = audioBuffer.getChannelData(channel);
                    for (let i = 0; i < Math.min(fadeInSamples, channelDataMulti.length); i++) {
                        const fadeValue = i / fadeInSamples;
                        channelDataMulti[i] *= fadeValue;
                    }
                }
            }
            
            // Apply audio processing for better quality
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            
            // High-pass filter to remove low-frequency noise (before compression)
            const highpass = audioContext.createBiquadFilter();
            highpass.type = 'highpass';
            highpass.frequency.value = 80; // Remove frequencies below 80Hz
            
            // Low-pass filter to remove high-frequency noise
            const lowpass = audioContext.createBiquadFilter();
            lowpass.type = 'lowpass';
            lowpass.frequency.value = 12000; // Keep frequencies up to 12kHz (good for voice)
            
            // Create compressor with gentler settings to prevent clipping
            const compressor = audioContext.createDynamicsCompressor();
            compressor.threshold.value = -18; // Slightly higher threshold
            compressor.knee.value = 6; // Smaller knee for smoother compression
            compressor.ratio.value = 4; // Less aggressive ratio
            compressor.attack.value = 0.01; // Slightly slower attack to catch initial spikes
            compressor.release.value = 0.25;
            
            // Limiter to prevent clipping (using compressor as limiter)
            const limiter = audioContext.createDynamicsCompressor();
            limiter.threshold.value = -1; // Very high threshold, acts as safety limiter
            limiter.knee.value = 0;
            limiter.ratio.value = 20; // High ratio = hard limiter
            limiter.attack.value = 0.001; // Very fast attack
            limiter.release.value = 0.01; // Fast release
            
            // Gain node for normalization (set to prevent clipping)
            const gainNode = audioContext.createGain();
            gainNode.gain.value = 0.85; // Slightly reduce gain to prevent clipping
            
            // Connect processing chain
            source.connect(highpass);
            highpass.connect(lowpass);
            lowpass.connect(compressor);
            compressor.connect(limiter);
            limiter.connect(gainNode);
            
            // Create destination for recording
            const destination = audioContext.createMediaStreamDestination();
            gainNode.connect(destination);
            
            // Use high-quality MediaRecorder with Opus codec
            const mimeTypes = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/ogg;codecs=opus'
            ];
            
            let selectedMimeType = 'audio/webm';
            for (const mimeType of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mimeType)) {
                    selectedMimeType = mimeType;
                    break;
                }
            }
            
            const compressedRecorder = new MediaRecorder(destination.stream, {
                mimeType: selectedMimeType,
                audioBitsPerSecond: this.options.compressionBitrate
            });
            
            return new Promise((resolve, reject) => {
                const chunks = [];
                compressedRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) chunks.push(e.data);
                };
                compressedRecorder.onstop = () => {
                    const compressedBlob = new Blob(chunks, { type: selectedMimeType });
                    audioContext.close();
                    resolve(compressedBlob);
                };
                compressedRecorder.onerror = (e) => {
                    audioContext.close();
                    reject(e);
                };
                
                // Start recording
                source.start(0);
                compressedRecorder.start();
                
                // Stop after audio duration
                const duration = audioBuffer.duration * 1000; // Convert to ms
                setTimeout(() => {
                    compressedRecorder.stop();
                    source.stop();
                }, duration + 100); // Add small buffer
            });
        } catch (error) {
            console.warn('Audio processing failed, using original:', error);
            // If processing fails, try simple re-encoding
            return this._simpleReencode(blob);
        }
    }

    /**
     * Simple re-encoding fallback without processing
     */
    async _simpleReencode(blob) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const arrayBuffer = await blob.arrayBuffer();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            
            const destination = audioContext.createMediaStreamDestination();
            source.connect(destination);
            
            const mimeTypes = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/ogg;codecs=opus'
            ];
            
            let selectedMimeType = 'audio/webm';
            for (const mimeType of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mimeType)) {
                    selectedMimeType = mimeType;
                    break;
                }
            }
            
            const recorder = new MediaRecorder(destination.stream, {
                mimeType: selectedMimeType,
                audioBitsPerSecond: this.options.compressionBitrate
            });
            
            return new Promise((resolve, reject) => {
                const chunks = [];
                recorder.ondataavailable = (e) => {
                    if (e.data.size > 0) chunks.push(e.data);
                };
                recorder.onstop = () => {
                    const reencodedBlob = new Blob(chunks, { type: selectedMimeType });
                    audioContext.close();
                    resolve(reencodedBlob);
                };
                recorder.onerror = () => {
                    audioContext.close();
                    reject(new Error('Re-encoding failed'));
                };
                
                source.start(0);
                recorder.start();
                
                setTimeout(() => {
                    recorder.stop();
                    source.stop();
                }, audioBuffer.duration * 1000 + 100);
            });
        } catch (error) {
            console.warn('Re-encoding failed, returning original:', error);
            return blob;
        }
    }

    /**
     * Upload audio with background support and progress tracking
     */
    async uploadAudio(formData, options = {}) {
        const uploadOptions = {
            keepalive: true, // Enable background upload
            signal: null,
            ...options
        };

        // Create AbortController for cancellation
        this.uploadController = new AbortController();
        if (uploadOptions.signal) {
            uploadOptions.signal.addEventListener('abort', () => {
                this.uploadController.abort();
            });
        }

        try {
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && this.options.onProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.options.onProgress(percentComplete);
                }
            });

            // Handle completion
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (this.options.onComplete) {
                            this.options.onComplete(response);
                        }
                    } catch (e) {
                        if (this.options.onComplete) {
                            this.options.onComplete({ success: true });
                        }
                    }
                } else {
                    this._handleError(`Upload failed: ${xhr.status} ${xhr.statusText}`);
                }
            });

            // Handle errors
            xhr.addEventListener('error', () => {
                this._handleError('Error de red al subir el audio.');
            });

            xhr.addEventListener('abort', () => {
                this._handleError('Subida cancelada.');
            });

            // Use fetch with keepalive for background uploads (fallback)
            // XHR doesn't support keepalive, so we'll use fetch as primary
            const fetchOptions = {
                method: 'POST',
                body: formData,
                keepalive: true,
                signal: this.uploadController.signal,
                credentials: 'include', // Include CSRF token
            };

            // Use fetch with keepalive for background upload support
            const response = await fetch(this.options.uploadUrl, fetchOptions);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Upload failed: ${response.status} ${errorText}`);
            }

            const result = await response.json();
            if (this.options.onComplete) {
                this.options.onComplete(result);
            }
            
            return result;
        } catch (error) {
            if (error.name === 'AbortError') {
                this._handleError('Subida cancelada.');
            } else {
                this._handleError('Error al subir el audio: ' + error.message);
            }
            throw error;
        }
    }

    /**
     * Get processed audio blob for preview (with fade-in and processing applied)
     */
    async getProcessedAudioBlob() {
        if (this.audioChunks.length === 0) {
            return null;
        }

        try {
            // Combine chunks into single blob
            const audioBlob = new Blob(this.audioChunks, { 
                type: this.mediaRecorder?.mimeType || 'audio/webm' 
            });

            // Process audio to add fade-in and prevent clipping
            const processedBlob = await this.compressAudio(audioBlob);
            return processedBlob;
        } catch (error) {
            console.warn('Failed to process audio for preview, using original:', error);
            // Fallback to original if processing fails
            return new Blob(this.audioChunks, { 
                type: this.mediaRecorder?.mimeType || 'audio/webm' 
            });
        }
    }

    /**
     * Process recorded audio and upload
     */
    async processAndUpload(metadata = {}) {
        if (this.audioChunks.length === 0) {
            this._handleError('No hay audio grabado para subir.');
            return false;
        }

        try {
            // Combine chunks into single blob
            const audioBlob = new Blob(this.audioChunks, { 
                type: this.mediaRecorder.mimeType || 'audio/webm' 
            });

            // Compress if needed
            const compressedBlob = await this.compressAudio(audioBlob);
            
            // Create FormData
            const formData = new FormData();
            formData.append('file', compressedBlob, `recording_${Date.now()}.webm`);
            
            // Add metadata
            Object.keys(metadata).forEach(key => {
                if (metadata[key] !== null && metadata[key] !== undefined) {
                    formData.append(key, metadata[key]);
                }
            });

            // Upload with background support
            await this.uploadAudio(formData);
            
            return true;
        } catch (error) {
            this._handleError('Error al procesar el audio: ' + error.message);
            return false;
        }
    }

    /**
     * Handle recording stop
     */
    _handleRecordingStop() {
        this.isRecording = false;
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    /**
     * Handle errors
     */
    _handleError(message) {
        if (this.options.onError) {
            this.options.onError(message);
        } else {
            console.error('AudioRecorder error:', message);
        }
    }

    /**
     * Cleanup resources
     */
    destroy() {
        this.cancelRecording();
        if (this.uploadController) {
            this.uploadController.abort();
        }
        this.mediaRecorder = null;
        this.audioChunks = [];
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioRecorder;
}

// Make available globally
window.AudioRecorder = AudioRecorder;
