// Admin Dashboard
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login';
}

const authHeaders = {
    'Authorization': `Bearer ${token}`
};

let machineModal = null;

const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
        headers: {
            ...authHeaders,
            ...(options.headers || {})
        },
        ...options
    });
    if (!response.ok) {
        let errorMessage = 'Помилка запиту';

        try {
            const errorData = await response.json();
            if (typeof errorData?.detail === 'string') {
                errorMessage = errorData.detail;
            }
        } catch (error) {
            console.error('Failed to parse error response:', error);
        }

        throw new Error(errorMessage);
    }
    if (response.status === 204) {
        return null;
    }
    return response.json();
};

const loadStats = async () => {
    const stats = await fetchJson('/admin-api/stats');
    document.getElementById('stat-users').textContent = stats.users;
    document.getElementById('stat-machines').textContent = stats.machines;
    document.getElementById('stat-active').textContent = stats.active_machines;
    document.getElementById('stat-bookings').textContent = stats.today_bookings;
};

const renderMachines = (machines) => {
    const table = document.getElementById('machines-table');
    table.innerHTML = '';
    machines.forEach((machine) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td data-label="ID">${machine.id}</td>
            <td data-label="Назва"><input class="form-control form-control-sm" value="${machine.name}" data-machine-name="${machine.id}"></td>
            <td data-label="Активна">
                <input type="checkbox" class="form-check-input" ${machine.is_active ? 'checked' : ''} data-machine-active="${machine.id}">
            </td>
            <td data-label="Дії">
                <div class="admin-actions">
                    <button class="btn btn-sm btn-outline-primary" data-save-machine="${machine.id}">Зберегти</button>
                    <button class="btn btn-sm btn-outline-danger" data-delete-machine="${machine.id}">Видалити</button>
                </div>
            </td>
        `;
        table.appendChild(row);
    });
};

const loadMachines = async () => {
    const machines = await fetchJson('/admin-api/machines');
    renderMachines(machines);
};

const loadUsers = async () => {
    const users = await fetchJson('/admin-api/users');
    const table = document.getElementById('users-table');
    table.innerHTML = '';
    users.forEach((user) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td data-label="ID">${user.id}</td>
            <td data-label="ПІБ">${user.full_name}</td>
            <td data-label="Прань доступно">${user.washes_left}</td>
            <td data-label="Використано">${user.washes_used_this_month}</td>
            <td data-label="Адмін">${user.is_admin ? 'Так' : 'Ні'}</td>
            <td data-label="Корекція">
                <div class="input-group input-group-sm admin-adjust-group">
                    <input type="number" class="form-control" placeholder="+/-" data-user-delta="${user.id}">
                    <button class="btn btn-outline-secondary" data-user-apply="${user.id}">Застосувати</button>
                </div>
            </td>
        `;
        table.appendChild(row);
    });
};

