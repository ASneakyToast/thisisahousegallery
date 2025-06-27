/**
 * Exhibition Feature Block Lightbox
 * Simplified vanilla JavaScript lightbox for exhibition galleries
 */

class ExhibitionFeatureLightbox {
  constructor() {
    this.galleries = [];
    this.lightbox = null;
    this.isScrollLocked = false;
    this.currentGallery = null;
    this.currentIndex = 0;
    this.totalImages = 0;
    
    // Simple image preloading
    this.preloadedImages = new Map(); // Cache for loaded images
    this.currentImage = null; // Current image element
    
    this.init();
  }

  init() {
    // Prevent double initialization
    if (window.exhibitionLightboxInitialized) return;
    window.exhibitionLightboxInitialized = true;

    // Setup galleries
    document.querySelectorAll('.exhibition-feature-gallery').forEach(gallery => {
      this.setupGallery(gallery);
    });

    // Get lightbox reference
    this.lightbox = document.getElementById('exhibition-lightbox');
    
    if (this.lightbox) {
      this.setupLightbox();
    }
  }

  setupGallery(galleryElement) {
    const galleryItems = galleryElement.querySelectorAll('.gallery-lightbox-item');
    
    const galleryData = {
      element: galleryElement,
      items: galleryItems,
      id: galleryElement.dataset.galleryId
    };

    // Setup gallery item interactions
    this.setupGalleryItems(galleryData);
    
    this.galleries.push(galleryData);
  }

  setupGalleryItems(galleryData) {
    galleryData.items.forEach((item, index) => {
      // Click event
      item.addEventListener('click', (e) => {
        e.preventDefault();
        this.openLightbox(galleryData, index);
      });

      // Keyboard support
      item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.openLightbox(galleryData, index);
        }
      });

