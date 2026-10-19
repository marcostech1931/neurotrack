#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroTrack Desktop - Aplicativo Python Nativo (Tkinter + SQLite3)
100% Baseado em Botões Clicáveis + Janela Separada para Lista de Pacientes
Acesso por login: usuário = nome completo (ou login personalizado) | senha = CPF (ou senha personalizada)
"""

import hashlib
import hmac
import os
import re
import secrets
import sys
import sqlite3
import tempfile
import unicodedata
import webbrowser
from datetime import datetime, date
from html import escape as esc
import tkinter as tk
from tkinter import ttk, messagebox

# Garante que o banco fique na mesma pasta do executável (.exe) ou script (.py)
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(APP_DIR, "neurotrack_dados.db")

# ==============================================================================
# OPÇÕES E PERGUNTAS DA ANAMNESE (Extraídas do PDF)
# ==============================================================================
OPCOES_ESCALA = ["SIM", "NÃO", "ÀS VEZES", "SEMPRE", "ESTÁVEL"]
OPCOES_NIVEL = ["ALTO", "BAIXO", "FLUTUANTE"]
OPCOES_COMP = ["EUFORIA", "APATIA", "CURIOSIDADE", "DESORGANIZADO"]

METAS_NEUROTRACK = [
    "Comunicação: Fazer Pedidos (Mand)",
    "Atenção: Resposta ao Nome",
    "Social: Esperar a Vez / Turnos",
    "Comportamento: Transição sem Crise"
]

SUPORTES_NEUROTRACK = [
    "Independente",
    "Dica Verbal",
    "Dica Gestual/Visual",
    "Ajuda Física"
]

REGULACAO_NEUROTRACK = [
    "Sem Intercorrência",
    "Leve (Autorregulou)",
    "Moderada (Pausa)",
    "Severa (Interrupção)"
]

SECOES_ANAMNESE = [
    ("1. Sistema Vestibular", [
        ("vest_1", "Qual foi o nível de alerta da criança durante atividades de movimento?", "nivel"),
        ("vest_2", "A criança demonstrou conforto durante atividades de movimento?", "escala"),
        ("vest_3", "A criança evitou ou demonstrou medo/insegurança nas atividades com movimento?", "escala"),
        ("vest_4", "Como foi o controle postural da criança durante o movimento?", "escala"),
        ("vest_5", "Realizou ajuste de postura conforme a demanda das atividades?", "escala"),
        ("vest_6", "A criança sustentou o pescoço e o tronco durante as atividades em movimento?", "escala"),
        ("vest_7", "A criança realizou movimentos contra a gravidade?", "escala"),
        ("vest_8", "Realizou co-contração de tronco superior e pescoço?", "escala"),
        ("vest_9", "Como foi o desempenho em atividades que exigiam coordenação motora bilateral?", "escala"),
        ("vest_10", "Apresentou estabilidade das funções visuais em atividades estáticas e dinâmicas?", "escala"),
    ]),
    ("2. Sistema Tátil", [
        ("tat_1", "A criança apresentou aversão por alguma textura?", "escala"),
        ("tat_2", "A criança apresentou aversão ao toque?", "escala"),
        ("tat_3", "Apresentou mudança de comportamento ao manusear determinadas texturas?", "escala"),
        ("tat_4", "A criança limpou, apertou, esfregou ou coçou partes do corpo quando tocada?", "escala"),
        ("tat_5", "Como a criança reagiu a toques suaves e com pressão?", "texto"),
        ("tat_6", "Apresentou expressões faciais negativas ao ser tocada ou explorar texturas?", "escala"),
        ("tat_7", "Procurou estímulos táteis em níveis mais altos que outras crianças de sua faixa etária?", "escala"),
        ("tat_8", "Apresentou dificuldade em registrar e/ou localizar o toque em parte do corpo?", "escala"),
        ("tat_9", "Conseguiu discriminar objetos sem a ajuda da visão (Estereognosia)?", "escala"),
    ]),
    ("3. Sistema Proprioceptivo", [
        ("pro_1", "A criança conseguiu localizar as partes do corpo no espaço?", "escala"),
        ("pro_2", "A criança apresentou bom controle postural?", "escala"),
        ("pro_3", "A criança apresentou baixo tônus muscular?", "escala"),
        ("pro_4", "A criança apresentou hipermobilidade articular?", "escala"),
        ("pro_5", "A criança assumiu posições não comuns?", "escala"),
        ("pro_6", "A criança andou na ponta dos pés?", "escala"),
        ("pro_7", "Como foi o alinhamento e a estabilidade articular durante as atividades?", "texto"),
        ("pro_8", "Como realizou descarga e transferência do peso durante as atividades?", "escala"),
        ("pro_9", "Como foi o desempenho em atividades de empurrar, jogar, agarrar, se pendurar?", "escala"),
        ("pro_10", "Conseguiu imitar posturas?", "escala"),
        ("pro_11", "Apresentou boa fluidez dos movimentos?", "escala"),
        ("pro_12", "A criança caiu ou tropeçou com frequência?", "escala"),
        ("pro_13", "Apresentou movimentação desorganizada (esbarra, cai, sem noção do espaço)?", "escala"),
        ("pro_14", "Apoiou o peso do seu corpo em locais do ambiente ou em pessoas?", "escala"),
    ]),
    ("4. Sistema Visual", [
        ("vis_1", "A criança buscou ou apresentou preferências por estímulos visuais?", "escala"),
        ("vis_2", "A criança percebeu as informações visuais do ambiente?", "escala"),
        ("vis_3", "A criança apresentou movimentação ocular regular?", "escala"),
        ("vis_4", "Apresentou capacidade de manter a atenção em determinado foco visual?", "escala"),
        ("vis_5", "A criança acompanhou com os olhos objetos em movimento?", "escala"),
        ("vis_6", "Apresentou movimentação desorganizada (esbarra, cai, sem noção do espaço)?", "escala"),
        ("vis_7", "A criança apresentou boa fluidez nos movimentos oculares?", "escala"),
        ("vis_8", "Associou com mais frequência o movimento da cabeça/corpo com o movimento ocular?", "escala"),
        ("vis_9", "Conseguiu fazer rastreamento visual no sentido vertical e horizontal?", "escala"),
        ("vis_10", "Precisou aproximar o objeto dos olhos mais que o esperado para sua faixa etária?", "escala"),
        ("vis_11", "A criança conseguiu acertar um objeto em determinado alvo?", "escala"),
        ("vis_12", "Apresentou coordenação óculo-manual satisfatória para a idade?", "escala"),
        ("vis_13", "Localizou objetos, figuras ou imagens no ambiente terapêutico quando solicitado?", "escala"),
        ("vis_14", "Localizou letras, figuras ou desenhos no papel quando solicitado?", "escala"),
        ("vis_15", "A criança fez cópia de traçados, figuras, letras e/ou texto?", "escala"),
        ("vis_16", "Conseguiu reproduzir um modelo criando com peças e/ou outros objetos 3D?", "escala"),
    ]),
    ("5. Alerta", [
        ("ale_1", "Qual foi o nível de alerta da criança durante a exploração do espaço terapêutico?", "nivel"),
        ("ale_2", "Manteve o mesmo nível de alerta ou observou-se variações com estímulos?", "escala"),
    ]),
    ("6. Reatividade (Modulação Sensorial)", [
        ("rea_1", "A criança explorou o ambiente terapêutico por iniciativa própria?", "escala"),
        ("rea_2", "Como foi o comportamento da criança ao explorar o espaço terapêutico?", "comp"),
        ("rea_3", "A criança se colocou em risco ao explorar o espaço (tem noção de perigo)?", "escala"),
        ("rea_4", "Interagiu com o terapeuta e/ou outras pessoas no espaço terapêutico?", "escala"),
        ("rea_5", "A criança seguiu comandos e/ou instruções do terapeuta?", "escala"),
        ("rea_6", "Pareceu hiper-reativa a um ou mais estímulos sensoriais presentes?", "escala"),
        ("rea_7", "Pareceu hiporreativa a um ou mais estímulos sensoriais presentes?", "escala"),
        ("rea_8", "Como a criança reagiu aos estímulos visuais (luz, cores, objetos em movimento)?", "escala"),
        ("rea_9", "Como a criança reagiu aos estímulos auditivos (sons, músicas, barulho, vozes)?", "escala"),
        ("rea_10", "Como a criança reagiu aos estímulos olfativos (não gostar ou preferências)?", "escala"),
        ("rea_11", "Como reagiu a estímulos gustativos (aversões ou preferências a sabores/texturas)?", "escala"),
        ("rea_12", "Como reagiu aos estímulos interoceptivos (temperatura, dor, sensações corporais)?", "texto"),
        ("rea_13", "A criança buscou por quantidades excessivas de estímulos sensoriais?", "escala"),
        ("rea_14", "Pareceu ansiosa ou em sobrecarga quando exposta a muitos estímulos sensoriais?", "escala"),
    ]),
    ("7. Percepção Sensorial (Discriminação)", [
        ("per_1", "Teve dificuldade em regular o comportamento e a resposta às sensações?", "escala"),
        ("per_2", "A criança registrou os estímulos sensoriais?", "escala"),
        ("per_3", "Ignorou um tipo particular de estímulo sensorial ou informação importante?", "escala"),
        ("per_4", "A criança não registrou algum estímulo sensorial específico?", "escala"),
        ("per_5", "A criança percebeu informações provenientes das diferentes sensações?", "escala"),
        ("per_6", "Discriminou as diferenças e variações na qualidade das sensações?", "escala"),
        ("per_7", "Demorou para reagir ou entender ao ser exposta aos estímulos sensoriais?", "escala"),
        ("per_8", "Conseguiu discriminar detalhes de objetos (duro/mole, tamanho, distância, velocidade)?", "escala"),
        ("per_9", "Quais as principais informações sensoriais procurou para conhecer e agir no espaço?", "texto"),
    ]),
    ("8. Práxis (Ideação, Planejamento e Execução)", [
        ("pra_1", "A criança conseguiu executar as atividades propostas?", "escala"),
        ("pra_2", "A criança apresentou iniciativa para explorar o ambiente terapêutico?", "escala"),
        ("pra_3", "Teve dificuldade em ter novas ideias para brincar ou se envolver nas atividades?", "escala"),
        ("pra_4", "Irritou-se facilmente ou precisou de ajuda constante para realizar as atividades?", "escala"),
        ("pra_5", "Precisou de ajuda para resolver problemas de sua faixa etária?", "escala"),
        ("pra_6", "A criança teve dificuldade com a execução motora das atividades?", "escala"),
        ("pra_7", "A criança conseguiu coordenar os movimentos?", "escala"),
        ("pra_8", "A criança conseguiu realizar movimentos motores complexos?", "escala"),
        ("pra_9", "Conseguiu descobrir ou se lembrar de como fazer motoramente algo?", "escala"),
        ("pra_10", "Teve dificuldade em sequenciar ou realizar etapas de uma atividade?", "escala"),
        ("pra_11", "Insistiu nos mesmos erros repetidamente durante suas atividades?", "escala"),
        ("pra_12", "Conseguiu imitar expressões faciais quando oferecido modelo pelo terapeuta?", "escala"),
        ("pra_13", "Conseguiu imitar posturas corporais quando oferecido modelo pelo terapeuta?", "escala"),
        ("pra_14", "Conseguiu imitar informações orais quando oferecido modelo pelo terapeuta?", "escala"),
        ("pra_15", "Conseguiu seguir instruções do terapeuta para realizar as etapas da atividade?", "escala"),
        ("pra_16", "Propôs novas atividades e/ou ideias com soluções para as atividades propostas?", "escala"),
    ]),
    ("9. Comportamento da Criança", [
        ("com_1", "Quais as principais informações sensoriais a criança procurou no espaço terapêutico?", "texto"),
        ("com_2", "Descreva a preferência da criança por brinquedos e brincadeiras do espaço:", "texto"),
    ]),
    ("10. Outras Observações", [
        ("out_1", "Descreva outras informações relevantes observadas durante a Observação Clínica:", "texto"),
    ]),
]


# ==============================================================================
# COMPONENTE DE BOTÕES DE SELEÇÃO (Substitui todos os <select> / Combobox)
# ==============================================================================
class GrupoBotoes(tk.Frame):
    """Grupo de botões onde o profissional clica diretamente na opção desejada."""
    def __init__(self, parent, opcoes, cor_ativa="#0284c7", pad_x=10, pad_y=5, permite_desmarcar=True, valor_inicial=""):
        super().__init__(parent, bg="white")
        self.opcoes = opcoes
        self.cor_ativa = cor_ativa
        self.permite_desmarcar = permite_desmarcar
        self.valor = valor_inicial
        self.botoes = {}

        for opc in opcoes:
            btn = tk.Button(
                self, text=opc, font=("Segoe UI", 9, "bold"),
                padx=pad_x, pady=pad_y, cursor="hand2", relief="solid", bd=1,
                command=lambda o=opc: self.selecionar(o)
            )
            btn.pack(side="left", padx=3, pady=2)
            self.botoes[opc] = btn

        self._atualizar_visual()

    def selecionar(self, opc):
        if self.permite_desmarcar and self.valor == opc:
            self.valor = ""
        else:
            self.valor = opc
        self._atualizar_visual()

    def _atualizar_visual(self):
        for opc, btn in self.botoes.items():
            if opc == self.valor:
                btn.config(bg=self.cor_ativa, fg="white", activebackground=self.cor_ativa, activeforeground="white")
            else:
                btn.config(bg="#f8fafc", fg="#334155", activebackground="#e2e8f0", activeforeground="#0f172a")

    def get(self):
        return self.valor

    def set(self, novo_valor):
        self.valor = novo_valor
        self._atualizar_visual()


# ==============================================================================
# BANCO DE DADOS INTEGRADO (SQLite3)
# ==============================================================================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS pacientes_anamnese (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL,
            data_nascimento TEXT,
            idade TEXT,
            data_observacao TEXT NOT NULL,
            terapeuta TEXT NOT NULL,
            registro_profissional TEXT,
            hipotese_diagnostica TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS respostas_anamnese (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            pergunta_id TEXT NOT NULL,
            resposta TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes_anamnese(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS sessoes_neurotrack (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            data_hora TEXT NOT NULL,
            meta TEXT NOT NULL,
            acertos_indep INTEGER NOT NULL DEFAULT 0,
            tentativas_ajuda INTEGER NOT NULL DEFAULT 0,
            taxa_independencia INTEGER NOT NULL DEFAULT 0,
            nivel_suporte TEXT NOT NULL,
            regulacao_sensorial TEXT NOT NULL,
            tempo_atencao INTEGER NOT NULL DEFAULT 10,
            observacoes TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes_anamnese(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS profissionais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            nome_normalizado TEXT NOT NULL UNIQUE,
            login_usuario TEXT,
            cpf_4 TEXT,
            cpf_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # Migração segura caso o banco já exista de versões anteriores
        cols = [r[1] for r in conn.execute("PRAGMA table_info(profissionais)").fetchall()]
        if "login_usuario" not in cols:
            conn.execute("ALTER TABLE profissionais ADD COLUMN login_usuario TEXT")
        if "cpf_4" not in cols:
            conn.execute("ALTER TABLE profissionais ADD COLUMN cpf_4 TEXT")
        conn.execute("UPDATE profissionais SET login_usuario = nome WHERE login_usuario IS NULL OR login_usuario = ''")


def formatar_cpf_4_digitos(cpf_str):
    cpf_num = re.sub(r"\D", "", str(cpf_str or ""))
    if len(cpf_num) >= 4:
        return f"{cpf_num[:3]}.{cpf_num[3:4]}**.***-**"
    return cpf_num or "Não informado"


def abreviar_nome_profissional(nome_completo):
    """Retorna apenas o primeiro nome e a inicial do sobrenome (ex.: 'Maria S.')."""
    partes = [p for p in str(nome_completo or "").strip().split() if p]
    if not partes:
        return "—"
    if len(partes) == 1:
        return partes[0]
    preposicoes = {"de", "da", "do", "das", "dos", "e"}
    sobrenomes = [p for p in partes[1:] if p.lower() not in preposicoes]
    sobrenome = sobrenomes[0] if sobrenomes else partes[1]
    return f"{partes[0]} {sobrenome[0].upper()}."


# ==============================================================================
# FUNÇÕES AUXILIARES: CPF, LOGIN, DATA DE NASCIMENTO E IDADE
# ==============================================================================
def somente_digitos(texto):
    return re.sub(r"\D", "", str(texto or ""))


def normalizar_nome(nome):
    """Maiúsculas, sem acentos e sem espaços repetidos (o login não diferencia maiúsc./acentos)."""
    s = unicodedata.normalize("NFKD", str(nome or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.upper().split())


def cpf_valido(cpf):
    cpf = somente_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        if ((soma * 10) % 11) % 10 != int(cpf[n]):
            return False
    return True


def _hash_senha(senha_str, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", str(senha_str).encode("utf-8"), bytes.fromhex(salt_hex), 200_000).hex()


def _verificar_senha_registro(senha_digitada, cpf_hash, salt_hex):
    """Verifica a senha digitada tanto de forma direta (senha personalizada) quanto apenas dígitos (CPF)."""
    s_raw = str(senha_digitada or "").strip()
    if not s_raw:
        return False
    if hmac.compare_digest(cpf_hash, _hash_senha(s_raw, salt_hex)):
        return True
    s_dig = somente_digitos(s_raw)
    if s_dig and hmac.compare_digest(cpf_hash, _hash_senha(s_dig, salt_hex)):
        return True
    return False


def cadastrar_profissional(nome, cpf):
    """Grava o profissional (o CPF fica guardado só como hash e os 4 primeiros dígitos para listagem)."""
    nome = " ".join(str(nome).split())
    cpf_dig = somente_digitos(cpf)
    cpf_4 = cpf_dig[:4]
    salt = secrets.token_hex(16)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """INSERT INTO profissionais
                   (nome, nome_normalizado, login_usuario, cpf_4, cpf_hash, salt)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (nome, normalizar_nome(nome), nome, cpf_4, _hash_senha(cpf_dig, salt), salt)
            )
        return True
    except sqlite3.IntegrityError:
        return False