const loadBookings = async () => {
    const today = new Date().toISOString().split('T')[0];
    const bookings = await fetchJson(`/admin-api/bookings?date_filter=${today}`);
    const table = document.getElementById('bookings-table');
    table.innerHTML = '';
    
    if (bookings.length === 0) {
        table.innerHTML = '<tr><td colspan="6" class="text-center py-3 text-muted">Немає бронювань на сьогодні</td></tr>';
        return;
    }
    
    bookings.forEach((booking) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td data-label="ID">${booking.id}</td>
            <td data-label="Користувач">${booking.user_full_name || 'N/A'}</td>
            <td data-label="Пральна машина">${booking.machine_id}</td>
            <td data-label="Дата">${booking.date}</td>
            <td data-label="Час">${booking.time_slot}</td>
            <td data-label="Створено">${booking.created_at}</td>
        `;
        table.appendChild(row);
    });
};

document.getElementById('add-machine-btn').addEventListener('click', () => {
    if (!machineModal) {
        machineModal = new bootstrap.Modal(document.getElementById('machine-modal'));
    }
    document.getElementById('machine-name').value = '';
    document.getElementById('machine-active').checked = true;
    document.getElementById('machine-modal-error').classList.add('d-none');
    machineModal.show();
});

document.getElementById('save-machine').addEventListener('click', async () => {
    const name = document.getElementById('machine-name').value.trim();
    const isActive = document.getElementById('machine-active').checked;
    const errorBox = document.getElementById('machine-modal-error');

    if (!name) {
        errorBox.textContent = 'Вкажіть назву машинки.';
        errorBox.classList.remove('d-none');
        return;
    }

    errorBox.classList.add('d-none');

    try {
        await fetchJson('/admin-api/machines', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, is_active: isActive })
        });

        machineModal.hide();
        await loadMachines();
        await loadStats();
    } catch (error) {
        errorBox.textContent = error.message;
        errorBox.classList.remove('d-none');
    }
});

document.getElementById('machines-table').addEventListener('click', async (event) => {
    const target = event.target;
    const machineId = target.getAttribute('data-save-machine') || target.getAttribute('data-delete-machine');
    if (!machineId) {
        return;
    }

    if (target.hasAttribute('data-save-machine')) {
        const nameInput = document.querySelector(`[data-machine-name="${machineId}"]`);
        const activeInput = document.querySelector(`[data-machine-active="${machineId}"]`);
        await fetchJson(`/admin-api/machines/${machineId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: nameInput.value.trim(),
                is_active: activeInput.checked
            })
        });
        await loadMachines();
        await loadStats();
    }

    if (target.hasAttribute('data-delete-machine')) {
        await fetchJson(`/admin-api/machines/${machineId}`, {
            method: 'DELETE'
        });
        await loadMachines();
        await loadStats();
    }
});

document.getElementById('users-table').addEventListener('click', async (event) => {
    const target = event.target;
    const userId = target.getAttribute('data-user-apply');
    if (!userId) {
        return;
    }

    const deltaInput = document.querySelector(`[data-user-delta="${userId}"]`);
    const deltaValue = Number(deltaInput.value);
    if (Number.isNaN(deltaValue) || deltaValue === 0) {
        return;
    }

    await fetchJson(`/admin-api/users/${userId}/adjust-washes?delta=${deltaValue}`, {
        method: 'POST'
    });
    deltaInput.value = '';
    await loadUsers();
    await loadStats();
});

Promise.all([loadStats(), loadMachines(), loadUsers(), loadBookings()]).catch((error) => {
    console.error(error);
});
// Debug: Load scheduler jobs
async function loadSchedulerJobs() {
    try {
        const data = await fetchJson('/admin-api/scheduler/jobs');
        
        const infoDiv = document.getElementById('scheduler-info');
        const table = document.getElementById('scheduler-jobs-table');
        
        if (data.status === 'error') {
            infoDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            table.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Scheduler не ініціалізований</td></tr>';
            return;
        }
        
        infoDiv.innerHTML = `
            <div class="alert alert-info mb-0">
                <strong>Status:</strong> ${data.scheduler_running ? '✅ Running' : '❌ Stopped'} | 
                <strong>Total Jobs:</strong> ${data.total_jobs}
            </div>
        `;
        
        if (data.jobs.length === 0) {
            table.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">Немає запланованих завдань</td></tr>';
            return;
        }
        
        table.innerHTML = '';
        data.jobs.forEach(job => {
            const row = document.createElement('tr');
            const nextRun = job.next_run_time ? new Date(job.next_run_time).toLocaleString('uk-UA') : 'N/A';
            
            row.innerHTML = `
                <td data-label="Job ID"><code class="small">${job.id}</code></td>
                <td data-label="Function"><small>${job.func}</small></td>
                <td data-label="Next Run">${nextRun}</td>
                <td data-label="Args"><small>${job.args}</small></td>
            `;
            table.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading scheduler jobs:', error);
        document.getElementById('scheduler-info').innerHTML = 
            `<div class="alert alert-danger">Помилка завантаження: ${error.message}</div>`;
    }
}

// Load scheduler jobs on page load
loadSchedulerJobs();