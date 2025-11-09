/**
 * Audio recording integration for job submission forms
 * Attaches recorded audio to file input for form submission
 */

(function() {
    'use strict';

    class JobSubmissionAudio {
        constructor(container, options = {}) {
            this.container = container;
            this.fileInputId = container.dataset.fileInputId || 'audio_file';
            this.fileInput = document.getElementById(this.fileInputId);
            
            if (!this.fileInput) {
                console.error(`File input #${this.fileInputId} not found`);
                return;
            }

            this.options = {
                maxDuration: options.maxDuration || 300000, // 5 minutes default for job submissions
                compressionBitrate: options.compressionBitrate || 192000,
                ...options
            };

            this.recorder = new AudioRecorder({
                maxDuration: this.options.maxDuration,
                compressionBitrate: this.options.compressionBitrate,
                onError: (error) => this._handleError(error)
            });

            this.recordingInterval = null;
            this.recordedBlob = null;
            
            this._initializeUI();
        }

        _initializeUI() {
            // Get UI elements
            this.startBtn = this.container.querySelector('#btn-start-recording-audio');
            this.retryBtn = this.container.querySelector('#btn-retry-recording-audio');
            this.stopBtn = this.container.querySelector('#btn-stop-recording-audio');
            this.cancelBtn = this.container.querySelector('#btn-cancel-recording-audio');
            this.statusDiv = this.container.querySelector('#recording-status-audio');
            this.timeSpan = this.container.querySelector('#recording-time-audio');
            this.previewDiv = this.container.querySelector('#recording-preview-audio');
            this.previewAudio = this.container.querySelector('#recording-audio-preview-audio');

            if (!this.startBtn || !this.stopBtn || !this.cancelBtn) {
                console.error('Recording UI elements not found');
                return;
            }

            // Bind event handlers
            this.startBtn.addEventListener('click', () => this._startRecording());
            this.retryBtn?.addEventListener('click', () => this._retryRecording());
            this.stopBtn.addEventListener('click', () => this._stopRecording());
            this.cancelBtn.addEventListener('click', () => this._cancelRecording());

            // Handle file input changes (if user uploads a file instead)
            this.fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0 && this.recordedBlob) {
                    // User uploaded a file, clear recorded audio
                    this._clearRecording();
                }
            });
        }

        async _startRecording() {
            if (!AudioRecorder.isSupported()) {
                this._showError('Your browser does not support audio recording. Please upload an audio file instead.');
                return;
            }

            const started = await this.recorder.startRecording();
            if (!started) {
                return; // Error already handled by recorder
            }

            // Update UI
            this.startBtn.style.display = 'none';
            this.retryBtn.style.display = 'none';
            this.stopBtn.style.display = 'inline-flex';
            this.cancelBtn.style.display = 'inline-flex';
            this.statusDiv.style.display = 'flex';
            this.previewDiv.style.display = 'none';

            // Start duration timer
            this.recordingInterval = setInterval(() => {
                const duration = this.recorder.getFormattedDuration();
                this.timeSpan.textContent = duration;
                
                // Check max duration
                if (this.recorder.getDuration() >= this.options.maxDuration) {
                    this._stopRecording();
                }
            }, 100);
        }

        _stopRecording() {
            const stopped = this.recorder.stopRecording();
            if (!stopped) return;

            // Clear interval
            if (this.recordingInterval) {
                clearInterval(this.recordingInterval);
                this.recordingInterval = null;
            }

            // Update UI
            this.startBtn.style.display = 'none';
            this.retryBtn.style.display = 'none';
            this.stopBtn.style.display = 'none';
            this.cancelBtn.style.display = 'none';
            this.statusDiv.style.display = 'none';

            // Process and attach to file input
            this._processAndAttach();
        }

        _cancelRecording() {
            this.recorder.cancelRecording();
            
            if (this.recordingInterval) {
                clearInterval(this.recordingInterval);
                this.recordingInterval = null;
            }

            this._clearRecording();
        }

        _retryRecording() {
            this._clearRecording();
        }

        async _processAndAttach() {
            if (this.recorder.audioChunks.length === 0) {
                return;
            }

            // Show loading state
            this.previewDiv.style.display = 'block';
            this.previewAudio.style.display = 'none';
            const loadingText = document.createElement('p');
            loadingText.textContent = 'Processing audio...';
            loadingText.className = 'processing-message';
            this.previewDiv.insertBefore(loadingText, this.previewAudio);

            try {
                // Get processed audio blob
                const processedBlob = await this.recorder.getProcessedAudioBlob();
                
                // Remove loading message
                const loadingMsg = this.previewDiv.querySelector('.processing-message');
                if (loadingMsg) loadingMsg.remove();

                if (processedBlob) {
                    this.recordedBlob = processedBlob;
                    
                    // Create a File object from the blob
                    const fileName = `recording_${Date.now()}.webm`;
                    const file = new File([processedBlob], fileName, {
                        type: processedBlob.type || 'audio/webm'
                    });

                    // Attach to file input using DataTransfer
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    this.fileInput.files = dataTransfer.files;

                    // Trigger change event so form knows there's a file
                    this.fileInput.dispatchEvent(new Event('change', { bubbles: true }));

                    // Show preview
                    const audioUrl = URL.createObjectURL(processedBlob);
                    this.previewAudio.src = audioUrl;
                    this.previewAudio.style.display = 'block';

                    // Show retry button
                    this.retryBtn.style.display = 'inline-flex';
                } else {
                    throw new Error('Failed to process audio');
                }
            } catch (error) {
                console.error('Error processing audio:', error);
                const loadingMsg = this.previewDiv.querySelector('.processing-message');
                if (loadingMsg) loadingMsg.remove();
                
                this._showError('Error processing audio. Please try again or upload a file.');
                this._clearRecording();
            }
        }

        _clearRecording() {
            // Clean up preview audio
            if (this.previewAudio.src) {
                URL.revokeObjectURL(this.previewAudio.src);
                this.previewAudio.src = '';
            }

            // Clear file input
            this.fileInput.value = '';
            this.recordedBlob = null;

            // Reset UI
            this.startBtn.style.display = 'inline-flex';
            this.retryBtn.style.display = 'none';
            this.stopBtn.style.display = 'none';
            this.cancelBtn.style.display = 'none';
            this.statusDiv.style.display = 'none';
            this.previewDiv.style.display = 'none';

            // Clear any error messages
            const existingMessage = this.container.querySelector('.audio-message');
            if (existingMessage) {
                existingMessage.remove();
            }
        }

        _handleError(message) {
            this._showError(message);
        }

        _showError(message) {
            // Remove existing messages
            const existing = this.container.querySelector('.audio-message');
            if (existing) {
                existing.remove();
            }

            const messageDiv = document.createElement('div');
            messageDiv.className = 'audio-message audio-message-error';
            messageDiv.setAttribute('role', 'alert');
            messageDiv.textContent = message;

            this.container.insertBefore(messageDiv, this.container.firstChild);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }

        destroy() {
            if (this.recordingInterval) {
                clearInterval(this.recordingInterval);
            }
            this.recorder.destroy();
            this._clearRecording();
        }
    }

    // Auto-initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        const containers = document.querySelectorAll('[data-audio-recording]');
        containers.forEach(container => {
            const fileInputId = container.dataset.fileInputId;
            if (!fileInputId) {
                console.warn('data-file-input-id attribute missing on audio recording container');
                return;
            }

            new JobSubmissionAudio(container, {
                maxDuration: parseInt(container.dataset.maxDuration) || 300000, // 5 minutes default
                compressionBitrate: parseInt(container.dataset.compressionBitrate) || 192000
            });
        });
    });

    // Export for manual initialization
    window.JobSubmissionAudio = JobSubmissionAudio;
})();
