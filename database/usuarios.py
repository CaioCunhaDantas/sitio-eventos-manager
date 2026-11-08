"""Senhas e login.

A senha passa por PBKDF2 (biblioteca padrão do Python): um cálculo
repetido muitas vezes de propósito, para que adivinhar senhas por
tentativa e erro fique lento. Só o resultado (hash) vai para o banco.
"""

import hashlib
import hmac
import secrets
from pathlib import Path

from database.criar_banco import CAMINHO_BANCO, conectar

ITERACOES = 600_000


def _gerar_hash(senha: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", senha.encode("utf-8"), bytes.fromhex(salt), ITERACOES
    ).hex()


def definir_senha(nome: str, senha: str, caminho_banco: Path = CAMINHO_BANCO) -> None:
    """Cria o usuário ou, se ele já existir, troca a senha."""
    salt = secrets.token_hex(16)
    senha_hash = _gerar_hash(senha, salt)
    with conectar(caminho_banco) as conexao:
        # UPSERT: insere; se o nome já existir, atualiza a senha
        conexao.execute(
            """
            INSERT INTO usuario (nome, senha_hash, salt) VALUES (?, ?, ?)
            ON CONFLICT (nome) DO UPDATE
                SET senha_hash = excluded.senha_hash, salt = excluded.salt
            """,
            (nome.strip(), senha_hash, salt),
        )
    conexao.close()


def existe_usuario(caminho_banco: Path = CAMINHO_BANCO) -> bool:
    with conectar(caminho_banco) as conexao:
        linha = conexao.execute("SELECT 1 FROM usuario LIMIT 1").fetchone()
    conexao.close()
    return linha is not None


def verificar_senha(senha: str, caminho_banco: Path = CAMINHO_BANCO) -> str | None:
    """Devolve o nome do usuário se a senha estiver certa; senão, None."""
    with conectar(caminho_banco) as conexao:
        usuarios = conexao.execute("SELECT nome, senha_hash, salt FROM usuario").fetchall()
    conexao.close()
    for nome, senha_hash, salt in usuarios:
        # compare_digest compara em tempo constante (não "vaza" pelo tempo
        # de resposta quantos caracteres do hash estavam certos)
        if hmac.compare_digest(_gerar_hash(senha, salt), senha_hash):
            return nome
    return None
