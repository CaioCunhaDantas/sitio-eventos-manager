-- =============================================================
-- Schema do banco - Gestão Sítio de Festas (SQLite)
--
-- Convenções:
--   * Valores em dinheiro são guardados em CENTAVOS (INTEGER).
--     Ex.: R$ 1.500,50 -> 150050. Evita erros de arredondamento.
--   * Datas em texto ISO 'AAAA-MM-DD'; horas em 'HH:MM'.
--   * STRICT faz o SQLite recusar valores do tipo errado
--     (por padrão ele aceita texto numa coluna INTEGER).
--   * Saldo devedor NÃO é guardado: é calculado como
--     valor_total - soma dos pagamentos (ver view no final).
--   * Este arquivo descreve o banco na versão MAIS NOVA. Bancos antigos
--     são atualizados pelas migrações em database/migracoes.py.
-- =============================================================

PRAGMA foreign_keys = ON;

-- -------------------------------------------------------------
-- Cliente: quem aluga o sítio
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cliente (
    id          INTEGER PRIMARY KEY,           -- gerado automaticamente
    nome        TEXT    NOT NULL CHECK (trim(nome) <> ''),
    telefone    TEXT    NOT NULL CHECK (trim(telefone) <> ''),
    email       TEXT,                          -- opcional
    observacoes TEXT,
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    -- Endereço separado em partes: permite analisar de onde vêm os clientes.
    -- Opcional no banco: numa pré-reserva ainda não temos esses dados.
    endereco    TEXT,                          -- rua e número
    bairro      TEXT,
    cidade      TEXT
) STRICT;

-- -------------------------------------------------------------
-- Reserva: uma festa em uma data
--
-- status 'pre_reserva' = cliente demonstrou interesse e ainda não
-- pagou o sinal. Nesse estado tipo_festa, num_convidados e
-- valor_total podem ficar em branco (dados incompletos). Para sair
-- da pré-reserva, eles passam a ser obrigatórios (último CHECK).
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reserva (
    id             INTEGER PRIMARY KEY,
    id_cliente     INTEGER NOT NULL
                   REFERENCES cliente (id) ON DELETE RESTRICT,
    data_festa     TEXT    NOT NULL
                   CHECK (data_festa IS date(data_festa)),   -- data válida
    hora_inicio    TEXT    NOT NULL
                   CHECK (hora_inicio IS strftime('%H:%M', hora_inicio)),
    hora_fim       TEXT    NOT NULL
                   CHECK (hora_fim IS strftime('%H:%M', hora_fim)),
    tipo_festa     TEXT    CHECK (trim(tipo_festa) <> ''),   -- texto livre
    num_convidados INTEGER CHECK (num_convidados > 0),
    valor_total    INTEGER CHECK (valor_total > 0),          -- centavos
    valor_sinal    INTEGER NOT NULL DEFAULT 0
                   CHECK (valor_sinal >= 0),                 -- centavos
    status         TEXT    NOT NULL DEFAULT 'pre_reserva'
                   CHECK (status IN ('pre_reserva', 'confirmada',
                                     'realizada', 'cancelada')),
    observacoes    TEXT,
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),

    -- Funcionamento do sítio: das 09:00 às 19:00
    CHECK (hora_inicio >= '09:00'),
    CHECK (hora_fim    <= '19:00'),
    CHECK (hora_inicio <  hora_fim),
    CHECK (valor_total IS NULL OR valor_sinal <= valor_total),
    -- Fora da pré-reserva, os dados da festa são obrigatórios
    CHECK (status = 'pre_reserva'
           OR (tipo_festa IS NOT NULL AND num_convidados IS NOT NULL
               AND valor_total IS NOT NULL))
) STRICT;

-- REGRA PRINCIPAL: apenas UMA festa por dia.
-- Índice único "parcial": só vale para reservas NÃO canceladas,
-- então cancelar uma reserva libera a data para outra.
CREATE UNIQUE INDEX IF NOT EXISTS ux_reserva_uma_por_dia
    ON reserva (data_festa)
    WHERE status <> 'cancelada';

-- Acelera "todas as reservas deste cliente"
CREATE INDEX IF NOT EXISTS ix_reserva_cliente ON reserva (id_cliente);

-- -------------------------------------------------------------
-- Pagamento: cada valor recebido de uma reserva
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pagamento (
    id              INTEGER PRIMARY KEY,
    id_reserva      INTEGER NOT NULL
                    REFERENCES reserva (id) ON DELETE RESTRICT,
    valor           INTEGER NOT NULL CHECK (valor > 0),          -- centavos
    data_pagamento  TEXT    NOT NULL
                    CHECK (data_pagamento IS date(data_pagamento)),
    tipo            TEXT    NOT NULL
                    CHECK (tipo IN ('sinal', 'parcela', 'quitacao')),
    forma_pagamento TEXT    NOT NULL
                    CHECK (forma_pagamento IN ('pix', 'dinheiro',
                                               'cartao_credito', 'cartao_debito',
                                               'transferencia')),
    observacao      TEXT,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
) STRICT;

CREATE INDEX IF NOT EXISTS ix_pagamento_reserva ON pagamento (id_reserva);

-- Trigger: regra que o banco executa sozinho a cada INSERT em pagamento.
-- Impede receber dinheiro de uma pré-reserva sem valor combinado
-- (sem valor_total não dá para calcular o saldo).
CREATE TRIGGER IF NOT EXISTS tg_pagamento_exige_dados
BEFORE INSERT ON pagamento
WHEN (SELECT valor_total FROM reserva WHERE id = NEW.id_reserva) IS NULL
BEGIN
    SELECT RAISE(ABORT, 'reserva_sem_dados_completos');
END;

-- -------------------------------------------------------------
-- Usuario: quem pode entrar no sistema (login)
-- A senha NUNCA é guardada: só o hash (impressão digital
-- irreversível) e o salt (valor aleatório que torna o hash único).
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuario (
    id         INTEGER PRIMARY KEY,
    nome       TEXT    NOT NULL UNIQUE CHECK (trim(nome) <> ''),
    senha_hash TEXT    NOT NULL,
    salt       TEXT    NOT NULL,
    criado_em  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
) STRICT;

-- -------------------------------------------------------------
-- View: situação financeira de cada reserva (saldo calculado)
-- Uma view é uma "consulta salva": se comporta como tabela,
-- mas é recalculada a cada uso, então nunca fica desatualizada.
-- -------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_saldo_reserva AS
SELECT
    r.id                               AS id_reserva,
    r.data_festa,
    c.nome                             AS cliente,
    r.status,
    r.valor_total,
    r.valor_sinal,
    COALESCE(SUM(p.valor), 0)          AS total_pago,
    r.valor_total - COALESCE(SUM(p.valor), 0) AS saldo_devedor,
    COALESCE(SUM(CASE WHEN p.tipo = 'sinal' THEN p.valor END), 0)
                                       AS sinal_pago
FROM reserva r
JOIN cliente c        ON c.id = r.id_cliente
LEFT JOIN pagamento p ON p.id_reserva = r.id
GROUP BY r.id;
