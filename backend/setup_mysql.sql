CREATE TABLE locais (
    id_local SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    endereco VARCHAR(255) NOT NULL
);

CREATE TABLE quadras (
    id_quadra SERIAL PRIMARY KEY,
    id_local INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    coberta BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (id_local) REFERENCES locais(id_local) ON DELETE CASCADE
);

CREATE TABLE horarios (
    id_horario SERIAL PRIMARY KEY,
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL
);

CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    senha_hash VARCHAR(255) NOT NULL
);

CREATE TABLE reservas (
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20),
    nome_quadra VARCHAR(100) NOT NULL,
    data_reserva DATE NOT NULL,
    horario TIME NOT NULL,
    FOREIGN KEY (nome_quadra) REFERENCES quadras(nome) ON DELETE CASCADE,
    FOREIGN KEY (telefone) REFERENCES usuarios(telefone) ON DELETE SET NULL
);

INSERT INTO locais (nome, endereco) VALUES
('Praça João da Silva Nery', 'Avenida Tancredo Neves - Centro'),
('Escola Estadual Mineko Hayashida', 'Avenida Tancredo Neves, 2960 - Centro');

INSERT INTO quadras (id_local, nome, tipo, coberta) VALUES
(1, 'Quadra de Futsal', 'Futebol Society', TRUE),
(2, 'Quadra de Vôlei', 'Vôlei de Areia', FALSE);

INSERT INTO horarios (hora_inicio, hora_fim) VALUES
('08:00', '09:00'),
('09:00', '10:00');

INSERT INTO usuarios (nome, email, telefone, senha_hash) VALUES
('Carlos Henrique', 'carlos.rick@gmail.com', '96991815496', 'senha_carlos');

INSERT INTO reservas (nome, telefone, nome_quadra, data_reserva, horario) VALUES
('Carlos Henrique', '96991815496', 'Quadra de Futsal', '2025-09-10', '08:00');
