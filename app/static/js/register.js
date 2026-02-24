// Register Page
document.querySelector('form').addEventListener('submit', (e) => {
    const fullName = document.querySelector('input[name="full_name"]').value.trim();
    const password = document.querySelector('input[name="password"]').value;
    const passwordConfirm = document.querySelector('input[name="password_confirm"]').value;

    if (!fullName) {
        e.preventDefault();
        showToast('Будь ласка, введіть ПІБ', 'danger');
        return;
    }

    if (password.length < 6) {
        e.preventDefault();
        showToast('Пароль має містити мінімум 6 символів', 'danger');
        return;
    }

    if (password !== passwordConfirm) {
        e.preventDefault();
        showToast('Паролі не збігаються', 'danger');
        return;
    }
});
