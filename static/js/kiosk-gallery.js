/**
 * Kiosk Gallery Animation System
 * Pure CSS animations with JavaScript control for fullscreen gallery
 */

class KioskGallery {
    constructor(element) {
        this.element = typeof element === 'string' ? document.querySelector(element) : element;
        if (!this.element) return;

        this.container = this.element.querySelector('.kiosk-gallery-container');
        this.loadingElement = this.element.querySelector('#kiosk-loading');
        this.progressBar = document.querySelector('#progress-bar');
        this.prevBtn = document.querySelector('#nav-prev');
        this.nextBtn = document.querySelector('#nav-next');

        // Configuration from data attributes
        this.autoAdvanceSeconds = parseInt(this.element.dataset.autoAdvance) || 8;
        this.imageCount = parseInt(this.element.dataset.imageCount) || 12;

        // Animation state
        this.currentSet = 0;
        this.totalSets = 0;
        this.allImages = [];
        this.imageSets = [];
        this.isAnimating = false;
        this.autoTimer = null;
        this.progressTimer = null;
        this.progressStartTime = 0;
        this.isPaused = false;

        // Size classes for random assignment
        this.sizeClasses = ['small', 'medium', 'large'];
        this.sizeWeights = [0.4, 0.4, 0.2]; // 40% small, 40% medium, 20% large

        this.init();
    }

    async init() {
        try {
            this.showLoading();
            await this.loadImages();
            this.hideLoading();
            this.setupImageSets();
            this.setupEventListeners();
            this.showFirstSet();
            this.startAutoAdvance();
        } catch (error) {
            console.error('Kiosk gallery initialization failed:', error);
            this.hideLoading();
        }
    }

    showLoading() {
        if (this.loadingElement) {
            this.loadingElement.style.display = 'block';
        }
    }

    hideLoading() {
        if (this.loadingElement) {
            this.loadingElement.classList.add('fade-out');
            setTimeout(() => {
                this.loadingElement.style.display = 'none';
            }, 500);
        }
    }

    async loadImages() {
        // Get all gallery images from the StreamField content
        const galleryImages = this.container.querySelectorAll('.gallery-image, .gallery-single-image');
        
        console.log('Kiosk Gallery Debug:');
        console.log('- Container:', this.container);
        console.log('- Gallery images found:', galleryImages.length);
        console.log('- Gallery images:', galleryImages);
        
        if (galleryImages.length === 0) {
            console.error('No images found in gallery. Make sure you have:');
            console.error('1. Created a KioskPage in the Wagtail admin');
            console.error('2. Added gallery blocks with images to the page');
            console.error('3. Published the page');
            throw new Error('No images found in gallery');
        }

        this.allImages = Array.from(galleryImages);
        
        // Preload images for better performance
        const imagePromises = this.allImages.map(item => {
            const img = item.querySelector('img');
            if (img && !img.complete) {
                return new Promise((resolve, reject) => {
                    img.onload = resolve;
                    img.onerror = reject;
                    if (img.complete) resolve();
                });
            }
            return Promise.resolve();
        });

        await Promise.all(imagePromises);
    }

    setupImageSets() {
        // Shuffle images for random display order
        const shuffledImages = [...this.allImages].sort(() => Math.random() - 0.5);
        
        // Split into sets of configured size
        this.imageSets = [];
        for (let i = 0; i < shuffledImages.length; i += this.imageCount) {
            const set = shuffledImages.slice(i, i + this.imageCount);
            this.imageSets.push(set);
        }
        
        this.totalSets = this.imageSets.length;
        
        // If we only have one set, duplicate it for smooth transitions
        if (this.totalSets === 1) {
            this.imageSets.push([...this.imageSets[0]]);
            this.totalSets = 2;
        }
    }

    assignRandomSizes(images) {
        images.forEach(item => {
            // Remove existing size classes
            item.classList.remove('gallery-item--small', 'gallery-item--medium', 'gallery-item--large');
            
            // Assign random size based on weights
            const randomValue = Math.random();
            let sizeClass = 'small';
            let cumulativeWeight = 0;
            
            for (let i = 0; i < this.sizeWeights.length; i++) {
                cumulativeWeight += this.sizeWeights[i];
                if (randomValue <= cumulativeWeight) {
                    sizeClass = this.sizeClasses[i];
                    break;
                }
            }
            
            item.classList.add(`gallery-item--${sizeClass}`);
        });
    }

