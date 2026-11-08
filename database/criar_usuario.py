"""Cadastra a pessoa que vai usar o sistema, ou troca a senha dela.

Uso (na raiz do projeto):
    py -m database.criar_usuario

A senha é digitada sem aparecer na tela.
"""

from getpass import getpass

from database.criar_banco import criar_banco
from database.usuarios import definir_senha

TAMANHO_MINIMO = 4


def main() -> None:
    criar_banco()  # garante que a tabela existe
    nome = input("Nome de quem vai usar o sistema (ex.: Neusa): ").strip()
    if not nome:
        print("Nome vazio. Nada foi alterado.")
        return

    senha = getpass("Senha: ")
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
