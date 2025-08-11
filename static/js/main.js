/**
 * e-Consulaire RDC - Main JavaScript File
 * Handles client-side functionality for the consular platform
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeFormValidation();
    initializeFileUpload();
    initializeTooltips();
    initializeAlerts();
    initializeLoadingStates();
    initializeFormHelpers();
    initializeDateValidation();
    initializeAccessibility();
});

/**
 * Form Validation Enhancement
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Real-time validation for required fields
        const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
        
        requiredFields.forEach(field => {
            field.addEventListener('blur', function() {
                validateField(field);
            });
            
            field.addEventListener('input', function() {
                if (field.classList.contains('is-invalid')) {
                    validateField(field);
                }
            });
        });
        
        // Email validation
        const emailFields = form.querySelectorAll('input[type="email"]');
        emailFields.forEach(field => {
            field.addEventListener('input', function() {
                validateEmail(field);
            });
        });
        
        // Password confirmation
        const passwordFields = form.querySelectorAll('input[name="password2"]');
        passwordFields.forEach(field => {
            field.addEventListener('input', function() {
                validatePasswordConfirmation(field);
            });
        });
        
        // Phone number formatting
        const phoneFields = form.querySelectorAll('input[name="phone"]');
        phoneFields.forEach(field => {
            field.addEventListener('input', function() {
                formatPhoneNumber(field);
            });
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    
    if (isRequired && !value) {
        setFieldInvalid(field, 'Ce champ est obligatoire.');
        return false;
    } else {
        setFieldValid(field);
        return true;
    }
}

function validateEmail(field) {
    const email = field.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (email && !emailRegex.test(email)) {
        setFieldInvalid(field, 'Veuillez entrer une adresse email valide.');
        return false;
    } else {
        setFieldValid(field);
        return true;
    }
}

function validatePasswordConfirmation(field) {
    const password = document.querySelector('input[name="password"]');
    const passwordConfirm = field;
    
    if (password && passwordConfirm.value !== password.value) {
        setFieldInvalid(passwordConfirm, 'Les mots de passe ne correspondent pas.');
        return false;
    } else {
        setFieldValid(passwordConfirm);
        return true;
    }
}

function formatPhoneNumber(field) {
    let value = field.value.replace(/\D/g, '');
    
    // Format for international numbers starting with country code
    if (value.startsWith('243')) {
        value = value.replace(/^(\d{3})(\d{2})(\d{3})(\d{4})$/, '+$1 $2 $3 $4');
    } else if (value.startsWith('0')) {
        // Domestic format
        value = value.replace(/^(\d{1})(\d{2})(\d{3})(\d{4})$/, '$1$2 $3 $4');
    }
    
    field.value = value;
}

function setFieldInvalid(field, message) {
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
    
    let feedback = field.parentNode.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        field.parentNode.appendChild(feedback);
    }
    feedback.textContent = message;
}

function setFieldValid(field) {
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
    
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

/**
 * File Upload Enhancement
 */
function initializeFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            handleFileSelection(e.target);
        });
        
        // Drag and drop functionality
        const wrapper = createFileDropZone(input);
        if (wrapper) {
            setupDragAndDrop(wrapper, input);
        }
    });
}

function handleFileSelection(input) {
    const files = Array.from(input.files);
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
    
    files.forEach((file, index) => {
        // Size validation
        if (file.size > maxSize) {
            setFieldInvalid(input, `Le fichier "${file.name}" est trop volumineux (max 16MB).`);
            input.value = '';
            return;
        }
        
        // Type validation
        if (!allowedTypes.includes(file.type)) {
            setFieldInvalid(input, `Le fichier "${file.name}" n'est pas d'un type autorisé.`);
            input.value = '';
            return;
        }
        
        setFieldValid(input);
        displayFilePreview(input, file);
    });
}

function createFileDropZone(input) {
    if (input.parentNode.classList.contains('file-drop-zone')) {
        return input.parentNode;
    }
    
    const wrapper = document.createElement('div');
    wrapper.className = 'file-drop-zone';
    wrapper.innerHTML = `
        <div class="drop-zone-content">
            <i class="fas fa-cloud-upload-alt fa-2x text-muted mb-2"></i>
            <p class="mb-1">Glissez-déposez vos fichiers ici ou</p>
            <p class="mb-0"><small class="text-muted">Cliquez pour sélectionner</small></p>
        </div>
    `;
    
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    
    return wrapper;
}

