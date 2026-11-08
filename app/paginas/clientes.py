import streamlit as st

from app.componentes import campos_endereco, guardar_aviso, mostrar_aviso
from app.formatacao import STATUS_TEXTO, data_curta, endereco_texto, reais
from database import repositorio as repo

st.title("Clientes")
mostrar_aviso()

# ---------- Cadastrar ----------
with st.expander("Cadastrar cliente novo", icon=":material/person_add:"):
    with st.form("novo_cliente", clear_on_submit=True):
        nome = st.text_input("Nome")
        telefone = st.text_input("Telefone / WhatsApp")
        email = st.text_input("E-mail (se tiver)")
        endereco, bairro, cidade = campos_endereco("novo_cliente")
        obs = st.text_area("Observações (ex.: quem indicou)")
        salvar = st.form_submit_button("Cadastrar", type="primary", width="stretch",
                                       icon=":material/check:")
    if salvar:
        if not nome.strip() or not telefone.strip():
            st.error("Nome e telefone são obrigatórios.")
        else:
            repo.criar_cliente(nome, telefone, email, obs, endereco, bairro, cidade)
            guardar_aviso(f"{nome.strip()} foi cadastrado(a)!")
            st.rerun()

# ---------- Lista ----------
busca = st.text_input("Procurar pelo nome, telefone, bairro ou cidade", icon=":material/search:")
clientes = repo.listar_clientes(busca)

if not clientes:
    st.info("Nenhum cliente encontrado." if busca else "Ainda não tem nenhum cliente cadastrado.")

for c in clientes:
    with st.expander(f"{c['nome']} — {c['telefone']}", icon=":material/person:"):
        endereco_atual = endereco_texto(c)
        st.markdown(f"**Endereço:** {endereco_atual}" if endereco_atual
                    else "**Endereço:** não cadastrado")
        if c["email"]:
            st.markdown(f"**E-mail:** {c['email']}")
        if c["observacoes"]:
            st.markdown(f"**Observações:** {c['observacoes']}")

        reservas = repo.reservas_do_cliente(c["id"])
        if reservas:
            st.markdown("**Festas:**")
            for r in reservas:
                saldo = r["saldo_devedor"] or 0  # pré-reserva sem valor: sem saldo
                falta = f" · falta {reais(saldo)}" if (
                    saldo > 0 and r["status"] != "cancelada") else ""
                st.markdown(f"- {data_curta(r['data_festa'])} — {r['tipo_festa'] or 'sem dados'} — "
                            f"{STATUS_TEXTO[r['status']]} — {reais(r['valor_total'])}{falta}")
        else:
            st.markdown("_Ainda não fez nenhuma festa._")

        if st.toggle("Alterar dados", key=f"alterar_cliente_{c['id']}"):
            with st.form(f"form_cliente_{c['id']}"):
                novo_nome = st.text_input("Nome", value=c["nome"])
                novo_tel = st.text_input("Telefone / WhatsApp", value=c["telefone"])
                novo_email = st.text_input("E-mail", value=c["email"] or "")
                novo_end, novo_bairro, nova_cidade = campos_endereco(f"cliente_{c['id']}", c)
                nova_obs = st.text_area("Observações", value=c["observacoes"] or "")
                salvar_cli = st.form_submit_button("Salvar alterações", type="primary",
                                                   width="stretch", icon=":material/check:")
            if salvar_cli:
                if not novo_nome.strip() or not novo_tel.strip():
                    st.error("Nome e telefone são obrigatórios.")
                else:
                    repo.atualizar_cliente(c["id"], novo_nome, novo_tel, novo_email, nova_obs,
                                           novo_end, novo_bairro, nova_cidade)
                    guardar_aviso("Dados do cliente salvos!")
                    st.rerun()