def autenticar_profissional(login_informado, senha_informada):
    """Autentica pelo login personalizado ou pelo nome completo, usando CPF ou senha personalizada."""
    login_norm = normalizar_nome(login_informado)
    if not login_norm or not str(senha_informada or "").strip():
        return None
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, nome, nome_normalizado, login_usuario, cpf_hash, salt FROM profissionais"
        ).fetchall()
    for _id, nome, nome_norm, login_usr, cpf_hash, salt in rows:
        login_usr_norm = normalizar_nome(login_usr or nome)
        if login_norm in (login_usr_norm, nome_norm):
            if _verificar_senha_registro(senha_informada, cpf_hash, salt):
                return nome
    return None


def listar_profissionais_resumo():
    """Retorna lista de profissionais cadastrados para a janela de gerenciamento."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT id, nome, login_usuario, cpf_4 FROM profissionais ORDER BY id ASC"
        ).fetchall()


def excluir_profissional_autenticado(prof_id, senha_atual):
    """Valida a senha/CPF atual do profissional antes de excluir o cadastro. Retorna (sucesso, mensagem)."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT cpf_hash, salt FROM profissionais WHERE id = ?",
            (prof_id,)
        ).fetchone()
        if not row:
            return False, "Cadastro não encontrado."
        cpf_hash, salt = row
        if not _verificar_senha_registro(senha_atual, cpf_hash, salt):
            return False, "A senha (ou CPF) atual informada está incorreta."
        conn.execute("DELETE FROM profissionais WHERE id = ?", (prof_id,))
    return True, "Cadastro excluído com sucesso!"


def atualizar_credenciais_profissional(prof_id, senha_atual, novo_login, nova_senha=""):
    """
    Valida a senha/CPF atual do profissional e atualiza o login (nome_normalizado / login_usuario)
    e, opcionalmente, a senha de acesso. Mantém o nome completo verdadeiro em 'nome' para relatórios.
    Retorna (sucesso: bool, mensagem: str).
    """
    novo_login_limpo = " ".join(str(novo_login or "").split())
    novo_login_norm = normalizar_nome(novo_login_limpo)
    if not novo_login_limpo:
        return False, "O campo de novo login não pode ficar vazio."

    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT nome, cpf_hash, salt, cpf_4 FROM profissionais WHERE id = ?",
            (prof_id,)
        ).fetchone()
        if not row:
            return False, "Cadastro não encontrado."

        nome_atual, cpf_hash, salt, cpf_4_atual = row
        if not _verificar_senha_registro(senha_atual, cpf_hash, salt):
            return False, "A senha (ou CPF) atual informada está incorreta."

        # Verifica se outro profissional já usa esse mesmo login/nome
        outros = conn.execute(
            "SELECT id, nome, login_usuario FROM profissionais WHERE id != ?",
            (prof_id,)
        ).fetchall()
        for oid, onome, ologin in outros:
            if novo_login_norm in (normalizar_nome(onome), normalizar_nome(ologin or onome)):
                return False, "Este login já está em uso por outro profissional."

        # Se ainda não tinha os 4 primeiros dígitos salvos e a senha atual era um CPF, aproveita para preencher
        novo_cpf_4 = cpf_4_atual
        dig_atual = somente_digitos(senha_atual)
        if (not novo_cpf_4) and len(dig_atual) >= 4:
            novo_cpf_4 = dig_atual[:4]

        nova_senha_str = str(nova_senha or "").strip()
        if nova_senha_str:
            novo_salt = secrets.token_hex(16)
            novo_hash = _hash_senha(nova_senha_str, novo_salt)
        else:
            novo_salt = salt
            novo_hash = cpf_hash

        try:
            conn.execute(
                """UPDATE profissionais
                   SET nome_normalizado = ?, login_usuario = ?, cpf_hash = ?, salt = ?, cpf_4 = ?
                   WHERE id = ?""",
                (novo_login_norm, novo_login_limpo, novo_hash, novo_salt, novo_cpf_4, prof_id)
            )
        except sqlite3.IntegrityError:
            return False, "Este login já está em uso por outro profissional."

    return True, "Credenciais de acesso atualizadas com sucesso!"


def calcular_idade(data_str, hoje=None):
    """Recebe 'DD/MM/AAAA' e devolve a idade por extenso ('5 anos e 3 meses'). Vazio se inválida."""
    try:
        nasc = datetime.strptime(str(data_str).strip(), "%d/%m/%Y").date()
    except ValueError:
        return ""
    hoje = hoje or date.today()
    if nasc > hoje or nasc.year < 1900:
        return ""
    total_meses = (hoje.year - nasc.year) * 12 + (hoje.month - nasc.month) - (1 if hoje.day < nasc.day else 0)
    anos, meses = divmod(total_meses, 12)
    partes = []
    if anos:
        partes.append(f"{anos} ano" + ("s" if anos != 1 else ""))
    if meses:
        partes.append(f"{meses} " + ("mês" if meses == 1 else "meses"))
    return " e ".join(partes) if partes else "Menos de 1 mês"


class CampoData(ttk.Entry):
    """Campo de data que já aparece como __/__/____ e coloca as barras sozinho enquanto se digita."""
    def __init__(self, parent, ao_alterar=None, **kw):
        super().__init__(parent, **kw)
        self.digitos = ""
        self.ao_alterar = ao_alterar
        self.bind("<KeyPress>", self._tecla)
        self.bind("<<Paste>>", self._colar)
        self.bind("<FocusIn>", lambda e: self.after_idle(self._cursor_fim))
        self.bind("<ButtonRelease-1>", lambda e: self.after_idle(self._cursor_fim))
        self._render()

    def _render(self):
        d = self.digitos.ljust(8, "_")
        self.delete(0, tk.END)
        self.insert(0, f"{d[:2]}/{d[2:4]}/{d[4:]}")
        self._cursor_fim()

    def _cursor_fim(self):
        n = len(self.digitos)
        self.icursor(n + (1 if n > 2 else 0) + (1 if n > 4 else 0))

    def _mudou(self):
        self._render()
        if self.ao_alterar:
            self.ao_alterar(self.valor())

    def _tecla(self, event):
        if event.keysym == "BackSpace":
            self.digitos = self.digitos[:-1]
            self._mudou()
            return "break"
        if event.keysym == "Delete":
            self.digitos = ""
            self._mudou()
            return "break"
        if event.char and event.char.isdigit():
            if len(self.digitos) < 8:
                self.digitos += event.char
                self._mudou()
            return "break"
        if event.char and event.char.isprintable():
            return "break"          # bloqueia letras, espaço e símbolos
        return None                  # Tab, setas, Ctrl+C etc. continuam normais

    def _colar(self, event):
        try:
            self.digitos = somente_digitos(self.clipboard_get())[:8]
        except tk.TclError:
            pass
        self._mudou()
        return "break"

    def tem_digitos(self):
        return bool(self.digitos)

    def valor(self):
        """'DD/MM/AAAA' quando completa; caso contrário, texto vazio."""
        if len(self.digitos) == 8:
            d = self.digitos
            return f"{d[:2]}/{d[2:4]}/{d[4:]}"
        return ""

    def limpar(self):
        self.digitos = ""
        self._mudou()

    def definir(self, texto):
        self.digitos = somente_digitos(texto)[:8]
        self._mudou()


