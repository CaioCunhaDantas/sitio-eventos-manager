"""Migrações: atualizam bancos ANTIGOS para a versão atual sem perder dados.

O SQLite guarda um número de versão dentro do próprio arquivo
(PRAGMA user_version). Cada migração leva o banco de uma versão para a
seguinte. Bancos novos já nascem na versão atual pelo schema.sql.

Para mudar o banco no futuro:
  1. altere o schema.sql (versão mais nova);
  2. adicione aqui uma migração que faz a mesma mudança num banco antigo;
  3. aumente VERSAO_ATUAL.
"""

VERSAO_ATUAL = 3

# versão de destino -> script SQL que leva da versão anterior até ela
MIGRACOES: dict[int, str] = {
    # v1 -> v2: endereço do cliente + pré-reserva com dados incompletos
    2: """
    PRAGMA foreign_keys = OFF;
    BEGIN;

    ALTER TABLE cliente ADD COLUMN endereco TEXT;
    ALTER TABLE cliente ADD COLUMN bairro   TEXT;
    ALTER TABLE cliente ADD COLUMN cidade   TEXT;

    -- O SQLite não altera CHECKs de uma tabela existente. Receita oficial:
    -- cria a tabela nova, copia os dados, apaga a antiga e renomeia.
    DROP VIEW IF EXISTS vw_saldo_reserva;   -- depende de reserva; o schema recria

    CREATE TABLE reserva_nova (
        id             INTEGER PRIMARY KEY,
        id_cliente     INTEGER NOT NULL REFERENCES cliente (id) ON DELETE RESTRICT,
        data_festa     TEXT    NOT NULL CHECK (data_festa IS date(data_festa)),
        hora_inicio    TEXT    NOT NULL CHECK (hora_inicio IS strftime('%H:%M', hora_inicio)),
        hora_fim       TEXT    NOT NULL CHECK (hora_fim IS strftime('%H:%M', hora_fim)),
        tipo_festa     TEXT    CHECK (trim(tipo_festa) <> ''),
        num_convidados INTEGER CHECK (num_convidados > 0),
        valor_total    INTEGER CHECK (valor_total > 0),
        valor_sinal    INTEGER NOT NULL DEFAULT 0 CHECK (valor_sinal >= 0),
        status         TEXT    NOT NULL DEFAULT 'pre_reserva'
                       CHECK (status IN ('pre_reserva', 'confirmada', 'realizada', 'cancelada')),
        observacoes    TEXT,
        criado_em      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
        CHECK (hora_inicio >= '09:00'),
        CHECK (hora_fim    <= '19:00'),
        CHECK (hora_inicio <  hora_fim),
        CHECK (valor_total IS NULL OR valor_sinal <= valor_total),
        CHECK (status = 'pre_reserva'
               OR (tipo_festa IS NOT NULL AND num_convidados IS NOT NULL
                   AND valor_total IS NOT NULL))
    ) STRICT;

    INSERT INTO reserva_nova
        SELECT id, id_cliente, data_festa, hora_inicio, hora_fim, tipo_festa,
               num_convidados, valor_total, valor_sinal, status, observacoes, criado_em
        FROM reserva;

    DROP TABLE reserva;                     -- apaga junto os índices antigos
    ALTER TABLE reserva_nova RENAME TO reserva;

    CREATE UNIQUE INDEX ux_reserva_uma_por_dia ON reserva (data_festa)
        WHERE status <> 'cancelada';
    CREATE INDEX ix_reserva_cliente ON reserva (id_cliente);

    PRAGMA user_version = 2;
    COMMIT;
    PRAGMA foreign_keys = ON;
    """,
    # v2 -> v3: CPF do cliente
    3: """
    BEGIN;
    ALTER TABLE cliente ADD COLUMN cpf TEXT
        CHECK (cpf IS NULL OR (length(cpf) = 11 AND cpf NOT GLOB '*[^0-9]*'));
    CREATE UNIQUE INDEX ux_cliente_cpf ON cliente (cpf) WHERE cpf IS NOT NULL;
    PRAGMA user_version = 3;
    COMMIT;
    """,
}
