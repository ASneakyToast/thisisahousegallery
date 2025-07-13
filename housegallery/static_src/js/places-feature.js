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
        this.isAnimating = false;
        this.animationQueue = [];
        
        if (this.placesContainer) {
            this.init();
        }
    }
    
    init() {
        this.setupEventListeners();
        this.setupKeyboardNavigation();
        this.setupResizeHandler();
        
        // Apply initial adaptive layout
        this.applyInitialLayout();
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
                card.setAttribute('data-state', 'inactive');
                const header = card.querySelector('[data-action="toggle-accordion"]');
                if (header) header.setAttribute('aria-expanded', 'false');
            }
        });
        
        if (isExpanded) {
            // Collapse this accordion and show all images
            this.expandedCards.delete(placeId);
            cardElement.setAttribute('data-state', 'inactive');
            const header = cardElement.querySelector('[data-action="toggle-accordion"]');
            if (header) header.setAttribute('aria-expanded', 'false');
            this.activePlace = null;
            this.showAllImages();
        } else {
            // Expand this accordion and filter images
            this.expandedCards.add(placeId);
            cardElement.setAttribute('data-state', 'active');
            const header = cardElement.querySelector('[data-action="toggle-accordion"]');
            if (header) header.setAttribute('aria-expanded', 'true');
            this.activePlace = placeId;
            this.filterImagesByPlace(placeId);
        }
    }
    
    filterImagesByPlace(placeId) {
        if (this.isAnimating) {
            this.animationQueue.push(() => this.filterImagesByPlace(placeId));
            return;
        }
        
        this.isAnimating = true;
        
        // Phase 1: Animate out items that will be hidden
        const itemsToHide = [];
        const itemsToShow = [];
        
        this.galleryItems.forEach(item => {
            const itemPlaceId = item.getAttribute('data-place-id');
            if (itemPlaceId === placeId) {
                itemsToShow.push(item);
            } else {
                itemsToHide.push(item);
            }
        });
        
        // Get adaptive layout settings
        const density = this.getContentDensity(itemsToShow.length);
        this.applyAdaptiveLayout(density);
        
        // Start hide animation with adaptive stagger
        itemsToHide.forEach((item, index) => {
            setTimeout(() => {
                item.classList.remove('gallery-item--visible', 'gallery-item--filtering-in');
                item.classList.add('gallery-item--filtering-out');
            }, index * density.staggerDelay); // Adaptive stagger delay
        });
        
        // After hide animation completes, show filtered items
        setTimeout(() => {
            // Hide items from DOM flow
            itemsToHide.forEach(item => {
                item.style.display = 'none';
                item.classList.remove('gallery-item--filtering-out', 'gallery-item--highlighted');
                item.classList.add('gallery-item--hidden');
            });
            
            // Show and animate in filtered items
            itemsToShow.forEach((item, index) => {
                item.style.display = 'inline-block';
                item.classList.remove('gallery-item--hidden', 'gallery-item--filtering-out');
                item.classList.add('gallery-item--highlighted');
                
                setTimeout(() => {
                    item.classList.add('gallery-item--filtering-in');
                    
                    // Clean up classes after animation
                    setTimeout(() => {
                        item.classList.remove('gallery-item--filtering-in');
                        item.classList.add('gallery-item--visible');
                        item.style.willChange = 'auto';
                    }, 400);
                }, index * Math.max(density.staggerDelay, 20) + 200); // Adaptive stagger + 200ms delay
            });
            
            this.updateGalleryState(true);
            
            // Mark animation as complete
            setTimeout(() => {
                this.isAnimating = false;
                this.processAnimationQueue();
            }, itemsToShow.length * Math.max(density.staggerDelay, 20) + 600);
            
        }, Math.max(itemsToHide.length * density.staggerDelay + 300, 400));
    }
    
    showAllImages() {
        if (this.isAnimating) {
            this.animationQueue.push(() => this.showAllImages());
            return;
        }
        
        this.isAnimating = true;
        
        // Find currently visible and hidden items
        const visibleItems = Array.from(this.galleryItems).filter(item => 
            item.style.display !== 'none'
        );
        const hiddenItems = Array.from(this.galleryItems).filter(item => 
            item.style.display === 'none'
        );
        
        // Get adaptive layout settings for all images
        const density = this.getContentDensity(this.galleryItems.length);
        this.applyAdaptiveLayout(density);
        
        // Phase 1: Animate out currently visible items (if any are highlighted)
        const exitStagger = Math.max(density.staggerDelay * 0.7, 10); // Faster exit
        visibleItems.forEach((item, index) => {
            setTimeout(() => {
                item.classList.remove('gallery-item--visible', 'gallery-item--filtering-in');
                item.classList.add('gallery-item--filtering-out');
            }, index * exitStagger);
        });
        
        // Phase 2: Show all items and animate them in
        setTimeout(() => {
            this.galleryItems.forEach((item, index) => {
                item.style.display = 'inline-block';
                item.classList.remove('gallery-item--hidden', 'gallery-item--highlighted', 'gallery-item--filtering-out');
                
                setTimeout(() => {
                    item.classList.add('gallery-item--filtering-in');
                    
                    // Clean up classes after animation
                    setTimeout(() => {
                        item.classList.remove('gallery-item--filtering-in');
                        item.classList.add('gallery-item--visible');
                        item.style.willChange = 'auto';
                    }, 400);
                }, index * Math.max(density.staggerDelay, 15) + 100); // Adaptive stagger + 100ms delay
            });
            
            this.updateGalleryState(false);
            
            // Mark animation as complete
            setTimeout(() => {
                this.isAnimating = false;
                this.processAnimationQueue();
            }, this.galleryItems.length * Math.max(density.staggerDelay, 15) + 500);
            
        }, Math.max(visibleItems.length * exitStagger + 200, 300));
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
    
    processAnimationQueue() {
        if (this.animationQueue.length > 0 && !this.isAnimating) {
            const nextAnimation = this.animationQueue.shift();
            nextAnimation();
        }
    }
    
    // Check if user prefers reduced motion
    prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    
    // Detect current screen breakpoint
    getCurrentBreakpoint() {
        const width = window.innerWidth;
        if (width >= 1024) return 'desktop';
        if (width >= 768) return 'tablet';
        if (width >= 480) return 'mobile';
        return 'small';
    }
    
    // Get default column count for current breakpoint
    getDefaultColumns() {
        const breakpoint = this.getCurrentBreakpoint();
        switch (breakpoint) {
            case 'desktop': return 5;
            case 'tablet': return 3;
            case 'mobile': return 2;
            case 'small': return 1;
            default: return 3;
        }
    }
    
    // Categorize content density and get optimal layout
    getContentDensity(visibleCount) {
        const defaultColumns = this.getDefaultColumns();
        const imagesPerColumn = visibleCount / defaultColumns;
        
        if (visibleCount <= 3) {
            return {
                type: 'minimal',
                columns: Math.min(visibleCount, 2),
                animationType: 'simple',
                staggerDelay: 0
            };
        } else if (visibleCount <= 8) {
            return {
                type: 'sparse',
                columns: Math.max(Math.min(defaultColumns - 1, visibleCount), 1),
                animationType: 'subtle',
                staggerDelay: 15
            };
        } else if (visibleCount <= 15) {
            return {
                type: 'compact',
                columns: Math.max(defaultColumns - 1, 2),
                animationType: 'standard',
                staggerDelay: 25
            };
        } else {
            return {
                type: 'full',
                columns: defaultColumns,
                animationType: 'standard',
                staggerDelay: 30
            };
        }
    }
    
    // Apply adaptive layout classes to gallery container
    applyAdaptiveLayout(density) {
        const galleryContainer = document.querySelector('.places-image-pool .gallery-container');
        if (!galleryContainer) return;
        
        // Remove existing density classes
        galleryContainer.classList.remove(
            'gallery-container--minimal',
            'gallery-container--sparse', 
            'gallery-container--compact',
            'gallery-container--full',
            'gallery-animation--simple',
            'gallery-animation--subtle',
            'gallery-animation--standard'
        );
        
        // Add new density classes
        galleryContainer.classList.add(`gallery-container--${density.type}`);
        galleryContainer.classList.add(`gallery-animation--${density.animationType}`);
        
        // Set CSS custom property for dynamic column count
        galleryContainer.style.setProperty('--adaptive-columns', density.columns);
    }
    
    // Set up window resize handler for responsive adaptation
    setupResizeHandler() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250); // Debounce resize events
        });
    }
    
    // Handle window resize events
    handleResize() {
        if (this.isAnimating) return; // Don't adjust during animations
        
        // Re-evaluate layout for current visible images
        const visibleItems = Array.from(this.galleryItems).filter(item => 
            item.style.display !== 'none'
        );
        
        const density = this.getContentDensity(visibleItems.length);
        this.applyAdaptiveLayout(density);
    }
    
    // Apply initial layout on page load
    applyInitialLayout() {
        // Set all items to visible initially
        this.galleryItems.forEach(item => {
            item.classList.add('gallery-item--visible');
        });
        
        // Apply layout for all images
        const density = this.getContentDensity(this.galleryItems.length);
        this.applyAdaptiveLayout(density);
    }
    
    // Public method to reset the feature
    reset() {
        this.activePlace = null;
        this.expandedCards.clear();
        this.isAnimating = false;
        this.animationQueue = [];
        
        // Reset all gallery items to visible state
        this.galleryItems.forEach(item => {
            item.style.display = 'inline-block';
            item.style.willChange = 'auto';
            item.classList.remove(
                'gallery-item--filtering-out', 
                'gallery-item--filtering-in', 
                'gallery-item--hidden', 
                'gallery-item--highlighted'
            );
            item.classList.add('gallery-item--visible');
        });
        
        this.placeCards.forEach(card => {
            card.setAttribute('data-state', 'inactive');
            const header = card.querySelector('[data-action="toggle-accordion"]');
            if (header) header.setAttribute('aria-expanded', 'false');
        });
        
        this.updateGalleryState(false);
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