    setupEventListeners() {
        // Navigation buttons
        this.prevBtn?.addEventListener('click', () => this.goToPrevious());
        this.nextBtn?.addEventListener('click', () => this.goToNext());

        // Touch/swipe support
        let startX = 0;
        let startY = 0;
        let isDragging = false;

        this.element.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            isDragging = true;
            this.pauseAutoAdvance();
        }, { passive: true });

        this.element.addEventListener('touchend', (e) => {
            if (!isDragging) return;

            const deltaX = e.changedTouches[0].clientX - startX;
            const deltaY = e.changedTouches[0].clientY - startY;
            const threshold = 100;

            // Only trigger if horizontal swipe is dominant
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > threshold) {
                if (deltaX > 0) {
                    this.goToPrevious();
                } else {
                    this.goToNext();
                }
            }

            isDragging = false;
            setTimeout(() => this.resumeAutoAdvance(), 3000); // Resume after 3 seconds
        }, { passive: true });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                this.goToPrevious();
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                this.goToNext();
            } else if (e.key === ' ') {
                e.preventDefault();
                this.toggleAutoAdvance();
            }
        });

        // Pause on hover/focus
        this.element.addEventListener('mouseenter', () => this.pauseAutoAdvance());
        this.element.addEventListener('mouseleave', () => this.resumeAutoAdvance());

        // Handle visibility changes (tab switching, etc.)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoAdvance();
            } else {
                this.resumeAutoAdvance();
            }
        });
    }

    showFirstSet() {
        if (this.imageSets.length === 0) return;

        const firstSet = this.imageSets[0];
        this.assignRandomSizes(firstSet);
        this.animateSetIn(firstSet);
        this.updateProgress();
    }

    animateSetIn(images) {
        if (this.isAnimating) return;
        this.isAnimating = true;

        // Hide all images first
        this.allImages.forEach(img => {
            img.style.display = 'none';
            img.classList.remove('animate-in', 'animate-out');
        });

        // Show and animate in the current set
        images.forEach(img => {
            img.style.display = 'inline-block';
            img.classList.add('animate-in');
        });

        // Set animation complete after the longest delay + animation duration
        const maxAnimationTime = 1100 + 800; // max delay + animation duration
        setTimeout(() => {
            this.isAnimating = false;
        }, maxAnimationTime);
    }

    animateSetOut(images) {
        return new Promise((resolve) => {
            images.forEach(img => {
                img.classList.remove('animate-in');
                img.classList.add('animate-out');
            });

            // Complete after the longest delay + animation duration
            const maxAnimationTime = 550 + 600; // max delay + animation duration
            setTimeout(() => {
                images.forEach(img => {
                    img.style.display = 'none';
                    img.classList.remove('animate-out');
                });
                resolve();
            }, maxAnimationTime);
        });
    }

    async transitionToSet(newIndex) {
        if (this.isAnimating || newIndex === this.currentSet) return;

        this.isAnimating = true;
        this.stopProgress();

        const currentImages = this.imageSets[this.currentSet];
        const nextImages = this.imageSets[newIndex];

        // Animate out current set
        await this.animateSetOut(currentImages);

        // Update current set and assign random sizes
        this.currentSet = newIndex;
        this.assignRandomSizes(nextImages);

        // Animate in new set
        this.animateSetIn(nextImages);
        this.updateProgress();
        this.startProgress();
    }

    goToNext() {
        const nextIndex = (this.currentSet + 1) % this.totalSets;
        this.transitionToSet(nextIndex);
        this.resetAutoAdvance();
    }

    goToPrevious() {
        const prevIndex = this.currentSet === 0 ? this.totalSets - 1 : this.currentSet - 1;
        this.transitionToSet(prevIndex);
        this.resetAutoAdvance();
    }

    startAutoAdvance() {
        if (this.autoAdvanceSeconds <= 0 || this.isPaused) return;

        this.autoTimer = setTimeout(() => {
            this.goToNext();
        }, this.autoAdvanceSeconds * 1000);

        this.startProgress();
    }

    stopAutoAdvance() {
        if (this.autoTimer) {
            clearTimeout(this.autoTimer);
            this.autoTimer = null;
        }
        this.stopProgress();
    }

    resetAutoAdvance() {
        this.stopAutoAdvance();
        if (!this.isPaused) {
            this.startAutoAdvance();
        }
    }

    pauseAutoAdvance() {
        this.isPaused = true;
        this.stopAutoAdvance();
    }

    resumeAutoAdvance() {
        this.isPaused = false;
        this.startAutoAdvance();
    }

    toggleAutoAdvance() {
        if (this.isPaused) {
            this.resumeAutoAdvance();
        } else {
            this.pauseAutoAdvance();
        }
    }

    startProgress() {
        if (!this.progressBar || this.autoAdvanceSeconds <= 0) return;

        this.progressStartTime = Date.now();
        this.updateProgressBar();
    }

    updateProgressBar() {
        if (!this.progressBar || this.isPaused) return;

        const elapsed = Date.now() - this.progressStartTime;
        const duration = this.autoAdvanceSeconds * 1000;
        const progress = Math.min((elapsed / duration) * 100, 100);

        this.progressBar.style.width = `${progress}%`;

        if (progress < 100) {
            this.progressTimer = requestAnimationFrame(() => this.updateProgressBar());
        }
    }

    stopProgress() {
        if (this.progressTimer) {
            cancelAnimationFrame(this.progressTimer);
            this.progressTimer = null;
        }
    }

    updateProgress() {
        // Reset progress bar with smooth transition
        if (this.progressBar) {
            this.progressBar.classList.add('animate');
            this.progressBar.style.width = '0%';
        }
    }

    destroy() {
        this.stopAutoAdvance();
        this.stopProgress();
        
        // Remove event listeners
        this.prevBtn?.removeEventListener('click', this.goToPrevious);
        this.nextBtn?.removeEventListener('click', this.goToNext);
        
        // Clean up any ongoing animations
        this.isAnimating = false;
    }
}

// Initialize kiosk gallery when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const kioskGallery = document.querySelector('#kiosk-gallery');
    if (kioskGallery) {
        window.kioskGallery = new KioskGallery(kioskGallery);
    }
});

// Export for global access
if (typeof window !== 'undefined') {
    window.KioskGallery = KioskGallery;
}