function setupDragAndDrop(wrapper, input) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        wrapper.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        wrapper.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        wrapper.addEventListener(eventName, unhighlight, false);
    });
    
    wrapper.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        input.files = files;
        handleFileSelection(input);
    }, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        wrapper.classList.add('drag-over');
    }
    
    function unhighlight() {
        wrapper.classList.remove('drag-over');
    }
}

function displayFilePreview(input, file) {
    let previewContainer = input.parentNode.querySelector('.file-preview');
    
    if (!previewContainer) {
        previewContainer = document.createElement('div');
        previewContainer.className = 'file-preview mt-2';
        input.parentNode.appendChild(previewContainer);
    }
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item d-flex align-items-center p-2 border rounded mb-2';
    
    const fileIcon = getFileIcon(file.type);
    const fileSize = formatFileSize(file.size);
    
    fileItem.innerHTML = `
        <i class="${fileIcon} me-2"></i>
        <div class="flex-grow-1">
            <div class="fw-medium">${file.name}</div>
            <small class="text-muted">${fileSize}</small>
        </div>
        <i class="fas fa-check-circle text-success"></i>
    `;
    
    previewContainer.appendChild(fileItem);
}

function getFileIcon(mimeType) {
    if (mimeType.startsWith('image/')) {
        return 'fas fa-image text-info';
    } else if (mimeType === 'application/pdf') {
        return 'fas fa-file-pdf text-danger';
    } else {
        return 'fas fa-file text-secondary';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Tooltips Initialization
 */
function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add tooltips to help icons
    const helpIcons = document.querySelectorAll('.help-icon');
    helpIcons.forEach(icon => {
        if (!icon.hasAttribute('data-bs-toggle')) {
            icon.setAttribute('data-bs-toggle', 'tooltip');
            icon.setAttribute('data-bs-placement', 'top');
            new bootstrap.Tooltip(icon);
        }
    });
}

/**
 * Alert Auto-dismiss
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        // Auto-dismiss success and info alerts after 5 seconds
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
}

/**
 * Loading States for Forms
 */
function initializeLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
            
            if (submitButton && !form.classList.contains('no-loading')) {
                // Store original text and disable button
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Traitement en cours...';
                submitButton.disabled = true;
                
                // Re-enable if there are validation errors
                setTimeout(() => {
                    if (form.querySelector('.is-invalid')) {
                        submitButton.innerHTML = originalText;
                        submitButton.disabled = false;
                    }
                }, 100);
                
                // Fallback to re-enable after 30 seconds
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 30000);
            }
        });
    });
}

/**
 * Form Helpers and Enhancements
 */
function initializeFormHelpers() {
    // Character counter for textareas
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(textarea => {
        addCharacterCounter(textarea);
    });
    
    // Auto-resize textareas
    const autoResizeTextareas = document.querySelectorAll('textarea.auto-resize');
    autoResizeTextareas.forEach(textarea => {
        autoResize(textarea);
        textarea.addEventListener('input', () => autoResize(textarea));
    });
    
    // Conditional fields based on select values
    initializeConditionalFields();
}

function addCharacterCounter(textarea) {
    const maxLength = parseInt(textarea.getAttribute('maxlength'));
    const counter = document.createElement('div');
    counter.className = 'character-counter text-muted small text-end mt-1';
    
    function updateCounter() {
        const remaining = maxLength - textarea.value.length;
        counter.textContent = `${remaining} caractères restants`;
        
        if (remaining < 10) {
            counter.classList.add('text-warning');
            counter.classList.remove('text-muted');
        } else {
            counter.classList.remove('text-warning');
            counter.classList.add('text-muted');
        }
    }
    
    textarea.parentNode.appendChild(counter);
    updateCounter();
    textarea.addEventListener('input', updateCounter);
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

function initializeConditionalFields() {
    // Handle "other" option fields
    const selects = document.querySelectorAll('select');
    selects.forEach(select => {
        const fieldName = select.name;
        const otherField = document.getElementById(fieldName + '_other_field') || 
                          document.querySelector(`[id*="${fieldName}_other"]`);
        
        if (otherField) {
            select.addEventListener('change', function() {
                if (this.value === 'autre' || this.value === 'other') {
                    otherField.style.display = 'block';
                    const input = otherField.querySelector('input, textarea');
                    if (input) input.required = true;
                } else {
                    otherField.style.display = 'none';
                    const input = otherField.querySelector('input, textarea');
                    if (input) {
                        input.required = false;
                        input.value = '';
                    }
                }
            });
            
            // Trigger on page load
            select.dispatchEvent(new Event('change'));
        }
    });
}

/**
 * Date Validation
 */
function initializeDateValidation() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(input => {
        // Set reasonable min/max dates if not already set
        if (!input.min && input.name.includes('birth')) {
            const minDate = new Date();
            minDate.setFullYear(minDate.getFullYear() - 100);
            input.min = minDate.toISOString().split('T')[0];
        }
        
        if (!input.max && input.name.includes('birth')) {
            const maxDate = new Date();
            maxDate.setFullYear(maxDate.getFullYear() - 16); // Minimum 16 years old
            input.max = maxDate.toISOString().split('T')[0];
        }
        
        // Set minimum date for appointments to tomorrow
        if (input.name.includes('preferred_date') || input.name.includes('appointment')) {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            input.min = tomorrow.toISOString().split('T')[0];
        }
        
        input.addEventListener('change', function() {
            validateDateInput(this);
        });
    });
}

