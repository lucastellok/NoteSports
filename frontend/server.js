// Outras rotas já existentes...

// Rota para obter os horários de uma quadra específica
app.get('/api/schedule', async (req, res) => {
    const court = req.query.court;
    // Supondo uma função para buscar horários no banco
    const schedule = await getCourtSchedule(court); 
    res.json(schedule);
});

// Rota para fazer uma reserva
app.post('/api/reserve', async (req, res) => {
    const { slotId, userCpf } = req.body;

    // Verifica se o CPF já possui uma reserva
    const existingReservation = await checkUserReservation(userCpf);
    if (existingReservation) {
        return res.json({ success: false, message: 'Você já possui uma reserva ativa.' });
    }

    // Lógica para realizar a reserva...
    const success = await makeReservation(slotId, userCpf);
    if (success) {
        res.json({ success: true });
    } else {
        res.json({ success: false, message: 'Erro ao fazer a reserva.' });
    }
});

// Funções fictícias para o exemplo:
async function getCourtSchedule(court) {
    // Exemplo de horários fictícios
    return [
        { id: 1, time: '08:00 - 09:00', status: false },
        { id: 2, time: '09:00 - 10:00', status: true },
        { id: 3, time: '10:00 - 11:00', status: false },
        // Outros horários...
    ];
}

async function checkUserReservation(cpf) {
    // Verifica no banco de dados se o CPF já tem uma reserva
    return false;  // Exemplo: retorna falso, indicando que não há reservas ativas
}

async function makeReservation(slotId, cpf) {
    // Lógica para criar a reserva no banco de dados
    return true;  // Exemplo: retorna verdadeiro se a reserva for bem-sucedida
}

app.listen(port, () => {
    console.log(`Servidor rodando em http://localhost:${port}`);
});
