// File Upload Validation Script for e-Consulaire RDC
// This script validates file sizes before form submission

// File size validation constants (in bytes)
const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB per file
const MAX_TOTAL_SIZE = 100 * 1024 * 1024; // 100MB total

/**
 * Initialize file upload validation for all file inputs on the page
 */
function initFileUploadValidation() {
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function(event) {
            const file = this.files[0];
            if (!file) return;
            
            // Check individual file size
            if (file.size > MAX_FILE_SIZE) {
                alert(`Le fichier "${file.name}" est trop volumineux (${(file.size / 1024 / 1024).toFixed(2)} MB).\n\nLa taille maximale par fichier est de 25 MB.\n\nVeuillez compresser ou réduire la qualité du fichier.`);
                this.value = ''; // Clear the file input
                return;
            }
            
            // Check total size of all files
            let totalSize = 0;
            document.querySelectorAll('input[type="file"]').forEach(fileInput => {
                if (fileInput.files[0]) {
                    totalSize += fileInput.files[0].size;
                }
            });
            
            if (totalSize > MAX_TOTAL_SIZE) {
                alert(`La taille totale des fichiers (${(totalSize / 1024 / 1024).toFixed(2)} MB) dépasse la limite de 100 MB.\n\nVeuillez réduire la taille ou le nombre de fichiers.`);
                this.value = ''; // Clear the file input
                return;
            }
            
            // Success - show file info
            console.log(`Fichier accepté: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
            console.log(`Taille totale: ${(totalSize / 1024 / 1024).toFixed(2)} MB / 100 MB`);
        });
    });
}

/**
 * Validate all files before form submission
 */
function validateFormBeforeSubmit(formElement) {
    let totalSize = 0;
    const files = formElement.querySelectorAll('input[type="file"]');
    
    for (const fileInput of files) {
        if (fileInput.files[0]) {
            const file = fileInput.files[0];
            
            // Check individual file size
            if (file.size > MAX_FILE_SIZE) {
                alert(`Le fichier "${file.name}" est trop volumineux (${(file.size / 1024 / 1024).toFixed(2)} MB).\n\nLa taille maximale par fichier est de 25 MB.`);
                return false;
            }
            
            totalSize += file.size;
        }
    }
    
    // Check total size
    if (totalSize > MAX_TOTAL_SIZE) {
        alert(`La taille totale des fichiers (${(totalSize / 1024 / 1024).toFixed(2)} MB) dépasse la limite de 100 MB.\n\nVeuillez réduire la taille des fichiers avant de soumettre.`);
        return false;
    }
    
    return true;
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFileUploadValidation);
} else {
    initFileUploadValidation();
}

// Add form validation on submit
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('form[enctype="multipart/form-data"]').forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateFormBeforeSubmit(this)) {
                event.preventDefault();
                return false;
            }
        });
    });
});