function validateDateInput(input) {
    const value = new Date(input.value);
    const min = input.min ? new Date(input.min) : null;
    const max = input.max ? new Date(input.max) : null;
    
    if (min && value < min) {
        setFieldInvalid(input, `La date doit être postérieure au ${formatDate(min)}.`);
        return false;
    }
    
    if (max && value > max) {
        setFieldInvalid(input, `La date doit être antérieure au ${formatDate(max)}.`);
        return false;
    }
    
    setFieldValid(input);
    return true;
}

function formatDate(date) {
    return date.toLocaleDateString('fr-FR');
}

/**
 * Accessibility Enhancements
 */
function initializeAccessibility() {
    // Add aria-labels to buttons without text
    const iconButtons = document.querySelectorAll('button:not([aria-label]) i.fa');
    iconButtons.forEach(icon => {
        const button = icon.closest('button');
        if (button && !button.textContent.trim()) {
            // Try to determine purpose from icon class
            let label = 'Action';
            if (icon.classList.contains('fa-edit')) label = 'Modifier';
            else if (icon.classList.contains('fa-delete')) label = 'Supprimer';
            else if (icon.classList.contains('fa-download')) label = 'Télécharger';
            else if (icon.classList.contains('fa-eye')) label = 'Voir';
            else if (icon.classList.contains('fa-print')) label = 'Imprimer';
            
            button.setAttribute('aria-label', label);
        }
    });
    
    // Add focus management for modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const focusableElement = modal.querySelector('input, button, select, textarea');
            if (focusableElement) {
                focusableElement.focus();
            }
        });
    });
    
    // Announce dynamic content changes to screen readers
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.id = 'live-region';
    document.body.appendChild(liveRegion);
    
    window.announceToScreenReader = function(message) {
        liveRegion.textContent = message;
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    };
}

/**
 * Utility Functions
 */

// Debounce function for performance optimization
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Format currency
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Show confirmation dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copié dans le presse-papiers', 'success');
    } catch (err) {
        console.error('Erreur lors de la copie:', err);
        showNotification('Erreur lors de la copie', 'error');
    }
}

// Show notification toast
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Print specific element
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Impression</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body { margin: 20px; }
                        .no-print { display: none !important; }
                    </style>
                </head>
                <body>
                    ${element.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

// Export object for global access
window.eConsulaire = {
    debounce,
    formatCurrency,
    confirmAction,
    copyToClipboard,
    showNotification,
    printElement,
    announceToScreenReader: () => {} // Will be overridden after DOM load
};

// CSS for file upload styling
const fileUploadStyles = `
<style>
.file-drop-zone {
    border: 2px dashed #dee2e6;
    border-radius: 0.375rem;
    padding: 2rem;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
    position: relative;
}

.file-drop-zone:hover {
    border-color: #0d6efd;
    background-color: #f8f9ff;
}

.file-drop-zone.drag-over {
    border-color: #0d6efd;
    background-color: #e7f3ff;
    transform: scale(1.02);
}

.file-drop-zone input[type="file"] {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
}

.drop-zone-content {
    pointer-events: none;
}

.file-item {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6 !important;
    transition: all 0.2s ease;
}

.file-item:hover {
    background-color: #e9ecef;
}

.character-counter {
    margin-top: 0.25rem;
}

@media (max-width: 768px) {
    .file-drop-zone {
        padding: 1rem;
    }
}
</style>
`;

// Inject styles into the document
document.addEventListener('DOMContentLoaded', function() {
    const head = document.head || document.getElementsByTagName('head')[0];
    const style = document.createElement('div');
    style.innerHTML = fileUploadStyles;
    head.appendChild(style.firstElementChild);
});
