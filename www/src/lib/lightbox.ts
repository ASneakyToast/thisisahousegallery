// Unified Gallery Lightbox — ported from exhibition-feature-lightbox.js.
// A reusable vanilla lightbox that works on both the exhibitions index and
// individual exhibition pages. Reads image metadata from data-* attributes on
// .gallery-lightbox-item buttons, supports prev/next, keyboard, touch swipe,
// a counter, artwork/showcard/opening/exhibition metadata, and body scroll lock.

export class UnifiedGalleryLightbox {
  private lightbox: HTMLElement | null = null;
  private currentGallery: { element: HTMLElement | null; items: HTMLElement[]; id: string } | null = null;
  private currentIndex = 0;
  private totalImages = 0;
  private currentImage: HTMLImageElement | null = null;
  private preloadedImages = new Map<string, { fullSrc: string }>();
  private isScrollLocked = false;

  init() {
    // Prevent double initialization (both pages include this module).
    if ((window as any).unifiedGalleryLightboxInitialized) return;
    (window as any).unifiedGalleryLightboxInitialized = true;

    const gallerySelectors = [
      '.exhibition-feature-gallery',
      '.unified-gallery-container',
      '.exhibition-page-gallery',
    ];
    gallerySelectors.forEach((selector) => {
      document.querySelectorAll<HTMLElement>(selector).forEach((gallery) => this.setupGallery(gallery));
    });

    this.setupIndividualGalleryItems();

    this.lightbox = document.getElementById('exhibition-lightbox');
    if (this.lightbox) this.setupLightbox();
  }

  private setupGallery(galleryElement: HTMLElement) {
    const items = Array.from(galleryElement.querySelectorAll<HTMLElement>('.gallery-lightbox-item'));
    const galleryData = {
      element: galleryElement,
      items,
      id: galleryElement.dataset.galleryId || 'exhibition',
    };
    items.forEach((item, index) => this.setupGalleryItem(item, () => this.openLightbox(galleryData, index)));
  }

