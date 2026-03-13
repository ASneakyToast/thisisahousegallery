/**
 * Kiosk Carousel — Virtual 3-Element Pool
 *
 * Only 3 slide DOM elements ever exist. Their roles rotate on each advance:
 *   current -> spare, next -> current, spare -> next (pre-populated)
 *
 * The full dataset lives in JSON embedded via Django's json_script filter.
 * No DOM creation/destruction during transitions.
 *
 * Falls back to legacy DOM-based cycling when no JSON data is present
 * (e.g. background carousels using StreamField display_images).
 */
const KioskCarousel = {
  init(containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    if (container.dataset.carouselInitialized) return;
    container.dataset.carouselInitialized = 'true';

    // Try to load items from embedded JSON (virtual pool mode)
    const dataScript = container.querySelector('script[type="application/json"]');
    if (!dataScript) {
      this._initLegacy(container);
      return;
    }

    let rawItems;
    try {
      rawItems = JSON.parse(dataScript.textContent);
    } catch (e) {
      return;
    }

    if (!rawItems || rawItems.length === 0) return;

    // Convert snake_case keys to camelCase for JS consumption
    this.items = rawItems.map(this._toCamelCase);
    this.container = container;
    this.currentIndex = 0;
    this.generation = 0;
    this.isTransitioning = false;
    this.intervalId = null;

    // Read configurable settings from data attributes
    this.interval = parseInt(container.dataset.carouselInterval, 10) || 5000;
    this.duration = parseInt(container.dataset.carouselDuration, 10) || 1200;
    this.transition = container.dataset.carouselTransition || 'crossfade';

    // Apply CSS custom property and transition class
    container.style.setProperty('--carousel-transition-duration', this.duration + 'ms');
    if (this.transition !== 'crossfade') {
      container.classList.add('transition-' + this.transition);
    }

    // Single item: show it statically, wire up click, done
    if (this.items.length === 1) {
      this._setupClickHandler();
      return;
    }

    // Build the 3-element pool
    this._createPool();

    // Wire up interactions and start
    this._setupClickHandler();
    this._setupPauseResume();
    this.start();
  },

  // --- Pool management ---------------------------------------------------

  _createPool() {
    // Adopt the server-rendered first slide as 'current'
    const existing = this.container.querySelector('.kiosk-carousel__slide');

    if (existing) {
      this.pool = {
        current: existing,
        next: this._createSlideElement(),
        spare: this._createSlideElement()
      };
    } else {
      // No server-rendered slide — create all three
      this.pool = {
        current: this._createSlideElement(),
        next: this._createSlideElement(),
        spare: this._createSlideElement()
      };
      this.container.appendChild(this.pool.current);
      this._populateSlide(this.pool.current, this.items[0], 0);
      this.pool.current.classList.add('carousel-active');
    }

    // Append next and spare to DOM (hidden by CSS — no carousel-active class)
    this.container.appendChild(this.pool.next);
    this.container.appendChild(this.pool.spare);

    // Pre-populate next with item[1]
    const nextIndex = this.items.length > 1 ? 1 : 0;
    this._populateSlide(this.pool.next, this.items[nextIndex], nextIndex);
  },

  _createSlideElement() {
    const button = document.createElement('button');
    button.className = 'gallery-lightbox-item kiosk-carousel__slide';
    button.setAttribute('data-media-type', 'image');

    const frame = document.createElement('span');
    frame.className = 'kiosk-carousel__frame';

    const img = document.createElement('img');
    img.decoding = 'async';
    img.alt = '';
    frame.appendChild(img);

    const caption = document.createElement('span');
    caption.className = 'kiosk-carousel__caption';
    caption.style.display = 'none';
    frame.appendChild(caption);

    button.appendChild(frame);
    return button;
  },

  _populateSlide(slideEl, item, index) {
    if (!item) return;

    // Data attributes for lightbox compatibility
    slideEl.dataset.mediaSrc = item.fullUrl || '';
    slideEl.dataset.thumbnailSrc = item.thumbUrl || '';
    slideEl.dataset.caption = item.caption || '';
    slideEl.dataset.index = index;
    slideEl.dataset.imageType = item.imageType || '';

    if (item.artworkTitle) {
      slideEl.dataset.artworkTitle = item.artworkTitle;
      slideEl.dataset.artworkArtist = item.artworkArtist || '';
      slideEl.dataset.artworkDate = item.artworkDate || '';
      slideEl.dataset.artworkMaterials = item.artworkMaterials || '';
      slideEl.dataset.artworkSize = item.artworkSize || '';
    } else {
      delete slideEl.dataset.artworkTitle;
      delete slideEl.dataset.artworkArtist;
      delete slideEl.dataset.artworkDate;
      delete slideEl.dataset.artworkMaterials;
      delete slideEl.dataset.artworkSize;
    }

    if (item.exhibitionTitle) {
      slideEl.dataset.exhibitionTitle = item.exhibitionTitle;
      slideEl.dataset.exhibitionDate = item.exhibitionDate || '';
    } else {
      delete slideEl.dataset.exhibitionTitle;
      delete slideEl.dataset.exhibitionDate;
    }

    if (item.imageCredit) {
      slideEl.dataset.imageCredit = item.imageCredit;
    } else {
      delete slideEl.dataset.imageCredit;
    }

    slideEl.setAttribute('aria-label',
      'View ' + (item.caption || 'image') + ' in lightbox');

    // Update the <img>
    const img = slideEl.querySelector('img');
    if (img) {
      img.src = item.thumbUrl || '';
      if (item.srcset) {
        img.srcset = item.srcset;
        img.sizes = '50vw';
      } else {
        img.removeAttribute('srcset');
        img.removeAttribute('sizes');
      }
      img.alt = item.caption || 'Gallery image';
      img.onerror = function() { this.onerror = null; };
    }

    // Update caption
    this._updateCaption(slideEl, item);
  },

  _updateCaption(slideEl, item) {
    const caption = slideEl.querySelector('.kiosk-carousel__caption');
    if (!caption) return;

    caption.innerHTML = '';

    if (item.artworkTitle) {
      caption.style.display = '';
      let el = document.createElement('span');
      el.className = 'kiosk-carousel__caption-title';
      el.textContent = item.artworkTitle;
      caption.appendChild(el);

      if (item.artworkArtist) {
        el = document.createElement('span');
        el.className = 'kiosk-carousel__caption-artist';
        el.textContent = item.artworkArtist;
        caption.appendChild(el);
      }

      const parts = [];
      if (item.artworkDate) parts.push(item.artworkDate);
      if (item.artworkMaterials) parts.push(item.artworkMaterials);
      if (item.artworkSize) parts.push(item.artworkSize);
      if (parts.length) {
        el = document.createElement('span');
        el.className = 'kiosk-carousel__caption-details';
        el.textContent = parts.join(', ');
        caption.appendChild(el);
      }
    } else if (item.exhibitionTitle) {
      caption.style.display = '';
      let el = document.createElement('span');
      el.className = 'kiosk-carousel__caption-title';
      el.textContent = item.exhibitionTitle;
      caption.appendChild(el);

      if (item.exhibitionDate) {
        el = document.createElement('span');
        el.className = 'kiosk-carousel__caption-details';
        el.textContent = item.exhibitionDate;
        caption.appendChild(el);
      }
    } else if (item.caption) {
      caption.style.display = '';
      const el = document.createElement('span');
      el.className = 'kiosk-carousel__caption-title';
      el.textContent = item.caption;
      caption.appendChild(el);
    } else {
      caption.style.display = 'none';
    }
  },

  // --- Advance logic ------------------------------------------------------

  advance() {
    if (this.isTransitioning) return;
    this.isTransitioning = true;
    this.generation++;
    const gen = this.generation;

    // Transition: deactivate current, activate next
    this.pool.current.classList.remove('carousel-active');
    this.pool.next.classList.add('carousel-active');

    // After CSS transition completes, rotate the pool
    setTimeout(() => {
      if (gen !== this.generation) return; // stale callback

      const oldCurrent = this.pool.current;
      const oldNext = this.pool.next;
      const oldSpare = this.pool.spare;

      this.pool.current = oldNext;
      this.pool.spare = oldCurrent;
      this.pool.next = oldSpare;

      this.currentIndex = (this.currentIndex + 1) % this.items.length;

      // Pre-populate the new 'next' slide
      const nextIdx = (this.currentIndex + 1) % this.items.length;
      this._populateSlide(this.pool.next, this.items[nextIdx], nextIdx);

      this.isTransitioning = false;
    }, this.duration);
  },

  start() {
    if (!this.intervalId) {
      this.intervalId = setInterval(() => this.advance(), this.interval);
    }
  },

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  },

  // --- Interaction --------------------------------------------------------

  _setupClickHandler() {
    this.container.addEventListener('click', (e) => {
      const slide = e.target.closest('.kiosk-carousel__slide');
      if (!slide) return;
      e.preventDefault();

      // Read index from the clicked slide's data attribute
      const index = parseInt(slide.dataset.index, 10);
      const openAt = isNaN(index) ? this.currentIndex : index;

      if (window.unifiedGalleryLightbox) {
        window.unifiedGalleryLightbox.openLightboxFromData(
          this.items,
          openAt,
          this.container.dataset.galleryId || 'kiosk-featured'
        );
      }
    });
  },

  _setupPauseResume() {
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) { this.stop(); } else { this.start(); }
    });
    document.addEventListener('lightbox:open', () => this.stop());
    document.addEventListener('lightbox:close', () => this.start());
  },

  // --- Helpers ------------------------------------------------------------

  _toCamelCase(item) {
    const out = {};
    for (const key in item) {
      out[key.replace(/_([a-z])/g, (_, c) => c.toUpperCase())] = item[key];
    }
    return out;
  },

  // --- Legacy fallback for DOM-based carousels (no JSON data) -------------

  _initLegacy(container) {
    const images = container.querySelectorAll(
      '.gallery-single-image, .gallery-image, .kiosk-carousel__slide'
    );
    if (images.length === 0) return;

    const interval = parseInt(container.dataset.carouselInterval, 10) || 5000;
    const duration = parseInt(container.dataset.carouselDuration, 10) || 1200;
    const transition = container.dataset.carouselTransition || 'crossfade';

    container.style.setProperty('--carousel-transition-duration', duration + 'ms');
    if (transition !== 'crossfade') {
      container.classList.add('transition-' + transition);
    }

    if (images.length === 1) {
      images[0].classList.add('carousel-active');
      return;
    }

    let currentIndex = 0;
    let intervalId = null;
    images[currentIndex].classList.add('carousel-active');

    function advance() {
      images[currentIndex].classList.remove('carousel-active');
      currentIndex = (currentIndex + 1) % images.length;
      images[currentIndex].classList.add('carousel-active');
    }

    function start() {
      if (!intervalId) { intervalId = setInterval(advance, interval); }
    }

    function stop() {
      if (intervalId) { clearInterval(intervalId); intervalId = null; }
    }

    document.addEventListener('visibilitychange', function() {
      if (document.hidden) { stop(); } else { start(); }
    });
    document.addEventListener('lightbox:open', stop);
    document.addEventListener('lightbox:close', start);

    start();
  }
};

window.KioskCarousel = KioskCarousel;
