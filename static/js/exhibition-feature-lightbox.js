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
    const mediaContainer = this.lightbox.querySelector('.exhibition-lightbox__media-container');
    const prevBtn = this.lightbox.querySelector('.exhibition-lightbox__prev');
    const nextBtn = this.lightbox.querySelector('.exhibition-lightbox__next');
    
    // Close events
    [closeBtn, backdrop, mediaContainer].forEach(element => {
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
    
    // Get artwork metadata if available
    const artworkData = this.getArtworkData(item);
    
    // Update lightbox content
    this.updateLightboxContent(mediaType, mediaSrc, thumbnailSrc, caption, artworkData);
    this.updateNavigation();
    this.updateCounter();
    
    // Show modal - force reflow to ensure backdrop-filter is calculated
    this.lightbox.style.display = 'flex';
    this.lightbox.offsetHeight; // Force reflow
    this.lightbox.setAttribute('aria-hidden', 'false');
    this.lightbox.classList.add('exhibition-lightbox--active');
    
    // Lock body scroll
    this.lockBodyScroll();
    
    // Focus management
    const closeBtn = this.lightbox.querySelector('.exhibition-lightbox__close');
    if (closeBtn) closeBtn.focus();
  }

  getArtworkData(item) {
    const imageType = item.dataset.imageType;
    const hasArtworkData = !!(item.dataset.artworkTitle);
    const imageCredit = item.dataset.imageCredit || null;
    
    // Priority 1: If we have artwork data, always show it regardless of image type
    if (hasArtworkData) {
      return {
        isExhibitionPhoto: false,
        isOpeningPhoto: false,
        title: item.dataset.artworkTitle || null,
        artist: item.dataset.artworkArtist || null,
        date: item.dataset.artworkDate || null,
        materials: item.dataset.artworkMaterials || null,
        size: item.dataset.artworkSize || null,
        credit: imageCredit,
        hasArtwork: true
      };
    }
    
    // Priority 2: Exhibition install photos
    if (imageType === 'exhibition') {
      return {
        isExhibitionPhoto: true,
        isOpeningPhoto: false,
        exhibitionTitle: item.dataset.exhibitionTitle || null,
        exhibitionDate: item.dataset.exhibitionDate || null,
        credit: imageCredit,
        hasArtwork: false
      };
    }
    
    // Priority 3: Opening photos
    if (imageType === 'opening') {
      return {
        isExhibitionPhoto: false,
        isOpeningPhoto: true,
        exhibitionTitle: item.dataset.exhibitionTitle || null,
        exhibitionDate: item.dataset.exhibitionDate || null,
        credit: imageCredit,
        hasArtwork: false
      };
    }
    
    // Default: No special metadata
    return {
      isExhibitionPhoto: false,
      isOpeningPhoto: false,
      credit: imageCredit,
      hasArtwork: false
    };
  }

  updateLightboxContent(mediaType, mediaSrc, thumbnailSrc, caption, artworkData) {
    const mediaContainer = this.lightbox.querySelector('.exhibition-lightbox__media-container');
    const titleContainer = this.lightbox.querySelector('.exhibition-lightbox__title');
    
    // Always use exhibition title at the top
    if (titleContainer && this.currentGallery) {
      titleContainer.textContent = this.currentGallery.id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    // Update artwork metadata display
    this.updateArtworkMetadata(artworkData);
    
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
    
    // Update navigation, counter, title, and artwork metadata
    this.updateNavigation();
    this.updateCounter();
    this.updateCurrentArtworkInfo();
    
    // Preload nearby images for smooth future transitions
    this.preloadNearbyImages();
  }
  
  updateCurrentArtworkInfo() {
    if (!this.currentGallery || !this.currentGallery.items[this.currentIndex]) return;
    
    const currentItem = this.currentGallery.items[this.currentIndex];
    const artworkData = this.getArtworkData(currentItem);
    
    // Always keep exhibition title at the top
    const titleContainer = this.lightbox.querySelector('.exhibition-lightbox__title');
    if (titleContainer && this.currentGallery) {
      titleContainer.textContent = this.currentGallery.id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    this.updateArtworkMetadata(artworkData);
  }
  
  updateArtworkMetadata(artworkData) {
    // Find or create artwork metadata container
    let metadataContainer = this.lightbox.querySelector('.exhibition-lightbox__artwork-metadata');
    
    if (!metadataContainer) {
      // Create metadata container if it doesn't exist
      const controlsPanel = this.lightbox.querySelector('.exhibition-lightbox__controls');
      const navigationPanel = this.lightbox.querySelector('.exhibition-lightbox__navigation');
      if (controlsPanel && navigationPanel) {
        metadataContainer = document.createElement('div');
        metadataContainer.className = 'exhibition-lightbox__artwork-metadata';
        // Insert before navigation panel to maintain order: header, metadata, navigation
        controlsPanel.insertBefore(metadataContainer, navigationPanel);
      }
    }
    
    if (!metadataContainer) return;
    
    // Clear existing content
    metadataContainer.innerHTML = '';
    
    // Add metadata based on image type
    if (artworkData && artworkData.isExhibitionPhoto) {
      // Display exhibition context for install photos
      const contextParts = [];
      if (artworkData.exhibitionTitle) contextParts.push(artworkData.exhibitionTitle);
      if (artworkData.exhibitionDate) contextParts.push(artworkData.exhibitionDate);
      contextParts.push('Exhibition Photo');
      
      const contextElement = document.createElement('div');
      contextElement.className = 'exhibition-lightbox__exhibition-context';
      contextElement.textContent = contextParts.join(', ');
      metadataContainer.appendChild(contextElement);
      
    } else if (artworkData && artworkData.isOpeningPhoto) {
      // Display exhibition context for opening photos
      const contextParts = [];
      if (artworkData.exhibitionTitle) contextParts.push(artworkData.exhibitionTitle);
      if (artworkData.exhibitionDate) contextParts.push(artworkData.exhibitionDate);
      contextParts.push('Opening Photo');
      
      const contextElement = document.createElement('div');
      contextElement.className = 'exhibition-lightbox__exhibition-context';
      contextElement.textContent = contextParts.join(', ');
      metadataContainer.appendChild(contextElement);
      
    } else if (artworkData && artworkData.hasArtwork) {
      // Display artwork metadata for artwork photos
      // Add artwork title first
      if (artworkData.title) {
        const titleElement = document.createElement('div');
        titleElement.className = 'exhibition-lightbox__artwork-title';
        titleElement.innerHTML = artworkData.title;
        metadataContainer.appendChild(titleElement);
      }
      
      // Then add artist name
      if (artworkData.artist) {
        const artistElement = document.createElement('div');
        artistElement.className = 'exhibition-lightbox__artwork-artist';
        artistElement.textContent = artworkData.artist;
        metadataContainer.appendChild(artistElement);
      }
      
      // Finally add other details
      const details = [];
      if (artworkData.date) details.push(artworkData.date);
      if (artworkData.materials) details.push(artworkData.materials);
      if (artworkData.size) details.push(artworkData.size);
      
      if (details.length > 0) {
        const detailsElement = document.createElement('div');
        detailsElement.className = 'exhibition-lightbox__artwork-details';
        detailsElement.textContent = details.join(' • ');
        metadataContainer.appendChild(detailsElement);
      }
    }
    
    // Add image credit if available (for all image types)
    if (artworkData && artworkData.credit) {
      const creditElement = document.createElement('div');
      creditElement.className = 'exhibition-lightbox__image-credit';
      creditElement.textContent = artworkData.credit;
      metadataContainer.appendChild(creditElement);
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
    
    // Reset display after transition
    setTimeout(() => {
      this.lightbox.style.display = '';
    }, 200);
    
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