document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');
    const currentUser = document.getElementById("currentUser")?.value || "";

    if (!calendarEl) {
        console.error("Ошибка: элемент календаря не найден!");
        return;
    }

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: `/api/events/${group_id}`,
        dateClick: function (info) {
            openModal('eventModal', info.dateStr);
        },
        eventClick: function (info) {
            window.location.href = `/event/${info.event.id}`;
        }
    });

    calendar.render();
});

// Функция открытия модального окна
function openModal(modalId, date = null) {
    const modal = document.getElementById(modalId);
    const overlay = document.getElementById('modalOverlay');

    if (modal && overlay) {
        modal.classList.add('active');
        overlay.classList.add('active');

        if (date) {
            const dateInput = modal.querySelector('#eventDate');
            if (dateInput) dateInput.value = date;
        }
    }
}

// Функция закрытия модального окна
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    const overlay = document.getElementById('modalOverlay');

    if (modal && overlay) {
        modal.classList.remove('active');
        overlay.classList.remove('active');
    }
}

// Отправка запроса на редактирование
function sendEditRequest(eventId) {
    const newEventName = prompt("Введите новое название события:");
    if (!newEventName) return;

    fetch('/api/request_edit_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            event_id: eventId,
            event_name: newEventName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Запрос на редактирование отправлен!");
        } else {
            alert("Ошибка: " + data.message);
        }
    })
    .catch(error => console.error("Ошибка при отправке запроса:", error));
}

//Отправка запроса на удаление
function sendDeleteRequest(eventId) {
    fetch('/api/request_delete_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Запрос на удаление отправлен!");
        } else {
            alert("Ошибка: " + data.message);
        }
    })
    .catch(error => console.error("Ошибка при отправке запроса:", error));
}

function openEditModal(event) {
    document.getElementById('editEventId').value = event.id;
    document.getElementById('editEventName').value = event.title;
    document.getElementById('editEventDate').value = event.start.toISOString().split('T')[0];

    openModal('editEventModal');
}

//Обработка формы добавления события
document.getElementById('eventForm')?.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!currentUser) {
        alert("Вы не вошли в аккаунт!");
        return;
    }

    const formData = new FormData(this);
    formData.append("created_by", currentUser);

    fetch('/add_event_ajax', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeModal('eventModal');
            location.reload();
        } else {
            alert('Ошибка: ' + data.message);
        }
    })
    .catch(error => console.error('Ошибка при добавлении события:', error));
});

// Обработка редактирования события
document.getElementById('editEventForm')?.addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    console.log("Данные перед отправкой:", Object.fromEntries(formData));

    fetch('/api/edit_event', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeModal('editEventModal');
            console.log("Успешно отправлено!");
        } else {
            alert('Ошибка при редактировании события: ' + data.message);
        }
    })
    .catch(error => console.error('Ошибка при редактировании события:', error));
});


// Обработка удаления события
document.getElementById('deleteEventBtn')?.addEventListener('click', function () {
    const eventId = document.getElementById('editEventId').value;

    if (!eventId) {
        alert("Ошибка: событие не выбрано!");
        return;
    }

    if (!confirm("Вы уверены, что хотите удалить это событие?")) {
        return;
    }

    fetch('/api/delete_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Событие успешно удалено!");
            closeModal('editEventModal');
            location.reload();
        } else {
            alert("Ошибка: " + data.message);
        }
    })
    .catch(error => console.error('Ошибка при удалении события:', error));
});

// Запрос на редактирование
document.getElementById("requestEditBtn")?.addEventListener("click", function () {
    const eventId = document.getElementById("editEventId").value;
    const newEventName = document.getElementById("editEventName").value;

    fetch("/api/request_edit_event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_id: eventId, event_name: newEventName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Запрос на редактирование отправлен!");
            closeModal("editEventModal");
        } else {
            alert("Ошибка: " + data.message);
        }
    })
    .catch(error => console.error("Ошибка при запросе редактирования:", error));
});
