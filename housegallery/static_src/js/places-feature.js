/**
 * Places Feature - Interactive places layout with image filtering
 * Handles clicking on place cards to filter images in the gallery
 */

class PlacesFeature {
    constructor() {
        this.placesContainer = document.querySelector('.places-feature-layout');
        this.placeCards = document.querySelectorAll('.place-info-card');
        this.galleryItems = document.querySelectorAll('.places-image-pool .gallery-item');
        this.activePlace = null;
        this.expandedCards = new Set();
        
        if (this.placesContainer) {
            this.init();
        }
    }
    
    init() {
        this.setupEventListeners();
        this.setupKeyboardNavigation();
    }
    
    setupEventListeners() {
        // Add event delegation for accordion toggle
        this.placeCards.forEach(card => {
            card.addEventListener('click', (e) => {
                e.preventDefault();
                const action = e.target.closest('[data-action]')?.getAttribute('data-action');
                const placeId = card.getAttribute('data-place-id');
                
                if (action === 'toggle-accordion') {
                    this.toggleAccordionAndFilter(placeId, card);
                }
            });
        });
    }
    
    setupKeyboardNavigation() {
        // Add keyboard support for accordion headers
        this.placeCards.forEach(card => {
            const header = card.querySelector('[data-action="toggle-accordion"]');
            
            if (header) {
                header.setAttribute('tabindex', '0');
                header.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const placeId = card.getAttribute('data-place-id');
                        this.toggleAccordionAndFilter(placeId, card);
                    }
                });
            }
        });
    }
    
    toggleAccordionAndFilter(placeId, cardElement) {
        const isExpanded = this.expandedCards.has(placeId);
        
        // First, collapse all other accordions and clear their active states
        this.placeCards.forEach(card => {
            const otherPlaceId = card.getAttribute('data-place-id');
            if (otherPlaceId !== placeId) {
                this.expandedCards.delete(otherPlaceId);
                card.classList.remove('place-info-card--expanded', 'place-info-card--active');
            }
        });
        
        if (isExpanded) {
            // Collapse this accordion and show all images
            this.expandedCards.delete(placeId);
            cardElement.classList.remove('place-info-card--expanded', 'place-info-card--active');
            this.activePlace = null;
            this.showAllImages();
        } else {
            // Expand this accordion and filter images
            this.expandedCards.add(placeId);
            cardElement.classList.add('place-info-card--expanded', 'place-info-card--active');
            this.activePlace = placeId;
            this.filterImagesByPlace(placeId);
        }
    }
    
    filterImagesByPlace(placeId) {
        this.galleryItems.forEach(item => {
            const itemPlaceId = item.getAttribute('data-place-id');
            if (itemPlaceId === placeId) {
                item.style.display = 'inline-block';
                item.classList.add('gallery-item--highlighted');
            } else {
                item.style.display = 'none';
                item.classList.remove('gallery-item--highlighted');
            }
        });
        
        // Add visual feedback
        this.updateGalleryState(true);
    }
    
    showAllImages() {
        this.galleryItems.forEach(item => {
            item.style.display = 'inline-block';
            item.classList.remove('gallery-item--highlighted');
        });
        
        // Remove visual feedback
        this.updateGalleryState(false);
    }
    
    updateGalleryState(isFiltered) {
        const galleryContainer = document.querySelector('.places-image-pool');
        if (galleryContainer) {
            if (isFiltered) {
                galleryContainer.classList.add('places-image-pool--filtered');
            } else {
                galleryContainer.classList.remove('places-image-pool--filtered');
            }
        }
    }
    
    // Public method to reset the feature
    reset() {
        this.activePlace = null;
        this.expandedCards.clear();
        this.showAllImages();
        this.placeCards.forEach(card => {
            card.classList.remove('place-info-card--active', 'place-info-card--expanded');
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.placesFeature = new PlacesFeature();
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PlacesFeature;
}