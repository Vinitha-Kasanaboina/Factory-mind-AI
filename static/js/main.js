/* FactoryMind AI - Main JavaScript Utilities */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // File Upload Drag and Drop Enhancement
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('id_file');

    if (dropZone && fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('border-primary'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('border-primary'), false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            updateFileLabel(files[0]);
        });

        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                updateFileLabel(this.files[0]);
            }
        });

        function updateFileLabel(file) {
            const label = document.getElementById('fileNameDisplay');
            if (label) {
                label.innerHTML = `<i class="bi bi-file-earmark-check text-success me-2"></i><strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)`;
            }
        }
    }
});
