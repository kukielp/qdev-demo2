// Configuration - Replace with your API Gateway URL after deployment
const API_URL = 'https://your-api-id.execute-api.your-region.amazonaws.com/Prod';

// DOM Elements
const uploadForm = document.getElementById('upload-form');
const photoFileInput = document.getElementById('photo-file');
const uploadButton = document.getElementById('upload-button');
const uploadStatus = document.getElementById('upload-status');
const photoList = document.getElementById('photo-list');
const noPhotosMessage = document.getElementById('no-photos-message');
const photoDetails = document.getElementById('photo-details');
const photoDisplay = document.getElementById('photo-display');
const photoFilename = document.getElementById('photo-filename');
const photoDate = document.getElementById('photo-date');
const photoId = document.getElementById('photo-id');
const downloadButton = document.getElementById('download-button');

// Store photo data
let photos = [];
let currentPhoto = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // For local development/testing, we'll use localStorage to simulate the backend
    loadPhotosFromLocalStorage();
    
    // In production, you would fetch photos from the API
    // fetchPhotos();
});

uploadForm.addEventListener('submit', handlePhotoUpload);
downloadButton.addEventListener('click', handlePhotoDownload);

// Functions
async function handlePhotoUpload(event) {
    event.preventDefault();
    
    if (!photoFileInput.files || photoFileInput.files.length === 0) {
        showStatus('Please select a photo to upload', 'error');
        return;
    }
    
    const file = photoFileInput.files[0];
    
    // Show loading state
    uploadButton.disabled = true;
    showStatus('Uploading photo...', 'info');
    
    try {
        // Read file as base64
        const fileContent = await readFileAsBase64(file);
        
        // Prepare request payload
        const payload = {
            fileName: file.name,
            fileContent: fileContent
        };
        
        // In production, you would call the API
        // const response = await uploadPhotoToAPI(payload);
        
        // For local development/testing, we'll simulate the API response
        const response = simulateUploadResponse(payload);
        
        // Add to local photos array
        photos.push(response);
        savePhotosToLocalStorage();
        
        // Update UI
        renderPhotoList();
        showStatus('Photo uploaded successfully!', 'success');
        
        // Reset form
        uploadForm.reset();
    } catch (error) {
        console.error('Upload error:', error);
        showStatus(`Upload failed: ${error.message}`, 'error');
    } finally {
        uploadButton.disabled = false;
    }
}

function handlePhotoDownload() {
    if (!currentPhoto) return;
    
    // In production, this would use the pre-signed URL from the API
    // window.open(currentPhoto.downloadUrl, '_blank');
    
    // For local development/testing, we'll create a download from the base64 data
    if (currentPhoto.fileContent) {
        const link = document.createElement('a');
        link.href = `data:image/jpeg;base64,${currentPhoto.fileContent}`;
        link.download = currentPhoto.fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function showPhotoDetails(photo) {
    currentPhoto = photo;
    
    // Update photo details
    photoFilename.textContent = photo.fileName;
    photoDate.textContent = formatDate(photo.uploadTimestamp);
    photoId.textContent = photo.photoId;
    
    // In production, this would use the pre-signed URL from the API
    // photoDisplay.src = photo.downloadUrl;
    
    // For local development/testing, we'll use the base64 data
    if (photo.fileContent) {
        photoDisplay.src = `data:image/jpeg;base64,${photo.fileContent}`;
    }
    
    // Show the details section
    photoDetails.style.display = 'block';
    
    // Scroll to the details section
    photoDetails.scrollIntoView({ behavior: 'smooth' });
}

function renderPhotoList() {
    // Clear current list
    while (photoList.firstChild) {
        if (photoList.firstChild === noPhotosMessage) break;
        photoList.removeChild(photoList.firstChild);
    }
    
    // Show/hide no photos message
    if (photos.length === 0) {
        noPhotosMessage.style.display = 'block';
        return;
    } else {
        noPhotosMessage.style.display = 'none';
    }
    
    // Add photos to list
    photos.forEach(photo => {
        const photoItem = document.createElement('div');
        photoItem.className = 'photo-item';
        photoItem.addEventListener('click', () => showPhotoDetails(photo));
        
        // Create thumbnail
        const thumbnail = document.createElement('img');
        if (photo.fileContent) {
            thumbnail.src = `data:image/jpeg;base64,${photo.fileContent}`;
        } else {
            thumbnail.src = 'placeholder.jpg'; // Add a placeholder image to your project
        }
        thumbnail.alt = photo.fileName;
        
        // Create info
        const info = document.createElement('div');
        info.className = 'photo-info';
        
        const name = document.createElement('p');
        name.textContent = photo.fileName;
        
        const date = document.createElement('p');
        date.className = 'photo-date';
        date.textContent = formatDate(photo.uploadTimestamp);
        
        info.appendChild(name);
        info.appendChild(date);
        
        photoItem.appendChild(thumbnail);
        photoItem.appendChild(info);
        
        photoList.appendChild(photoItem);
    });
}

function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `status ${type}`;
}

// Helper Functions
function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            // Extract base64 data (remove the data URL prefix)
            const base64String = reader.result.split(',')[1];
            resolve(base64String);
        };
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// API Functions
async function uploadPhotoToAPI(payload) {
    const response = await fetch(`${API_URL}/photos`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to upload photo');
    }
    
    return response.json();
}

async function fetchPhotoFromAPI(photoId) {
    const response = await fetch(`${API_URL}/photos/${photoId}`);
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to fetch photo');
    }
    
    return response.json();
}

// Local Storage Functions (for development/testing)
function savePhotosToLocalStorage() {
    localStorage.setItem('photos', JSON.stringify(photos));
}

function loadPhotosFromLocalStorage() {
    const storedPhotos = localStorage.getItem('photos');
    if (storedPhotos) {
        photos = JSON.parse(storedPhotos);
        renderPhotoList();
    }
}

// Simulate API Responses (for development/testing)
function simulateUploadResponse(payload) {
    return {
        photoId: generateUUID(),
        fileName: payload.fileName,
        uploadTimestamp: new Date().toISOString(),
        s3Key: `${generateUUID()}/${payload.fileName}`,
        fileContent: payload.fileContent // Only for local testing
    };
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}