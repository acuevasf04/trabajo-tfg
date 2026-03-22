#!/usr/bin/env python3
"""
SYSMON — Monitor de Sistema con SSH
Tkinter app con menú de servidores, conexión SSH y ejecución de monitoreo.sh
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import threading
import queue
import os
import json
import signal
from datetime import datetime
from pathlib import Path

# Paleta
BG       = "#0d1117"
SURFACE  = "#161b22"
SURFACE2 = "#1c2128"
BORDER   = "#21262d"
ACCENT   = "#00ff88"
ACCENT_D = "#00cc6a"
TEXT     = "#c9d1d9"
TEXT_DIM = "#6e7681"
ERROR    = "#ff4757"
WARN     = "#ffa502"
INFO     = "#58a6ff"
SUCCESS  = "#3fb950"

FONT     = ("Courier New", 9)
FONT_B   = ("Courier New", 9,  "bold")
FONT_LG  = ("Courier New", 11, "bold")
FONT_XL  = ("Courier New", 14, "bold")

SERVERS_FILE = Path.home() / ".sysmon_servers.json"


# Persistencia

def load_servers():
    if SERVERS_FILE.exists():
        try:
            return json.loads(SERVERS_FILE.read_text())
        except Exception:
            pass
    return []


def save_servers(servers):
    SERVERS_FILE.write_text(json.dumps(servers, indent=2))


# Diálogo Agregar / Editar Servidor

class ServerDialog(tk.Toplevel):
    def __init__(self, parent, server=None):
        super().__init__(parent)
        self.result = None
        self.title("Agregar servidor" if server is None else "Editar servidor")
        self.configure(bg=SURFACE)
        self.resizable(False, False)
        self.grab_set()

        pad = dict(padx=16, pady=6)

        # Título
        tk.Label(self, text="── CONFIGURAR SERVIDOR ──",
                 font=FONT_B, fg=ACCENT, bg=SURFACE).pack(pady=(16, 4))

        fields_frame = tk.Frame(self, bg=SURFACE)
        fields_frame.pack(fill=tk.X, padx=20, pady=8)

        def field(label, default="", show=None):
            tk.Label(fields_frame, text=label, font=("Courier New", 7, "bold"),
                     fg=TEXT_DIM, bg=SURFACE, anchor=tk.W).pack(fill=tk.X)
            var = tk.StringVar(value=default)
            kw = dict(textvariable=var, font=FONT, bg=BG, fg=TEXT,
                      insertbackground=ACCENT, relief=tk.FLAT, bd=0,
                      highlightthickness=1, highlightbackground=BORDER,
                      highlightcolor=ACCENT)
            if show:
                kw["show"] = show
            e = tk.Entry(fields_frame, **kw)
            e.pack(fill=tk.X, ipady=6, ipadx=8, pady=(0, 10))
            return var

        s = server or {}
        self.v_name     = field("NOMBRE / ALIAS",   s.get("name", ""))
        self.v_host     = field("HOST / IP",         s.get("host", ""))
        self.v_port     = field("PUERTO",            s.get("port", "22"))
        self.v_user     = field("USUARIO",           s.get("user", ""))
        self.v_password = field("CONTRASEÑA (opc.)", s.get("password", ""), show="•")
        self.v_key      = field("CLAVE SSH (ruta)",  s.get("key", ""))
        self.v_script   = field("SCRIPT REMOTO",     s.get("script", "~/monitoreo.sh"))

        # Botones
        btn_row = tk.Frame(self, bg=SURFACE)
        btn_row.pack(fill=tk.X, padx=20, pady=(0, 16))

        tk.Button(btn_row, text="CANCELAR", font=FONT_B,
                  bg=BORDER, fg=TEXT, relief=tk.FLAT, bd=0,
                  activebackground=ERROR, activeforeground="#fff",
                  cursor="hand2", padx=16, pady=6,
                  command=self.destroy).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Button(btn_row, text="GUARDAR", font=FONT_B,
                  bg=ACCENT, fg=BG, relief=tk.FLAT, bd=0,
                  activebackground=ACCENT_D, activeforeground=BG,
                  cursor="hand2", padx=16, pady=6,
                  command=self._save).pack(side=tk.RIGHT)

        self._center(parent)

    def _save(self):
        host = self.v_host.get().strip()
        user = self.v_user.get().strip()
        if not host or not user:
            messagebox.showwarning("Campos requeridos",
                                   "Host y Usuario son obligatorios.", parent=self)
            return
        self.result = {
            "name":     self.v_name.get().strip() or host,
            "host":     host,
            "port":     self.v_port.get().strip() or "22",
            "user":     user,
            "password": self.v_password.get(),
            "key":      self.v_key.get().strip(),
            "script":   self.v_script.get().strip() or "~/monitoreo.sh",
            "status":   "disconnected",
        }
        self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


# Aplicación Principal

class SysmonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SYSMON — Monitor SSH")
        self.geometry("1100x720")
        self.minsize(800, 560)
        self.configure(bg=BG)

        self._servers   = load_servers()
        self._active    = None        # servidor seleccionado
        self._process   = None
        self._q         = queue.Queue()
        self._line_count = 0

        self._build_menu()
        self._build_ui()
        self._poll_queue()
        self._refresh_list()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # Menú nativo

    def _build_menu(self):
        menubar = tk.Menu(self, bg=SURFACE, fg=TEXT,
                          activebackground=ACCENT, activeforeground=BG,
                          relief=tk.FLAT, bd=0)

        # Servidores
        m_srv = tk.Menu(menubar, tearoff=0, bg=SURFACE, fg=TEXT,
                        activebackground=ACCENT, activeforeground=BG)
        m_srv.add_command(label="➕  Agregar servidor",   command=self._add_server)
        m_srv.add_command(label="✏️   Editar servidor",    command=self._edit_server)
        m_srv.add_command(label="🗑️   Eliminar servidor",  command=self._delete_server)
        m_srv.add_separator()
        m_srv.add_command(label="🔌  Conectar",           command=self._connect)
        m_srv.add_command(label="⏏️   Desconectar",        command=self._disconnect)
        m_srv.add_separator()
        m_srv.add_command(label="❌  Salir",              command=self._on_close)
        menubar.add_cascade(label="Servidores", menu=m_srv)

        # Acciones
        m_act = tk.Menu(menubar, tearoff=0, bg=SURFACE, fg=TEXT,
                        activebackground=ACCENT, activeforeground=BG)
        m_act.add_command(label="▶  Ejecutar monitoreo.sh", command=self._run_script)
        m_act.add_command(label="■  Detener ejecución",     command=self._stop_script)
        m_act.add_separator()
        m_act.add_command(label="🧹  Limpiar terminal",      command=self._clear_terminal)
        menubar.add_cascade(label="Acciones", menu=m_act)

        # Ayuda
        m_help = tk.Menu(menubar, tearoff=0, bg=SURFACE, fg=TEXT,
                         activebackground=ACCENT, activeforeground=BG)
        m_help.add_command(label="ℹ️   Acerca de", command=self._about)
        menubar.add_cascade(label="Ayuda", menu=m_help)

        self.config(menu=menubar)

    # UI

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, height=52)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⬡ SYSMON", font=("Courier New", 15, "bold"),
                 fg=ACCENT, bg=SURFACE).pack(side=tk.LEFT, padx=18, pady=10)
        tk.Label(hdr, text="// SSH Monitor v3.0",
                 font=FONT, fg=TEXT_DIM, bg=SURFACE).pack(side=tk.LEFT)

        self._hdr_conn = tk.Label(hdr, text="SIN CONEXIÓN",
                                   font=FONT_B, fg=TEXT_DIM, bg=SURFACE)
        self._hdr_conn.pack(side=tk.RIGHT, padx=18)
        self._hdr_dot = tk.Label(hdr, text="●", font=("Courier New", 13),
                                  fg=TEXT_DIM, bg=SURFACE)
        self._hdr_dot.pack(side=tk.RIGHT, padx=(0, 4))

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        # Layout principal: sidebar + contenido
        body = tk.Frame(self, bg=BG)
        body.pack(fill=tk.BOTH, expand=True)

        self._build_sidebar(body)

        # Divisor vertical
        tk.Frame(body, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)

        self._build_content(body)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=SURFACE, width=230)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Título sidebar
        sh = tk.Frame(sidebar, bg=SURFACE2, pady=8)
        sh.pack(fill=tk.X)
        tk.Label(sh, text="SERVIDORES", font=("Courier New", 7, "bold"),
                 fg=TEXT_DIM, bg=SURFACE2).pack(side=tk.LEFT, padx=12)
        tk.Button(sh, text="+", font=FONT_B, bg=ACCENT, fg=BG,
                  relief=tk.FLAT, bd=0, cursor="hand2",
                  activebackground=ACCENT_D, activeforeground=BG,
                  padx=8, pady=0,
                  command=self._add_server).pack(side=tk.RIGHT, padx=8)

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill=tk.X)

        # Lista de servidores
        list_frame = tk.Frame(sidebar, bg=SURFACE)
        list_frame.pack(fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(list_frame, bg=BORDER, troughcolor=SURFACE)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._srv_list = tk.Listbox(list_frame,
                                     font=FONT,
                                     bg=SURFACE, fg=TEXT,
                                     selectbackground=ACCENT,
                                     selectforeground=BG,
                                     relief=tk.FLAT, bd=0,
                                     activestyle="none",
                                     highlightthickness=0,
                                     yscrollcommand=sb.set)
        self._srv_list.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self._srv_list.yview)
        self._srv_list.bind("<<ListboxSelect>>", self._on_select)
        self._srv_list.bind("<Double-Button-1>", lambda e: self._connect())

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill=tk.X)

        # Botones rápidos
        btns = tk.Frame(sidebar, bg=SURFACE, pady=8)
        btns.pack(fill=tk.X)

        def sb_btn(text, fg, cmd):
            tk.Button(btns, text=text, font=("Courier New", 8),
                      bg=SURFACE2, fg=fg, relief=tk.FLAT, bd=0,
                      activebackground=BORDER, activeforeground=TEXT,
                      cursor="hand2", pady=5,
                      command=cmd).pack(fill=tk.X, padx=8, pady=2)

        sb_btn("🔌  Conectar",         ACCENT, self._connect)
        sb_btn("✏️   Editar",           INFO,   self._edit_server)
        sb_btn("🗑️   Eliminar",         ERROR,  self._delete_server)

        # Info del servidor seleccionado
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill=tk.X)
        self._srv_info = tk.Label(sidebar, text="Selecciona un servidor",
                                   font=("Courier New", 7), fg=TEXT_DIM,
                                   bg=SURFACE, wraplength=200, justify=tk.LEFT,
                                   padx=10, pady=8)
        self._srv_info.pack(fill=tk.X)

    def _build_content(self, parent):
        content = tk.Frame(parent, bg=BG)
        content.pack(fill=tk.BOTH, expand=True)

        # Panel de control SSH
        ctrl = tk.Frame(content, bg=SURFACE, padx=16, pady=12)
        ctrl.pack(fill=tk.X)

        # Fila 1
        row1 = tk.Frame(ctrl, bg=SURFACE)
        row1.pack(fill=tk.X, pady=(0, 8))

        # Script remoto
        f1 = tk.Frame(row1, bg=SURFACE)
        f1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        tk.Label(f1, text="SCRIPT REMOTO", font=("Courier New", 7, "bold"),
                 fg=TEXT_DIM, bg=SURFACE).pack(anchor=tk.W)
        self._script_var = tk.StringVar(value="~/monitoreo.sh")
        tk.Entry(f1, textvariable=self._script_var,
                 font=FONT, bg=BG, fg=TEXT, insertbackground=ACCENT,
                 relief=tk.FLAT, bd=0, highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT
                 ).pack(fill=tk.X, ipady=6, ipadx=8)

        # Argumentos
        f2 = tk.Frame(row1, bg=SURFACE)
        f2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        tk.Label(f2, text="ARGUMENTOS", font=("Courier New", 7, "bold"),
                 fg=TEXT_DIM, bg=SURFACE).pack(anchor=tk.W)
        self._args_var = tk.StringVar()
        tk.Entry(f2, textvariable=self._args_var,
                 font=FONT, bg=BG, fg=TEXT, insertbackground=ACCENT,
                 relief=tk.FLAT, bd=0, highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT
                 ).pack(fill=tk.X, ipady=6, ipadx=8)

        # Botones
        btn_f = tk.Frame(row1, bg=SURFACE)
        btn_f.pack(side=tk.LEFT, anchor=tk.S)

        self._run_btn = tk.Button(btn_f, text="▶  EJECUTAR",
                                   font=FONT_B, bg=ACCENT, fg=BG,
                                   relief=tk.FLAT, bd=0,
                                   activebackground=ACCENT_D, activeforeground=BG,
                                   cursor="hand2", padx=18, pady=7,
                                   state=tk.DISABLED,
                                   command=self._run_script)
        self._run_btn.pack(side=tk.LEFT)

        self._stop_btn = tk.Button(btn_f, text="■  STOP",
                                    font=FONT_B, bg=BG, fg=ERROR,
                                    relief=tk.FLAT, bd=0,
                                    highlightthickness=1, highlightbackground=ERROR,
                                    activebackground=ERROR, activeforeground="#fff",
                                    cursor="hand2", padx=14, pady=7,
                                    state=tk.DISABLED,
                                    command=self._stop_script)
        self._stop_btn.pack(side=tk.LEFT, padx=(6, 0))

        self._clear_btn = tk.Button(btn_f, text="🧹",
                                     font=("Courier New", 10),
                                     bg=BORDER, fg=TEXT_DIM,
                                     relief=tk.FLAT, bd=0,
                                     cursor="hand2", padx=10, pady=7,
                                     command=self._clear_terminal)
        self._clear_btn.pack(side=tk.LEFT, padx=(6, 0))

        tk.Frame(content, bg=BORDER, height=1).pack(fill=tk.X)

        # ── Terminal ──
        term_hdr = tk.Frame(content, bg="#0a0c0f", padx=12, pady=7)
        term_hdr.pack(fill=tk.X)
        for c in ("#ff5f57", "#ffbd2e", "#28c840"):
            tk.Label(term_hdr, text="●", fg=c, bg="#0a0c0f",
                     font=("Courier New", 9)).pack(side=tk.LEFT, padx=2)
        self._term_title = tk.Label(term_hdr, text="terminal — sin conexión",
                                     font=FONT, fg=TEXT_DIM, bg="#0a0c0f")
        self._term_title.pack(side=tk.RIGHT)

        term_f = tk.Frame(content, bg=BG)
        term_f.pack(fill=tk.BOTH, expand=True)

        vsb = tk.Scrollbar(term_f, bg=BORDER, troughcolor=BG)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._terminal = tk.Text(term_f, font=FONT,
                                  bg=BG, fg=TEXT,
                                  insertbackground=ACCENT,
                                  relief=tk.FLAT, bd=0,
                                  wrap=tk.WORD, state=tk.DISABLED,
                                  yscrollcommand=vsb.set,
                                  selectbackground=ACCENT, selectforeground=BG,
                                  spacing1=2, spacing3=2, padx=16, pady=12)
        self._terminal.pack(fill=tk.BOTH, expand=True)
        vsb.config(command=self._terminal.yview)

        self._terminal.tag_config("stdout",  foreground=TEXT)
        self._terminal.tag_config("stderr",  foreground=WARN)
        self._terminal.tag_config("error",   foreground=ERROR)
        self._terminal.tag_config("system",  foreground=ACCENT)
        self._terminal.tag_config("info",    foreground=INFO)
        self._terminal.tag_config("ts",      foreground=TEXT_DIM)
        self._terminal.tag_config("bold",    font=FONT_B)

        self._twrite("⬡ SYSMON SSH Monitor listo.\n", "system")
        self._twrite("  Agrega un servidor en el menú o con el botón '+'\n", "info")
        self._twrite("  Haz doble clic en un servidor para conectarte.\n\n", "info")

        # Barra de estado
        tk.Frame(content, bg=BORDER, height=1).pack(fill=tk.X)
        sbar = tk.Frame(content, bg=SURFACE, pady=4)
        sbar.pack(fill=tk.X)

        self._lbl_lines  = tk.Label(sbar, text="LÍNEAS: 0",   font=FONT, fg=TEXT_DIM, bg=SURFACE)
        self._lbl_lines.pack(side=tk.LEFT, padx=14)
        self._lbl_time   = tk.Label(sbar, text="INICIO: —",   font=FONT, fg=TEXT_DIM, bg=SURFACE)
        self._lbl_time.pack(side=tk.LEFT, padx=8)
        self._lbl_state  = tk.Label(sbar, text="ESTADO: INACTIVO", font=FONT, fg=TEXT_DIM, bg=SURFACE)
        self._lbl_state.pack(side=tk.RIGHT, padx=14)

    # Lista de servidores

    def _refresh_list(self):
        self._srv_list.delete(0, tk.END)
        for s in self._servers:
            icon = "🟢" if s.get("status") == "connected" else "⚫"
            self._srv_list.insert(tk.END, f"  {icon}  {s['name']}")
        self._on_select()

    def _on_select(self, _=None):
        idx = self._get_selected_idx()
        if idx is None:
            return
        s = self._servers[idx]
        self._srv_info.config(
            text=f"Host:    {s['host']}:{s['port']}\n"
                 f"Usuario: {s['user']}\n"
                 f"Script:  {s['script']}"
        )

    def _get_selected_idx(self):
        sel = self._srv_list.curselection()
        return sel[0] if sel else None

    # CRUD Servidores

    def _add_server(self):
        dlg = ServerDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self._servers.append(dlg.result)
            save_servers(self._servers)
            self._refresh_list()
            self._twrite(f"✓ Servidor '{dlg.result['name']}' agregado.\n", "system")

    def _edit_server(self):
        idx = self._get_selected_idx()
        if idx is None:
            messagebox.showinfo("Seleccionar", "Selecciona un servidor primero.")
            return
        dlg = ServerDialog(self, self._servers[idx])
        self.wait_window(dlg)
        if dlg.result:
            dlg.result["status"] = self._servers[idx].get("status", "disconnected")
            self._servers[idx] = dlg.result
            save_servers(self._servers)
            self._refresh_list()
            self._twrite(f"✓ Servidor '{dlg.result['name']}' actualizado.\n", "system")

    def _delete_server(self):
        idx = self._get_selected_idx()
        if idx is None:
            messagebox.showinfo("Seleccionar", "Selecciona un servidor primero.")
            return
        name = self._servers[idx]["name"]
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{name}'?"):
            self._servers.pop(idx)
            save_servers(self._servers)
            self._refresh_list()
            self._twrite(f"✗ Servidor '{name}' eliminado.\n", "error")
            if self._active and self._active["name"] == name:
                self._active = None
                self._set_connected(False)

    #  Conexión SSH

    def _connect(self):
        idx = self._get_selected_idx()
        if idx is None:
            messagebox.showinfo("Seleccionar", "Selecciona un servidor primero.")
            return
        s = self._servers[idx]
        self._twrite(f"\n── Conectando a {s['user']}@{s['host']}:{s['port']} ──\n", "info")

        # Probar conexión SSH (ssh -q exit)
        threading.Thread(target=self._test_ssh,
                         args=(s, idx), daemon=True).start()

    def _test_ssh(self, s, idx):
        cmd = self._build_ssh_cmd(s, extra=["-o", "ConnectTimeout=8",
                                             "-o", "BatchMode=yes",
                                             "exit"])
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=12)
            ok = r.returncode == 0
        except Exception as e:
            ok = False

        def update():
            if ok:
                self._servers[idx]["status"] = "connected"
                self._active = self._servers[idx]
                save_servers(self._servers)
                self._refresh_list()
                self._set_connected(True, s)
                self._script_var.set(s.get("script", "~/monitoreo.sh"))
                self._twrite(f"✓ Conectado a {s['name']}  ({s['host']})\n", "system")
            else:
                self._twrite(f"✗ No se pudo conectar a {s['host']}. "
                             f"Verifica host, usuario y clave SSH.\n", "error")
                self._twrite("  Asegúrate de tener acceso sin contraseña (clave pública) "
                             "o usa el campo 'Contraseña'.\n", "info")

        self.after(0, update)

    def _disconnect(self):
        if not self._active:
            return
        name = self._active["name"]
        self._stop_script()
        for s in self._servers:
            if s["name"] == name:
                s["status"] = "disconnected"
        save_servers(self._servers)
        self._active = None
        self._set_connected(False)
        self._refresh_list()
        self._twrite(f"\n⬡ Desconectado de '{name}'.\n", "system")

    def _set_connected(self, connected, server=None):
        if connected and server:
            self._hdr_dot.config(fg=ACCENT)
            self._hdr_conn.config(fg=ACCENT, text=f"{server['user']}@{server['host']}")
            self._term_title.config(text=f"{server['user']}@{server['host']} — SSH")
            self._run_btn.config(state=tk.NORMAL, bg=ACCENT)
            self._lbl_state.config(text="ESTADO: CONECTADO", fg=ACCENT)
        else:
            self._hdr_dot.config(fg=TEXT_DIM)
            self._hdr_conn.config(fg=TEXT_DIM, text="SIN CONEXIÓN")
            self._term_title.config(text="terminal — sin conexión")
            self._run_btn.config(state=tk.DISABLED, bg=TEXT_DIM)
            self._lbl_state.config(text="ESTADO: DESCONECTADO", fg=TEXT_DIM)

    #  SSH Command builder

    def _build_ssh_cmd(self, s, extra=None):
        cmd = ["ssh",
               "-p", s.get("port", "22"),
               "-o", "StrictHostKeyChecking=no"]
        if s.get("key"):
            cmd += ["-i", s["key"]]
        if extra:
            cmd += extra
        cmd.append(f"{s['user']}@{s['host']}")
        return cmd

    # Ejecutar script

    def _run_script(self):
        if not self._active:
            messagebox.showwarning("Sin conexión", "Conecta a un servidor primero.")
            return
        if self._process and self._process.poll() is None:
            return

        script = self._script_var.get().strip() or "~/monitoreo.sh"
        args   = self._args_var.get().strip()
        remote_cmd = f"bash {script} {args}".strip()

        self._clear_terminal()
        self._lbl_time.config(text=f"INICIO: {datetime.now().strftime('%H:%M:%S')}")
        self._line_count = 0
        self._set_exec(True)
        self._twrite(f"$ ssh {self._active['user']}@{self._active['host']} \"{remote_cmd}\"\n\n", "info")

        s = self._active
        ssh_cmd = self._build_ssh_cmd(s, extra=[remote_cmd])
        self._process = None

        threading.Thread(target=self._worker, args=(ssh_cmd,), daemon=True).start()

    def _worker(self, cmd):
        try:
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            self._process = proc
            for line in iter(proc.stdout.readline, ""):
                if line:
                    lw = line.lower()
                    tag = ("error"  if any(w in lw for w in ["error", "fail", "traceback"]) else
                           "stderr" if any(w in lw for w in ["warn", "warning"]) else
                           "stdout")
                    self._q.put((line.rstrip(), tag))
            proc.stdout.close()
            rc = proc.wait()
            self._q.put((f"\n✓ Finalizado — código de salida: {rc}", "system"))
        except FileNotFoundError:
            self._q.put(("✗ 'ssh' no encontrado. Instala OpenSSH.", "error"))
        except Exception as e:
            self._q.put((f"✗ Error: {e}", "error"))
        finally:
            self._q.put(None)

    def _stop_script(self):
        if self._process and self._process.poll() is None:
            try:
                self._process.send_signal(signal.SIGTERM)
                self._twrite("\n⬡ Ejecución detenida (SIGTERM)\n", "system")
            except Exception:
                pass

    #  Terminal helpers

    def _twrite(self, text, tag="stdout"):
        self._terminal.config(state=tk.NORMAL)
        self._terminal.insert(tk.END, text, tag)
        self._terminal.see(tk.END)
        self._terminal.config(state=tk.DISABLED)

    def _clear_terminal(self):
        self._terminal.config(state=tk.NORMAL)
        self._terminal.delete("1.0", tk.END)
        self._terminal.config(state=tk.DISABLED)
        self._line_count = 0
        self._lbl_lines.config(text="LÍNEAS: 0")

    def _poll_queue(self):
        try:
            while True:
                item = self._q.get_nowait()
                if item is None:
                    self._set_exec(False)
                else:
                    line, tag = item
                    ts = datetime.now().strftime("%H:%M:%S")
                    self._twrite(f"[{ts}] ", "ts")
                    self._twrite(f"{line}\n", tag)
                    self._line_count += 1
                    self._lbl_lines.config(text=f"LÍNEAS: {self._line_count}")
        except queue.Empty:
            pass
        self.after(50, self._poll_queue)

    def _set_exec(self, running):
        if running:
            self._run_btn.config(state=tk.DISABLED, bg=TEXT_DIM)
            self._stop_btn.config(state=tk.NORMAL)
            self._lbl_state.config(text="ESTADO: EJECUTANDO", fg=WARN)
        else:
            self._run_btn.config(state=tk.NORMAL if self._active else tk.DISABLED,
                                  bg=ACCENT if self._active else TEXT_DIM)
            self._stop_btn.config(state=tk.DISABLED)
            self._lbl_state.config(
                text="ESTADO: CONECTADO" if self._active else "ESTADO: INACTIVO",
                fg=ACCENT if self._active else TEXT_DIM)

    # Misc 
    def _about(self):
        messagebox.showinfo("SYSMON",
            "SYSMON — SSH Monitor v3.0\n\n"
            "Conecta a servidores SSH y ejecuta\n"
            "scripts de monitoreo remotamente.\n\n"
            "Requiere: ssh (OpenSSH) en el PATH.")

    def _on_close(self):
        self._stop_script()
        self.destroy()


if __name__ == "__main__":
    app = SysmonApp()
    app.mainloop()