      // Style as clickable
      item.style.cursor = 'pointer';
    });
  }

  setupLightbox() {
    // Setup close functionality
    const closeBtn = this.lightbox.querySelector('.exhibition-lightbox__close');
    const backdrop = this.lightbox.querySelector('.exhibition-lightbox__backdrop');
    const prevBtn = this.lightbox.querySelector('.exhibition-lightbox__prev');
    const nextBtn = this.lightbox.querySelector('.exhibition-lightbox__next');
    
    // Close events
    [closeBtn, backdrop].forEach(element => {
      if (element) {
        element.addEventListener('click', () => this.closeLightbox());
      }
    });

    // Navigation events
    if (prevBtn) {
      prevBtn.addEventListener('click', () => this.navigatePrevious());
    }
    
    if (nextBtn) {
      nextBtn.addEventListener('click', () => this.navigateNext());
    }

    // Keyboard navigation
    this.lightbox.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeLightbox();
      } else if (e.key === 'ArrowLeft') {
        this.navigatePrevious();
      } else if (e.key === 'ArrowRight') {
        this.navigateNext();
      }
      
      // Trap focus within modal
      if (e.key === 'Tab') {
        this.trapFocus(e);
      }
    });

    // Touch/swipe support
    this.setupTouchSupport();
  }

  setupTouchSupport() {
    let startX = 0;
    let startY = 0;
    const mediaContainer = this.lightbox.querySelector('.exhibition-lightbox__media-container');
    
    mediaContainer.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    });

    mediaContainer.addEventListener('touchend', (e) => {
      const endX = e.changedTouches[0].clientX;
      const endY = e.changedTouches[0].clientY;
      const diffX = startX - endX;
      const diffY = startY - endY;

      // Only register swipe if horizontal movement is greater than vertical
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
        if (diffX > 0) {
          this.navigateNext();
        } else {
          this.navigatePrevious();
        }
      }
    });
  }

  openLightbox(galleryData, index) {
    this.currentGallery = galleryData;
    this.currentIndex = index;
    this.totalImages = galleryData.items.length;
    
    // Reset state
    this.currentImage = null;
    
    const item = galleryData.items[index];
    const mediaType = item.dataset.mediaType;
    const mediaSrc = item.dataset.mediaSrc;
    const thumbnailSrc = item.dataset.thumbnailSrc;
    const caption = item.dataset.caption;
    
    // Update lightbox content
    this.updateLightboxContent(mediaType, mediaSrc, thumbnailSrc, caption);
    this.updateNavigation();
    this.updateCounter();
    
    // Show modal
    this.lightbox.setAttribute('aria-hidden', 'false');
    this.lightbox.classList.add('exhibition-lightbox--active');
    
    // Lock body scroll
    this.lockBodyScroll();
    
    // Focus management
    const closeBtn = this.lightbox.querySelector('.exhibition-lightbox__close');
    if (closeBtn) closeBtn.focus();
  }

  updateLightboxContent(mediaType, mediaSrc, thumbnailSrc, caption) {
    const mediaContainer = this.lightbox.querySelector('.exhibition-lightbox__media-container');
    const titleContainer = this.lightbox.querySelector('.exhibition-lightbox__title');
    
    // Update title
    if (titleContainer && this.currentGallery) {
      titleContainer.textContent = this.currentGallery.id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    // Create or update the image element
    this.initializeImage(mediaContainer);
    
    // Load the current image
    this.loadCurrentImage();
    
    // Preload nearby images for smooth navigation
    this.preloadNearbyImages();
  }

  initializeImage(container) {
    // Create image element if it doesn't exist
    let image = container.querySelector('.exhibition-lightbox__image');
    if (!image) {
      container.innerHTML = '';
      image = document.createElement('img');
      image.className = 'exhibition-lightbox__image';
      container.appendChild(image);
    }
    
    this.currentImage = image;
  }

  loadCurrentImage() {
    if (!this.currentImage || !this.currentGallery) return;
    
    const item = this.currentGallery.items[this.currentIndex];
    if (!item) return;
    
    const imageKey = `${this.currentIndex}`;
    
    // Check if image is preloaded
    if (this.preloadedImages.has(imageKey)) {
      const imageData = this.preloadedImages.get(imageKey);
      this.currentImage.src = imageData.fullSrc;
      this.currentImage.classList.add('exhibition-lightbox__image--visible');
    } else {
      // Show thumbnail first, then load full image
      this.currentImage.src = item.dataset.thumbnailSrc;
      this.currentImage.style.filter = 'blur(2px)';
      this.currentImage.classList.add('exhibition-lightbox__image--visible');
      
      // Load full resolution
      this.preloadImage(this.currentIndex, () => {
        if (this.preloadedImages.has(imageKey)) {
          const imageData = this.preloadedImages.get(imageKey);
          this.currentImage.src = imageData.fullSrc;
          this.currentImage.style.filter = 'none';
        }
      });
    }
  }

  navigatePrevious() {
    if (this.totalImages <= 1) return;
    
    // Update currentIndex
    this.currentIndex = this.currentIndex > 0 ? this.currentIndex - 1 : this.totalImages - 1;
    
    // Update image and UI
    this.updateCurrentImage();
  }

  navigateNext() {
    if (this.totalImages <= 1) return;
    
    // Update currentIndex
    this.currentIndex = this.currentIndex < this.totalImages - 1 ? this.currentIndex + 1 : 0;
    
    // Update image and UI
    this.updateCurrentImage();
  }

  updateCurrentImage() {
    // Fade out current image
    if (this.currentImage) {
      this.currentImage.classList.remove('exhibition-lightbox__image--visible');
    }
    
    // Load new image after brief fade
    setTimeout(() => {
      this.loadCurrentImage();
    }, 75);
    
    // Update navigation, counter, and title
    this.updateNavigation();
    this.updateCounter();
    this.updateTitle();
    
    // Preload nearby images for smooth future transitions
    this.preloadNearbyImages();
  }
  
  updateTitle() {
    const titleContainer = this.lightbox.querySelector('.exhibition-lightbox__title');
    if (titleContainer && this.currentGallery) {
      titleContainer.textContent = this.currentGallery.id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  }

  preloadNearbyImages() {
    // Preload images around current index for smooth navigation
    const bufferSize = 3;
    const start = Math.max(0, this.currentIndex - bufferSize);
    const end = Math.min(this.totalImages, this.currentIndex + bufferSize + 1);
    
    for (let i = start; i < end; i++) {
      const imageKey = `${i}`;
      if (!this.preloadedImages.has(imageKey)) {
        this.preloadImage(i);
      }
    }
  }

  preloadImage(imageIndex, callback = null) {
    const item = this.currentGallery.items[imageIndex];
    if (!item) return;
    
    const img = new Image();
    const imageKey = `${imageIndex}`;
    
    img.onload = () => {
      this.preloadedImages.set(imageKey, {
        fullSrc: item.dataset.mediaSrc,
        thumbnailSrc: item.dataset.thumbnailSrc,
        aspectRatio: img.naturalWidth / img.naturalHeight
      });
      
      if (callback) callback();
    };
    
    img.src = item.dataset.mediaSrc;
  }

  updateNavigation() {
    const prevBtn = this.lightbox.querySelector('.exhibition-lightbox__prev');
    const nextBtn = this.lightbox.querySelector('.exhibition-lightbox__next');
    
    // Always show navigation buttons when there are multiple images
    if (prevBtn) {
      prevBtn.style.display = this.totalImages > 1 ? 'block' : 'none';
    }
    
    if (nextBtn) {
      nextBtn.style.display = this.totalImages > 1 ? 'block' : 'none';
    }
  }

  updateCounter() {
    const currentSpan = this.lightbox.querySelector('.exhibition-lightbox__current');
    const totalSpan = this.lightbox.querySelector('.exhibition-lightbox__total');
    
    if (currentSpan) currentSpan.textContent = this.currentIndex + 1;
    if (totalSpan) totalSpan.textContent = this.totalImages;
  }

  closeLightbox() {
    this.lightbox.setAttribute('aria-hidden', 'true');
    this.lightbox.classList.remove('exhibition-lightbox--active');
    
    // Clear content to free memory
    const mediaContainer = this.lightbox.querySelector('.exhibition-lightbox__media-container');
    if (mediaContainer) {
      mediaContainer.innerHTML = '';
    }
    
    // Unlock body scroll
    this.unlockBodyScroll();
    
    // Clear current gallery reference and reset state
    this.currentGallery = null;
    this.currentIndex = 0;
    this.totalImages = 0;
    this.currentImage = null;
    this.preloadedImages.clear();
  }

  lockBodyScroll() {
    if (!this.isScrollLocked) {
      document.body.style.overflow = 'hidden';
      this.isScrollLocked = true;
    }
  }

  unlockBodyScroll() {
    if (this.isScrollLocked) {
      document.body.style.overflow = '';
      this.isScrollLocked = false;
    }
  }

  trapFocus(e) {
    const focusableElements = this.lightbox.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new ExhibitionFeatureLightbox());
} else {
  new ExhibitionFeatureLightbox();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ExhibitionFeatureLightbox;
}