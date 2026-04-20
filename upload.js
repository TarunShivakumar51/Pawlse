// File upload handler with S3 presigned URL flow
// Drop this in your FastAPI static directory

// CONFIGURATION - Update this to match your FastAPI endpoint
const BACKEND_URL = '/api/presigned-url';

// DOM elements
let uploadZone, fileInput, fileInfo, fileName, fileMeta, progressBar, progressFill, status;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    uploadZone = document.getElementById('uploadZone');
    fileInput = document.getElementById('fileInput');
    fileInfo = document.getElementById('fileInfo');
    fileName = document.getElementById('fileName');
    fileMeta = document.getElementById('fileMeta');
    progressBar = document.getElementById('progressBar');
    progressFill = document.getElementById('progressFill');
    status = document.getElementById('status');

    setupEventListeners();
});

function setupEventListeners() {
    // Click to upload
    uploadZone.addEventListener('click', () => fileInput.click());

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragging');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragging');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragging');
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file);
    });
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showStatus(message, type, details = null) {
    status.innerHTML = message;
    status.className = `status visible ${type}`;
    
    if (details) {
        const codeBlock = document.createElement('div');
        codeBlock.className = 'code-block';
        codeBlock.textContent = JSON.stringify(details, null, 2);
        status.appendChild(codeBlock);
    }
}

async function handleFile(file) {
    // Show file info
    fileName.textContent = file.name;
    fileMeta.textContent = `${file.type || 'unknown type'} • ${formatBytes(file.size)}`;
    fileInfo.classList.add('visible');

    // Reset status and progress
    status.classList.remove('visible');
    progressBar.classList.remove('visible');
    progressFill.style.width = '0%';

    try {
        // Step 1: Get presigned URL from FastAPI backend
        showStatus('⏳ Getting upload URL...', 'loading');
        
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: file.name,
                content_type: file.type || 'application/octet-stream'
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        
        if (!data.upload_url) {
            throw new Error('No upload_url in response');
        }

        showStatus('✓ Got presigned URL', 'success', { 
            url: data.upload_url.substring(0, 100) + '...' 
        });

        // Step 2: Upload to S3 using presigned URL
        await uploadToS3(file, data.upload_url);

    } catch (error) {
        showStatus(`✗ Error: ${error.message}`, 'error');
        console.error('Upload error:', error);
    }
}

async function uploadToS3(file, uploadUrl) {
    showStatus('⏳ Uploading to S3...', 'loading');
    progressBar.classList.add('visible');

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressFill.style.width = percentComplete + '%';
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                showStatus('✓ Upload complete!', 'success', { 
                    status: xhr.status,
                    uploaded: formatBytes(file.size)
                });
                resolve();
            } else {
                reject(new Error(`S3 upload failed: ${xhr.status}`));
            }
        });

        xhr.addEventListener('error', () => {
            reject(new Error('Network error during upload'));
        });

        xhr.open('PUT', uploadUrl);
        xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
        xhr.send(file);
    });
}