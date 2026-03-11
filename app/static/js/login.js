// Login Page
const passwordForm = document.getElementById('password-login-form');
const passwordError = document.getElementById('password-error');

passwordForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    passwordError.classList.add('d-none');
    const formData = new FormData(passwordForm);
    const username = formData.get('username');
    const password = formData.get('password');

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            throw new Error('Невірний логін або пароль');
        }

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        document.cookie = `access_token=${data.access_token}; path=/`;
        window.location.href = '/dashboard';
    } catch (error) {
        passwordError.textContent = error.message;
        passwordError.classList.remove('d-none');
    }
});

function onTelegramAuth(user) {
    document.getElementById('telegram-login-container').classList.add('d-none');
    document.getElementById('loading-spinner').classList.remove('d-none');

    fetch('/auth/login/telegram', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(user)
    })
    .then(response => {
        if (!response.ok) throw new Error('Помилка авторизації');
        return response.json();
    })
    .then(data => {
        localStorage.setItem('access_token', data.access_token);
        document.cookie = `access_token=${data.access_token}; path=/`;
        window.location.href = '/dashboard';
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Не вдалося увійти. Спробуйте ще раз.', 'danger');
        document.getElementById('telegram-login-container').classList.remove('d-none');
        document.getElementById('loading-spinner').classList.add('d-none');
    });
}
