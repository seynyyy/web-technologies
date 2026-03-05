// Register Page
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fullName = document.querySelector('input[name="full_name"]').value.trim();
    const password = document.querySelector('input[name="password"]').value;
    const passwordConfirm = document.querySelector('input[name="password_confirm"]').value;

    if (!fullName) {
        showToast('Будь ласка, введіть ПІБ', 'danger');
        return;
    }

    if (password.length < 6) {
        showToast('Пароль має містити мінімум 6 символів', 'danger');
        return;
    }

    if (password !== passwordConfirm) {
        showToast('Паролі не збігаються', 'danger');
        return;
    }

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                full_name: fullName,
                password: password,
                password_confirm: passwordConfirm
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showToast(data.detail || 'Помилка реєстрації', 'danger');
            return;
        }

        localStorage.setItem('access_token', data.access_token);
        document.cookie = `access_token=${data.access_token}; path=/`;
        
        showToast('Успішна реєстрація! Перенаправлення...', 'success');
        window.location.href = '/dashboard';
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Помилка при відправці форми', 'danger');
    }
});