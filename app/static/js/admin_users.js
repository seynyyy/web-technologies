// Admin Users Management
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login';
}

const authHeaders = {
    'Authorization': `Bearer ${token}`
};

let currentEditUserId = null;
let allUsers = [];
let editUserModal = null;

const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
        headers: {
            ...authHeaders,
            ...(options.headers || {})
        },
        ...options
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    if (response.status === 204) {
        return null;
    }
    return response.json();
};

const loadUsers = async () => {
    try {
        allUsers = await fetchJson('/admin-api/users');
        renderUsers(allUsers);
    } catch (error) {
        console.error('Помилка завантаження користувачів:', error);
    }
};

const renderUsers = (users) => {
    const table = document.getElementById('users-table');
    table.innerHTML = '';
    users.forEach((user) => {
        const row = document.createElement('tr');
        const telegramLink = user.telegram_id 
            ? `<a href="tg://user?id=${user.telegram_id}" target="_blank" class="badge text-bg-info">${user.telegram_id}</a>` 
            : '<span class="text-muted">—</span>';
        
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.full_name}</td>
            <td>${telegramLink}</td>
            <td>${user.washes_left}</td>
            <td>${user.washes_used_this_month}</td>
            <td>${user.is_admin ? '<span class="badge text-bg-warning">Так</span>' : '<span class="text-muted">Ні</span>'}</td>
            <td>${user.is_active ? '<span class="badge text-bg-success">Так</span>' : '<span class="badge text-bg-danger">Ні</span>'}</td>
            <td>${user.has_discount ? '<span class="badge text-bg-info">Так</span>' : '<span class="text-muted">Ні</span>'}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" data-edit-user="${user.id}">Редагувати</button>
            </td>
        `;
        table.appendChild(row);
    });
};

const openEditModal = (user) => {
    currentEditUserId = user.id;
    document.getElementById('edit-full-name').value = user.full_name;
    document.getElementById('edit-washes-left').value = user.washes_left;
    document.getElementById('edit-washes-used').value = user.washes_used_this_month;
    document.getElementById('edit-is-admin').checked = user.is_admin;
    document.getElementById('edit-is-active').checked = user.is_active;
    document.getElementById('edit-has-discount').checked = user.has_discount;
    document.getElementById('edit-modal-error').classList.add('d-none');
    
    if (!editUserModal) {
        editUserModal = new bootstrap.Modal(document.getElementById('edit-user-modal'));
    }
    editUserModal.show();
};

const saveUser = async () => {
    if (!currentEditUserId) return;

    const updates = {
        full_name: document.getElementById('edit-full-name').value.trim(),
        washes_left: Number(document.getElementById('edit-washes-left').value),
        washes_used_this_month: Number(document.getElementById('edit-washes-used').value),
        is_admin: document.getElementById('edit-is-admin').checked,
        is_active: document.getElementById('edit-is-active').checked,
        has_discount: document.getElementById('edit-has-discount').checked
    };

    if (!updates.full_name) {
        document.getElementById('edit-modal-error').textContent = 'ПІБ не може бути порожним.';
        document.getElementById('edit-modal-error').classList.remove('d-none');
        return;
    }

    try {
        await fetchJson(`/admin-api/users/${currentEditUserId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        });

        editUserModal.hide();
        await loadUsers();
        showToast('Користувача успішно оновлено', 'success');
    } catch (error) {
        console.error('Помилка:', error);
        document.getElementById('edit-modal-error').textContent = `Помилка: ${error.message}`;
        document.getElementById('edit-modal-error').classList.remove('d-none');
    }
};

document.getElementById('save-user-btn').addEventListener('click', saveUser);

document.getElementById('users-table').addEventListener('click', (event) => {
    const editBtn = event.target.closest('[data-edit-user]');
    if (editBtn) {
        const userId = Number(editBtn.getAttribute('data-edit-user'));
        const user = allUsers.find(u => u.id === userId);
        if (user) {
            openEditModal(user);
        }
    }
});

document.getElementById('search-users').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const filtered = allUsers.filter(user => 
        user.full_name.toLowerCase().includes(query)
    );
    renderUsers(filtered);
});

loadUsers();
