-- Script de configuração do banco de dados MySQL para o sistema de quadras
-- Execute este script no MySQL para criar o banco e as tabelas

-- Criar o banco de dados
CREATE DATABASE IF NOT EXISTS quadras_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usar o banco de dados
USE quadras_db;

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_telefone (telefone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de quadras
CREATE TABLE IF NOT EXISTS quadras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    local VARCHAR(255) NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    ativa BOOLEAN DEFAULT TRUE,
    INDEX idx_ativa (ativa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de reservas
CREATE TABLE IF NOT EXISTS reservas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_unico VARCHAR(10) NOT NULL UNIQUE,
    usuario_id INT NOT NULL,
    quadra_id INT NOT NULL,
    data_reserva DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL,
    status ENUM('Pendente', 'Aprovado', 'Reprovado') DEFAULT 'Pendente',
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    FOREIGN KEY (quadra_id) REFERENCES quadras (id) ON DELETE CASCADE,
    INDEX idx_data_hora (data_reserva, hora_inicio),
    INDEX idx_status (status),
    INDEX idx_codigo_unico (codigo_unico)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inserir quadras padrão
INSERT IGNORE INTO quadras (nome, local, tipo) VALUES
('Arena de Vôlei', 'Praça da Juventude', 'Vôlei'),
('Quadra Poliesportiva', 'Praça da Juventude', 'Poliesportiva'),
('Campo Sintético', 'Praça da Juventude', 'Futebol'),
('Arena de Vôlei', 'Praça Central', 'Vôlei'),
('Quadra Poliesportiva', 'Praça Central', 'Poliesportiva'),
('Quadra Poliesportiva', 'Quadra do Sarney', 'Poliesportiva');

-- Inserir alguns dados de exemplo para teste (opcional)
-- Usuário de exemplo
INSERT IGNORE INTO usuarios (nome, telefone) VALUES
('João Silva', '(96) 99999-1234'),
('Maria Santos', '(96) 99999-5678'),
('Pedro Oliveira', '(96) 99999-9012');

-- Reservas de exemplo
INSERT IGNORE INTO reservas (codigo_unico, usuario_id, quadra_id, data_reserva, hora_inicio, hora_fim, status, observacoes) VALUES
('A123', 1, 1, '2025-01-15', '17:00:00', '18:00:00', 'Aprovado', 'Reserva para treino de vôlei'),
('B456', 2, 2, '2025-01-15', '18:00:00', '19:00:00', 'Pendente', 'Jogo de futsal'),
('C789', 3, 3, '2025-01-15', '19:00:00', '20:00:00', 'Aprovado', 'Treino de futebol'),
('D012', 1, 4, '2025-01-15', '20:00:00', '21:00:00', 'Reprovado', 'Conflito de horário');

-- Verificar se as tabelas foram criadas corretamente
SHOW TABLES;

-- Verificar dados inseridos
SELECT 'Quadras cadastradas:' as info;
SELECT * FROM quadras;

SELECT 'Usuários cadastrados:' as info;
SELECT * FROM usuarios;

SELECT 'Reservas cadastradas:' as info;
SELECT r.*, u.nome as usuario_nome, q.nome as quadra_nome 
FROM reservas r 
JOIN usuarios u ON r.usuario_id = u.id 
JOIN quadras q ON r.quadra_id = q.id;

-- Estatísticas básicas
SELECT 'Estatísticas do sistema:' as info;
SELECT 
    (SELECT COUNT(*) FROM quadras) as total_quadras,
    (SELECT COUNT(*) FROM usuarios) as total_usuarios,
    (SELECT COUNT(*) FROM reservas) as total_reservas,
    (SELECT COUNT(*) FROM reservas WHERE status = 'Pendente') as reservas_pendentes,
    (SELECT COUNT(*) FROM reservas WHERE status = 'Aprovado') as reservas_aprovadas,
    (SELECT COUNT(*) FROM reservas WHERE status = 'Reprovado') as reservas_reprovadas;