class DialogoCadastroProfissional(tk.Toplevel):
    """Cadastro de um novo profissional (nome completo + CPF)."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Cadastrar Profissional")
        self.configure(bg="white", padx=24, pady=18)
        self.resizable(False, False)
        self.transient(parent)
        self.nome_cadastrado = None

        tk.Label(self, text="Nome completo do profissional:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_nome = ttk.Entry(self, width=42, font=("Segoe UI", 10))
        self.ent_nome.pack(pady=(2, 10))

        tk.Label(self, text="CPF (será a senha de acesso inicial):", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_cpf = ttk.Entry(self, width=42, font=("Segoe UI", 10), show="•")
        self.ent_cpf.pack(pady=(2, 10))

        tk.Label(self, text="Confirme o CPF:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_cpf2 = ttk.Entry(self, width=42, font=("Segoe UI", 10), show="•")
        self.ent_cpf2.pack(pady=(2, 14))

        tk.Button(
            self, text="CADASTRAR", bg="#0d9488", fg="white", activebackground="#0f766e", activeforeground="white",
            font=("Segoe UI", 10, "bold"), pady=8, cursor="hand2", relief="flat", command=self.salvar
        ).pack(fill="x")

        self.bind("<Return>", lambda e: self.salvar())
        self.ent_nome.focus_set()
        self.grab_set()

    def salvar(self):
        nome = " ".join(self.ent_nome.get().split())
        if len(nome.split()) < 2:
            messagebox.showwarning("Nome incompleto", "Digite o nome completo do profissional.", parent=self)
            return
        if not cpf_valido(self.ent_cpf.get()):
            messagebox.showwarning("CPF inválido", "Informe um CPF válido (11 dígitos).", parent=self)
            return
        if somente_digitos(self.ent_cpf.get()) != somente_digitos(self.ent_cpf2.get()):
            messagebox.showwarning("CPF diferente", "A confirmação do CPF não confere.", parent=self)
            return
        if not cadastrar_profissional(nome, self.ent_cpf.get()):
            messagebox.showwarning("Já cadastrado", "Já existe um profissional com esse nome/login.", parent=self)
            return
        self.nome_cadastrado = nome
        messagebox.showinfo("Cadastro concluído", f"Profissional '{nome}' cadastrado.\n\nEntre com o nome completo e o CPF.", parent=self)
        self.destroy()


class DialogoEditarCredenciais(tk.Toplevel):
    """Permite ao profissional alterar seu login e sua senha (caso não queira usar Nome e CPF)."""
    def __init__(self, parent, prof_id, nome_abrev, login_atual):
        super().__init__(parent)
        self.prof_id = prof_id
        self.atualizado = False
        self.novo_login = None

        self.title(f"Editar Login e Senha — {nome_abrev}")
        self.configure(bg="white", padx=24, pady=18)
        self.resizable(False, False)
        self.transient(parent)

        tk.Label(
            self, text=f"Profissional: {nome_abrev}",
            bg="white", fg="#0369a1", font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(self, text="Senha / CPF atual (obrigatório para confirmar):", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_atual = ttk.Entry(self, width=44, font=("Segoe UI", 10), show="•")
        self.ent_atual.pack(pady=(2, 10))

        tk.Label(self, text="Novo Login de Acesso (pode ser apelido, usuário ou nome):", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_login = ttk.Entry(self, width=44, font=("Segoe UI", 10))
        self.ent_login.insert(0, login_atual)
        self.ent_login.pack(pady=(2, 10))

        tk.Label(self, text="Nova Senha (deixe em branco para manter a senha atual):", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_nova = ttk.Entry(self, width=44, font=("Segoe UI", 10), show="•")
        self.ent_nova.pack(pady=(2, 10))

        tk.Label(self, text="Confirmar Nova Senha:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_nova2 = ttk.Entry(self, width=44, font=("Segoe UI", 10), show="•")
        self.ent_nova2.pack(pady=(2, 6))

        self.var_mostrar = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self, text="Mostrar senhas digitadas", variable=self.var_mostrar,
            bg="white", activebackground="white", font=("Segoe UI", 9),
            command=self._alternar_mostrar
        ).pack(anchor="w", pady=(0, 12))

        tk.Button(
            self, text="SALVAR ALTERAÇÕES", bg="#0284c7", fg="white",
            activebackground="#0369a1", activeforeground="white",
            font=("Segoe UI", 10, "bold"), pady=8, cursor="hand2", relief="flat",
            command=self.salvar
        ).pack(fill="x")

        self.bind("<Return>", lambda e: self.salvar())
        self.ent_atual.focus_set()
        self.grab_set()

    def _alternar_mostrar(self):
        ch = "" if self.var_mostrar.get() else "•"
        self.ent_atual.config(show=ch)
        self.ent_nova.config(show=ch)
        self.ent_nova2.config(show=ch)

    def salvar(self):
        senha_atual = self.ent_atual.get().strip()
        novo_login = self.ent_login.get().strip()
        nova_senha = self.ent_nova.get().strip()
        nova_senha2 = self.ent_nova2.get().strip()

        if not senha_atual:
            messagebox.showwarning("Confirmação", "Informe a senha ou CPF atual para autorizar a alteração.", parent=self)
            return
        if not novo_login:
            messagebox.showwarning("Login inválido", "Informe o novo login desejado.", parent=self)
            return
        if nova_senha or nova_senha2:
            if len(nova_senha) < 4:
                messagebox.showwarning("Nova senha", "A nova senha deve ter pelo menos 4 caracteres.", parent=self)
                return
            if nova_senha != nova_senha2:
                messagebox.showwarning("Nova senha", "A confirmação da nova senha não confere.", parent=self)
                return

        ok, msg = atualizar_credenciais_profissional(self.prof_id, senha_atual, novo_login, nova_senha)
        if not ok:
            messagebox.showerror("Não foi possível atualizar", msg, parent=self)
            return

        self.atualizado = True
        self.novo_login = " ".join(novo_login.split())
        messagebox.showinfo("Sucesso", msg, parent=self)
        self.destroy()


class DialogoExcluirProfissional(tk.Toplevel):
    """Solicita a senha/CPF atual do profissional antes de confirmar a exclusão do cadastro."""
    def __init__(self, parent, prof_id, nome_abrev):
        super().__init__(parent)
        self.prof_id = prof_id
        self.nome_abrev = nome_abrev
        self.excluido = False

        self.title(f"Excluir Cadastro — {nome_abrev}")
        self.configure(bg="white", padx=24, pady=18)
        self.resizable(False, False)
        self.transient(parent)

        tk.Label(
            self, text=f"Excluir acesso de: {nome_abrev}",
            bg="white", fg="#dc2626", font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            self,
            text="Para confirmar a exclusão, digite a senha (ou CPF) atual deste profissional:",
            bg="white", fg="#334155", font=("Segoe UI", 9), wraplength=340, justify="left"
        ).pack(anchor="w", pady=(0, 8))

        self.ent_senha = ttk.Entry(self, width=42, font=("Segoe UI", 10), show="•")
        self.ent_senha.pack(pady=(0, 6))

        self.var_mostrar = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self, text="Mostrar senha", variable=self.var_mostrar,
            bg="white", activebackground="white", font=("Segoe UI", 9),
            command=lambda: self.ent_senha.config(show="" if self.var_mostrar.get() else "•")
        ).pack(anchor="w", pady=(0, 12))

        botoes = tk.Frame(self, bg="white")
        botoes.pack(fill="x")

        tk.Button(
            botoes, text="🗑 CONFIRMAR EXCLUSÃO", bg="#dc2626", fg="white",
            activebackground="#b91c1c", activeforeground="white",
            font=("Segoe UI", 9, "bold"), padx=14, pady=8, cursor="hand2", relief="flat",
            command=self.confirmar
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(
            botoes, text="CANCELAR", bg="#e2e8f0", fg="#334155",
            font=("Segoe UI", 9, "bold"), padx=14, pady=8, cursor="hand2", relief="flat",
            command=self.destroy
        ).pack(side="right")

        self.bind("<Return>", lambda e: self.confirmar())
        self.ent_senha.focus_set()
        self.grab_set()

    def confirmar(self):
        senha = self.ent_senha.get().strip()
        if not senha:
            messagebox.showwarning("Confirmação", "Informe a senha ou CPF atual para excluir o cadastro.", parent=self)
            return

        ok, msg = excluir_profissional_autenticado(self.prof_id, senha)
        if not ok:
            messagebox.showerror("Acesso negado", msg, parent=self)
            self.ent_senha.delete(0, tk.END)
            return

        self.excluido = True
        messagebox.showinfo("Excluído", f"O cadastro de '{self.nome_abrev}' foi excluído com sucesso.", parent=self)
        self.destroy()


class DialogoGerenciarLogins(tk.Toplevel):
    """Janela para visualizar os cadastros (1º nome + inicial do sobrenome e 4 dígitos do CPF), editar ou excluir."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_login = parent
        self.title("Gerenciar Logins Cadastrados")
        self.geometry("610x390")
        self.configure(bg="white", padx=18, pady=14)
        self.resizable(False, False)
        self.transient(parent)

        tk.Label(
            self, text="Profissionais Cadastrados",
            bg="white", fg="#0f172a", font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")
        tk.Label(
            self,
            text="Exibição protegida: apenas 1º nome + inicial do sobrenome e os 4 primeiros dígitos do CPF.",
            bg="white", fg="#64748b", font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(0, 10))

        cols = ("id", "profissional", "cpf_4", "modo_login")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=9)
        self.tree.heading("id", text="Nº")
        self.tree.heading("profissional", text="Profissional")
        self.tree.heading("cpf_4", text="CPF (4 Primeiros Dígitos)")
        self.tree.heading("modo_login", text="Tipo de Login")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("profissional", width=190, anchor="w")
        self.tree.column("cpf_4", width=175, anchor="center")
        self.tree.column("modo_login", width=130, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=(0, 12))

        bar = tk.Frame(self, bg="white")
        bar.pack(fill="x")

        tk.Button(
            bar, text="✏️ EDITAR LOGIN / SENHA", bg="#0284c7", fg="white",
            activebackground="#0369a1", activeforeground="white",
            font=("Segoe UI", 9, "bold"), padx=12, pady=7, cursor="hand2", relief="flat",
            command=self.editar_selecionado
        ).pack(side="left")

        tk.Button(
            bar, text="➕ NOVO CADASTRO", bg="#0d9488", fg="white",
            activebackground="#0f766e", activeforeground="white",
            font=("Segoe UI", 9, "bold"), padx=12, pady=7, cursor="hand2", relief="flat",
            command=self.novo_cadastro
        ).pack(side="left", padx=6)

        tk.Button(
            bar, text="🗑 EXCLUIR", bg="#dc2626", fg="white",
            activebackground="#b91c1c", activeforeground="white",
            font=("Segoe UI", 9, "bold"), padx=12, pady=7, cursor="hand2", relief="flat",
            command=self.excluir_selecionado
        ).pack(side="left")

        tk.Button(
            bar, text="FECHAR", bg="#e2e8f0", fg="#334155",
            font=("Segoe UI", 9, "bold"), padx=14, pady=7, cursor="hand2", relief="flat",
            command=self.destroy
        ).pack(side="right")

        self._dados_map = {}
        self.carregar()
        self.grab_set()

    def carregar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._dados_map.clear()

        for r in listar_profissionais_resumo():
            pid = r["id"]
            nome_abrev = abreviar_nome_profissional(r["nome"])
            cpf4_fmt = formatar_cpf_4_digitos(r["cpf_4"]) if r["cpf_4"] else "**.***.***-**"
            login_usr = r["login_usuario"] or r["nome"]
            personalizado = normalizar_nome(login_usr) != normalizar_nome(r["nome"])
            tipo_txt = "Personalizado" if personalizado else "Nome / Padrão"

            self._dados_map[pid] = {
                "nome_abrev": nome_abrev,
                "login_atual": login_usr,
            }
            self.tree.insert("", tk.END, iid=str(pid), values=(pid, nome_abrev, cpf4_fmt, tipo_txt))

    def editar_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selecione", "Clique primeiro em um profissional da lista para editar.", parent=self)
            return
        pid = int(sel[0])
        info = self._dados_map.get(pid)
        if not info:
            return
        dlg = DialogoEditarCredenciais(self, pid, info["nome_abrev"], info["login_atual"])
        self.wait_window(dlg)
        if dlg.atualizado:
            self.carregar()
            if dlg.novo_login and hasattr(self.parent_login, "ent_nome"):
                self.parent_login.ent_nome.delete(0, tk.END)
                self.parent_login.ent_nome.insert(0, dlg.novo_login)

    def novo_cadastro(self):
        dlg = DialogoCadastroProfissional(self)
        self.wait_window(dlg)
        if dlg.nome_cadastrado:
            self.carregar()
            if hasattr(self.parent_login, "ent_nome"):
                self.parent_login.ent_nome.delete(0, tk.END)
                self.parent_login.ent_nome.insert(0, dlg.nome_cadastrado)

    def excluir_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Excluir", "Clique primeiro em um profissional da lista para excluir.", parent=self)
            return
        pid = int(sel[0])
        info = self._dados_map.get(pid)
        if not info:
            return

        dlg = DialogoExcluirProfissional(self, pid, info["nome_abrev"])
        self.wait_window(dlg)
        if dlg.excluido:
            self.carregar()


