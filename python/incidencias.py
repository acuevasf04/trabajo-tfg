#!/usr/bin/env python3
"""
Gestion de Incidencias - AROMARIS
Версия simplificada
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os, json, uuid
from datetime import datetime
from pathlib import Path

# ── Configuracion ──────────────────────────────────────────────────────────
BASE_DIR  = Path(r"C:\aromaris\incidencias")
DATA_FILE = BASE_DIR / "incidencias.json"

ESTADOS = ["Activo", "En curso", "Finalizada"]

COLORES = {
    "Activo":     ("#fff3cd", "#856404"),
    "En curso":   ("#cce5ff", "#004085"),
    "Finalizada": ("#d4edda", "#155724"),
}

# ── Helpers de datos ───────────────────────────────────────────────────────

def cargar():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def guardar(datos):
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")

def guardar_txt(inc):
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    dept = inc["departamento"].replace(" ", "_")
    ruta = BASE_DIR / f"INC-{inc['id'][:8].upper()}_{dept}.txt"
    contenido = (
        f"ID:            {inc['id'][:8].upper()}\n"
        f"Titulo:        {inc['titulo']}\n"
        f"Departamento:  {inc['departamento']}\n"
        f"Estado:        {inc['estado']}\n"
        f"Fecha:         {inc['fecha']}\n"
        f"Actualizado:   {inc['actualizado']}\n"
        f"\nDescripcion:\n{inc['descripcion']}\n"
    )
    ruta.write_text(contenido, encoding="utf-8")
    return ruta

# ── Ventana principal ──────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestion de Incidencias")
        self.geometry("800x520")
        self.resizable(True, True)
        self.configure(bg="#f5f5f5")

        self._datos = cargar()
        self._construir()
        self._actualizar_lista()

    def _construir(self):
        FONT = ("Segoe UI", 9)
        FONT_B = ("Segoe UI", 9, "bold")

        # ── Barra superior ──
        top = tk.Frame(self, bg="#2d3142", pady=10, padx=16)
        top.pack(fill=tk.X)
        tk.Label(top, text="Incidencias AROMARIS", font=("Segoe UI", 12, "bold"),
                 fg="white", bg="#2d3142").pack(side=tk.LEFT)
        tk.Label(top, text=str(BASE_DIR), font=("Segoe UI", 8),
                 fg="#aab", bg="#2d3142").pack(side=tk.RIGHT)

        # ── Filtro por departamento ──
        filtro_frame = tk.Frame(self, bg="#e8e8e8", padx=12, pady=8)
        filtro_frame.pack(fill=tk.X)

        tk.Label(filtro_frame, text="Departamento:", font=FONT_B,
                 bg="#e8e8e8").pack(side=tk.LEFT)
        self.v_dept = tk.StringVar()
        self.v_dept.trace_add("write", lambda *_: self._actualizar_lista())
        tk.Entry(filtro_frame, textvariable=self.v_dept, font=FONT,
                 width=20, relief=tk.SOLID, bd=1).pack(side=tk.LEFT, padx=(6, 16))

        tk.Label(filtro_frame, text="Estado:", font=FONT_B,
                 bg="#e8e8e8").pack(side=tk.LEFT)
        self.v_filtro_estado = tk.StringVar(value="Todos")
        self.v_filtro_estado.trace_add("write", lambda *_: self._actualizar_lista())
        cb = ttk.Combobox(filtro_frame, textvariable=self.v_filtro_estado,
                          values=["Todos"] + ESTADOS,
                          state="readonly", width=12, font=FONT)
        cb.pack(side=tk.LEFT, padx=6)

        # ── Tabla ──
        tabla_frame = tk.Frame(self)
        tabla_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        cols = ("id", "titulo", "departamento", "estado", "fecha")
        self.tabla = ttk.Treeview(tabla_frame, columns=cols,
                                   show="headings", height=14)
        anchos = {"id": 80, "titulo": 220, "departamento": 140,
                  "estado": 100, "fecha": 130}
        cabeceras = {"id": "ID", "titulo": "Titulo", "departamento": "Departamento",
                     "estado": "Estado", "fecha": "Fecha"}
        for c in cols:
            self.tabla.heading(c, text=cabeceras[c])
            self.tabla.column(c, width=anchos[c], anchor=tk.CENTER if c in ("id","estado","fecha") else tk.W)

        sb = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla.pack(fill=tk.BOTH, expand=True)

        # Colores por estado
        for estado, (bg, fg) in COLORES.items():
            self.tabla.tag_configure(estado.replace(" ", "_"), background=bg, foreground=fg)

        self.tabla.bind("<Double-Button-1>", lambda _: self._editar())

        # ── Botones ──
        botones = tk.Frame(self, bg="#f5f5f5", pady=8)
        botones.pack(fill=tk.X, padx=12)

        def btn(texto, color, cmd):
            tk.Button(botones, text=texto, font=FONT_B,
                      bg=color, fg="white", relief=tk.FLAT,
                      padx=14, pady=6, cursor="hand2",
                      activebackground=color, command=cmd
                      ).pack(side=tk.LEFT, padx=(0, 6))

        btn("+ Nueva",  "#2d3142", self._nueva)
        btn("Editar",   "#0d6efd", self._editar)
        btn("Eliminar", "#dc3545", self._eliminar)

        # Estado rapido
        tk.Label(botones, text="  Cambiar estado:",
                 font=FONT, bg="#f5f5f5").pack(side=tk.LEFT, padx=(12, 4))
        self.v_cambio = tk.StringVar(value=ESTADOS[0])
        ttk.Combobox(botones, textvariable=self.v_cambio,
                     values=ESTADOS, state="readonly",
                     width=10, font=FONT).pack(side=tk.LEFT)
        tk.Button(botones, text="Aplicar", font=FONT_B,
                  bg="#198754", fg="white", relief=tk.FLAT,
                  padx=10, pady=6, cursor="hand2",
                  command=self._cambiar_estado).pack(side=tk.LEFT, padx=6)

        # Total
        self.lbl_total = tk.Label(botones, text="", font=FONT, bg="#f5f5f5", fg="#888")
        self.lbl_total.pack(side=tk.RIGHT)

    # ── Actualizar tabla ───────────────────────────────────────────────────

    def _actualizar_lista(self):
        self.tabla.delete(*self.tabla.get_children())
        dept    = self.v_dept.get().strip().lower()
        estado  = self.v_filtro_estado.get()
        visibles = 0

        for inc in self._datos:
            if dept and dept not in inc.get("departamento", "").lower():
                continue
            if estado != "Todos" and inc.get("estado") != estado:
                continue
            tag = inc.get("estado", "Activo").replace(" ", "_")
            self.tabla.insert("", tk.END, iid=inc["id"], tags=(tag,), values=(
                inc["id"][:8].upper(),
                inc["titulo"],
                inc["departamento"],
                inc["estado"],
                inc["fecha"],
            ))
            visibles += 1

        self.lbl_total.config(text=f"{visibles} de {len(self._datos)} incidencias")

    # ── CRUD ──────────────────────────────────────────────────────────────

    def _nueva(self):
        dlg = FormularioDialog(self, dept_default=self.v_dept.get().strip())
        self.wait_window(dlg)
        if dlg.resultado:
            self._datos.append(dlg.resultado)
            guardar(self._datos)
            ruta = guardar_txt(dlg.resultado)
            self._actualizar_lista()
            messagebox.showinfo("Guardado", f"Incidencia creada.\nFichero: {ruta}")

    def _editar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecciona una incidencia.")
            return
        inc = next((i for i in self._datos if i["id"] == sel[0]), None)
        if not inc:
            return
        dlg = FormularioDialog(self, inc=inc)
        self.wait_window(dlg)
        if dlg.resultado:
            idx = next(i for i, x in enumerate(self._datos) if x["id"] == sel[0])
            self._datos[idx] = dlg.resultado
            guardar(self._datos)
            guardar_txt(dlg.resultado)
            self._actualizar_lista()

    def _eliminar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecciona una incidencia.")
            return
        inc = next((i for i in self._datos if i["id"] == sel[0]), None)
        if not inc:
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{inc['titulo']}'?"):
            self._datos = [i for i in self._datos if i["id"] != sel[0]]
            guardar(self._datos)
            self._actualizar_lista()

    def _cambiar_estado(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecciona una incidencia.")
            return
        nuevo = self.v_cambio.get()
        for inc in self._datos:
            if inc["id"] == sel[0]:
                inc["estado"]     = nuevo
                inc["actualizado"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                guardar_txt(inc)
                break
        guardar(self._datos)
        self._actualizar_lista()


# ── Formulario nueva / editar ──────────────────────────────────────────────

class FormularioDialog(tk.Toplevel):
    def __init__(self, parent, inc=None, dept_default=""):
        super().__init__(parent)
        self.resultado = None
        self._inc = inc or {}
        self.title("Nueva incidencia" if not inc else "Editar incidencia")
        self.configure(bg="white")
        self.resizable(False, False)
        self.grab_set()

        FONT   = ("Segoe UI", 9)
        FONT_B = ("Segoe UI", 9, "bold")

        f = tk.Frame(self, bg="white", padx=20, pady=16)
        f.pack()

        def campo(etiqueta, var, ancho=38):
            tk.Label(f, text=etiqueta, font=FONT_B, bg="white",
                     anchor=tk.W).pack(fill=tk.X, pady=(8, 2))
            tk.Entry(f, textvariable=var, font=FONT, width=ancho,
                     relief=tk.SOLID, bd=1).pack(fill=tk.X, ipady=5)

        self.v_titulo = tk.StringVar(value=self._inc.get("titulo", ""))
        campo("Titulo *", self.v_titulo)

        self.v_dept = tk.StringVar(value=self._inc.get("departamento", dept_default))
        campo("Departamento *", self.v_dept)

        # Estado
        tk.Label(f, text="Estado", font=FONT_B, bg="white",
                 anchor=tk.W).pack(fill=tk.X, pady=(8, 2))
        self.v_estado = tk.StringVar(value=self._inc.get("estado", "Activo"))
        ttk.Combobox(f, textvariable=self.v_estado,
                     values=ESTADOS, state="readonly",
                     font=FONT, width=36).pack(fill=tk.X, ipady=3)

        # Descripcion
        tk.Label(f, text="Descripcion *", font=FONT_B, bg="white",
                 anchor=tk.W).pack(fill=tk.X, pady=(8, 2))
        self.txt = tk.Text(f, font=FONT, width=40, height=5,
                           relief=tk.SOLID, bd=1, padx=6, pady=6, wrap=tk.WORD)
        self.txt.pack(fill=tk.X)
        if self._inc.get("descripcion"):
            self.txt.insert("1.0", self._inc["descripcion"])

        # Botones
        btns = tk.Frame(f, bg="white")
        btns.pack(fill=tk.X, pady=(14, 0))
        tk.Button(btns, text="Cancelar", font=FONT, bg="#e0e0e0", fg="#333",
                  relief=tk.FLAT, padx=14, pady=6, cursor="hand2",
                  command=self.destroy).pack(side=tk.RIGHT, padx=(6, 0))
        tk.Button(btns, text="Guardar", font=FONT_B, bg="#2d3142", fg="white",
                  relief=tk.FLAT, padx=14, pady=6, cursor="hand2",
                  command=self._guardar).pack(side=tk.RIGHT)

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _guardar(self):
        titulo = self.v_titulo.get().strip()
        dept   = self.v_dept.get().strip()
        desc   = self.txt.get("1.0", tk.END).strip()

        if not titulo or not dept or not desc:
            messagebox.showwarning("Campos requeridos",
                "Titulo, Departamento y Descripcion son obligatorios.", parent=self)
            return

        ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.resultado = {
            "id":           self._inc.get("id", str(uuid.uuid4())),
            "titulo":       titulo,
            "departamento": dept,
            "estado":       self.v_estado.get(),
            "descripcion":  desc,
            "fecha":        self._inc.get("fecha", ahora),
            "actualizado":  ahora,
        }
        self.destroy()


if __name__ == "__main__":
    App().mainloop()