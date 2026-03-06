// Newsletter form handler for subscribe and unsubscribe pages

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

document.addEventListener('DOMContentLoaded', () => {
    initForm('newsletter-form', 'newsletter-messages');
    initForm('unsubscribe-form', 'unsubscribe-messages');
});
