// Newsletter form handler for subscribe and unsubscribe pages
import { animate, stagger } from 'animejs';

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const ACCENT_COLOR = '#e91e63';

// --- Entrance animations ---

function runEntranceAnimation() {
    if (prefersReducedMotion) return;

    const hero = document.querySelector('[data-nl-hero]');
    if (!hero) return;

    const items = hero.querySelectorAll('[data-nl-animate]');
    if (!items.length) return;

    // Set initial state
    items.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(12px)';
    });

    animate(items, {
        opacity: [0, 1],
        translateY: [12, 0],
        delay: stagger(120, { start: 100 }),
        duration: 500,
        easing: 'easeOutCubic',
    });
}

// --- Body reveal on scroll ---

function initBodyReveal() {
    if (prefersReducedMotion) return;

    const body = document.querySelector('[data-nl-animate="body"]');
    if (!body) return;

    body.style.opacity = '0';
    body.style.transform = 'translateY(20px)';

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animate(body, {
                    opacity: [0, 1],
                    translateY: [20, 0],
                    duration: 500,
                    easing: 'easeOutCubic',
                });
                observer.unobserve(body);
            }
        });
    }, { threshold: 0.1 });

    observer.observe(body);
}

// --- Form handling ---

function initNewsletterForm() {
    const form = document.getElementById('newsletter-form');
    if (!form) return;

    const card = form.closest('.nl-card');
    const messages = document.getElementById('newsletter-messages');
    const submitBtn = form.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.nl-form__button-text');
    const btnArrow = submitBtn.querySelector('.nl-form__button-arrow');
    const originalText = btnText ? btnText.textContent : submitBtn.textContent;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);

        // Loading state
        submitBtn.disabled = true;
        if (btnText) btnText.textContent = 'Sending...';
        if (btnArrow) btnArrow.style.display = 'none';

        if (messages) {
            messages.textContent = '';
            messages.className = 'nl-form__messages';
        }

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (messages) {
                if (data.success) {
                    messages.textContent = data.message;
                    messages.classList.add('nl-form__messages--success');
                    form.reset();

                    // Success button state
                    if (btnText) btnText.textContent = 'Subscribed!';
                    setTimeout(() => {
                        if (btnText) btnText.textContent = originalText;
                        if (btnArrow) btnArrow.style.display = '';
                        submitBtn.disabled = false;
                    }, 3000);

                    // Celebration flash
                    if (!prefersReducedMotion && card) {
                        animate(card, {
                            boxShadow: [
                                '4px 4px 0px #121212',
                                `4px 4px 0px ${ACCENT_COLOR}`,
                                '4px 4px 0px #121212',
                            ],
                            duration: 600,
                            easing: 'easeInOutQuad',
                        });
                    }
                } else {
                    messages.textContent = data.error;
                    messages.classList.add('nl-form__messages--error');
                    restoreButton();
                }
            } else {
                restoreButton();
            }
        } catch {
            if (messages) {
                messages.textContent = 'Connection error. Please try again.';
                messages.classList.add('nl-form__messages--error');
            }
            restoreButton();
        }

        function restoreButton() {
            submitBtn.disabled = false;
            if (btnText) btnText.textContent = originalText;
            if (btnArrow) btnArrow.style.display = '';
        }
    });
}

// --- Legacy unsubscribe form handler ---

function initForm(formId, messagesId) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const messages = document.getElementById(messagesId);
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        submitBtn.disabled = true;
        submitBtn.textContent = originalText + '...';

        if (messages) {
            messages.textContent = '';
            messages.className = messages.className.replace(/--success|--error/g, '');
        }

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (messages) {
                if (data.success) {
                    messages.textContent = data.message;
                    messages.className += ' ' + messages.className.split(' ')[0] + '--success';
                    form.reset();
                } else {
                    messages.textContent = data.error;
                    messages.className += ' ' + messages.className.split(' ')[0] + '--error';
                }
            }
        } catch {
            if (messages) {
                messages.textContent = 'Connection error. Please try again.';
                messages.className += ' ' + messages.className.split(' ')[0] + '--error';
            }
        }

        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    });
}

// --- Init ---

document.addEventListener('DOMContentLoaded', () => {
    runEntranceAnimation();
    initBodyReveal();
    initNewsletterForm();
    initForm('unsubscribe-form', 'unsubscribe-messages');
});
