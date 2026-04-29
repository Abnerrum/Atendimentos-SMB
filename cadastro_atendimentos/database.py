"""
╔══════════════════════════════════════════════════════════════════╗
║   MÓDULO DE BANCO DE DADOS — SQLite                             ║
║   Persistência local para os atendimentos cadastrados            ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

# Caminho do banco de dados (persistente no disco)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atendimentos.db")

# ─────────────────────────────────────────────────────────────────
# GERENCIADOR DE CONEXÃO
# ─────────────────────────────────────────────────────────────────

@contextmanager
def get_connection():
    """Context manager para conexões SQLite thread-safe."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO
# ─────────────────────────────────────────────────────────────────

def init_database():
    """Cria a tabela de atendimentos se não existir."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS atendimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                atendente TEXT NOT NULL,
                data_atendimento TEXT NOT NULL,
                numero_pedido TEXT NOT NULL UNIQUE,
                nome_cliente TEXT NOT NULL,
                valor_pedido REAL NOT NULL,
                email_cliente TEXT,
                arquivo_comprovante TEXT,
                data_hora_registro TEXT NOT NULL
            )
        """)

# ─────────────────────────────────────────────────────────────────
# OPERAÇÕES CRUD
# ─────────────────────────────────────────────────────────────────

def salvar_atendimento(dados: dict) -> bool:
    """Insere um novo atendimento no banco de dados."""
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO atendimentos 
                (atendente, data_atendimento, numero_pedido, nome_cliente, 
                 valor_pedido, email_cliente, arquivo_comprovante, data_hora_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dados["atendente"],
                dados["data_atendimento"],
                dados["numero_pedido"],
                dados["nome_cliente"],
                dados["valor_pedido"],
                dados.get("email_cliente", ""),
                dados.get("arquivo_comprovante", ""),
                dados["data_hora_registro"]
            ))
        return True
    except sqlite3.IntegrityError:
        raise ValueError(f"Já existe um atendimento com o número de pedido '{dados['numero_pedido']}'.")
    except Exception as e:
        raise RuntimeError(f"Erro ao salvar atendimento: {e}")

def carregar_atendimentos() -> list:
    """Retorna todos os atendimentos cadastrados, ordenados por data de registro (mais recentes primeiro)."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT id, atendente, data_atendimento, numero_pedido, nome_cliente,
                   valor_pedido, email_cliente, arquivo_comprovante, data_hora_registro
            FROM atendimentos
            ORDER BY data_hora_registro DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def buscar_atendimento_por_id(atendimento_id: int) -> dict | None:
    """Busca um atendimento específico pelo ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def contar_atendimentos() -> int:
    """Retorna o total de atendimentos cadastrados."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) as total FROM atendimentos")
        return cursor.fetchone()["total"]

def obter_valor_total() -> float:
    """Retorna a soma de todos os valores de pedido."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT COALESCE(SUM(valor_pedido), 0) as total FROM atendimentos")
        return cursor.fetchone()["total"]

def atualizar_atendimento(atendimento_id: int, dados: dict) -> bool:
    """Atualiza os campos de um atendimento existente pelo ID."""
    try:
        with get_connection() as conn:
            conn.execute("""
                UPDATE atendimentos
                SET atendente = ?,
                    data_atendimento = ?,
                    numero_pedido = ?,
                    nome_cliente = ?,
                    valor_pedido = ?,
                    email_cliente = ?
                WHERE id = ?
            """, (
                dados["atendente"],
                dados["data_atendimento"],
                dados["numero_pedido"],
                dados["nome_cliente"],
                dados["valor_pedido"],
                dados.get("email_cliente", ""),
                atendimento_id,
            ))
        return True
    except sqlite3.IntegrityError:
        raise ValueError(f"Já existe outro atendimento com o número de pedido '{dados['numero_pedido']}'.")
    except Exception as e:
        raise RuntimeError(f"Erro ao atualizar atendimento: {e}")

def limpar_todos_dados() -> bool:
    """Remove todos os atendimentos do banco de dados (uso administrativo)."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM atendimentos")
        return True
    except Exception as e:
        raise RuntimeError(f"Erro ao limpar dados: {e}")

# ─────────────────────────────────────────────────────────────────
# ESTATÍSTICAS PARA DASHBOARD
# ─────────────────────────────────────────────────────────────────

def estatisticas_por_atendente() -> list:
    """Retorna estatísticas agregadas por atendente."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT 
                atendente,
                COUNT(*) as total_atendimentos,
                SUM(valor_pedido) as valor_total,
                AVG(valor_pedido) as valor_medio
            FROM atendimentos
            GROUP BY atendente
            ORDER BY total_atendimentos DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def estatisticas_por_periodo() -> list:
    """Retorna estatísticas agregadas por data de atendimento."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT 
                data_atendimento,
                COUNT(*) as total_atendimentos,
                SUM(valor_pedido) as valor_total
            FROM atendimentos
            GROUP BY data_atendimento
            ORDER BY data_atendimento ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

# Inicializa o banco na importação do módulo
init_database()