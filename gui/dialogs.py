import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog


# ---------------------------------------------------------------------------
# Confirmaciones simples (usan messagebox, son suficientes para sí/no)
# ---------------------------------------------------------------------------

def confirm_overwrite(parent, name: str) -> bool:
    """Pregunta si se desea sobrescribir un archivo/directorio existente."""
    return messagebox.askyesno(
        "Nombre ya existe",
        f"Ya existe '{name}' en este directorio.\n¿Desea sobrescribirlo?",
        parent=parent,
    )


def confirm_recursive_delete(parent, name: str) -> bool:
    """Pregunta si se desea eliminar un directorio no vacío de forma recursiva."""
    return messagebox.askyesno(
        "Directorio no vacío",
        f"'{name}' contiene archivos o subdirectorios.\n"
        f"¿Desea eliminarlo de forma recursiva (todo su contenido)?",
        parent=parent,
    )


def show_error(parent, title: str, message: str) -> None:
    messagebox.showerror(title, message, parent=parent)


def show_info(parent, title: str, message: str) -> None:
    messagebox.showinfo(title, message, parent=parent)


def show_disk_full(parent) -> None:
    messagebox.showerror(
        "Disco lleno",
        "No hay suficientes sectores libres para completar esta operación.",
        parent=parent,
    )


# ---------------------------------------------------------------------------
# Formularios con un solo campo (usan simpledialog)
# ---------------------------------------------------------------------------

def ask_name(parent, title: str, prompt: str) -> str | None:
    """Pide un nombre simple (para MKDIR, CambiarDIR por nombre, FIND, etc.)."""
    return simpledialog.askstring(title, prompt, parent=parent)


# ---------------------------------------------------------------------------
# Formulario de archivo (nombre + contenido) — necesita más de un campo,
# así que se construye con un Toplevel propio.
# ---------------------------------------------------------------------------

class FileFormDialog(tk.Toplevel):
    """
    Diálogo con dos campos: nombre de archivo y contenido.
    Uso:
        dialog = FileFormDialog(parent, title="Crear archivo")
        parent.wait_window(dialog)
        if dialog.result is not None:
            name, content = dialog.result
    """

    def __init__(self, parent, title="Archivo", initial_name="", initial_content=""):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Nombre del archivo:").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.name_var = tk.StringVar(value=initial_name)
        self.name_entry = ttk.Entry(frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(frame, text="Contenido:").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.content_text = tk.Text(frame, width=50, height=12, wrap="word")
        self.content_text.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self.content_text.insert("1.0", initial_content)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(button_frame, text="Cancelar", command=self._cancel).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Aceptar", command=self._accept).pack(side="right")

        self.name_entry.focus_set()
        self.bind("<Escape>", lambda e: self._cancel())

    def _accept(self):
        name = self.name_var.get().strip()
        content = self.content_text.get("1.0", "end-1c")
        if not name:
            show_error(self, "Nombre inválido", "El nombre del archivo no puede estar vacío.")
            return
        self.result = (name, content)
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class MoveDialog(tk.Toplevel):
    """Diálogo con dos campos: ruta origen y ruta destino, para MoVer."""

    def __init__(self, parent, current_path="/"):
        super().__init__(parent)
        self.title("Mover / Renombrar")
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Nombre origen (en directorio actual):").grid(row=0, column=0, sticky="w")
        self.source_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.source_var, width=40).grid(row=1, column=0, pady=(0, 10))

        ttk.Label(frame, text="Ruta/nombre destino:").grid(row=2, column=0, sticky="w")
        self.dest_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.dest_var, width=40).grid(row=3, column=0, pady=(0, 10))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, sticky="e")
        ttk.Button(button_frame, text="Cancelar", command=self._cancel).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Aceptar", command=self._accept).pack(side="right")

        self.bind("<Escape>", lambda e: self._cancel())

    def _accept(self):
        source = self.source_var.get().strip()
        dest = self.dest_var.get().strip()
        if not source or not dest:
            show_error(self, "Datos incompletos", "Debe indicar origen y destino.")
            return
        self.result = (source, dest)
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# ---------------------------------------------------------------------------
# CoPY — diálogo con las 3 variantes (real->virtual, virtual->real,
# virtual->virtual). El resultado siempre es una tupla
# (modo, origen, destino) donde modo es uno de:
#   "real_a_virtual", "virtual_a_real", "virtual_a_virtual"
# ---------------------------------------------------------------------------

