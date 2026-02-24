// Dashboard: Cancel Booking
document.querySelectorAll('[data-booking-id]').forEach((button) => {
    button.addEventListener('click', async () => {
        const bookingId = button.getAttribute('data-booking-id');
        const token = localStorage.getItem('access_token');

        if (!token) {
            alert('Будь ласка, увійдіть у систему.');
            window.location.href = '/login';
            return;
        }

        try {
            const response = await fetch(`/bookings/${bookingId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error('Не вдалося скасувати бронювання');
            }

            window.location.reload();
        } catch (error) {
            showToast(error.message, 'danger');
        }
    });
});

// Dashboard: Update Name Form
document.getElementById('update-name-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    const formData = new FormData(e.target);
    const errorBox = document.getElementById('name-error');
    errorBox.classList.add('d-none');

    try {
        const response = await fetch('/auth/update-profile', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Не вдалося оновити ПІБ');
        }

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        document.cookie = `access_token=${data.access_token}; path=/; max-age=86400`;
        
        showToast('ПІБ успішно оновлено', 'success');
        setTimeout(() => window.location.reload(), 1500);
    } catch (error) {
        console.error('Error:', error);
        errorBox.textContent = error.message;
        errorBox.classList.remove('d-none');
        showToast(error.message, 'danger');
    }
});

// Dashboard: Change Password Form
document.getElementById('change-password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const errorBox = document.getElementById('password-error');
    errorBox.classList.add('d-none');

    if (newPassword.length < 6) {
        errorBox.textContent = 'Новий пароль має містити мінімум 6 символів.';
        errorBox.classList.remove('d-none');
        showToast('Пароль має містити мінімум 6 символів', 'danger');
        return;
    }

    if (newPassword !== confirmPassword) {
        errorBox.textContent = 'Паролі не співпадають.';
        errorBox.classList.remove('d-none');
        showToast('Паролі не співпадають', 'danger');
        return;
    }

    const formData = new FormData(e.target);
    formData.delete('confirm-password');

    try {
        const response = await fetch('/auth/change-password', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Не вдалося змінити пароль');
        }

        showToast('Пароль успішно змінено', 'success');
        e.target.reset();
        errorBox.classList.add('d-none');
    } catch (error) {
        console.error('Error:', error);
        errorBox.textContent = error.message;
        errorBox.classList.remove('d-none');
        showToast(error.message, 'danger');
    }
});
// Dashboard: Link Telegram via Telegram Auth Widget
function onTelegramLink(user) {
    const token = localStorage.getItem('access_token');
    const errorBox = document.getElementById('telegram-error');
    errorBox.classList.add('d-none');

    fetch('/auth/link-telegram', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(user)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.detail || 'Не вдалося приєднати Telegram акаунт');
            });
        }
        return response.json();
    })
    .then(data => {
        showToast('Telegram акаунт успішно приєднано', 'success');
        setTimeout(() => window.location.reload(), 1500);
    })
    .catch(error => {
        console.error('Error:', error);
        errorBox.textContent = error.message;
        errorBox.classList.remove('d-none');
        showToast(error.message, 'danger');
    });
}

// Dashboard: Toggle Telegram Notifications
const notificationToggle = document.getElementById('notification-toggle');
if (notificationToggle) {
    notificationToggle.addEventListener('change', async (e) => {
        const token = localStorage.getItem('access_token');
        const isEnabled = e.target.checked;

        try {
            const response = await fetch('/auth/update-notification-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ notify: isEnabled })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Не вдалося оновити налаштування');
            }

            const message = isEnabled 
                ? 'Сповіщення увімкнено' 
                : 'Сповіщення вимкнено';
            showToast(message, 'success');
        } catch (error) {
            console.error('Error:', error);
            // Revert toggle on error
            e.target.checked = !isEnabled;
            showToast(error.message, 'danger');
        }
    });
}