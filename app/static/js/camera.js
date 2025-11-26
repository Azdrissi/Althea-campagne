// LocalCampaign - Module de capture photo via webcam

let currentStream = null;
let currentStudentId = null;
let currentPhotoType = null;

const cameraModalHTML = `
<div class="modal fade" id="cameraModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title">
                    <i class="bi bi-camera me-2"></i>Capture Photo
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="text-center">
                    <video id="video-preview" autoplay playsinline style="max-width: 100%; border-radius: 8px;"></video>
                    <canvas id="photo-canvas" style="display: none;"></canvas>
                    <div id="photo-result" style="display: none;">
                        <img id="captured-photo" style="max-width: 100%; border-radius: 8px;">
                    </div>
                    <div id="countdown" class="display-4 text-primary mt-3" style="display: none;"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" onclick="stopCamera()" data-bs-dismiss="modal">
                    <i class="bi bi-x-circle me-1"></i>Annuler
                </button>
                <button type="button" id="btn-capture" class="btn btn-primary" onclick="startCountdown()">
                    <i class="bi bi-camera me-1"></i>Capturer (3s)
                </button>
                <button type="button" id="btn-save" class="btn btn-success" style="display: none;" onclick="savePhoto()">
                    <i class="bi bi-check-circle me-1"></i>Enregistrer
                </button>
                <button type="button" id="btn-retake" class="btn btn-warning" style="display: none;" onclick="retakePhoto()">
                    <i class="bi bi-arrow-counterclockwise me-1"></i>Reprendre
                </button>
            </div>
        </div>
    </div>
</div>
`;

document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('cameraModal')) {
        document.body.insertAdjacentHTML('beforeend', cameraModalHTML);
    }
});

async function capturePhoto(type, studentId) {
    currentPhotoType = type;
    currentStudentId = studentId;

    const modal = new bootstrap.Modal(document.getElementById('cameraModal'));
    modal.show();

    document.getElementById('video-preview').style.display = 'block';
    document.getElementById('photo-result').style.display = 'none';
    document.getElementById('btn-capture').style.display = 'inline-block';
    document.getElementById('btn-save').style.display = 'none';
    document.getElementById('btn-retake').style.display = 'none';
    document.getElementById('countdown').style.display = 'none';

    try {
        currentStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'user',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        });

        const video = document.getElementById('video-preview');
        video.srcObject = currentStream;
        video.play();

    } catch (error) {
        console.error('Erreur caméra:', error);
        alert('Impossible d\'accéder à la caméra. Vérifiez les permissions.');
        modal.hide();
    }
}

function startCountdown() {
    const countdownEl = document.getElementById('countdown');
    const btnCapture = document.getElementById('btn-capture');

    btnCapture.disabled = true;
    countdownEl.style.display = 'block';

    let count = 3;
    countdownEl.textContent = count;

    const interval = setInterval(() => {
        count--;
        if (count > 0) {
            countdownEl.textContent = count;
        } else {
            clearInterval(interval);
            countdownEl.style.display = 'none';
            takePicture();
            btnCapture.disabled = false;
        }
    }, 1000);
}

function takePicture() {
    const video = document.getElementById('video-preview');
    const canvas = document.getElementById('photo-canvas');
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = canvas.toDataURL('image/jpeg', 0.85);

    const capturedPhoto = document.getElementById('captured-photo');
    capturedPhoto.src = imageData;

    stopCamera();

    document.getElementById('video-preview').style.display = 'none';
    document.getElementById('photo-result').style.display = 'block';
    document.getElementById('btn-capture').style.display = 'none';
    document.getElementById('btn-save').style.display = 'inline-block';
    document.getElementById('btn-retake').style.display = 'inline-block';
}

async function retakePhoto() {
    document.getElementById('video-preview').style.display = 'block';
    document.getElementById('photo-result').style.display = 'none';
    document.getElementById('btn-capture').style.display = 'inline-block';
    document.getElementById('btn-save').style.display = 'none';
    document.getElementById('btn-retake').style.display = 'none';

    try {
        currentStream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'user' } 
        });

        const video = document.getElementById('video-preview');
        video.srcObject = currentStream;
        video.play();
    } catch (error) {
        console.error('Erreur caméra:', error);
        alert('Impossible de redémarrer la caméra.');
    }
}

function savePhoto() {
    const capturedPhoto = document.getElementById('captured-photo');
    const photoData = capturedPhoto.src;

    const btnSave = document.getElementById('btn-save');
    const originalText = btnSave.innerHTML;
    btnSave.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enregistrement...';
    btnSave.disabled = true;

    fetch('/photos/capture', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            student_id: currentStudentId,
            type: currentPhotoType,
            photo: photoData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (window.LocalCampaign) {
                LocalCampaign.showAlert('Photo enregistrée avec succès !', 'success');
            } else {
                alert('Photo enregistrée avec succès !');
            }

            const modal = bootstrap.Modal.getInstance(document.getElementById('cameraModal'));
            modal.hide();

            setTimeout(() => location.reload(), 500);
        } else {
            if (window.LocalCampaign) {
                LocalCampaign.showAlert('Erreur : ' + data.error, 'danger');
            } else {
                alert('Erreur : ' + data.error);
            }
            btnSave.innerHTML = originalText;
            btnSave.disabled = false;
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        if (window.LocalCampaign) {
            LocalCampaign.showAlert('Erreur lors de l\'enregistrement', 'danger');
        } else {
            alert('Erreur lors de l\'enregistrement');
        }
        btnSave.innerHTML = originalText;
        btnSave.disabled = false;
    });
}

function stopCamera() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const cameraModal = document.getElementById('cameraModal');
    if (cameraModal) {
        cameraModal.addEventListener('hidden.bs.modal', function() {
            stopCamera();
        });
    }
});

console.log('✓ Module Camera chargé');
