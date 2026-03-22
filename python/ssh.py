#!/usr/bin/env python3
"""
Monitor SSH - Version simplificada
Conecta a servidores SSH y ejecuta monitoreo.sh
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import queue
import json
import signal
from datetime import datetime
from pathlib import Path

SERVIDORES_FILE = Path.home() / ".monitor_servidores.json"
FONT = ("Courier New", 9)
FONT_B = ("Courier New", 9, "bold")


# ── Persistencia ──────────────────────────────────────────────────────────────

def cargar_servidores():
    if SERVIDORES_FILE.exists():
        try:
            return json.loads(SERVIDORES_FILE.read_text())
        except Exception:
            pass
    return []

def guardar_servidores(servidores):
    SERVIDORES_FILE.write_text(json.dumps(servidores, indent=2))


# ── Formulario de servidor ────────────────────────────────────────────────────

class FormularioServidor(tk.Toplevel):
    def __init__(self, parent, servidor=None):
        super().__init__(parent)
        self.resultado = None
        s = servidor or {}
        self.title("Servidor" if not servidor else "Editar servidor")
        self.configure(bg="white")
        self.resizable(False, False)
        self.grab_set()

        f = tk.Frame(self, bg="white", padx=20, pady=16)
        f.pack()

        FONT_L = ("Segoe UI", 9, "bold")
        FONT_E = ("Segoe UI", 9)

        def campo(etiqueta, valor="", show=None):
            tk.Label(f, text=etiqueta, font=FONT_L, bg="white",
                     anchor=tk.W).pack(fill=tk.X, pady=(8, 2))
            var = tk.StringVar(value=valor)
            kw = dict(textvariable=var, font=FONT_E, width=30,
                      relief=tk.SOLID, bd=1)
            if show:
                kw["show"] = show
            tk.Entry(f, **kw).pack(fill=tk.X, ipady=5)
            return var

        self.v_nombre = campo("Nombre / Alias",       s.get("nombre", ""))
        self.v_host   = campo("Host / IP *",           s.get("host",   ""))
        self.v_puerto = campo("Puerto",                s.get("puerto", "22"))
        self.v_usuario= campo("Usuario *",             s.get("usuario",""))
        self.v_clave  = campo("Clave SSH (ruta opc.)", s.get("clave",  ""))
        self.v_script = campo("Script remoto",         s.get("script", "~/monitoreo.sh"))

        btns = tk.Frame(f, bg="white")
        btns.pack(fill=tk.X, pady=(14, 0))
        tk.Button(btns, text="Cancelar", font=FONT_E, bg="#e0e0e0",
                  relief=tk.FLAT, padx=12, pady=6, cursor="hand2",
                  command=self.destroy).pack(side=tk.RIGHT, padx=(6, 0))
        tk.Button(btns, text="Guardar", font=FONT_L, bg="#2d3142", fg="white",
                  relief=tk.FLAT, padx=12, pady=6, cursor="hand2",
                  command=self._guardar).pack(side=tk.RIGHT)

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _guardar(self):
        host    = self.v_host.get().strip()
        usuario = self.v_usuario.get().strip()
        if not host or not usuario:
            messagebox.showwarning("Requerido", "Host y Usuario son obligatorios.", parent=self)
            return
        self.resultado = {
            "nombre":  self.v_nombre.get().strip() or host,
            "host":    host,
            "puerto":  self.v_puerto.get().strip() or "22",
            "usuario": usuario,
            "clave":   self.v_clave.get().strip(),
            "script":  self.v_script.get().strip() or "~/monitoreo.sh",
        }
        self.destroy()


# ── Aplicacion principal ──────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor SSH")
        self.geometry("860x580")
        self.configure(bg="#f5f5f5")

        self._servidores  = cargar_servidores()
        self._conectado   = None
        self._proceso     = None
        self._cola        = queue.Queue()
        self._lineas      = 0

        self._construir()
        self._refrescar_lista()
        self._leer_cola()

        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _construir(self):
        # ── Panel izquierdo: lista de servidores ──
        izq = tk.Frame(self, bg="#2d3142", width=200)
        izq.pack(side=tk.LEFT, fill=tk.Y)
        izq.pack_propagate(False)

        tk.Label(izq, text="Servidores", font=("Segoe UI", 10, "bold"),
                 fg="white", bg="#2d3142").pack(pady=(12, 6))

        tk.Frame(izq, bg="#444", height=1).pack(fill=tk.X, padx=8)

        # Lista
        self.lista = tk.Listbox(izq, font=("Segoe UI", 9),
                                 bg="#1e2430", fg="#c9d1d9",
                                 selectbackground="#00ff88",
                                 selectforeground="#000",
                                 relief=tk.FLAT, bd=0,
                                 highlightthickness=0,
                                 activestyle="none")
        self.lista.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.lista.bind("<Double-Button-1>", lambda _: self._conectar())

        tk.Frame(izq, bg="#444", height=1).pack(fill=tk.X, padx=8)

        # Botones de lista
        for texto, cmd in [("+ Agregar", self._agregar),
                            ("Editar",   self._editar),
                            ("Eliminar", self._eliminar)]:
            tk.Button(izq, text=texto, font=("Segoe UI", 8),
                      bg="#1e2430", fg="#c9d1d9",
                      relief=tk.FLAT, bd=0, pady=6, cursor="hand2",
                      activebackground="#2d3748", activeforeground="white",
                      command=cmd).pack(fill=tk.X, padx=4, pady=1)

        # ── Panel derecho: terminal ──
        der = tk.Frame(self, bg="#f5f5f5")
        der.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Barra de conexion
        barra = tk.Frame(der, bg="#e8e8e8", padx=10, pady=8)
        barra.pack(fill=tk.X)

        self.lbl_conexion = tk.Label(barra, text="Sin conexion",
                                      font=("Segoe UI", 9, "bold"),
                                      fg="#888", bg="#e8e8e8")
        self.lbl_conexion.pack(side=tk.LEFT)

        self.btn_stop = tk.Button(barra, text="Detener", font=("Segoe UI", 8),
                                   bg="#dc3545", fg="white", relief=tk.FLAT,
                                   padx=10, pady=4, cursor="hand2",
                                   state=tk.DISABLED, command=self._detener)
        self.btn_stop.pack(side=tk.RIGHT, padx=(6, 0))

        self.btn_run = tk.Button(barra, text="▶ Ejecutar monitoreo.sh",
                                  font=("Segoe UI", 8, "bold"),
                                  bg="#198754", fg="white", relief=tk.FLAT,
                                  padx=10, pady=4, cursor="hand2",
                                  state=tk.DISABLED, command=self._ejecutar)
        self.btn_run.pack(side=tk.RIGHT, padx=(6, 0))

        tk.Label(barra, text="Script:", font=("Segoe UI", 8),
                 bg="#e8e8e8").pack(side=tk.RIGHT, padx=(12, 4))
        self.v_script = tk.StringVar(value="~/monitoreo.sh")
        tk.Entry(barra, textvariable=self.v_script, font=("Segoe UI", 8),
                 width=22, relief=tk.SOLID, bd=1).pack(side=tk.RIGHT)

        # Botón conectar
        self.btn_conectar = tk.Button(barra, text="Conectar",
                                       font=("Segoe UI", 8, "bold"),
                                       bg="#0d6efd", fg="white", relief=tk.FLAT,
                                       padx=10, pady=4, cursor="hand2",
                                       state=tk.DISABLED, command=self._conectar)
        self.btn_conectar.pack(side=tk.RIGHT, padx=(0, 6))

        # Terminal
        term_f = tk.Frame(der, bg="#0d1117")
        term_f.pack(fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(term_f, bg="#21262d", troughcolor="#0d1117")
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.terminal = tk.Text(term_f, font=FONT,
                                 bg="#0d1117", fg="#c9d1d9",
                                 insertbackground="#00ff88",
                                 relief=tk.FLAT, bd=0,
                                 state=tk.DISABLED,
                                 yscrollcommand=sb.set,
                                 padx=12, pady=10, wrap=tk.WORD)
        self.terminal.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.terminal.yview)

        self.terminal.tag_config("ok",     foreground="#00ff88")
        self.terminal.tag_config("error",  foreground="#ff4757")
        self.terminal.tag_config("warn",   foreground="#ffa502")
        self.terminal.tag_config("info",   foreground="#58a6ff")
        self.terminal.tag_config("ts",     foreground="#4a5568")

        # Barra de estado
        tk.Frame(der, bg="#21262d", height=1).pack(fill=tk.X)
        status_f = tk.Frame(der, bg="#161b22", pady=4, padx=10)
        status_f.pack(fill=tk.X)
        self.lbl_lineas = tk.Label(status_f, text="Lineas: 0",
                                    font=("Segoe UI", 7), fg="#4a5568", bg="#161b22")
        self.lbl_lineas.pack(side=tk.LEFT)
        tk.Label(status_f, text="Doble clic en servidor para conectar",
                 font=("Segoe UI", 7), fg="#4a5568", bg="#161b22").pack(side=tk.RIGHT)

        self._escribir("Monitor SSH listo. Agrega un servidor y conectate.\n", "info")

    # ── Lista de servidores ───────────────────────────────────────────────────

    def _refrescar_lista(self):
        self.lista.delete(0, tk.END)
        for s in self._servidores:
            icono = "● " if self._conectado and self._conectado["nombre"] == s["nombre"] else "○ "
            self.lista.insert(tk.END, icono + s["nombre"])

    def _seleccionado_idx(self):
        sel = self.lista.curselection()
        return sel[0] if sel else None

    # ── CRUD servidores ───────────────────────────────────────────────────────

    def _agregar(self):
        dlg = FormularioServidor(self)
        self.wait_window(dlg)
        if dlg.resultado:
            self._servidores.append(dlg.resultado)
            guardar_servidores(self._servidores)
            self._refrescar_lista()

    def _editar(self):
        idx = self._seleccionado_idx()
        if idx is None:
            messagebox.showinfo("Aviso", "Selecciona un servidor.")
            return
        dlg = FormularioServidor(self, self._servidores[idx])
        self.wait_window(dlg)
        if dlg.resultado:
            self._servidores[idx] = dlg.resultado
            guardar_servidores(self._servidores)
            self._refrescar_lista()

    def _eliminar(self):
        idx = self._seleccionado_idx()
        if idx is None:
            messagebox.showinfo("Aviso", "Selecciona un servidor.")
            return
        nombre = self._servidores[idx]["nombre"]
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{nombre}'?"):
            self._servidores.pop(idx)
            guardar_servidores(self._servidores)
            self._refrescar_lista()
            if self._conectado and self._conectado["nombre"] == nombre:
                self._conectado = None
                self._set_conectado(False)

    # ── Conexion SSH ──────────────────────────────────────────────────────────

    def _conectar(self):
        idx = self._seleccionado_idx()
        if idx is None:
            messagebox.showinfo("Aviso", "Selecciona un servidor.")
            return
        s = self._servidores[idx]
        self._escribir(f"\nConectando a {s['usuario']}@{s['host']}...\n", "info")
        threading.Thread(target=self._probar_ssh, args=(s, idx), daemon=True).start()

    def _probar_ssh(self, s, idx):
        cmd = self._cmd_ssh(s) + ["-o", "ConnectTimeout=8",
                                   "-o", "BatchMode=yes", "exit"]
        try:
            ok = subprocess.run(cmd, capture_output=True, timeout=12).returncode == 0
        except Exception:
            ok = False

        def actualizar():
            if ok:
                self._conectado = s
                self.v_script.set(s.get("script", "~/monitoreo.sh"))
                self._set_conectado(True, s)
                self._refrescar_lista()
                self._escribir(f"Conectado a {s['nombre']} ({s['host']})\n", "ok")
            else:
                self._escribir(f"Error: no se pudo conectar a {s['host']}\n", "error")
                self._escribir("Verifica host, usuario y clave SSH.\n", "warn")

        self.after(0, actualizar)

    def _set_conectado(self, conectado, s=None):
        if conectado and s:
            self.lbl_conexion.config(text=f"Conectado: {s['usuario']}@{s['host']}", fg="#00ff88")
            self.btn_run.config(state=tk.NORMAL)
            self.btn_conectar.config(text="Desconectar", bg="#6c757d",
                                      command=self._desconectar)
        else:
            self.lbl_conexion.config(text="Sin conexion", fg="#888")
            self.btn_run.config(state=tk.DISABLED)
            self.btn_conectar.config(text="Conectar", bg="#0d6efd",
                                      command=self._conectar)

    def _desconectar(self):
        self._detener()
        self._conectado = None
        self._set_conectado(False)
        self._refrescar_lista()
        self._escribir("\nDesconectado.\n", "info")

    def _cmd_ssh(self, s):
        cmd = ["ssh", "-p", s.get("puerto", "22"),
               "-o", "StrictHostKeyChecking=no"]
        if s.get("clave"):
            cmd += ["-i", s["clave"]]
        cmd.append(f"{s['usuario']}@{s['host']}")
        return cmd

    # ── Ejecucion del script ──────────────────────────────────────────────────

    def _ejecutar(self):
        if not self._conectado:
            return
        script = self.v_script.get().strip() or "~/monitoreo.sh"
        self._lineas = 0
        self._limpiar_terminal()
        self._escribir(f"$ ssh {self._conectado['usuario']}@{self._conectado['host']} 'bash {script}'\n\n", "ts")

        cmd = self._cmd_ssh(self._conectado) + [f"bash {script}"]
        self._proceso = None
        self.btn_run.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        threading.Thread(target=self._worker, args=(cmd,), daemon=True).start()

    def _worker(self, cmd):
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            self._proceso = proc
            for linea in iter(proc.stdout.readline, ""):
                if linea:
                    lw = linea.lower()
                    tag = ("error" if "error" in lw or "fail" in lw else
                           "warn"  if "warn"  in lw else "")
                    self._cola.put((linea.rstrip(), tag))
            proc.stdout.close()
            rc = proc.wait()
            self._cola.put((f"\nFinalizado — codigo: {rc}", "ok" if rc == 0 else "error"))
        except FileNotFoundError:
            self._cola.put(("Error: 'ssh' no encontrado. Instala OpenSSH.", "error"))
        except Exception as e:
            self._cola.put((f"Error: {e}", "error"))
        finally:
            self._cola.put(None)

    def _detener(self):
        if self._proceso and self._proceso.poll() is None:
            try:
                self._proceso.send_signal(signal.SIGTERM)
            except Exception:
                pass

    # ── Terminal ──────────────────────────────────────────────────────────────

    def _escribir(self, texto, tag=""):
        self.terminal.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self.terminal.insert(tk.END, f"[{ts}] ", "ts")
        self.terminal.insert(tk.END, texto + "\n" if not texto.endswith("\n") else texto, tag or "")
        self.terminal.see(tk.END)
        self.terminal.config(state=tk.DISABLED)

    def _limpiar_terminal(self):
        self.terminal.config(state=tk.NORMAL)
        self.terminal.delete("1.0", tk.END)
        self.terminal.config(state=tk.DISABLED)

    def _leer_cola(self):
        try:
            while True:
                item = self._cola.get_nowait()
                if item is None:
                    self.btn_run.config(state=tk.NORMAL if self._conectado else tk.DISABLED)
                    self.btn_stop.config(state=tk.DISABLED)
                else:
                    linea, tag = item
                    ts = datetime.now().strftime("%H:%M:%S")
                    self.terminal.config(state=tk.NORMAL)
                    self.terminal.insert(tk.END, f"[{ts}] ", "ts")
                    self.terminal.insert(tk.END, linea + "\n", tag or "")
                    self.terminal.see(tk.END)
                    self.terminal.config(state=tk.DISABLED)
                    self._lineas += 1
                    self.lbl_lineas.config(text=f"Lineas: {self._lineas}")
        except queue.Empty:
            pass
        self.after(50, self._leer_cola)

    def _cerrar(self):
        self._detener()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
