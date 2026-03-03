// Newsletter subscription form handler
// Works for both the dedicated signup page form and the footer form

function initNewsletterForm(form) {
    if (!form) return;

    const messagesId = form.id === 'footer-newsletter-form'
        ? 'footer-newsletter-messages'
        : 'newsletter-messages';

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const messages = document.getElementById(messagesId);
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        submitBtn.disabled = true;
        submitBtn.textContent = 'Subscribing...';

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

document.addEventListener('DOMContentLoaded', () => {
    initNewsletterForm(document.getElementById('newsletter-form'));
    initNewsletterForm(document.getElementById('footer-newsletter-form'));
});
