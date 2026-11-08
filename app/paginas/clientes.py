import streamlit as st

from app.componentes import campos_cadastro, erros_do_cadastro, guardar_aviso, mostrar_aviso
from app.formatacao import STATUS_TEXTO, data_curta, endereco_texto, reais
from database import cpf as cpf_util
from database import repositorio as repo

st.title("Clientes")
mostrar_aviso()


def salvar_cliente(acao, *args) -> bool:
    """Chama criar/atualizar e mostra erro de CPF em português. True se salvou."""
    try:
        acao(*args)
        return True
    except repo.CpfInvalidoError:
        st.error("CPF inválido. Confira os números.")
    except repo.CpfDuplicadoError as erro:
        st.error(f"Esse CPF já está cadastrado para **{erro.args[0]}**.")
    return False


# ---------- Cadastrar ----------
with st.expander("Cadastrar cliente novo", icon=":material/person_add:"):
    with st.form("novo_cliente", clear_on_submit=False):
        nome = st.text_input("Nome")
        telefone = st.text_input("Telefone / WhatsApp")
        email = st.text_input("E-mail (se tiver)")
        cpf, endereco, bairro, cidade = campos_cadastro("novo_cliente")
        obs = st.text_area("Observações (ex.: quem indicou)")
        salvar = st.form_submit_button("Cadastrar", type="primary", width="stretch",
                                       icon=":material/check:")
    if salvar:
        erros = [] if (nome.strip() and telefone.strip()) else ["Nome e telefone são obrigatórios."]
        erros += erros_do_cadastro(cpf, endereco, bairro, cidade, obrigatorio=False)
        for erro in erros:
            st.error(erro)
        if not erros and salvar_cliente(repo.criar_cliente, nome, telefone, email, obs,
                                        endereco, bairro, cidade, cpf):
            guardar_aviso(f"{nome.strip()} foi cadastrado(a)!")
            st.rerun()

# ---------- Lista ----------
busca = st.text_input("Procurar pelo nome, telefone, CPF, bairro ou cidade",
                      icon=":material/search:")
clientes = repo.listar_clientes(busca)

if not clientes:
    st.info("Nenhum cliente encontrado." if busca else "Ainda não tem nenhum cliente cadastrado.")

for c in clientes:
    with st.expander(f"{c['nome']} — {c['telefone']}", icon=":material/person:"):
        st.markdown(f"**CPF:** {cpf_util.formatar(c['cpf']) if c['cpf'] else 'não cadastrado'}")
        endereco_atual = endereco_texto(c)
        st.markdown(f"**Endereço:** {endereco_atual or 'não cadastrado'}")
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
                novo_cpf, novo_end, novo_bairro, nova_cidade = campos_cadastro(
                    f"cliente_{c['id']}", c)
                nova_obs = st.text_area("Observações", value=c["observacoes"] or "")
                salvar_cli = st.form_submit_button("Salvar alterações", type="primary",
                                                   width="stretch", icon=":material/check:")
            if salvar_cli:
                erros = ([] if (novo_nome.strip() and novo_tel.strip())
                         else ["Nome e telefone são obrigatórios."])
                erros += erros_do_cadastro(novo_cpf, novo_end, novo_bairro, nova_cidade,
                                           obrigatorio=False)
                for erro in erros:
                    st.error(erro)
                if not erros and salvar_cliente(repo.atualizar_cliente, c["id"], novo_nome,
                                                novo_tel, novo_email, nova_obs, novo_end,
                                                novo_bairro, nova_cidade, novo_cpf):
                    guardar_aviso("Dados do cliente salvos!")
                    st.rerun()