  private setupIndividualGalleryItems() {
    const unifiedGallery = document.querySelector<HTMLElement>('.unified-gallery-container');
    if (!unifiedGallery) return;

    const galleryData = {
      element: unifiedGallery,
      items: Array.from(unifiedGallery.querySelectorAll<HTMLElement>('.gallery-lightbox-item')),
      id: unifiedGallery.dataset.galleryId || 'exhibition',
    };

    // Visible gallery items (photos) open the unified gallery at their index.
    const visibleItems = document.querySelectorAll<HTMLElement>(
      '.gallery-lightbox-item:not(.unified-gallery-container .gallery-lightbox-item)'
    );
    visibleItems.forEach((item) => {
      this.setupGalleryItem(item, () => {
        const target = parseInt(item.dataset.quickviewIndex || '0', 10) || 0;
        this.openLightbox(galleryData, target);
      });
    });

    // Artwork cards open the unified gallery at their quickview index.
    document.querySelectorAll<HTMLElement>('.exhibition-artwork-card[data-artwork-id]').forEach((card) => {
      card.style.cursor = 'pointer';
      card.addEventListener('click', (e) => {
        e.preventDefault();
        const target = parseInt(card.dataset.quickviewIndex || '0', 10) || 0;
        this.openLightbox(galleryData, target);
      });
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          (card as HTMLElement).click();
        }
      });
    });
  }

  private setupGalleryItem(item: HTMLElement, open: () => void) {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      open();
    });
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        (item as HTMLElement).click();
      }
    });
    item.style.cursor = 'pointer';
  }

  private setupLightbox() {
    const closeBtn = this.lightbox!.querySelector('.exhibition-lightbox__close');
    const backdrop = this.lightbox!.querySelector('.exhibition-lightbox__backdrop');
    const mediaContainer = this.lightbox!.querySelector('.exhibition-lightbox__media-container');
    const prevBtn = this.lightbox!.querySelector('.exhibition-lightbox__prev');
    const nextBtn = this.lightbox!.querySelector('.exhibition-lightbox__next');

    [closeBtn, backdrop, mediaContainer].forEach((el) => {
      if (el) el.addEventListener('click', () => this.closeLightbox());
    });
    if (prevBtn) prevBtn.addEventListener('click', () => this.navigate(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => this.navigate(1));

    this.lightbox!.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.closeLightbox();
      else if (e.key === 'ArrowLeft') this.navigate(-1);
      else if (e.key === 'ArrowRight') this.navigate(1);
      else if (e.key === 'Tab') this.trapFocus(e);
    });

    this.setupTouchSupport();
  }

  private setupTouchSupport() {
    let startX = 0;
    let startY = 0;
    const mediaContainer = this.lightbox!.querySelector('.exhibition-lightbox__media-container');
    mediaContainer?.addEventListener('touchstart', (e) => {
      startX = (e as TouchEvent).touches[0].clientX;
      startY = (e as TouchEvent).touches[0].clientY;
    });
    mediaContainer?.addEventListener('touchend', (e) => {
      const endX = (e as TouchEvent).changedTouches[0].clientX;
      const endY = (e as TouchEvent).changedTouches[0].clientY;
      const diffX = startX - endX;
      const diffY = startY - endY;
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
        this.navigate(diffX > 0 ? 1 : -1);
      }
    });
  }

  private openLightbox(galleryData: { element: HTMLElement | null; items: HTMLElement[]; id: string }, index: number) {
    if (!galleryData.items.length) return;
    this.currentGallery = galleryData;
    this.currentIndex = index;
    this.totalImages = galleryData.items.length;
    this.currentImage = null;

    this.updateContent(galleryData.items[index]);
    this.updateNavigation();
    this.updateCounter();

    this.lightbox!.style.display = 'flex';
    this.lightbox!.offsetHeight; // force reflow
    this.lightbox!.setAttribute('aria-hidden', 'false');
    this.lightbox!.classList.add('exhibition-lightbox--active');
    this.lockBodyScroll();
    document.dispatchEvent(new CustomEvent('lightbox:open'));
    this.lightbox!.querySelector('.exhibition-lightbox__close')?.focus();
  }

  private navigate(dir: number) {
    if (this.totalImages <= 1) return;
    this.currentIndex = (this.currentIndex + dir + this.totalImages) % this.totalImages;
    this.currentImage?.classList.remove('exhibition-lightbox__image--visible');
    setTimeout(() => {
      if (this.currentGallery) this.updateContent(this.currentGallery!.items[this.currentIndex]);
    }, 75);
    this.updateNavigation();
    this.updateCounter();
    this.preloadNearby();
  }

  private updateContent(item: HTMLElement) {
    const mediaContainer = this.lightbox!.querySelector('.exhibition-lightbox__media-container');
    const titleContainer = this.lightbox!.querySelector('.exhibition-lightbox__title');
    if (titleContainer && this.currentGallery) {
      titleContainer.textContent = this.currentGallery.id.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
    }

    this.updateArtworkMetadata(item);
    this.loadImage(item, mediaContainer!);
    this.preloadNearby();
  }

  private loadImage(item: HTMLElement, container: Element) {
    let image = container.querySelector<HTMLImageElement>('.exhibition-lightbox__image');
    if (!image) {
      container.innerHTML = '';
      image = document.createElement('img');
      image.className = 'exhibition-lightbox__image';
      container.appendChild(image);
    }
    this.currentImage = image;

    const key = `${this.currentIndex}`;
    if (this.preloadedImages.has(key)) {
      image.src = this.preloadedImages.get(key)!.fullSrc;
      image.classList.add('exhibition-lightbox__image--visible');
    } else {
      image.src = item.dataset.thumbnailSrc || '';
      image.style.filter = 'blur(2px)';
      image.classList.add('exhibition-lightbox__image--visible');
      const img = new Image();
      img.onload = () => {
        this.preloadedImages.set(key, { fullSrc: item.dataset.mediaSrc || '' });
        if (this.currentIndex === parseInt(key, 10)) {
          image!.src = item.dataset.mediaSrc || '';
          image!.style.filter = 'none';
        }
      };
      img.src = item.dataset.mediaSrc || '';
    }
  }

  private preloadNearby() {
    const buffer = 3;
    for (let i = Math.max(0, this.currentIndex - buffer); i < Math.min(this.totalImages, this.currentIndex + buffer + 1); i++) {
      const key = `${i}`;
      if (this.preloadedImages.has(key) || !this.currentGallery) continue;
      const item = this.currentGallery.items[i];
      const img = new Image();
      img.onload = () => this.preloadedImages.set(key, { fullSrc: item.dataset.mediaSrc || '' });
      img.src = item.dataset.mediaSrc || '';
    }
  }

  private updateArtworkMetadata(item: HTMLElement) {
    const d = item.dataset;
    const mediaContainer = this.lightbox!.querySelector('.exhibition-lightbox__media-container');
    let metadata = this.lightbox!.querySelector('.exhibition-lightbox__artwork-metadata');
    if (!metadata) {
      metadata = document.createElement('div');
      metadata.className = 'exhibition-lightbox__artwork-metadata';
      this.lightbox!.querySelector('.exhibition-lightbox__controls')?.insertBefore(
        metadata,
        this.lightbox!.querySelector('.exhibition-lightbox__navigation')
      );
    }
    metadata.innerHTML = '';

    const hasArtwork = !!d.artworkTitle;
    if (hasArtwork) {
      if (d.artworkTitle) {
        const el = document.createElement('div');
        el.className = 'exhibition-lightbox__artwork-title';
        el.innerHTML = d.artworkTitle;
        metadata.appendChild(el);
      }
      if (d.artworkArtist) {
        const el = document.createElement('div');
        el.className = 'exhibition-lightbox__artwork-artist';
        el.textContent = d.artworkArtist;
        metadata.appendChild(el);
      }
      const details = [d.artworkDate, d.artworkMaterials, d.artworkSize].filter(Boolean).join(' • ');
      if (details) {
        const el = document.createElement('div');
        el.className = 'exhibition-lightbox__artwork-details';
        el.textContent = details;
        metadata.appendChild(el);
      }
    } else if (d.imageType === 'exhibition' || d.imageType === 'opening' || d.imageType === 'showcard') {
      const label = d.imageType === 'showcard' ? (d.caption || 'Exhibition Showcard') : d.imageType === 'opening' ? 'Opening Photo' : 'Exhibition Photo';
      const parts = [d.exhibitionTitle, d.exhibitionDate, label].filter(Boolean).join(', ');
      const el = document.createElement('div');
      el.className = 'exhibition-lightbox__exhibition-context';
      el.textContent = parts;
      metadata.appendChild(el);
    }

    if (d.imageCredit) {
      const el = document.createElement('div');
      el.className = 'exhibition-lightbox__image-credit';
      el.textContent = d.imageCredit;
      metadata.appendChild(el);
    }
    void mediaContainer;
  }

  private updateNavigation() {
    const prevBtn = this.lightbox!.querySelector<HTMLElement>('.exhibition-lightbox__prev');
    const nextBtn = this.lightbox!.querySelector<HTMLElement>('.exhibition-lightbox__next');
    const show = this.totalImages > 1;
    if (prevBtn) prevBtn.style.display = show ? 'block' : 'none';
    if (nextBtn) nextBtn.style.display = show ? 'block' : 'none';
  }

  private updateCounter() {
    const cur = this.lightbox!.querySelector('.exhibition-lightbox__current');
    const total = this.lightbox!.querySelector('.exhibition-lightbox__total');
    if (cur) cur.textContent = String(this.currentIndex + 1);
    if (total) total.textContent = String(this.totalImages);
  }

  private closeLightbox() {
    this.lightbox!.setAttribute('aria-hidden', 'true');
    this.lightbox!.classList.remove('exhibition-lightbox--active');
    setTimeout(() => {
      this.lightbox!.style.display = '';
    }, 200);
    const mediaContainer = this.lightbox!.querySelector('.exhibition-lightbox__media-container');
    if (mediaContainer) mediaContainer.innerHTML = '';
    this.unlockBodyScroll();
    document.dispatchEvent(new CustomEvent('lightbox:close'));
    this.currentGallery = null;
    this.currentIndex = 0;
    this.totalImages = 0;
    this.currentImage = null;
    this.preloadedImages.clear();
  }

  private lockBodyScroll() {
    if (!this.isScrollLocked) {
      document.body.style.overflow = 'hidden';
      this.isScrollLocked = true;
    }
  }

  private unlockBodyScroll() {
    if (this.isScrollLocked) {
      document.body.style.overflow = '';
      this.isScrollLocked = false;
    }
  }

  private trapFocus(e: KeyboardEvent) {
    const focusable = this.lightbox!.querySelectorAll<HTMLElement>('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
}