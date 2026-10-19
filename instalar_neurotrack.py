#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador do NeuroTrack Clínico
- Copia o aplicativo para a pasta do usuário (%LOCALAPPDATA%\\NeuroTrack)
- Cria o atalho "NeuroTrack Clínico" na Área de Trabalho
- Preserva o banco de dados (neurotrack_dados.db) se já existir

Coloque este arquivo na mesma pasta de neurotrack_desktop.py (ou neurotrack_desktop.exe)
e execute (duplo clique em instalar_neurotrack.bat).
"""

import os
import shutil
import subprocess
import sys

NOME_APP = "NeuroTrack Clínico"
ARQ_PY = "neurotrack_desktop.py"
ARQ_EXE = "neurotrack_desktop.exe"
ARQ_DB = "neurotrack_dados.db"


def pasta_origem():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def pasta_destino():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "NeuroTrack")
    return os.path.join(os.path.expanduser("~"), ".local", "share", "NeuroTrack")


def _ps(texto):
    """Escapa texto para string entre aspas simples do PowerShell."""
    return "'" + str(texto).replace("'", "''") + "'"


def criar_atalho_windows(alvo, argumentos, pasta_trabalho, icone):
    script = "\n".join([
        "$ErrorActionPreference = 'Stop'",
        "$ws = New-Object -ComObject WScript.Shell",
        "$desktop = [Environment]::GetFolderPath('Desktop')",  # funciona mesmo com OneDrive
        "$lnk = $ws.CreateShortcut((Join-Path $desktop 'NeuroTrack.lnk'))",
        f"$lnk.TargetPath = {_ps(alvo)}",
        f"$lnk.Arguments = {_ps(argumentos)}",
        f"$lnk.WorkingDirectory = {_ps(pasta_trabalho)}",
        f"$lnk.IconLocation = {_ps(icone)}",
        f"$lnk.Description = {_ps(NOME_APP)}",
        "$lnk.Save()",
    ])
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True, text=True, creationflags=0x08000000  # CREATE_NO_WINDOW
    )
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip() or "Falha ao criar o atalho.")


def criar_atalho_linux(comando, pasta_trabalho):
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(desktop):
        desktop = os.path.expanduser("~")
    caminho = os.path.join(desktop, "NeuroTrack.desktop")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(
            "[Desktop Entry]\nType=Application\n"
            f"Name={NOME_APP}\nExec={comando}\nPath={pasta_trabalho}\nTerminal=false\n"
        )
    os.chmod(caminho, 0o755)


def instalar():
    origem, destino = pasta_origem(), pasta_destino()
    usa_exe = os.path.isfile(os.path.join(origem, ARQ_EXE))
    arquivo = ARQ_EXE if usa_exe else ARQ_PY
    if not os.path.isfile(os.path.join(origem, arquivo)):
        raise FileNotFoundError(f"Não encontrei '{ARQ_PY}' (nem '{ARQ_EXE}') na pasta do instalador:\n{origem}")

    os.makedirs(destino, exist_ok=True)
    shutil.copy2(os.path.join(origem, arquivo), os.path.join(destino, arquivo))

    # Leva o banco atual junto, sem nunca sobrescrever um banco já instalado
    db_origem, db_destino = os.path.join(origem, ARQ_DB), os.path.join(destino, ARQ_DB)
    if os.path.isfile(db_origem) and not os.path.exists(db_destino) and os.path.abspath(origem) != os.path.abspath(destino):
        shutil.copy2(db_origem, db_destino)

    app = os.path.join(destino, arquivo)
    if os.name == "nt":
        if usa_exe:
            criar_atalho_windows(app, "", destino, app)
        else:
            pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")  # sem janela de console
            interpretador = pythonw if os.path.isfile(pythonw) else sys.executable
            criar_atalho_windows(interpretador, f'"{app}"', destino, interpretador)
    else:
        criar_atalho_linux(app if usa_exe else f'"{sys.executable}" "{app}"', destino)
    return destino


def avisar(titulo, mensagem, erro=False):
    try:
        import tkinter as tk
        from tkinter import messagebox
        raiz = tk.Tk()
        raiz.withdraw()
        (messagebox.showerror if erro else messagebox.showinfo)(titulo, mensagem)
        raiz.destroy()
    except Exception:
        print(f"{titulo}: {mensagem}")


if __name__ == "__main__":
    try:
        destino = instalar()
        avisar(
            "Instalação concluída",
            f"{NOME_APP} instalado em:\n{destino}\n\nUm atalho 'NeuroTrack' foi criado na Área de Trabalho."
        )
    except Exception as e:
        avisar("Erro na instalação", str(e), erro=True)
        sys.exit(1)
