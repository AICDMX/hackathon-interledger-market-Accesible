/**
 * UI controller for audio contribution form with recording
 * Integrates AudioRecorder with the contribution form
 */

(function() {
    'use strict';

    class AudioContributionUI {
        constructor(containerId, options = {}) {
            this.container = document.getElementById(containerId);
            if (!this.container) {
                console.error(`Container #${containerId} not found`);
                return;
            }

            this.options = {
                maxDuration: options.maxDuration || 30000, // 30 seconds
                uploadUrl: options.uploadUrl || '/api/audio/contributions/upload/',
                csrfToken: options.csrfToken || this._getCSRFToken(),
                targetSlug: options.targetSlug || '',
                languageCode: options.languageCode || '',
                ...options
            };

            this.recorder = new AudioRecorder({
                maxDuration: this.options.maxDuration,
                compressionBitrate: this.options.compressionBitrate || 192000,
                uploadUrl: this.options.uploadUrl,
                onProgress: (percent) => this._handleUploadProgress(percent),
                onComplete: (result) => this._handleUploadComplete(result),
                onError: (error) => this._handleError(error)
            });

            this.recordingInterval = null;
            this.isUploading = false;
            
            this._initializeUI();
        }

        _getCSRFToken() {
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1];
            return cookieValue || '';
        }

        _initializeUI() {
            // Create recording UI elements
            this._createRecordingUI();
            
            // Bind file upload handler
            const fileInput = this.container.querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.addEventListener('change', (e) => this._handleFileSelect(e));
            }

            // Update form submission to handle recording
            const form = this.container.querySelector('form');
            if (form) {
                form.addEventListener('submit', (e) => this._handleFormSubmit(e));
            }
        }

        _createRecordingUI() {
            const form = this.container.querySelector('form');
            if (!form) return;

            // Create recording section
            const recordingSection = document.createElement('div');
            recordingSection.className = 'audio-recording-section';
            recordingSection.innerHTML = `
                <div class="recording-controls">
                    <button type="button" class="btn-record" id="btn-start-recording" aria-label="Iniciar grabaci?n">
                        <span class="record-icon" aria-hidden="true">??</span>
                        <span class="record-label">Grabar</span>
                    </button>
                    <button type="button" class="btn-retry" id="btn-retry-recording" style="display: none;" aria-label="Volver a grabar">
                        <span class="retry-icon" aria-hidden="true">??</span>
                        <span class="retry-label">Volver a grabar</span>
                    </button>
                    <button type="button" class="btn-stop" id="btn-stop-recording" style="display: none;" aria-label="Detener grabaci?n">
                        <span class="stop-icon" aria-hidden="true">?</span>
                        <span class="stop-label">Detener</span>
                    </button>
                    <button type="button" class="btn-cancel" id="btn-cancel-recording" style="display: none;" aria-label="Cancelar grabaci?n">
                        <span class="cancel-icon" aria-hidden="true">?</span>
                        <span class="cancel-label">Cancelar</span>
                    </button>
                </div>
                <div class="recording-status" id="recording-status" style="display: none;" role="status" aria-live="polite">
                    <span class="recording-indicator" aria-hidden="true">?</span>
                    <span class="recording-time" id="recording-time">0:00</span>
                </div>
                <div class="recording-preview" id="recording-preview" style="display: none;">
                    <audio controls id="recording-audio-preview"></audio>
                    <div class="preview-actions">
                        <button type="button" class="btn-upload-recording" id="btn-upload-recording">
                            Subir grabaci?n
                        </button>
                    </div>
                </div>
                <div class="upload-progress" id="upload-progress" style="display: none;" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
                    <div class="progress-bar" id="progress-bar"></div>
                    <span class="progress-text" id="progress-text">0%</span>
                </div>
            `;

            // Insert before file input
            const fileInputGroup = form.querySelector('.form-group:has(input[type="file"])');
            if (fileInputGroup) {
                fileInputGroup.parentNode.insertBefore(recordingSection, fileInputGroup);
            } else {
                form.insertBefore(recordingSection, form.firstChild);
            }

            // Bind recording buttons
            const startBtn = recordingSection.querySelector('#btn-start-recording');
            const retryBtn = recordingSection.querySelector('#btn-retry-recording');
            const stopBtn = recordingSection.querySelector('#btn-stop-recording');
            const cancelBtn = recordingSection.querySelector('#btn-cancel-recording');
            const uploadBtn = recordingSection.querySelector('#btn-upload-recording');

            startBtn?.addEventListener('click', () => this._startRecording());
            retryBtn?.addEventListener('click', () => this._retryRecording());
            stopBtn?.addEventListener('click', () => this._stopRecording());
            cancelBtn?.addEventListener('click', () => this._cancelRecording());
            uploadBtn?.addEventListener('click', () => this._uploadRecording());

            // Store references
            this.startBtn = startBtn;
            this.retryBtn = retryBtn;
            this.stopBtn = stopBtn;
            this.cancelBtn = cancelBtn;
            this.uploadBtn = uploadBtn;
            this.statusDiv = recordingSection.querySelector('#recording-status');
            this.timeSpan = recordingSection.querySelector('#recording-time');
            this.previewDiv = recordingSection.querySelector('#recording-preview');
            this.previewAudio = recordingSection.querySelector('#recording-audio-preview');
            this.progressDiv = recordingSection.querySelector('#upload-progress');
            this.progressBar = recordingSection.querySelector('#progress-bar');
            this.progressText = recordingSection.querySelector('#progress-text');
        }

        async _startRecording() {
            if (!AudioRecorder.isSupported()) {
                this._showError('Tu navegador no soporta grabaci?n de audio. Por favor, sube un archivo de audio.');
                return;
            }

            const started = await this.recorder.startRecording();
            if (!started) {
                return; // Error already handled by recorder
            }

            // Update UI
            this.startBtn.style.display = 'none';
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

            // Show preview with retry option
            this._showPreview();
        }

        _cancelRecording() {
            this.recorder.cancelRecording();
            
            if (this.recordingInterval) {
                clearInterval(this.recordingInterval);
                this.recordingInterval = null;
            }

            // Reset UI
            this.startBtn.style.display = 'inline-flex';
            this.retryBtn.style.display = 'none';
            this.stopBtn.style.display = 'none';
            this.cancelBtn.style.display = 'none';
            this.statusDiv.style.display = 'none';
            this.previewDiv.style.display = 'none';
            
            // Clean up preview if it exists
            if (this.previewAudio.src) {
                URL.revokeObjectURL(this.previewAudio.src);
                this.previewAudio.src = '';
            }
        }

        _retryRecording() {
            // Clear current recording
            this.recorder.cancelRecording();
            
            // Clean up preview audio
            if (this.previewAudio.src) {
                URL.revokeObjectURL(this.previewAudio.src);
                this.previewAudio.src = '';
            }
            
            // Clear any processing messages
            const loadingMsg = this.previewDiv.querySelector('.processing-message');
            if (loadingMsg) {
                loadingMsg.remove();
            }
            
            // Reset UI to initial state
            this.startBtn.style.display = 'inline-flex';
            this.retryBtn.style.display = 'none';
            this.stopBtn.style.display = 'none';
            this.cancelBtn.style.display = 'none';
            this.statusDiv.style.display = 'none';
            this.previewDiv.style.display = 'none';
            this.progressDiv.style.display = 'none';
            
            // Clear any error messages
            const existingMessage = this.container.querySelector('.audio-message');
            if (existingMessage) {
                existingMessage.remove();
            }
            
            // Reset upload button state
            if (this.uploadBtn) {
                this.uploadBtn.disabled = false;
                this.uploadBtn.textContent = 'Subir grabaci?n';
            }
        }

        _showPreview() {
            if (this.recorder.audioChunks.length === 0) {
                return;
            }

            // Show loading state
            this.previewDiv.style.display = 'block';
            this.previewAudio.style.display = 'none';
            const loadingText = document.createElement('p');
            loadingText.textContent = 'Procesando audio...';
            loadingText.className = 'processing-message';
            this.previewDiv.insertBefore(loadingText, this.previewAudio);

            // Get processed audio (with fade-in and clipping prevention)
            this.recorder.getProcessedAudioBlob().then(processedBlob => {
                // Remove loading message
                const loadingMsg = this.previewDiv.querySelector('.processing-message');
                if (loadingMsg) loadingMsg.remove();

                if (processedBlob) {
                    const audioUrl = URL.createObjectURL(processedBlob);
                    this.previewAudio.src = audioUrl;
                    this.previewAudio.style.display = 'block';
                } else {
                    // Fallback to original if processing failed
                    const audioBlob = new Blob(this.recorder.audioChunks, { 
                        type: this.recorder.mediaRecorder?.mimeType || 'audio/webm' 
                    });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    this.previewAudio.src = audioUrl;
                    this.previewAudio.style.display = 'block';
                }
            }).catch(error => {
                console.error('Error processing audio for preview:', error);
                // Fallback to original
                const loadingMsg = this.previewDiv.querySelector('.processing-message');
                if (loadingMsg) loadingMsg.remove();
                
                const audioBlob = new Blob(this.recorder.audioChunks, { 
                    type: this.recorder.mediaRecorder?.mimeType || 'audio/webm' 
                });
                const audioUrl = URL.createObjectURL(audioBlob);
                this.previewAudio.src = audioUrl;
                this.previewAudio.style.display = 'block';
            });
            
            // Show retry button instead of record button
            this.startBtn.style.display = 'none';
            this.retryBtn.style.display = 'inline-flex';
        }

        async _uploadRecording() {
            if (this.isUploading) return;

            const form = this.container.querySelector('form');
            const languageInput = form?.querySelector('input[name="language_code"]');
            const notesInput = form?.querySelector('textarea[name="notes"]');

            const metadata = {
                language_code: this.options.languageCode || languageInput?.value || '',
                notes: notesInput?.value || '',
                target_slug: this.options.targetSlug || ''
            };

            this.isUploading = true;
            this.uploadBtn.disabled = true;
            this.uploadBtn.textContent = 'Subiendo...';
            this.progressDiv.style.display = 'block';
            this.progressDiv.setAttribute('aria-valuenow', '0');

            try {
                await this.recorder.processAndUpload(metadata);
            } catch (error) {
                // Error handled by onError callback
            } finally {
                this.isUploading = false;
            }
        }

        _handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;

            // Validate file type
            if (!file.type.startsWith('audio/')) {
                this._showError('Por favor, selecciona un archivo de audio v?lido.');
                event.target.value = '';
                return;
            }

            // Validate file size (max 10MB)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                this._showError('El archivo es demasiado grande. M?ximo 10MB.');
                event.target.value = '';
                return;
            }
        }

        _handleFormSubmit(event) {
            // If recording is in progress, stop it first
            if (this.recorder.isRecording) {
                event.preventDefault();
                this._stopRecording();
                setTimeout(() => {
                    event.target.submit();
                }, 500);
                return;
            }

            // If there's a recording but not uploaded, prevent form submit
            if (this.recorder.audioChunks.length > 0 && !this.isUploading) {
                event.preventDefault();
                this._showError('Por favor, sube la grabaci?n o canc?lala antes de continuar.');
                return;
            }
        }

        _handleUploadProgress(percent) {
            const rounded = Math.round(percent);
            this.progressBar.style.width = `${rounded}%`;
            this.progressText.textContent = `${rounded}%`;
            this.progressDiv.setAttribute('aria-valuenow', rounded);
        }

        _handleUploadComplete(result) {
            this.progressDiv.style.display = 'none';
            this.uploadBtn.disabled = false;
            this.uploadBtn.textContent = 'Subir grabaci?n';

            // Show success message
            this._showSuccess('?Audio subido correctamente! El equipo lo revisar? antes de publicarlo.');

            // Reset recording
            this.recorder.audioChunks = [];
            this.previewDiv.style.display = 'none';
            if (this.previewAudio.src) {
                URL.revokeObjectURL(this.previewAudio.src);
                this.previewAudio.src = '';
            }
            
            // Reset UI to show record button again
            this.startBtn.style.display = 'inline-flex';
            this.retryBtn.style.display = 'none';

            // Optionally reload page or show success state
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        }

        _handleError(message) {
            this._showError(message);
            this.isUploading = false;
            if (this.uploadBtn) {
                this.uploadBtn.disabled = false;
                this.uploadBtn.textContent = 'Subir grabaci?n';
            }
            this.progressDiv.style.display = 'none';
        }

        _showError(message) {
            this._showMessage(message, 'error');
        }

        _showSuccess(message) {
            this._showMessage(message, 'success');
        }

        _showMessage(message, type) {
            // Remove existing messages
            const existing = this.container.querySelector('.audio-message');
            if (existing) {
                existing.remove();
            }

            const messageDiv = document.createElement('div');
            messageDiv.className = `audio-message audio-message-${type}`;
            messageDiv.setAttribute('role', 'alert');
            messageDiv.textContent = message;

            const form = this.container.querySelector('form');
            if (form) {
                form.insertBefore(messageDiv, form.firstChild);
            } else {
                this.container.insertBefore(messageDiv, this.container.firstChild);
            }

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
        }
    }

    // Auto-initialize if data attribute is present
    document.addEventListener('DOMContentLoaded', function() {
        const containers = document.querySelectorAll('[data-audio-contribution]');
        containers.forEach(container => {
            const containerId = container.id || `audio-contribution-${Math.random().toString(36).substr(2, 9)}`;
            if (!container.id) {
                container.id = containerId;
            }

            const options = {
                maxDuration: parseInt(container.dataset.maxDuration) || 30000,
                uploadUrl: container.dataset.uploadUrl || '/api/audio/contributions/upload/',
                targetSlug: container.dataset.targetSlug || '',
                languageCode: container.dataset.languageCode || '',
                compressionBitrate: parseInt(container.dataset.compressionBitrate) || 192000 // High quality default
            };

            new AudioContributionUI(containerId, options);
        });
    });

    // Export for manual initialization
    window.AudioContributionUI = AudioContributionUI;
})();
