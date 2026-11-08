# 🏡 Gestão Sítio de Festas

Sistema simples de gestão de reservas, clientes e pagamentos para um sítio de eventos familiar, pensado para ser usado por pessoas sem familiaridade com tecnologia.

> 🚧 **Status:** em desenvolvimento (fase de modelagem)

---

## 📌 Sobre o projeto

Este projeto nasceu de uma necessidade real: ajudar minha família a organizar a agenda e as finanças do sítio de festas que administra. Hoje o controle é feito de forma manual, o que dificulta saber quais datas estão livres, quem já pagou o sinal e quanto ainda falta receber.

O objetivo é entregar uma ferramenta **simples e direta**, com poucas telas, letras grandes e linguagem do dia a dia, além de gerar **análises de dados** sobre o negócio (sazonalidade, faturamento, tipos de festa mais procurados).

Projeto desenvolvido por um aluno de Ciência de Dados do IBMEC, aplicando modelagem de dados, SQL, Python e design centrado no usuário em um caso real.

---

## 🎯 Funcionalidades planejadas

- [ ] Calendário com datas livres e ocupadas
- [ ] Cadastro de clientes
- [ ] Cadastro de reservas (data, horário, tipo de festa, nº de convidados, valor)
- [ ] Bloqueio automático de conflito de datas
- [ ] Controle de pagamentos (sinal, parcelas e saldo devedor)
- [ ] Lista de clientes com pagamento pendente
- [ ] Painel de análises (faturamento mensal, sazonalidade, ticket médio, taxa de cancelamento)
- [ ] Backup automático do banco de dados
- [ ] Exportação de relatórios para Excel

---

## 🗂️ Modelo de dados

Entidades principais e seus relacionamentos:

- **Cliente** (1) —— (N) **Reserva**
- **Reserva** (1) —— (N) **Pagamento**

| Entidade | Atributos principais |
|---|---|
| Cliente | id, nome, telefone, e-mail |
| Reserva | id, id_cliente, data, hora_início, hora_fim, tipo_festa, nº_convidados, valor_total, status |
| Pagamento | id, id_reserva, valor, data, forma_pagamento |

> O diagrama entidade-relacionamento (notação de Peter Chen) será adicionado em `docs/diagrama_er.png`.

---

## 🛠️ Tecnologias

| Camada | Ferramenta |
|---|---|
| Linguagem | Python |
| Banco de dados | SQLite |
| Interface | Streamlit |
| Análise de dados | Pandas |
| Versionamento | Git / GitHub |

---

## 📁 Estrutura prevista

```
sitio-eventos-manager/
├── app/            # telas e interface (Streamlit)
├── database/       # script SQL e acesso ao banco
├── docs/           # diagrama ER, prints e documentação
├── backups/        # cópias de segurança do banco
├── requirements.txt
└── README.md
```

---

## 🚀 Como executar

**Para testar no seu computador** (com dados fictícios de demonstração):

```bash
git clone https://github.com/CaioCunhaDantas/sitio-eventos-manager.git
cd sitio-eventos-manager
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
py -m database.dados_exemplo
$env:SITIO_DB = "database/demo.db"; .venv\Scripts\streamlit run app/main.py
```

**Testes automáticos:** `py -m unittest -v`

**Uso real, ligado 24h e acessível pelo celular:** veja [docs/implantacao.md](docs/implantacao.md).

---

## 🧭 Roadmap

1. **Levantamento de requisitos** com a família
2. **Modelagem**: diagrama ER, modelo lógico e script SQL
3. **MVP**: clientes, reservas, calendário e bloqueio de conflitos
4. **Pagamentos** e controle de inadimplência
5. **Dashboard** de análise de dados
6. **Testes de usabilidade** com o usuário final e ajustes
7. **Extras**: backup automático, exportação para Excel

---

## 👤 Autor

**Caio Cunha Dantas**
Estudante de Ciência de Dados — IBMEC

---

## 📄 Licença

Projeto de uso pessoal e educacional. Licença a definir.