class TelaLogin(tk.Tk):
    """Primeira tela do aplicativo: usuário = nome completo (ou login) | senha = CPF (ou senha)."""
    def __init__(self):
        super().__init__()
        self.title("NeuroTrack Clínico — Acesso do Profissional")
        self.geometry("460x465")
        self.resizable(False, False)
        self.configure(bg="#f1f5f9")
        self.profissional = None

        topo = tk.Frame(self, bg="#0369a1", pady=16)
        topo.pack(fill="x")
        tk.Label(topo, text="NeuroTrack Clínico", bg="#0369a1", fg="white", font=("Segoe UI", 16, "bold")).pack()
        tk.Label(topo, text="AMCAP - Associação de Moradores Casa do Povo", bg="#0369a1", fg="#e0f2fe", font=("Segoe UI", 9)).pack()

        corpo = tk.Frame(self, bg="white", padx=28, pady=20)
        corpo.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(corpo, text="Nome completo do profissional (ou Login)", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_nome = ttk.Entry(corpo, font=("Segoe UI", 11))
        self.ent_nome.pack(fill="x", pady=(2, 12))

        tk.Label(corpo, text="Senha (CPF ou senha personalizada)", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_senha = ttk.Entry(corpo, font=("Segoe UI", 11), show="•")
        self.ent_senha.pack(fill="x", pady=(2, 4))

        self.var_mostrar = tk.BooleanVar(value=False)
        tk.Checkbutton(
            corpo, text="Mostrar senha", variable=self.var_mostrar, bg="white", activebackground="white",
            font=("Segoe UI", 9), command=lambda: self.ent_senha.config(show="" if self.var_mostrar.get() else "•")
        ).pack(anchor="w", pady=(0, 12))

        tk.Button(
            corpo, text="ENTRAR", bg="#0284c7", fg="white", activebackground="#0369a1", activeforeground="white",
            font=("Segoe UI", 11, "bold"), pady=8, cursor="hand2", relief="flat", command=self.entrar
        ).pack(fill="x")

        rodape_links = tk.Frame(corpo, bg="white")
        rodape_links.pack(fill="x", pady=(14, 0))

        tk.Button(
            rodape_links, text="Cadastrar novo profissional", bg="white", fg="#0369a1", activebackground="#e0f2fe",
            font=("Segoe UI", 9, "underline"), cursor="hand2", relief="flat", bd=0, command=self.cadastrar
        ).pack()

        tk.Button(
            rodape_links, text="Gerenciar logins cadastrados (ver / editar login e senha)",
            bg="#f1f5f9", fg="#0f172a", activebackground="#e2e8f0",
            font=("Segoe UI", 9, "bold"), padx=10, pady=5, cursor="hand2", relief="flat",
            command=self.gerenciar_logins
        ).pack(fill="x", pady=(8, 0))

        self.bind("<Return>", lambda e: self.entrar())
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.ent_nome.focus_set()

    def entrar(self):
        nome = self.ent_nome.get().strip()
        senha = self.ent_senha.get()
        if not nome or not senha:
            messagebox.showwarning("Acesso", "Informe o login (ou nome completo) e a senha (ou CPF).")
            return
        profissional = autenticar_profissional(nome, senha)
        if not profissional:
            messagebox.showerror(
                "Acesso negado",
                "Login/Nome ou Senha/CPF incorretos.\n\n"
                "Se for o primeiro acesso, use 'Cadastrar novo profissional'."
            )
            self.ent_senha.delete(0, tk.END)
            return
        self.profissional = profissional
        self.destroy()

    def cadastrar(self):
        dlg = DialogoCadastroProfissional(self)
        self.wait_window(dlg)
        if dlg.nome_cadastrado:
            self.ent_nome.delete(0, tk.END)
            self.ent_nome.insert(0, dlg.nome_cadastrado)
            self.ent_senha.delete(0, tk.END)
            self.ent_senha.focus_set()

    def gerenciar_logins(self):
        dlg = DialogoGerenciarLogins(self)
        self.wait_window(dlg)


# ==============================================================================
# IMPRESSÃO DE ANAMNESE E NEUROTRACK (A4)
# ==============================================================================
def abrir_impressao_html(html_content, prefixo="relatorio"):
    fd, path = tempfile.mkstemp(suffix=".html", prefix=f"{prefixo}_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html_content)
    webbrowser.open(f"file://{path}")


def gerar_relatorio_anamnese(paciente_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        pac = conn.execute("SELECT * FROM pacientes_anamnese WHERE id = ?", (paciente_id,)).fetchone()
        if not pac:
            messagebox.showerror("Erro", "Paciente não encontrado.")
            return
        resps = dict(conn.execute(
            "SELECT pergunta_id, resposta FROM respostas_anamnese WHERE paciente_id = ?",
            (paciente_id,)
        ).fetchall())

    cpf_4 = formatar_cpf_4_digitos(pac["cpf"])

    blocos_html = ""
    for titulo_sec, perguntas in SECOES_ANAMNESE:
        blocos_html += f"<h2>{titulo_sec}</h2>"
        for qid, qtexto, qtipo in perguntas:
            val = esc(resps.get(qid, "") or "—")
            classe = "q qtexto" if qtipo == "texto" else "q"
            blocos_html += f"""
            <div class="{classe}">
              <div class="qt">{qtexto}</div>
              <div class="qa">{val}</div>
            </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Anamnese - {pac['nome']}</title>
<style>
  body {{ font: 13px/1.45 "Segoe UI", Arial, sans-serif; color: #0f172a; margin: 0; background: #e2e8f0; }}
  .bar {{ background: #0369a1; color: #fff; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }}
  .btn {{ background: #fff; color: #0369a1; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }}
  .sheet {{ max-width: 800px; margin: 16px auto; background: #fff; padding: 28px 34px; border-radius: 8px; }}
  h1 {{ margin: 0 0 4px; font-size: 18px; }}
  .sub {{ color: #64748b; font-size: 12px; margin-bottom: 16px; }}
  .ident {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 20px; border: 1px solid #cbd5e1; padding: 12px; border-radius: 6px; margin-bottom: 16px; }}
  .full {{ grid-column: 1 / -1; }}
  .lab {{ font-size: 10px; text-transform: uppercase; color: #64748b; display: block; }}
  h2 {{ font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #0f172a; padding-bottom: 4px; margin: 18px 0 8px; break-after: avoid; }}
  .q {{ display: flex; justify-content: space-between; gap: 12px; padding: 5px 0; border-bottom: 1px dotted #cbd5e1; break-inside: avoid; }}
  .qt {{ flex: 1; }}
  .qa {{ font-weight: 700; color: #0369a1; min-width: 120px; text-align: right; }}
  .qtexto {{ display: block; }}
  .qtexto .qa {{ text-align: left; white-space: pre-wrap; min-width: 0; margin-top: 3px; font-weight: 600; }}
  .pre {{ white-space: pre-wrap; }}
  .assin {{ margin-top: 48px; width: 60%; border-top: 1px solid #0f172a; padding-top: 6px; font-size: 12px; break-inside: avoid; }}
  @page {{ size: A4; margin: 12mm; }}
  @media print {{ body {{ background: #fff; }} .bar {{ display: none; }} .sheet {{ margin: 0; padding: 0; max-width: none; }} }}
</style>
</head>
<body onload="setTimeout(() => window.print(), 300)">
  <div class="bar">
    <span>Visualização de Impressão — Anamnese Clínica</span>
    <button class="btn" onclick="window.print()">Imprimir / Salvar PDF</button>
  </div>
  <div class="sheet">
    <h1>ANAMNESE CLÍNICA — OBSERVAÇÃO NÃO ESTRUTURADA</h1>
    <div class="sub">Terapia Infantil / TEA</div>
    <div class="ident">
      <div class="full"><span class="lab">Nome do Paciente</span><b>{esc(pac['nome'])}</b></div>
      <div><span class="lab">CPF (4 primeiros dígitos)</span>{cpf_4}</div>
      <div><span class="lab">Data de Nascimento / Idade</span>{pac['data_nascimento'] or '-'} ({pac['idade'] or '-'})</div>
      <div><span class="lab">Data da Observação</span>{pac['data_observacao']}</div>
      <div><span class="lab">Terapeuta Responsável</span>{esc(pac['terapeuta'])}</div>
      <div class="full"><span class="lab">Hipótese Diagnóstica</span><span class="pre">{esc(pac['hipotese_diagnostica'] or '-')}</span></div>
    </div>
    {blocos_html}
    <div class="assin">
      Assinatura e Carimbo do(a) Terapeuta<br>
      <b>{pac['terapeuta']}</b> {('· ' + pac['registro_profissional']) if pac['registro_profissional'] else ''}
    </div>
  </div>
</body>
</html>"""
    abrir_impressao_html(html, prefixo="anamnese")


def gerar_relatorio_neurotrack(paciente_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        pac = conn.execute("SELECT * FROM pacientes_anamnese WHERE id = ?", (paciente_id,)).fetchone()
        if not pac:
            messagebox.showerror("Erro", "Paciente não encontrado.")
            return
        sessoes = conn.execute(
            "SELECT * FROM sessoes_neurotrack WHERE paciente_id = ? ORDER BY id DESC",
            (paciente_id,)
        ).fetchall()

    cpf_4 = formatar_cpf_4_digitos(pac["cpf"])

    sessoes_html = ""
    if not sessoes:
        sessoes_html = "<p>Nenhuma sessão do NeuroTrack foi registrada para este paciente ainda.</p>"
    else:
        for idx, s in enumerate(sessoes):
            total = s["acertos_indep"] + s["tentativas_ajuda"]
            status = "Critério de Domínio Atingido (≥80%)" if s["taxa_independencia"] >= 80 else (
                "Habilidade em Aquisição (50-79%)" if s["taxa_independencia"] >= 50 else "Fase Inicial / Alto Suporte (<50%)"
            )
            sessoes_html += f"""
            <div class="card">
              <div class="card-head">
                <span>Sessão #{len(sessoes) - idx} — {s['meta']}</span>
                <span>Data/Hora: {s['data_hora']}</span>
              </div>
              <div class="metrics">
                <div class="box"><span class="lab">Acertos Independentes</span><b>{s['acertos_indep']}</b></div>
                <div class="box"><span class="lab">Tentativas com Ajuda</span><b>{s['tentativas_ajuda']}</b></div>
                <div class="box"><span class="lab">Taxa Independência ({total} tent.)</span><b>{s['taxa_independencia']}%</b> <small>({status})</small></div>
                <div class="box"><span class="lab">Nível de Suporte (Prompt)</span><b>{s['nivel_suporte']}</b></div>
                <div class="box"><span class="lab">Regulação Sensorial</span><b>{s['regulacao_sensorial']}</b></div>
                <div class="box"><span class="lab">Atenção Sustentada</span><b>{s['tempo_atencao']} min</b></div>
              </div>
              <div class="obs"><span class="lab">Observações Qualitativas e Estratégias:</span><span class="pre">{esc(s['observacoes'] or 'Sem observações.')}</span></div>
            </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>NeuroTrack - {pac['nome']}</title>
<style>
  body {{ font: 13px/1.45 "Segoe UI", Arial, sans-serif; color: #0f172a; margin: 0; background: #e2e8f0; }}
  .bar {{ background: #0d9488; color: #fff; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }}
  .btn {{ background: #fff; color: #0d9488; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }}
  .sheet {{ max-width: 800px; margin: 16px auto; background: #fff; padding: 28px 34px; border-radius: 8px; }}
  h1 {{ margin: 0 0 4px; font-size: 18px; }}
  .sub {{ color: #64748b; font-size: 12px; margin-bottom: 16px; }}
  .ident {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 20px; border: 1px solid #cbd5e1; padding: 12px; border-radius: 6px; margin-bottom: 16px; }}
  .full {{ grid-column: 1 / -1; }}
  .lab {{ font-size: 10px; text-transform: uppercase; color: #64748b; display: block; }}
  h2 {{ font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #0f172a; padding-bottom: 4px; margin: 18px 0 10px; }}
  .card {{ border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 12px; break-inside: avoid; }}
  .card-head {{ display: flex; justify-content: space-between; font-weight: bold; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 8px; }}
  .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 8px; }}
  .box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 6px 8px; border-radius: 4px; }}
  .obs {{ border-top: 1px dotted #cbd5e1; padding-top: 6px; }}
  .pre {{ white-space: pre-wrap; }}
  .assin {{ margin-top: 48px; width: 60%; border-top: 1px solid #0f172a; padding-top: 6px; font-size: 12px; break-inside: avoid; }}
  @page {{ size: A4; margin: 12mm; }}
  @media print {{ body {{ background: #fff; }} .bar {{ display: none; }} .sheet {{ margin: 0; padding: 0; max-width: none; }} }}
</style>
</head>
<body onload="setTimeout(() => window.print(), 300)">
  <div class="bar">
    <span>Visualização de Impressão — Relatório NeuroTrack</span>
    <button class="btn" onclick="window.print()">Imprimir / Salvar PDF</button>
  </div>
  <div class="sheet">
    <h1>NEUROTRACK — REGISTRO CLÍNICO DE SESSÕES (TEA)</h1>
    <div class="sub">Acompanhamento de Tentativas Discretas (DTT) e Regulação Sensorial</div>
    <div class="ident">
      <div class="full"><span class="lab">Nome do Paciente</span><b>{esc(pac['nome'])}</b></div>
      <div><span class="lab">CPF (4 Primeiros Dígitos)</span>{cpf_4}</div>
      <div><span class="lab">Terapeuta Responsável</span>{pac['terapeuta']}</div>
      <div class="full"><span class="lab">Hipótese Diagnóstica</span><span class="pre">{esc(pac['hipotese_diagnostica'] or '-')}</span></div>
    </div>
    <h2>Sessões Registradas ({len(sessoes)})</h2>
    {sessoes_html}
    <div class="assin">
      Assinatura e Carimbo do(a) Terapeuta<br>
      <b>{pac['terapeuta']}</b> {('· ' + pac['registro_profissional']) if pac['registro_profissional'] else ''}
    </div>
  </div>
</body>
</html>"""
    abrir_impressao_html(html, prefixo="neurotrack")


# ==============================================================================
# EVOLUÇÃO ENTRE ANAMNESES (RELATÓRIO COMPARATIVO)
# ==============================================================================
# SIM / SEMPRE = sinal POSITIVO para a criança
PERGUNTAS_POSITIVAS = {
    "vest_2", "vest_4", "vest_5", "vest_6", "vest_7", "vest_8", "vest_9", "vest_10",
    "tat_9",
    "pro_1", "pro_2", "pro_8", "pro_9", "pro_10", "pro_11",
    "vis_2", "vis_3", "vis_4", "vis_5", "vis_7", "vis_9", "vis_11", "vis_12",
    "vis_13", "vis_14", "vis_15", "vis_16",
    "rea_1", "rea_4", "rea_5",
    "per_2", "per_5", "per_6", "per_8",
    "pra_1", "pra_2", "pra_7", "pra_8", "pra_9", "pra_12", "pra_13", "pra_14", "pra_15", "pra_16",
}

# SIM / SEMPRE = sinal NEGATIVO (a nota é invertida: responder NÃO passa a ser a melhor resposta)
PERGUNTAS_NEGATIVAS = {
    "vest_3",
    "tat_1", "tat_2", "tat_3", "tat_4", "tat_6", "tat_7", "tat_8",
    "pro_3", "pro_4", "pro_5", "pro_6", "pro_12", "pro_13",
    "vis_6", "vis_10",
    "rea_3", "rea_6", "rea_7", "rea_13", "rea_14",
    "per_1", "per_3", "per_4", "per_7",
    "pra_3", "pra_4", "pra_5", "pra_6", "pra_10", "pra_11",
}

PONTOS_ESCALA = {"NÃO": 0, "ÀS VEZES": 1, "SIM": 2, "SEMPRE": 3}   # "ESTÁVEL" não pontua


def pontuar_resposta(qid, resposta):
    """Nota de 0 (pior) a 3 (melhor), já considerando se SIM é positivo ou negativo. None = não comparável."""
    pts = PONTOS_ESCALA.get(resposta)
    if pts is None:
        return None
    if qid in PERGUNTAS_POSITIVAS:
        return pts
    if qid in PERGUNTAS_NEGATIVAS:
        return 3 - pts
    return None


def _data_para_ordenar(txt):
    try:
        return datetime.strptime(str(txt).strip(), "%d/%m/%Y").date()
    except ValueError:
        return date.min


def veredito_evolucao(melhoras, pioras):
    if melhoras > pioras:
        return "positiva"
    if pioras > melhoras:
        return "negativa"
    return "estavel"


def carregar_anamneses_da_crianca(cpf):
    """Todas as anamneses da criança (mesmo CPF) em ordem cronológica."""
    anamneses = []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        for p in conn.execute("SELECT * FROM pacientes_anamnese WHERE cpf = ?", (cpf,)).fetchall():
            resps = dict(conn.execute(
                "SELECT pergunta_id, resposta FROM respostas_anamnese WHERE paciente_id = ?", (p["id"],)
            ).fetchall())
            anamneses.append({
                "id": p["id"], "nome": p["nome"], "data": p["data_observacao"],
                "terapeuta": p["terapeuta"], "respostas": resps,
            })
    anamneses.sort(key=lambda a: (_data_para_ordenar(a["data"]), a["id"]))
    return anamneses


def analisar_evolucao(anamneses):
    """anamneses: lista cronológica de {'respostas': {pergunta_id: resposta}, ...}."""
    n = len(anamneses)
    comparaveis = PERGUNTAS_POSITIVAS | PERGUNTAS_NEGATIVAS
    secoes = []
    totais = {"melhoras": 0, "pioras": 0, "estaveis": 0, "sem_dados": 0}
    todos_comuns = []

    for titulo, perguntas in SECOES_ANAMNESE:
        itens = []
        for qid, qtexto, qtipo in perguntas:
            if qid not in comparaveis:
                continue
            respostas = [a["respostas"].get(qid, "") for a in anamneses]
            notas = [pontuar_resposta(qid, r) for r in respostas]
            validas = [x for x in notas if x is not None]
            resultado = None
            if len(validas) >= 2:                       # 1ª nota válida x última nota válida
                delta = validas[-1] - validas[0]
                resultado = "melhora" if delta > 0 else ("piora" if delta < 0 else "estavel")
            itens.append({"id": qid, "texto": qtexto, "respostas": respostas, "notas": notas, "resultado": resultado})
        if not itens:
            continue

        melhoras = sum(1 for i in itens if i["resultado"] == "melhora")
        pioras = sum(1 for i in itens if i["resultado"] == "piora")
        estaveis = sum(1 for i in itens if i["resultado"] == "estavel")
        totais["melhoras"] += melhoras
        totais["pioras"] += pioras
        totais["estaveis"] += estaveis
        totais["sem_dados"] += sum(1 for i in itens if i["resultado"] is None)

        # Índice (0-100%) de cada anamnese, só com as perguntas respondidas em TODAS elas
        comuns = [i for i in itens if all(x is not None for x in i["notas"])]
        todos_comuns.extend(comuns)
        indices = [None] * n
        if comuns:
            indices = [round(sum(i["notas"][k] for i in comuns) / (3 * len(comuns)) * 100) for k in range(n)]
        secoes.append({
            "titulo": titulo, "itens": itens, "melhoras": melhoras, "pioras": pioras,
            "estaveis": estaveis, "indices": indices, "n_comuns": len(comuns),
        })

    indice_geral = [None] * n
    if todos_comuns:
        indice_geral = [round(sum(i["notas"][k] for i in todos_comuns) / (3 * len(todos_comuns)) * 100) for k in range(n)]
    return {
        "n": n, "secoes": secoes, "totais": totais, "indice_geral": indice_geral,
        "n_comuns": len(todos_comuns),
        "veredito": veredito_evolucao(totais["melhoras"], totais["pioras"]),
    }


def _cores_serie(n):
    if n <= 1:
        return ["hsl(205,85%,40%)"]
    return [f"hsl(205,85%,{round(78 - 46 * k / (n - 1))}%)" for k in range(n)]


def _quebrar_rotulo(txt, limite=14):
    linhas, atual = [], ""
    for palavra in txt.split():
        if atual and len(atual) + 1 + len(palavra) > limite:
            linhas.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    if atual:
        linhas.append(atual)
    return linhas


def svg_grafico_barras(grupos, n, cores):
    """grupos: [(nome, [% por anamnese ou None])] -> SVG de barras agrupadas (0 a 100%)."""
    W, H = 900, 340
    esq, dire, topo, base = 44, 12, 22, 62
    pw, ph = W - esq - dire, H - topo - base
    partes = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Gráfico comparativo">']
    for v in (0, 25, 50, 75, 100):
        y = topo + ph * (1 - v / 100)
        partes.append(f'<line x1="{esq}" y1="{y:.1f}" x2="{W - dire}" y2="{y:.1f}" stroke="#e2e8f0"/>')
        partes.append(f'<text x="{esq - 6}" y="{y + 3:.1f}" font-size="10" text-anchor="end" fill="#64748b">{v}%</text>')
    gw = pw / len(grupos)
    bw = min(34, gw * 0.8 / n)
    fonte = 9 if bw >= 24 else 7
    for gi, (nome, valores) in enumerate(grupos):
        x0 = esq + gi * gw + (gw - bw * n) / 2
        for k, v in enumerate(valores):
            if v is None:
                continue
            h = ph * v / 100
            x, y = x0 + k * bw, topo + ph - h
            partes.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw - 2:.1f}" height="{h:.1f}" fill="{cores[k]}"/>')
            if bw >= 12:
                partes.append(f'<text x="{x + (bw - 2) / 2:.1f}" y="{y - 3:.1f}" font-size="{fonte}" text-anchor="middle" fill="#0f172a">{v}%</text>')
        cx = esq + gi * gw + gw / 2
        for li, linha in enumerate(_quebrar_rotulo(nome)):
            partes.append(f'<text x="{cx:.1f}" y="{topo + ph + 16 + li * 12}" font-size="10" text-anchor="middle" fill="#0f172a">{esc(linha)}</text>')
    partes.append("</svg>")
    return "".join(partes)


CSS_COMPARATIVO = """
  * { box-sizing: border-box; }
  body { font: 12px/1.4 "Segoe UI", Arial, sans-serif; color: #0f172a; margin: 0; background: #e2e8f0;
         -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .bar { background: #6d28d9; color: #fff; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }
  .btn { background: #fff; color: #6d28d9; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }
  .sheet { max-width: 1000px; margin: 16px auto; background: #fff; padding: 26px 30px; border-radius: 8px; }
  h1 { margin: 0 0 4px; font-size: 18px; }
  .sub { color: #64748b; margin-bottom: 14px; }
  .ident { border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 12px; margin-bottom: 14px;
           display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 6px 16px; }
  .lab { font-size: 10px; text-transform: uppercase; color: #64748b; display: block; }
  .veredito { border-radius: 6px; padding: 10px 14px; font-size: 14px; font-weight: 700; margin-bottom: 10px; }
  .v-positiva { background: #ecfdf5; border: 1px solid #6ee7b7; color: #065f46; }
  .v-negativa { background: #fef2f2; border: 1px solid #fca5a5; color: #991b1b; }
  .v-estavel { background: #f1f5f9; border: 1px solid #cbd5e1; color: #334155; }
  .resumo { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
  .kpi { flex: 1; min-width: 130px; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px; background: #f8fafc; }
  .kpi b { font-size: 20px; display: block; }
  .pos { color: #047857; font-weight: 700; } .neg { color: #b91c1c; font-weight: 700; } .neu { color: #475569; font-weight: 700; }
  h2 { font-size: 13px; text-transform: uppercase; border-bottom: 2px solid #0f172a; padding-bottom: 4px;
       margin: 18px 0 8px; break-after: avoid; display: flex; justify-content: space-between; gap: 12px; }
  h2 small { font-size: 10px; text-transform: none; font-weight: normal; color: #475569; }
  .grafico { border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px; margin-bottom: 6px; break-inside: avoid; }
  .grafico svg { width: 100%; height: auto; }
  .legenda { display: flex; gap: 14px; flex-wrap: wrap; margin: 4px 0 2px; font-size: 11px; }
  .legenda i { display: inline-block; width: 12px; height: 12px; margin-right: 5px; vertical-align: -1px; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
  th, td { border: 1px solid #e2e8f0; padding: 4px 6px; vertical-align: middle; }
  th { background: #f1f5f9; font-size: 10px; text-transform: uppercase; text-align: center; }
  th small { display: block; text-transform: none; font-weight: normal; color: #64748b; }
  td.q { width: 40%; } td.r { text-align: center; font-weight: 700; font-size: 11px; }
  td.ev { text-align: center; white-space: nowrap; }
  tr { break-inside: avoid; }
  .n0 { background: #fecaca; } .n1 { background: #fed7aa; } .n2 { background: #d9f99d; } .n3 { background: #86efac; }
  .nn { background: #f8fafc; color: #94a3b8; }
  .nota { color: #475569; font-size: 11px; margin-top: 16px; border-top: 1px dotted #cbd5e1; padding-top: 8px; }
  .assin { margin-top: 40px; width: 40%; border-top: 1px solid #0f172a; padding-top: 6px; font-size: 12px; break-inside: avoid; }
  @page { size: A4 landscape; margin: 10mm; }
  @media print { body { background: #fff; } .bar { display: none; } .sheet { margin: 0; padding: 0; max-width: none; border-radius: 0; } }
"""

VEREDITOS = {
    "positiva": ("v-positiva", "▲ EVOLUÇÃO POSITIVA"),
    "negativa": ("v-negativa", "▼ EVOLUÇÃO NEGATIVA"),
    "estavel": ("v-estavel", "● SEM MUDANÇA SIGNIFICATIVA"),
}


def _selo_evolucao(resultado):
    return {
        "melhora": '<span class="pos">▲ Melhora</span>',
        "piora": '<span class="neg">▼ Piora</span>',
        "estavel": '<span class="neu">● Sem alteração</span>',
    }.get(resultado, '<span class="neu">— sem dados</span>')


def _fmt_indice(v):
    return "—" if v is None else f"{v}%"


def montar_html_comparativo(anamneses, cpf):
    ev = analisar_evolucao(anamneses)
    n = ev["n"]
    tot = ev["totais"]
    nome = anamneses[-1]["nome"]
    cores = _cores_serie(n)
    classe_v, texto_v = VEREDITOS[ev["veredito"]]

    cab_cols = "".join(
        f'<th>{esc(a["data"])}<small>{esc(a["terapeuta"])}</small></th>' for a in anamneses
    )

    blocos = ""
    for sec in ev["secoes"]:
        linhas = ""
        for it in sec["itens"]:
            celulas = ""
            for resp, nota in zip(it["respostas"], it["notas"]):
                classe = f"n{nota}" if nota is not None else "nn"
                celulas += f'<td class="r {classe}">{esc(resp) if resp else "—"}</td>'
            linhas += (
                f'<tr><td class="q">{esc(it["texto"])}</td>{celulas}'
                f'<td class="ev">{_selo_evolucao(it["resultado"])}</td></tr>'
            )
        blocos += (
            f'<h2><span>{esc(sec["titulo"])}</span>'
            f'<small>▲ {sec["melhoras"]} melhora(s) · ▼ {sec["pioras"]} piora(s) · ● {sec["estaveis"]} sem alteração</small></h2>'
            f'<table><tr><th>Pergunta</th>{cab_cols}<th>Evolução</th></tr>{linhas}</table>'
        )

    grupos = []
    if any(v is not None for v in ev["indice_geral"]):
        grupos.append(("Geral", ev["indice_geral"]))
    for sec in ev["secoes"]:
        if any(v is not None for v in sec["indices"]):
            nome_curto = re.sub(r"^\d+\.\s*", "", sec["titulo"]).split("(")[0].strip()
            grupos.append((nome_curto, sec["indices"]))
    if grupos:
        legenda = "".join(
            f'<span><i style="background:{cores[k]}"></i>{esc(a["data"])}</span>' for k, a in enumerate(anamneses)
        )
        grafico = (
            f'<div class="grafico">{svg_grafico_barras(grupos, n, cores)}'
            f'<div class="legenda">{legenda}</div></div>'
        )
    else:
        grafico = '<p class="nota">Não há perguntas comparáveis respondidas em todas as anamneses para montar o gráfico.</p>'

    ig = ev["indice_geral"]
    kpi_indice = f'{_fmt_indice(ig[0])} → {_fmt_indice(ig[-1])}'
    datas = [a["data"] for a in anamneses]

    return (
        '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">'
        f'<title>Evolução - {esc(nome)}</title><style>{CSS_COMPARATIVO}</style></head>'
        '<body onload="setTimeout(() => window.print(), 300)">'
        '<div class="bar"><span>Visualização de Impressão — Relatório Comparativo de Evolução</span>'
        '<button class="btn" onclick="window.print()">Imprimir / Salvar PDF</button></div>'
        '<div class="sheet">'
        '<h1>RELATÓRIO COMPARATIVO DE EVOLUÇÃO — ANAMNESE CLÍNICA</h1>'
        '<div class="sub">Comparação das respostas fixas entre as anamneses da mesma criança</div>'
        '<div class="ident">'
        f'<div><span class="lab">Nome do Paciente</span><b>{esc(nome)}</b></div>'
        f'<div><span class="lab">CPF (4 primeiros dígitos)</span>{esc(formatar_cpf_4_digitos(cpf))}</div>'
        f'<div><span class="lab">Anamneses comparadas</span>{n} ({esc(datas[0])} a {esc(datas[-1])})</div>'
        '</div>'
        f'<div class="veredito {classe_v}">{texto_v}: {tot["melhoras"]} pergunta(s) melhoraram e {tot["pioras"]} pioraram</div>'
        '<div class="resumo">'
        f'<div class="kpi"><span class="lab">Melhoras</span><b class="pos">▲ {tot["melhoras"]}</b></div>'
        f'<div class="kpi"><span class="lab">Pioras</span><b class="neg">▼ {tot["pioras"]}</b></div>'
        f'<div class="kpi"><span class="lab">Sem alteração</span><b class="neu">● {tot["estaveis"]}</b></div>'
        f'<div class="kpi"><span class="lab">Sem dados para comparar</span><b class="neu">{tot["sem_dados"]}</b></div>'
        f'<div class="kpi"><span class="lab">Índice geral (1ª → última)</span><b>{kpi_indice}</b></div>'
        '</div>'
        '<h2><span>Gráfico comparativo por área</span>'
        f'<small>índice de 0 a 100% (perguntas respondidas em todas as anamneses: {ev["n_comuns"]})</small></h2>'
        f'{grafico}'
        f'{blocos}'
        '<div class="nota"><b>Como ler:</b> NÃO e ÀS VEZES indicam resposta mais negativa; SIM e SEMPRE, mais positiva. '
        'Nas perguntas em que SIM é um sinal desfavorável (por exemplo, aversão ou medo), a leitura é invertida. '
        'A coluna Evolução compara a primeira e a última resposta válida de cada pergunta. '
        'Perguntas de nível, comportamento, texto livre, respostas ESTÁVEL e perguntas em branco não entram na comparação. '
        'Este relatório é um apoio à análise; a interpretação clínica é do(a) terapeuta.</div>'
        '<div class="assin">Assinatura e Carimbo do(a) Terapeuta<br>'
        f'<b>{esc(anamneses[-1]["terapeuta"])}</b></div>'
        '</div></body></html>'
    )


def gerar_relatorio_comparativo(cpf):
    anamneses = carregar_anamneses_da_crianca(cpf)
    if len(anamneses) < 2:
        messagebox.showinfo("Relatório Comparativo", "São necessárias pelo menos 2 anamneses da mesma criança.")
        return
    abrir_impressao_html(montar_html_comparativo(anamneses, cpf), prefixo="comparativo")


def contar_sessoes(ids):
    if not ids:
        return 0
    marcas = ",".join("?" * len(ids))
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            f"SELECT COUNT(*) FROM sessoes_neurotrack WHERE paciente_id IN ({marcas})", list(ids)
        ).fetchone()[0]


def excluir_anamneses(ids):
    """Apaga as anamneses, as respostas e as sessões NeuroTrack ligadas a elas (numa única transação)."""
    lista = [(i,) for i in ids]
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany("DELETE FROM sessoes_neurotrack WHERE paciente_id = ?", lista)
        conn.executemany("DELETE FROM respostas_anamnese WHERE paciente_id = ?", lista)
        conn.executemany("DELETE FROM pacientes_anamnese WHERE id = ?", lista)


# ==============================================================================
# JANELA SEPARADA: LISTA DE PACIENTES REGISTRADOS
# ==============================================================================
class JanelaListaPacientes(tk.Toplevel):
    """Janela separada para consultar pacientes, imprimir Anamnese/NeuroTrack ou abrir paciente no NeuroTrack."""
    def __init__(self, app_principal):
        super().__init__(app_principal)
        self.app = app_principal
        self.title("Lista de Pacientes Registrados — Anamnese & NeuroTrack")
        self.geometry("1040x620")
        self.configure(bg="white")

        # Cabeçalho da janela separada
        header = tk.Frame(self, bg="#0f172a", padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(
            header, text="📋 PACIENTES REGISTRADOS (NOME E 4 PRIMEIROS DÍGITOS DO CPF)",
            bg="#0f172a", fg="white", font=("Segoe UI", 11, "bold")
        ).pack(side="left")

        body = tk.Frame(self, bg="white", padx=16, pady=12)
        body.pack(fill="both", expand=True)

        # Linha 1: busca
        bar = tk.Frame(body, bg="white")
        bar.pack(fill="x", pady=(0, 6))

        tk.Label(bar, text="Buscar por nome:", bg="white", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.ent_busca = ttk.Entry(bar, width=28, font=("Segoe UI", 10))
        self.ent_busca.pack(side="left", padx=8)
        self.ent_busca.bind("<KeyRelease>", lambda e: self.carregar_dados())

        # Linha 2: ações
        acoes = tk.Frame(body, bg="white")
        acoes.pack(fill="x", pady=(0, 10))

        tk.Button(
            acoes, text="▶ ABRIR NO NEUROTRACK", bg="#f59e0b", fg="white",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, cursor="hand2", relief="flat",
            command=self.abrir_no_neurotrack
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            acoes, text="➕ ABRIR NOVA ANAMNESE", bg="#16a34a", fg="white",
            activebackground="#15803d", activeforeground="white",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, cursor="hand2", relief="flat",
            command=self.abrir_nova_anamnese
        ).pack(side="left", padx=4)

        tk.Button(
            acoes, text="🖨️ IMPRIMIR ANAMNESE", bg="#0284c7", fg="white",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, cursor="hand2", relief="flat",
            command=self.imprimir_anamnese
        ).pack(side="left", padx=4)

        tk.Button(
            acoes, text="🖨️ IMPRIMIR NEUROTRACK", bg="#0d9488", fg="white",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, cursor="hand2", relief="flat",
            command=self.imprimir_neurotrack
        ).pack(side="left", padx=4)

        # Botão do relatório comparativo: só aparece quando a criança selecionada tem 2+ anamneses
        self.btn_comparar = tk.Button(
            acoes, text="📈 GERAR RELATÓRIO COMPARATIVO", bg="#6d28d9", fg="white",
            activebackground="#5b21b6", activeforeground="white",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, cursor="hand2", relief="flat",
            command=self.gerar_comparativo
        )
        self._btn_visivel = False
        self.grupos = {}

        tk.Button(
            acoes, text="🗑 EXCLUIR", bg="#dc2626", fg="white",
            activebackground="#b91c1c", activeforeground="white",
            font=("Segoe UI", 9, "bold"), padx=10, pady=6, cursor="hand2", relief="flat",
            command=self.excluir_selecionado
        ).pack(side="right", padx=(4, 0))

        # Tabela: cada criança é uma linha e, logo abaixo, as anamneses feitas com suas datas
        cols = ("id", "nome", "cpf_4", "data_obs", "sessoes")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=15)
        self.tree.heading("id", text="Nº")
        self.tree.heading("nome", text="Criança / Anamnese")
        self.tree.heading("cpf_4", text="CPF (4 Primeiros Dígitos)")
        self.tree.heading("data_obs", text="Data da Anamnese")
        self.tree.heading("sessoes", text="Sessões NeuroTrack")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nome", width=320, anchor="w")
        self.tree.column("cpf_4", width=190, anchor="center")
        self.tree.column("data_obs", width=130, anchor="center")
        self.tree.column("sessoes", width=150, anchor="center")
        self.tree.tag_configure("crianca", background="#e0f2fe")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._ao_selecionar)

        tk.Label(
            body,
            text="Clique no nome da criança ou na data de uma anamnese. Use 'Abrir Nova Anamnese' para registrar outra anamnese da mesma criança "
                 "(já com Nome e CPF preenchidos). Com 2 ou mais anamneses, aparece o botão 'Gerar Relatório Comparativo'.",
            bg="white", fg="#64748b", font=("Segoe UI", 9), pady=6, wraplength=980, justify="left"
        ).pack(anchor="w")

        self.carregar_dados()

    def carregar_dados(self):
        busca = self.ent_busca.get().strip().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT p.*,
                       (SELECT COUNT(*) FROM sessoes_neurotrack s WHERE s.paciente_id = p.id) AS total_sessoes
                FROM pacientes_anamnese p
                ORDER BY p.id ASC
            """).fetchall()

        # Agrupa por criança (mesmo CPF)
        por_crianca = {}
        for r in rows:
            chave = somente_digitos(r["cpf"]) or f"id{r['id']}"
            por_crianca.setdefault(chave, []).append(r)

        self.grupos = {}
        for chave, lista in sorted(por_crianca.items(), key=lambda kv: max(x["id"] for x in kv[1]), reverse=True):
            lista.sort(key=lambda x: (_data_para_ordenar(x["data_observacao"]), x["id"]))
            if busca and not any(busca in x["nome"].lower() for x in lista):
                continue
            self.grupos[chave] = [x["id"] for x in lista]
            total_sessoes = sum(x["total_sessoes"] for x in lista)
            gid = f"g{chave}"
            self.tree.insert("", tk.END, iid=gid, open=True, tags=("crianca",), values=(
                "", lista[-1]["nome"], formatar_cpf_4_digitos(chave),
                f"{len(lista)} anamnese(s)",
                f"{total_sessoes} sessão(ões)" if total_sessoes else "Nenhuma (0)"
            ))
            for i, x in enumerate(lista, 1):
                sessoes_txt = f"{x['total_sessoes']} sessão(ões)" if x["total_sessoes"] else "Nenhuma (0)"
                self.tree.insert(gid, tk.END, iid=f"a{x['id']}", values=(
                    x["id"], f"        └ {i}ª anamnese", "", x["data_observacao"], sessoes_txt
                ))
        self._ao_selecionar()

    def _chave_selecionada(self):
        sel = self.tree.selection()
        if not sel:
            return None
        iid = sel[0]
        if iid.startswith("g"):
            return iid[1:]
        pai = self.tree.parent(iid)
        return pai[1:] if pai else None

    def _ao_selecionar(self, event=None):
        chave = self._chave_selecionada()
        mostrar = bool(chave) and len(self.grupos.get(chave, [])) >= 2
        if mostrar and not self._btn_visivel:
            self.btn_comparar.pack(side="left", padx=4)
            self._btn_visivel = True
        elif not mostrar and self._btn_visivel:
            self.btn_comparar.pack_forget()
            self._btn_visivel = False

    def _selecionado_id(self):
        """Id de UMA anamnese. Se a criança tiver várias, é preciso clicar na data desejada."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selecione um Paciente", "Clique primeiro sobre o nome do paciente na lista.", parent=self)
            return None
        iid = sel[0]
        if iid.startswith("a"):
            return int(iid[1:])
        ids = self.grupos.get(iid[1:], [])
        if len(ids) == 1:
            return ids[0]
        messagebox.showwarning(
            "Escolha a Anamnese",
            f"Esta criança tem {len(ids)} anamneses. Clique na data da anamnese desejada.",
            parent=self
        )
        return None

    def gerar_comparativo(self):
        chave = self._chave_selecionada()
        if not chave or len(self.grupos.get(chave, [])) < 2:
            messagebox.showwarning("Relatório Comparativo", "Selecione uma criança com pelo menos 2 anamneses.", parent=self)
            return
        gerar_relatorio_comparativo(chave)

    def excluir_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning(
                "Excluir", "Clique primeiro na criança (exclui tudo dela) ou na data de uma anamnese (exclui só essa).",
                parent=self
            )
            return
        iid = sel[0]
        chave = self._chave_selecionada()
        nome = self.tree.item("g" + chave, "values")[1] if chave else ""

        if iid.startswith("a"):
            ids = [int(iid[1:])]
            data = self.tree.item(iid, "values")[3]
            sessoes = contar_sessoes(ids)
            if not messagebox.askyesno(
                "Excluir anamnese",
                f"Excluir a anamnese de {data} de '{nome}'?\n\n"
                f"Isso também apaga as {sessoes} sessão(ões) do NeuroTrack ligadas a ela.\n\n"
                "Esta ação não pode ser desfeita.",
                icon="warning", default="no", parent=self
            ):
                return
            resumo = f"Anamnese de {data} excluída."
        else:
            ids = list(self.grupos.get(chave, []))
            if not ids:
                return
            sessoes = contar_sessoes(ids)
            if not messagebox.askyesno(
                "Excluir criança",
                f"Excluir TODOS os registros de '{nome}'?\n\n"
                f"• {len(ids)} anamnese(s)\n• {sessoes} sessão(ões) do NeuroTrack\n\n"
                "Esta ação não pode ser desfeita.",
                icon="warning", default="no", parent=self
            ):
                return
            if not messagebox.askyesno(
                "Confirmar exclusão", f"Confirma a exclusão definitiva de '{nome}'?",
                icon="warning", default="no", parent=self
            ):
                return
            resumo = f"Todos os registros de '{nome}' foram excluídos."

        excluir_anamneses(ids)
        self.app.paciente_excluido(ids)
        self.carregar_dados()
        messagebox.showinfo("Exclusão concluída", resumo, parent=self)

    def imprimir_anamnese(self):
        pid = self._selecionado_id()
        if pid:
            gerar_relatorio_anamnese(pid)

    def imprimir_neurotrack(self):
        pid = self._selecionado_id()
        if pid:
            gerar_relatorio_neurotrack(pid)

    def abrir_no_neurotrack(self):
        pid = self._selecionado_id()
        if pid:
            self.app.carregar_paciente_no_neurotrack(pid)
            self.destroy()

    def abrir_nova_anamnese(self):
        chave = self._chave_selecionada()
        if not chave:
            messagebox.showwarning("Selecione um Paciente", "Clique primeiro sobre o nome do paciente na lista.", parent=self)
            return
        ids = self.grupos.get(chave, [])
        if not ids:
            return
        # Usa o registro mais recente da criança para pré-preencher a identificação
        self.app.carregar_paciente_na_nova_anamnese(ids[-1])
        self.destroy()


# ==============================================================================
# JANELA PRINCIPAL DO APLICATIVO
# ==============================================================================
class NeuroTrackApp(tk.Tk):
    def __init__(self, profissional=""):
        super().__init__()
        self.profissional = profissional
        self.canvas_ativo = None
        self.title("NeuroTrack Clínico  — Associação de Moradores Casa do Povo )")
        self.geometry("1080x760")
        self.minsize(960, 640)
        self.configure(bg="#f1f5f9")

        self.paciente_atual_id = None
        self.paciente_atual_nome = ""
        self.paciente_atual_cpf4 = ""
        self.janela_lista = None

        self.botoes_anamnese = {}
        self.indep_count = 0
        self.prompt_count = 0
        self.attention_min = 10

        # Barra Superior Fixa com Botão para abrir a Lista Separada de Pacientes
        header = tk.Frame(self, bg="#0369a1", padx=16, pady=10)
        header.pack(fill="x")

        tk.Label(
            header, text="NeuroTrack FHIR — Anamnese Clínica & Registro de Sessão",
            bg="#0369a1", fg="white", font=("Segoe UI", 13, "bold")
        ).pack(side="left")

        tk.Button(
            header, text="📋 ABRIR LISTA DE PACIENTES REGISTRADOS",
            bg="#ffffff", fg="#0369a1", activebackground="#e0f2fe", activeforeground="#0369a1",
            font=("Segoe UI", 10, "bold"), padx=14, pady=6, cursor="hand2", relief="flat",
            command=self.abrir_janela_lista
        ).pack(side="right")

        tk.Label(
            header, text=f"👤 {self.profissional}", bg="#0369a1", fg="white", font=("Segoe UI", 10, "bold")
        ).pack(side="right", padx=14)

        # Barra de navegação por botões entre Etapa 1 (Anamnese) e Etapa 2 (NeuroTrack)
        nav_bar = tk.Frame(self, bg="#e2e8f0", padx=16, pady=6)
        nav_bar.pack(fill="x")

        self.btn_ir_anam = tk.Button(
            nav_bar, text="ETAPA 1: PREENCHER NOVA ANAMNESE",
            bg="#0284c7", fg="white", font=("Segoe UI", 10, "bold"),
            padx=16, pady=6, relief="flat", cursor="hand2",
            command=self.mostrar_tela_anamnese
        )
        self.btn_ir_anam.pack(side="left", padx=(0, 8))

        self.btn_ir_nt = tk.Button(
            nav_bar, text="ETAPA 2: SESSÃO NEUROTRACK",
            bg="#cbd5e1", fg="#334155", font=("Segoe UI", 10, "bold"),
            padx=16, pady=6, relief="flat", cursor="hand2",
            command=self.mostrar_tela_neurotrack
        )
        self.btn_ir_nt.pack(side="left")

        # Container Principal das Telas
        self.main_container = tk.Frame(self, bg="white")
        self.main_container.pack(fill="both", expand=True, padx=12, pady=10)

        self.frame_anamnese = tk.Frame(self.main_container, bg="white")
        self.frame_neurotrack = tk.Frame(self.main_container, bg="white")

        self._build_tela_anamnese()
        self._build_tela_neurotrack()

        self.mostrar_tela_anamnese()

    def mostrar_tela_anamnese(self):
        self.frame_neurotrack.pack_forget()
        self.frame_anamnese.pack(fill="both", expand=True)
        self.canvas_ativo = self.canvas_anam
        self.btn_ir_anam.config(bg="#0284c7", fg="white")
        self.btn_ir_nt.config(bg="#cbd5e1", fg="#334155")

    def mostrar_tela_neurotrack(self):
        self.frame_anamnese.pack_forget()
        self.frame_neurotrack.pack(fill="both", expand=True)
        self.canvas_ativo = self.canvas_nt
        self.btn_ir_nt.config(bg="#0d9488", fg="white")
        self.btn_ir_anam.config(bg="#cbd5e1", fg="#334155")

    def abrir_janela_lista(self):
        if self.janela_lista and self.janela_lista.winfo_exists():
            self.janela_lista.carregar_dados()
            self.janela_lista.lift()
            self.janela_lista.focus_force()
        else:
            self.janela_lista = JanelaListaPacientes(self)

    # --------------------------------------------------------------------------
    # TELA 1: ANAMNESE (100% com Botões Clicáveis)
    # --------------------------------------------------------------------------
    def _build_tela_anamnese(self):
        self.canvas_anam, self.scroll_anam = self._criar_area_rolavel(self.frame_anamnese, padx=20, pady=15)
        self.bind_all("<MouseWheel>", self._on_wheel)

        # 1. Identificação do Paciente
        lf_id = tk.LabelFrame(
            self.scroll_anam, text=" 1. IDENTIFICAÇÃO DA CRIANÇA ",
            font=("Segoe UI", 10, "bold"), bg="white", fg="#0369a1", padx=12, pady=10
        )
        lf_id.pack(fill="x", pady=(0, 14))
        for i in range(4):
            lf_id.columnconfigure(i, weight=1)

        tk.Label(lf_id, text="Nome do Paciente *:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        self.ent_nome = ttk.Entry(lf_id, font=("Segoe UI", 10))
        self.ent_nome.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4, padx=6)

        tk.Label(lf_id, text="CPF da Criança *:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        self.ent_cpf = ttk.Entry(lf_id, font=("Segoe UI", 10))
        self.ent_cpf.grid(row=1, column=1, sticky="ew", pady=4, padx=6)

        tk.Label(lf_id, text="Data Nascimento (DD/MM/AAAA):", bg="white", font=("Segoe UI", 9)).grid(row=1, column=2, sticky="w", pady=4)
        self.ent_nasc = CampoData(lf_id, ao_alterar=self._atualizar_idade, font=("Segoe UI", 10))
        self.ent_nasc.grid(row=1, column=3, sticky="ew", pady=4, padx=6)

        tk.Label(lf_id, text="Idade Atual (automática):", bg="white", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=4)
        self.var_idade = tk.StringVar()
        self.ent_idade = ttk.Entry(lf_id, textvariable=self.var_idade, state="readonly", font=("Segoe UI", 10))
        self.ent_idade.grid(row=2, column=1, sticky="ew", pady=4, padx=6)

        tk.Label(lf_id, text="Data da Observação *:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=2, column=2, sticky="w", pady=4)
        self.ent_data_obs = ttk.Entry(lf_id, font=("Segoe UI", 10))
        self.ent_data_obs.insert(0, date.today().strftime("%d/%m/%Y"))
        self.ent_data_obs.grid(row=2, column=3, sticky="ew", pady=4, padx=6)

        tk.Label(lf_id, text="Terapeuta Responsável:", bg="white", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", pady=4)
        self.var_terapeuta = tk.StringVar(value=self.profissional)
        self.ent_terapeuta = ttk.Entry(lf_id, textvariable=self.var_terapeuta, state="readonly", font=("Segoe UI", 10))
        self.ent_terapeuta.grid(row=3, column=1, columnspan=3, sticky="ew", pady=4, padx=6)

        tk.Label(lf_id, text="Hipótese Diagnóstica:", bg="white", font=("Segoe UI", 9)).grid(row=4, column=0, sticky="nw", pady=4)
        self.txt_hipotese = tk.Text(lf_id, height=6, wrap="word", font=("Segoe UI", 10), bd=1, relief="solid")
        self.txt_hipotese.grid(row=4, column=1, columnspan=3, sticky="ew", pady=4, padx=6)

        # Perguntas com Botões Clicáveis
        for titulo_sec, perguntas in SECOES_ANAMNESE:
            sec_frame = tk.LabelFrame(
                self.scroll_anam, text=f" {titulo_sec.upper()} ",
                font=("Segoe UI", 10, "bold"), bg="white", fg="#0f172a", padx=12, pady=8
            )
            sec_frame.pack(fill="x", pady=8)

            for qid, qtexto, qtipo in perguntas:
                q_box = tk.Frame(sec_frame, bg="white", pady=6)
                q_box.pack(fill="x")

                tk.Label(
                    q_box, text=qtexto, bg="white", fg="#1e293b",
                    font=("Segoe UI", 9, "bold"), wraplength=920, justify="left", anchor="w"
                ).pack(anchor="w", pady=(0, 4))

                if qtipo in ("escala", "nivel", "comp"):
                    opcoes = OPCOES_ESCALA if qtipo == "escala" else (OPCOES_NIVEL if qtipo == "nivel" else OPCOES_COMP)
                    grp = GrupoBotoes(q_box, opcoes, cor_ativa="#0284c7", pad_x=12, pad_y=4)
                    grp.pack(anchor="w")
                    self.botoes_anamnese[qid] = grp
                else:
                    ent = tk.Text(q_box, height=6, wrap="word", font=("Segoe UI", 10), bd=1, relief="solid")
                    ent.pack(fill="x", padx=2)
                    self.botoes_anamnese[qid] = ent

                tk.Frame(sec_frame, bg="#f1f5f9", height=1).pack(fill="x", pady=2)

        # Botão Salvar Anamnese e Iniciar NeuroTrack em sequência
        tk.Button(
            self.scroll_anam,
            text="SALVAR ANAMNESE E INICIAR NEUROTRACK EM SEQUÊNCIA  ➔",
            bg="#0284c7", fg="white", activebackground="#0369a1", activeforeground="white",
            font=("Segoe UI", 11, "bold"), pady=14, cursor="hand2", relief="flat",
            command=self.salvar_anamnese_e_iniciar_neurotrack
        ).pack(fill="x", pady=20)

    def _criar_area_rolavel(self, parent, padx=20, pady=15):
        canvas = tk.Canvas(parent, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="white", padx=padx, pady=pady)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return canvas, inner

    def _on_wheel(self, event):
        try:
            if event.widget.winfo_toplevel() is not self:
                return                      # roda do mouse em outra janela (lista de pacientes)
            if isinstance(event.widget, tk.Text) and event.widget.yview() != (0.0, 1.0):
                return                      # o próprio campo de texto tem barra para rolar
        except (tk.TclError, AttributeError):
            return
        if self.canvas_ativo is not None:
            self.canvas_ativo.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _atualizar_idade(self, data_str):
        self.var_idade.set(calcular_idade(data_str))

    @staticmethod
    def _valor_widget(widget):
        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end-1c").strip()
        return widget.get().strip()

    def salvar_anamnese_e_iniciar_neurotrack(self):
        nome = self.ent_nome.get().strip()
        cpf = re.sub(r"\D", "", self.ent_cpf.get())
        terapeuta = self.ent_terapeuta.get().strip()
        data_obs = self.ent_data_obs.get().strip()

        if not nome or not cpf or not terapeuta:
            messagebox.showwarning("Campos Obrigatórios", "Preencha Nome do Paciente, CPF (mínimo 4 dígitos) e Terapeuta.")
            return
        if len(cpf) < 4:
            messagebox.showwarning("CPF Inválido", "Informe pelo menos os 4 primeiros dígitos do CPF.")
            return

        nasc = self.ent_nasc.valor()
        if self.ent_nasc.tem_digitos() and not nasc:
            messagebox.showwarning("Data de Nascimento", "Complete a data de nascimento (DD/MM/AAAA) ou deixe em branco.")
            return
        if nasc and not calcular_idade(nasc):
            messagebox.showwarning("Data de Nascimento", "Data de nascimento inválida ou no futuro.")
            return

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute("""
                INSERT INTO pacientes_anamnese (
                    nome, cpf, data_nascimento, idade, data_observacao,
                    terapeuta, registro_profissional, hipotese_diagnostica
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nome, cpf, nasc, self.var_idade.get().strip(),
                data_obs, terapeuta, "", self.txt_hipotese.get("1.0", "end-1c").strip()
            ))
            paciente_id = cur.lastrowid

            for qid, widget in self.botoes_anamnese.items():
                val = self._valor_widget(widget)
                if val:
                    conn.execute(
                        "INSERT INTO respostas_anamnese (paciente_id, pergunta_id, resposta) VALUES (?, ?, ?)",
                        (paciente_id, qid, val)
                    )

        # Limpa o formulário de Anamnese
        self.ent_nome.delete(0, tk.END)
        self.ent_cpf.delete(0, tk.END)
        self.ent_nasc.limpar()                      # também zera a idade
        self.txt_hipotese.delete("1.0", tk.END)
        for widget in self.botoes_anamnese.values():
            if isinstance(widget, GrupoBotoes):
                widget.set("")
            elif isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
            else:
                widget.delete(0, tk.END)

        # Carrega automaticamente a criança recém-salva no NeuroTrack em sequência
        self.carregar_paciente_no_neurotrack(paciente_id)
        messagebox.showinfo(
            "Anamnese Salva!",
            f"Anamnese de '{nome}' salva com sucesso!\n\nIniciando o NeuroTrack em sequência para este paciente."
        )

    # --------------------------------------------------------------------------
    # TELA 2: NEUROTRACK (100% com Botões Clicáveis, Sem <select>)
    # --------------------------------------------------------------------------
    def _build_tela_neurotrack(self):
        self.canvas_nt, frame = self._criar_area_rolavel(self.frame_neurotrack, padx=20, pady=14)

        # Banner do Paciente Ativo + Botão para Trocar pela Lista Separada
        pac_bar = tk.Frame(frame, bg="#f0fdfa", bd=1, relief="solid", padx=14, pady=10)
        pac_bar.pack(fill="x", pady=(0, 12))

        self.lbl_paciente_ativo = tk.Label(
            pac_bar,
            text="Nenhum paciente selecionado (Preencha a Anamnese ou abra um paciente na Lista)",
            bg="#f0fdfa", fg="#0f766e", font=("Segoe UI", 11, "bold")
        )
        self.lbl_paciente_ativo.pack(side="left")

        tk.Button(
            pac_bar, text="Trocar / Abrir Outro Paciente da Lista",
            bg="#0d9488", fg="white", font=("Segoe UI", 9, "bold"),
            padx=12, pady=4, cursor="hand2", relief="flat",
            command=self.abrir_janela_lista
        ).pack(side="right")

        # 1. Botões de Meta Ativa em Foco (Goal)
        lf_meta = tk.LabelFrame(
            frame, text=" META ATIVA EM FOCO (CLIQUE NO BOTÃO DA META) ",
            font=("Segoe UI", 9, "bold"), bg="white", fg="#0f172a", padx=10, pady=8
        )
        lf_meta.pack(fill="x", pady=4)
        self.grp_meta = GrupoBotoes(
            lf_meta, METAS_NEUROTRACK, cor_ativa="#0d9488",
            pad_x=10, pad_y=6, permite_desmarcar=False, valor_inicial=METAS_NEUROTRACK[0]
        )
        self.grp_meta.pack(anchor="w")

        # 2. Contadores Touch de Tentativas Clínicas (DTT)
        lf_dtt = tk.LabelFrame(
            frame, text=" REGISTRO DE TENTATIVAS CLÍNICAS (DTT) ",
            font=("Segoe UI", 9, "bold"), bg="white", fg="#0f172a", padx=12, pady=8
        )
        lf_dtt.pack(fill="x", pady=6)
        lf_dtt.columnconfigure(0, weight=1)
        lf_dtt.columnconfigure(1, weight=1)

        # Bloco Independente
        f_ind = tk.Frame(lf_dtt, bg="#ecfdf5", bd=1, relief="solid", padx=12, pady=8)
        f_ind.grid(row=0, column=0, sticky="ew", padx=6)
        tk.Label(f_ind, text="ACERTOS INDEPENDENTES", bg="#ecfdf5", fg="#065f46", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.lbl_indep = tk.Label(f_ind, text="0", bg="#ecfdf5", fg="#047857", font=("Segoe UI", 22, "bold"))
        self.lbl_indep.pack(pady=2)
        bf1 = tk.Frame(f_ind, bg="#ecfdf5")
        bf1.pack(fill="x")
        tk.Button(bf1, text="− 1", font=("Segoe UI", 11, "bold"), width=6, cursor="hand2", command=lambda: self._ajustar_dtt("ind", -1)).pack(side="left", padx=2)
        tk.Button(bf1, text="+ 1 Acerto Independente", bg="#059669", fg="white", font=("Segoe UI", 11, "bold"), cursor="hand2", command=lambda: self._ajustar_dtt("ind", 1)).pack(side="left", fill="x", expand=True, padx=2)

        # Bloco Com Suporte
        f_prm = tk.Frame(lf_dtt, bg="#fffbeb", bd=1, relief="solid", padx=12, pady=8)
        f_prm.grid(row=0, column=1, sticky="ew", padx=6)
        tk.Label(f_prm, text="TENTATIVAS COM SUPORTE / AJUDA", bg="#fffbeb", fg="#92400e", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.lbl_prompt = tk.Label(f_prm, text="0", bg="#fffbeb", fg="#b45309", font=("Segoe UI", 22, "bold"))
        self.lbl_prompt.pack(pady=2)
        bf2 = tk.Frame(f_prm, bg="#fffbeb")
        bf2.pack(fill="x")
        tk.Button(bf2, text="− 1", font=("Segoe UI", 11, "bold"), width=6, cursor="hand2", command=lambda: self._ajustar_dtt("prm", -1)).pack(side="left", padx=2)
        tk.Button(bf2, text="+ 1 Com Ajuda", bg="#d97706", fg="white", font=("Segoe UI", 11, "bold"), cursor="hand2", command=lambda: self._ajustar_dtt("prm", 1)).pack(side="left", fill="x", expand=True, padx=2)

        self.lbl_taxa = tk.Label(
            lf_dtt, text="Taxa de Independência: 0% (0 tentativas) — Sem registros",
            bg="white", fg="#334155", font=("Segoe UI", 10, "bold"), pady=6
        )
        self.lbl_taxa.grid(row=1, column=0, columnspan=2)

        # 3. Botões de Nível de Suporte (Prompt) e Regulação Sensorial
        lf_botoes = tk.LabelFrame(
            frame, text=" NÍVEL DE SUPORTE, REGULAÇÃO SENSORIAL E TEMPO DE ATENÇÃO ",
            font=("Segoe UI", 9, "bold"), bg="white", fg="#0f172a", padx=12, pady=8
        )
        lf_botoes.pack(fill="x", pady=6)

        row_sup = tk.Frame(lf_botoes, bg="white", pady=3)
        row_sup.pack(fill="x")
        tk.Label(row_sup, text="Nível de Suporte (Prompt):", bg="white", font=("Segoe UI", 9, "bold"), width=24, anchor="w").pack(side="left")
        self.grp_suporte = GrupoBotoes(
            row_sup, SUPORTES_NEUROTRACK, cor_ativa="#0284c7",
            pad_x=12, pad_y=4, permite_desmarcar=False, valor_inicial=SUPORTES_NEUROTRACK[0]
        )
        self.grp_suporte.pack(side="left")

        row_reg = tk.Frame(lf_botoes, bg="white", pady=3)
        row_reg.pack(fill="x")
        tk.Label(row_reg, text="Regulação Sensorial:", bg="white", font=("Segoe UI", 9, "bold"), width=24, anchor="w").pack(side="left")
        self.grp_regulacao = GrupoBotoes(
            row_reg, REGULACAO_NEUROTRACK, cor_ativa="#0d9488",
            pad_x=12, pad_y=4, permite_desmarcar=False, valor_inicial=REGULACAO_NEUROTRACK[0]
        )
        self.grp_regulacao.pack(side="left")

        row_att = tk.Frame(lf_botoes, bg="white", pady=4)
        row_att.pack(fill="x")
        tk.Label(row_att, text="Tempo de Atenção Sustentada:", bg="white", font=("Segoe UI", 9, "bold"), width=24, anchor="w").pack(side="left")
        tk.Button(row_att, text="− 1 min", font=("Segoe UI", 9, "bold"), padx=8, cursor="hand2", command=lambda: self._ajustar_atencao(-1)).pack(side="left", padx=3)
        self.lbl_atencao = tk.Label(row_att, text="10 min", bg="#f1f5f9", fg="#0f172a", font=("Segoe UI", 11, "bold"), width=10, pady=3)
        self.lbl_atencao.pack(side="left", padx=4)
        tk.Button(row_att, text="+ 1 min", font=("Segoe UI", 9, "bold"), padx=8, cursor="hand2", command=lambda: self._ajustar_atencao(1)).pack(side="left", padx=3)
        tk.Button(row_att, text="+ 5 min", font=("Segoe UI", 9, "bold"), padx=8, cursor="hand2", command=lambda: self._ajustar_atencao(5)).pack(side="left", padx=3)

        # 4. Observações Qualitativas
        tk.Label(frame, text="Observações Qualitativas e Estratégias:", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 2))
        self.txt_obs_nt = tk.Text(frame, height=6, wrap="word", font=("Segoe UI", 10), bd=1, relief="solid")
        self.txt_obs_nt.pack(fill="x", pady=2)

        # Botão Finalizar Sessão e Abrir Lista de Pacientes
        tk.Button(
            frame,
            text="SALVAR NEUROTRACK JUNTO COM O PACIENTE E ABRIR LISTA  ➔",
            bg="#0d9488", fg="white", activebackground="#0f766e", activeforeground="white",
            font=("Segoe UI", 11, "bold"), pady=12, cursor="hand2", relief="flat",
            command=self.salvar_sessao_neurotrack
        ).pack(fill="x", pady=10)

    def paciente_excluido(self, ids):
        if self.paciente_atual_id in ids:
            self.paciente_atual_id = None
            self.paciente_atual_nome = ""
            self.paciente_atual_cpf4 = ""
            self.lbl_paciente_ativo.config(
                text="Nenhum paciente selecionado (Preencha a Anamnese ou abra um paciente na Lista)"
            )

    def carregar_paciente_no_neurotrack(self, paciente_id):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            pac = conn.execute("SELECT * FROM pacientes_anamnese WHERE id = ?", (paciente_id,)).fetchone()
            if not pac:
                return
            self.paciente_atual_id = pac["id"]
            self.paciente_atual_nome = pac["nome"]
            self.paciente_atual_cpf4 = formatar_cpf_4_digitos(pac["cpf"])

        self.lbl_paciente_ativo.config(
            text=f"Paciente Ativo: {self.paciente_atual_nome}   |   CPF: {self.paciente_atual_cpf4}"
        )
        self.mostrar_tela_neurotrack()

    def carregar_paciente_na_nova_anamnese(self, paciente_id):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            pac = conn.execute("SELECT * FROM pacientes_anamnese WHERE id = ?", (paciente_id,)).fetchone()
            if not pac:
                return

        # Preenche os dados de identificação da criança para manter o mesmo CPF na comparação
        self.ent_nome.delete(0, tk.END)
        self.ent_nome.insert(0, pac["nome"] or "")

        self.ent_cpf.delete(0, tk.END)
        self.ent_cpf.insert(0, pac["cpf"] or "")

        self.ent_nasc.definir(pac["data_nascimento"] or "")
        if not self.var_idade.get() and pac["idade"]:
            self.var_idade.set(pac["idade"])

        self.ent_data_obs.delete(0, tk.END)
        self.ent_data_obs.insert(0, date.today().strftime("%d/%m/%Y"))

        self.txt_hipotese.delete("1.0", tk.END)
        if pac["hipotese_diagnostica"]:
            self.txt_hipotese.insert("1.0", pac["hipotese_diagnostica"])

        # Zera todas as respostas para o preenchimento da nova anamnese
        for widget in self.botoes_anamnese.values():
            if isinstance(widget, GrupoBotoes):
                widget.set("")
            elif isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
            else:
                widget.delete(0, tk.END)

        self.mostrar_tela_anamnese()
        self.canvas_anam.yview_moveto(0)

    def _ajustar_dtt(self, tipo, delta):
        if tipo == "ind":
            self.indep_count = max(0, self.indep_count + delta)
            self.lbl_indep.config(text=str(self.indep_count))
        else:
            self.prompt_count = max(0, self.prompt_count + delta)
            self.lbl_prompt.config(text=str(self.prompt_count))

        total = self.indep_count + self.prompt_count
        if total == 0:
            self.lbl_taxa.config(text="Taxa de Independência: 0% (0 tentativas) — Sem registros", fg="#334155")
        else:
            pct = round((self.indep_count / total) * 100)
            status = "Critério de Domínio Atingido (≥80%)" if pct >= 80 else (
                "Habilidade em Aquisição (50-79%)" if pct >= 50 else "Fase Inicial / Alto Suporte (<50%)"
            )
            cor = "#059669" if pct >= 80 else ("#d97706" if pct >= 50 else "#0284c7")
            self.lbl_taxa.config(text=f"Taxa de Independência: {pct}% ({total} tentativas) — {status}", fg=cor)

    def _ajustar_atencao(self, delta):
        self.attention_min = max(1, self.attention_min + delta)
        self.lbl_atencao.config(text=f"{self.attention_min} min")

    def salvar_sessao_neurotrack(self):
        if not self.paciente_atual_id:
            messagebox.showwarning(
                "Paciente Não Selecionado",
                "Preencha uma Anamnese primeiro ou clique em 'Abrir Lista de Pacientes Registrados' para escolher um paciente."
            )
            return

        total = self.indep_count + self.prompt_count
        pct = round((self.indep_count / total) * 100) if total > 0 else 0
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO sessoes_neurotrack (
                    paciente_id, data_hora, meta, acertos_indep, tentativas_ajuda,
                    taxa_independencia, nivel_suporte, regulacao_sensorial, tempo_atencao, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.paciente_atual_id, agora, self.grp_meta.get(),
                self.indep_count, self.prompt_count, pct,
                self.grp_suporte.get(), self.grp_regulacao.get(),
                self.attention_min, self.txt_obs_nt.get("1.0", tk.END).strip()
            ))

        # Reseta os contadores para a próxima sessão
        self.indep_count = 0
        self.prompt_count = 0
        self.attention_min = 10
        self.lbl_indep.config(text="0")
        self.lbl_prompt.config(text="0")
        self.lbl_atencao.config(text="10 min")
        self._ajustar_dtt("ind", 0)
        self.txt_obs_nt.delete("1.0", tk.END)

        messagebox.showinfo(
            "Sessão Salva!",
            f"Sessão do NeuroTrack salva junto ao paciente '{self.paciente_atual_nome}'.\n\nAbrindo a Lista de Pacientes para impressão!"
        )
        self.abrir_janela_lista()


if __name__ == "__main__":
    init_db()
    login = TelaLogin()
    login.mainloop()
    if login.profissional:
        app = NeuroTrackApp(login.profissional)
        app.mainloop()