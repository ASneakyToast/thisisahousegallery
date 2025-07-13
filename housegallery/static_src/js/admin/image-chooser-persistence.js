/**
 * Image Chooser Persistence Module
 * 
 * Persists image selections across pagination in Wagtail's MultipleChooserPanel
 * by storing selections in localStorage and restoring them when modal content reloads.
 */

class ImageChooserPersistence {
    constructor() {
        this.storagePrefix = 'wagtail_image_chooser_selections_';
        this.currentFieldName = null;
        this.isModalOpen = false;
        
        console.log('🔥 ImageChooserPersistence: Initializing...');
        this.bindEvents();
        console.log('🔥 ImageChooserPersistence: Initialized successfully');
    }
    
    bindEvents() {
        // Listen for modal workflow events
        document.addEventListener('wagtail:modal-workflow-start', (e) => {
            this.handleModalStart(e);
        });
        
        document.addEventListener('wagtail:modal-workflow-response', (e) => {
            this.handleModalResponse(e);
        });
        
        document.addEventListener('wagtail:modal-workflow-close', (e) => {
            this.handleModalClose(e);
        });
        
        // Listen for selection changes via event delegation
        document.addEventListener('change', (e) => {
            if (this.isImageChooserCheckbox(e.target)) {
                this.handleSelectionChange(e.target);
            }
        });
    }
    
    handleModalStart(event) {
        console.log('🔥 Modal workflow start event:', event);
        // Check if this is an image chooser modal
        const modal = event.detail.modal;
        console.log('🔥 Modal element:', modal);
        if (this.isImageChooserModal(modal)) {
            console.log('🔥 Image chooser modal detected');
            this.isModalOpen = true;
            this.currentFieldName = this.extractFieldName(modal);
            console.log('🔥 Field name extracted:', this.currentFieldName);
        }
    }
    
    handleModalResponse(event) {
        // Only handle if we're in an image chooser modal
        if (this.isModalOpen && this.currentFieldName) {
            // Small delay to ensure DOM is updated
            setTimeout(() => {
                this.restoreSelections();
            }, 100);
        }
    }
    
    handleModalClose(event) {
        // Clean up when modal closes
        if (this.isModalOpen) {
            // If the modal was closed with selections, clear the stored data
            const modal = event.detail.modal;
            if (this.isSuccessfulSelection(modal)) {
                this.clearStoredSelections();
            }
            
            this.isModalOpen = false;
            this.currentFieldName = null;
        }
    }
    
    handleSelectionChange(checkbox) {
        if (!this.isModalOpen || !this.currentFieldName) return;
        
        const imageId = this.extractImageId(checkbox);
        if (!imageId) return;
        
        let selections = this.getStoredSelections();
        
        if (checkbox.checked) {
            selections.add(imageId);
        } else {
            selections.delete(imageId);
        }
        
        this.storeSelections(selections);
    }
    
    isImageChooserModal(modal) {
        // Check if the modal contains image chooser elements
        const modalContent = modal.querySelector('.modal-content');
        return modalContent && (
            modalContent.querySelector('.image-chooser') ||
            modalContent.querySelector('.chooser-results') ||
            modalContent.querySelector('[data-chooser-type="image"]')
        );
    }
    
    isImageChooserCheckbox(element) {
        // Check if this is a checkbox in the image chooser
        return element.type === 'checkbox' && 
               element.name === 'image' &&
               this.isModalOpen;
    }
    
    extractFieldName(modal) {
        // Extract field name from modal URL or data attributes
        const iframe = modal.querySelector('iframe');
        if (iframe && iframe.src) {
            const url = new URL(iframe.src);
            const params = new URLSearchParams(url.search);
            return params.get('field_name') || 'default';
        }
        
        // Fallback: look for field name in modal data
        const fieldNameEl = modal.querySelector('[data-field-name]');
        if (fieldNameEl) {
            return fieldNameEl.getAttribute('data-field-name');
        }
        
        return 'default';
    }
    
    extractImageId(checkbox) {
        // Extract image ID from checkbox value or data attributes
        return checkbox.value || checkbox.getAttribute('data-image-id');
    }
    
    isSuccessfulSelection(modal) {
        // Check if the modal was closed due to successful selection
        // This is a heuristic - we assume success if modal has selected items
        return modal.querySelector('.chosen') || 
               modal.querySelector('[data-chosen="true"]');
    }
    
    getStorageKey() {
        return this.storagePrefix + this.currentFieldName;
    }
    
    getStoredSelections() {
        const key = this.getStorageKey();
        const stored = localStorage.getItem(key);
        
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                return new Set(parsed);
            } catch (e) {
                console.warn('Failed to parse stored image selections:', e);
            }
        }
        
        return new Set();
    }
    
    storeSelections(selections) {
        const key = this.getStorageKey();
        const array = Array.from(selections);
        localStorage.setItem(key, JSON.stringify(array));
        console.log('🔥 Stored selections:', array, 'for key:', key);
    }
    
    clearStoredSelections() {
        const key = this.getStorageKey();
        localStorage.removeItem(key);
    }
    
    restoreSelections() {
        const selections = this.getStoredSelections();
        
        if (selections.size === 0) return;
        
        // Find all image checkboxes in the current modal view
        const checkboxes = document.querySelectorAll('input[type="checkbox"][name="image"]');
        
        checkboxes.forEach(checkbox => {
            const imageId = this.extractImageId(checkbox);
            if (imageId && selections.has(imageId)) {
                checkbox.checked = true;
                
                // Trigger change event to ensure any other listeners are notified
                const event = new Event('change', { bubbles: true });
                checkbox.dispatchEvent(event);
                
                // Add visual feedback if available
                const row = checkbox.closest('tr, .chooser-result');
                if (row) {
                    row.classList.add('selected');
                }
            }
        });
        
        console.log(`Restored ${selections.size} image selections for field: ${this.currentFieldName}`);
    }
}

// Initialize the persistence system when DOM is ready
console.log('🔥 Image chooser persistence script loaded, DOM state:', document.readyState);
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🔥 DOM loaded, initializing persistence');
        new ImageChooserPersistence();
    });
} else {
    console.log('🔥 DOM already loaded, initializing persistence immediately');
    new ImageChooserPersistence();
}

export default ImageChooserPersistence;