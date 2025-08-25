// Função para carregar as quadras na página de reservas
document.addEventListener('DOMContentLoaded', () => {
    const courtSelect = document.getElementById('courtSelect');
    const scheduleTable = document.getElementById('scheduleTable');

    courtSelect.addEventListener('change', loadSchedule);

    // Carregar horários com base na quadra selecionada
    async function loadSchedule() {
        const selectedCourt = courtSelect.value;
        // Supondo uma API que retorna horários e status
        const response = await fetch(`/api/schedule?court=${selectedCourt}`);
        const schedule = await response.json();

        scheduleTable.innerHTML = ''; // Limpar a tabela
        schedule.forEach(slot => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${slot.time}</td>
                <td>${slot.status ? 'Ocupado' : 'Disponível'}</td>
                <td><button class="btn btn-${slot.status ? 'secondary' : 'primary'}" ${slot.status ? 'disabled' : ''} onclick="reserveSlot('${slot.id}')">${slot.status ? 'Indisponível' : 'Reservar'}</button></td>
            `;
            scheduleTable.appendChild(row);
        });
    }

    // Reservar um horário
    async function reserveSlot(slotId) {
        const userCpf = prompt("Digite seu CPF:");
        const userAge = prompt("Digite sua idade:");

        if (!validateCpf(userCpf)) {
            alert("CPF inválido!");
            return;
        }

        if (userAge < 18) {
            alert("Você deve ter mais de 18 anos para fazer uma reserva.");
            return;
        }

        try {
            const response = await fetch(`/api/reserve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slotId, userCpf })
            });

            const result = await response.json();
            if (result.success) {
                alert('Reserva feita com sucesso!');
                loadSchedule();
            } else {
                alert('Erro ao fazer reserva: ' + result.message);
            }
        } catch (error) {
            console.error('Erro ao reservar:', error);
        }
    }

    // Validação de CPF (simplificada)
    function validateCpf(cpf) {
        return /^[0-9]{11}$/.test(cpf);
    }

    loadSchedule();  // Carregar a tabela ao carregar a página
});

// Função para carregar as reservas do usuário na página de perfil
document.addEventListener('DOMContentLoaded', () => {
    const reservationList = document.getElementById('reservationList');
    const searchButton = document.getElementById('searchButton');
    const reservationTableBody = document.getElementById('reservationTableBody');
    
    // Função para carregar as reservas ao clicar no botão de busca
    searchButton.addEventListener('click', loadReservationsByCode);

    async function loadReservationsFromApi() {
        const response = await fetch('/api/user/reservations');
        const reservations = await response.json();

        reservationList.innerHTML = '';
        reservations.forEach(reservation => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.textContent = `${reservation.court} - ${reservation.time}`;
            reservationList.appendChild(item);
        });
    }

    loadReservationsFromApi();  // Carregar as reservas ao abrir a aba de perfil

    // Função para carregar as reservas com base no código de reserva inserido
    function loadReservationsByCode() {
        const reservationCode = document.getElementById('reservationCode').value;
        const reservations = JSON.parse(localStorage.getItem('reservations')) || [];
        reservationTableBody.innerHTML = '';

        // Filtra as reservas com o código de reserva inserido
        const userReservations = reservations.filter(res => res.reservationCode === reservationCode);

        if (userReservations.length === 0) {
            alert('Nenhuma reserva encontrada para esse código.');
        } else {
            userReservations.forEach(reservation => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${reservation.time}</td>
                    <td>${formatDate(reservation.date)}</td>
                    <td>${reservation.location}</td>
                `;
                reservationTableBody.appendChild(row);
            });
        }
    }

    // Função para formatar a data (apenas dia/mês)
    function formatDate(date) {
        const [year, month, day] = date.split('-');
        return `${day}/${month}`;
    }
});

// Função para adicionar uma nova reserva manualmente
function addReservation() {
    const time = document.getElementById('time').value;
    const date = document.getElementById('date').value;
    const owner = document.getElementById('owner').value;
    const location = document.getElementById('location').value;
    const reservationCode = document.getElementById('reservationCode').value;

    const reservation = { time, date, owner, location, reservationCode };
    const reservations = JSON.parse(localStorage.getItem('reservations')) || [];
    reservations.push(reservation);
    localStorage.setItem('reservations', JSON.stringify(reservations));

    alert('Horário adicionado com sucesso!');
    document.getElementById('addReservationForm').reset();
}

// Função para carregar as reservas com base no código de reserva inserido
document.addEventListener('DOMContentLoaded', () => {
    const searchButton = document.querySelector('#searchButton'); // Certifique-se que o botão tem o id 'searchButton'

    // Carregar as reservas ao clicar no botão
    searchButton.addEventListener('click', loadReservationsByCode);
});

function loadReservationsByCode() {
    const reservationCode = document.getElementById('reservationCode').value;
    const reservations = JSON.parse(localStorage.getItem('reservations')) || [];
    const reservationTableBody = document.getElementById('reservationTableBody');
    reservationTableBody.innerHTML = '';

    // Filtra as reservas com o código de reserva inserido
    const userReservations = reservations.filter(res => res.reservationCode === reservationCode);

    if (userReservations.length === 0) {
        alert('Nenhuma reserva encontrada para esse código.');
    } else {
        userReservations.forEach(reservation => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${reservation.time}</td>
                <td>${formatDate(reservation.date)}</td>
                <td>${reservation.location}</td>
            `;
            reservationTableBody.appendChild(row);
        });
    }
}

// Função para formatar a data (apenas dia/mês)
function formatDate(date) {
    const [year, month, day] = date.split('-');
    return `${day}/${month}`;
}
