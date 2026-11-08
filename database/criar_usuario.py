"""Cadastra a pessoa que vai usar o sistema, ou troca a senha dela.

Uso (na raiz do projeto):
    py -m database.criar_usuario

Segurança:
  * A senha é digitada sem aparecer na tela (getpass) e nunca é gravada
    em arquivo nem no histórico do terminal.
  * O banco guarda apenas o hash (PBKDF2), nunca a senha.
  * Nunca escreva a senha real no código, em comandos ou em commits.
"""

from getpass import getpass

from database.criar_banco import CAMINHO_BANCO, conectar, criar_banco
from database.usuarios import definir_senha

TAMANHO_MINIMO = 8


def nomes_cadastrados() -> list[str]:
    conexao = conectar()
    nomes = [linha["nome"] for linha in conexao.execute("SELECT nome FROM usuario")]
    conexao.close()
    return nomes


def main() -> None:
    criar_banco()  # garante que a tabela existe
    print(f"Banco: {CAMINHO_BANCO}")

    existentes = nomes_cadastrados()
    if existentes:
        print(f"Usuário(s) já cadastrado(s): {', '.join(existentes)}")
        print("Para TROCAR a senha, digite o mesmo nome.")

    nome = input("Nome de quem vai usar o sistema (ex.: Neusa): ").strip()
    if not nome:
        print("Nome vazio. Nada foi alterado.")
        return

    if existentes and nome not in existentes:
        # Toda senha cadastrada abre o sistema: evitar usuário esquecido
        resposta = input(f"'{nome}' é um usuário NOVO (o(s) antigo(s) continua(m) "
                         "entrando com a senha deles). Continuar? (s/n): ")
        if resposta.strip().lower() != "s":
            print("Nada foi alterado.")
            return

    senha = getpass(f"Senha (mínimo {TAMANHO_MINIMO} caracteres, não aparece na tela): ")
    if len(senha) < TAMANHO_MINIMO:
        print(f"A senha precisa ter pelo menos {TAMANHO_MINIMO} caracteres. Nada foi alterado.")
        return
    if getpass("Repita a senha: ") != senha:
        print("As senhas não conferem. Nada foi alterado.")
        return

    definir_senha(nome, senha)
    print(f"Pronto! {nome} já pode entrar no sistema com essa senha.")


if __name__ == "__main__":
    main()