class CopyDialog(tk.Toplevel):
    """
    Primero se elige la variante con radiobuttons, y según la elección
    se habilitan los campos correspondientes (algunos usan un selector
    de archivo real de Windows en vez de un Entry de texto).
    """

    MODES = [
        ("real_a_virtual", "De mi computadora (real) → al File System virtual"),
        ("virtual_a_real", "Del File System virtual → a mi computadora (real)"),
        ("virtual_a_virtual", "Dentro del File System virtual (virtual → virtual)"),
    ]

    def __init__(self, parent, current_virtual_path="/"):
        super().__init__(parent)
        self.title("CoPY")
        self.resizable(False, False)
        self.result = None
        self.transient(parent)
        self.grab_set()
        self.current_virtual_path = current_virtual_path

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Tipo de copia:", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )

        self.mode_var = tk.StringVar(value=self.MODES[0][0])
        for i, (value, label) in enumerate(self.MODES):
            ttk.Radiobutton(
                frame, text=label, value=value, variable=self.mode_var,
                command=self._on_mode_change,
            ).grid(row=1 + i, column=0, columnspan=2, sticky="w")

        ttk.Separator(frame, orient="horizontal").grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=10
        )

        # --- Campo de origen ---
        ttk.Label(frame, text="Origen:").grid(row=5, column=0, sticky="w")
        self.source_var = tk.StringVar()
        self.source_entry = ttk.Entry(frame, textvariable=self.source_var, width=40)
        self.source_entry.grid(row=6, column=0, sticky="ew")
        self.source_browse_btn = ttk.Button(frame, text="Elegir...", command=self._browse_source)
        self.source_browse_btn.grid(row=6, column=1, padx=(6, 0))

        # --- Campo de destino ---
        ttk.Label(frame, text="Destino:").grid(row=7, column=0, sticky="w", pady=(8, 0))
        self.dest_var = tk.StringVar()
        self.dest_entry = ttk.Entry(frame, textvariable=self.dest_var, width=40)
        self.dest_entry.grid(row=8, column=0, sticky="ew")
        self.dest_browse_btn = ttk.Button(frame, text="Elegir...", command=self._browse_dest)
        self.dest_browse_btn.grid(row=8, column=1, padx=(6, 0))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=9, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(button_frame, text="Cancelar", command=self._cancel).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Copiar", command=self._accept).pack(side="right")

        self._on_mode_change()
        self.bind("<Escape>", lambda e: self._cancel())

    def _on_mode_change(self):
        mode = self.mode_var.get()

        if mode == "real_a_virtual":
            self.source_var.set("")
            self.dest_var.set(self.current_virtual_path)
            self.source_browse_btn.configure(state="normal")
            self.dest_browse_btn.configure(state="disabled")
        elif mode == "virtual_a_real":
            self.source_var.set("")
            self.dest_var.set("")
            self.source_browse_btn.configure(state="disabled")
            self.dest_browse_btn.configure(state="normal")
        else:  # virtual_a_virtual
            self.source_var.set("")
            self.dest_var.set(self.current_virtual_path)
            self.source_browse_btn.configure(state="disabled")
            self.dest_browse_btn.configure(state="disabled")

    def _browse_source(self):
        path = filedialog.askopenfilename(parent=self, title="Seleccionar archivo real")
        if path:
            self.source_var.set(path)

    def _browse_dest(self):
        path = filedialog.asksaveasfilename(parent=self, title="Guardar como (ruta real)")
        if path:
            self.dest_var.set(path)

    def _accept(self):
        source = self.source_var.get().strip()
        dest = self.dest_var.get().strip()
        if not source or not dest:
            show_error(self, "Datos incompletos", "Debe indicar origen y destino.")
            return
        self.result = (self.mode_var.get(), source, dest)
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# ---------------------------------------------------------------------------
# CREATE — diálogo inicial para crear el disco virtual (sectores + tamaño
# de sector). Se muestra antes de abrir la ventana principal.
# ---------------------------------------------------------------------------

class CreateDiskDialog(tk.Toplevel):
    """
    Pide sector_count y sector_size. result queda como (sector_count,
    sector_size) si el usuario acepta, o None si cancela (en cuyo caso
    el programa debe cerrarse, ya que no hay disco con qué trabajar).
    """

    def __init__(self, parent, default_sector_count=200, default_sector_size=64,
                 disk_already_exists=False):
        super().__init__(parent)
        self.title("CREATE — Crear disco virtual")
        self.resizable(False, False)
        self.result = None
        self.transient(parent)

        frame = ttk.Frame(self, padding=14)
        frame.pack(fill="both", expand=True)

        if disk_already_exists:
            note = (
                "Ya existe un disco virtual guardado de una sesión anterior.\n"
                "Si continúa, se usará el tamaño con el que fue creado "
                "originalmente (los valores de abajo se ignorarán)."
            )
            ttk.Label(frame, text=note, foreground="#555", wraplength=320,
                      justify="left").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(frame, text="Cantidad de sectores:").grid(row=1, column=0, sticky="w")
        self.sector_count_var = tk.StringVar(value=str(default_sector_count))
        ttk.Entry(frame, textvariable=self.sector_count_var, width=15).grid(
            row=1, column=1, sticky="w", padx=(8, 0)
        )

        ttk.Label(frame, text="Tamaño de sector (bytes):").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.sector_size_var = tk.StringVar(value=str(default_sector_size))
        ttk.Entry(frame, textvariable=self.sector_size_var, width=15).grid(
            row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0)
        )

        self.total_label = ttk.Label(frame, text="", foreground="#0a6")
        self.total_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.sector_count_var.trace_add("write", lambda *_: self._update_total())
        self.sector_size_var.trace_add("write", lambda *_: self._update_total())
        self._update_total()

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(button_frame, text="Salir", command=self._cancel).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Crear disco", command=self._accept).pack(side="right")

        self.bind("<Escape>", lambda e: self._cancel())

        # Centrar en la pantalla (no relativo al padre, que puede ser
        # una ventana de 1x1 prácticamente invisible) y asegurar que
        # quede al frente con el foco.
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"+{x}+{y}")

        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()
        self.grab_set()

    def _update_total(self):
        try:
            count = int(self.sector_count_var.get())
            size = int(self.sector_size_var.get())
            self.total_label.configure(text=f"Tamaño total del disco: {count * size:,} bytes")
        except ValueError:
            self.total_label.configure(text="")

    def _accept(self):
        try:
            count = int(self.sector_count_var.get())
            size = int(self.sector_size_var.get())
        except ValueError:
            show_error(self, "Datos inválidos", "Sectores y tamaño deben ser números enteros.")
            return

        if count <= 0 or size <= 0:
            show_error(self, "Datos inválidos", "Sectores y tamaño deben ser mayores a cero.")
            return

        self.result = (count, size)
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()
