"""
gui/main_window.py
Responsable: Persona B

Ventana principal. Layout:

    [ Ruta actual: /Documentos/Fotos                              ]
    [-------------------------------------------------------------]
    [  TREE (panel izq.)   |   Directorio actual (panel der.)     ]
    [                       |                                       ]
    [-------------------------------------------------------------]
    [ MKDIR | FILE | CD | ModFILE | Ver | CoPY | MoVer | RM | FIND ]

Depende únicamente de la interfaz acordada en docs/SHARED.md (mkdir,
create_file, list_dir, change_dir, tree, etc.) — funciona igual con
MockFS o con el FileSystem real, sin tocar este archivo.
"""

import tkinter as tk
from tkinter import ttk

from gui import dialogs
from file_system.exceptions import (
    DuplicateNameError,
    DiskFullError,
    PathNotFoundError,
    InvalidNameError,
    NotEmptyError,
)


class MainWindow:
    def __init__(self, fs, root=None):
        self.fs = fs

        # Si ya existe una raíz de Tkinter (ej. la que usó el diálogo de
        # CREATE en main.py), se reutiliza en vez de crear una segunda
        # instancia de Tk(), lo cual no está permitido.
        self.root = root if root is not None else tk.Tk()
        self.root.deiconify()
        self.root.title("OS File System Simulator")
        self.root.geometry("1000x650")
        self.root.minsize(800, 500)

        self._build_layout()
        self._refresh_all()

    # ------------------------------------------------------------------
    # Construcción del layout
    # ------------------------------------------------------------------

    def _build_layout(self):
        self._build_path_bar()
        self._build_main_panels()
        self._build_command_bar()

    def _build_path_bar(self):
        bar = ttk.Frame(self.root, padding=(10, 8))
        bar.pack(fill="x", side="top")

        ttk.Label(bar, text="Ruta actual:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.path_var = tk.StringVar(value="/")
        ttk.Label(bar, textvariable=self.path_var, font=("Segoe UI", 10)).pack(side="left", padx=(6, 0))

        ttk.Separator(self.root, orient="horizontal").pack(fill="x")

    def _build_main_panels(self):
        container = ttk.Frame(self.root, padding=8)
        container.pack(fill="both", expand=True)

        # --- Panel izquierdo: TREE completo, siempre visible ---
        left = ttk.Frame(container)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        ttk.Label(left, text="Estructura completa (TREE)", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.tree_text = tk.Text(left, width=40, wrap="none", state="disabled",
                                  font=("Consolas", 10), background="#f4f4f4")
        self.tree_text.pack(fill="both", expand=True, pady=(4, 0))

        # --- Panel derecho: contenido del directorio actual ---
        right = ttk.Frame(container)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))

        ttk.Label(right, text="Contenido del directorio actual", font=("Segoe UI", 9, "bold")).pack(anchor="w")

        columns = ("tipo", "tamaño")
        self.dir_table = ttk.Treeview(right, columns=columns, show="tree headings", height=15)
        self.dir_table.heading("#0", text="Nombre")
        self.dir_table.heading("tipo", text="Tipo")
        self.dir_table.heading("tamaño", text="Tamaño (bytes)")
        self.dir_table.column("#0", width=220)
        self.dir_table.column("tipo", width=90, anchor="center")
        self.dir_table.column("tamaño", width=120, anchor="e")
        self.dir_table.pack(fill="both", expand=True, pady=(4, 0))
        self.dir_table.bind("<Double-1>", self._on_dir_table_double_click)

    def _build_command_bar(self):
        ttk.Separator(self.root, orient="horizontal").pack(fill="x")
        bar = ttk.Frame(self.root, padding=8)
        bar.pack(fill="x", side="bottom")

        commands = [
            ("MKDIR", self.cmd_mkdir),
            ("FILE", self.cmd_create_file),
            ("CambiarDIR", self.cmd_change_dir),
            ("Subir (..)", self.cmd_go_up),
            ("ModFILE", self.cmd_modify_file),
            ("VerPropiedades", self.cmd_properties),
            ("VerFile", self.cmd_view_file),
            ("CoPY", self.cmd_copy),
            ("MoVer", self.cmd_move),
            ("ReMove", self.cmd_remove),
            ("FIND", self.cmd_find),
        ]

        for label, handler in commands:
            ttk.Button(bar, text=label, command=handler).pack(side="left", padx=3)

    # ------------------------------------------------------------------
    # Refrescar vistas tras cualquier operación
    # ------------------------------------------------------------------

    def _refresh_all(self):
        self._refresh_path()
        self._refresh_dir_table()
        self._refresh_tree()

    def _refresh_path(self):
        self.path_var.set(self.fs.get_current_path())

    def _refresh_dir_table(self):
        self.dir_table.delete(*self.dir_table.get_children())
        for entry in self.fs.list_dir():
            tipo = "Directorio" if entry["tipo"] == "dir" else "Archivo"
            tamaño = "-" if entry["tipo"] == "dir" else entry.get("tamaño", 0)
            icon = "📁" if entry["tipo"] == "dir" else "📄"
            self.dir_table.insert(
                "", "end",
                text=f"{icon} {entry['nombre']}",
                values=(tipo, tamaño),
            )

    def _refresh_tree(self):
        self.tree_text.configure(state="normal")
        self.tree_text.delete("1.0", "end")
        self.tree_text.insert("1.0", self.fs.tree())
        self.tree_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # Helpers de selección
    # ------------------------------------------------------------------

    def _selected_name(self):
        """Devuelve el nombre (sin ícono) del elemento seleccionado en la
        tabla del directorio actual, o None si no hay selección."""
        selection = self.dir_table.selection()
        if not selection:
            dialogs.show_info(self.root, "Sin selección", "Seleccione primero un archivo o directorio en la tabla.")
            return None
        text = self.dir_table.item(selection[0], "text")
        # quita el ícono (📁/📄) y el espacio inicial
        return text.split(" ", 1)[1] if " " in text else text

    def _full_path(self, name):
        base = self.fs.get_current_path()
        if base == "/":
            return f"/{name}"
        return f"{base}/{name}"

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------

    def cmd_mkdir(self):
        name = dialogs.ask_name(self.root, "MKDIR", "Nombre del nuevo directorio:")
        if not name:
            return
        self._create_with_overwrite_check(name, is_dir=True)

    def cmd_create_file(self):
        dialog = dialogs.FileFormDialog(self.root, title="FILE — Crear archivo")
        self.root.wait_window(dialog)
        if dialog.result is None:
            return
        name, content = dialog.result
        self._create_with_overwrite_check(name, is_dir=False, content=content)

    def _create_with_overwrite_check(self, name, is_dir, content=""):
        try:
            if is_dir:
                self.fs.mkdir(name)
            else:
                self.fs.create_file(name, content)
        except DuplicateNameError:
            if dialogs.confirm_overwrite(self.root, name):
                try:
                    # Sobrescribir: se elimina lo existente y se crea de nuevo
                    self.fs.remove(self._full_path(name), recursive=True)
                    if is_dir:
                        self.fs.mkdir(name)
                    else:
                        self.fs.create_file(name, content)
                except DiskFullError:
                    dialogs.show_disk_full(self.root)
                    return
            else:
                return
        except DiskFullError:
            dialogs.show_disk_full(self.root)
            return
        except InvalidNameError as e:
            dialogs.show_error(self.root, "Nombre inválido", str(e))
            return
        self._refresh_all()

    def cmd_change_dir(self):
        name = dialogs.ask_name(self.root, "CambiarDIR", "Nombre del directorio (o '..' para subir):")
        if not name:
            return
        self._change_dir_to(name)

    def cmd_go_up(self):
        self._change_dir_to("..")

    def _change_dir_to(self, target):
        try:
            self.fs.change_dir(target)
        except PathNotFoundError:
            dialogs.show_error(self.root, "Ruta no encontrada", f"El directorio '{target}' no existe.")
            return
        self._refresh_all()

    def cmd_modify_file(self):
        name = self._selected_name()
        if name is None:
            return
        path = self._full_path(name)
        try:
            current_content = self.fs.read_file(path)
        except PathNotFoundError:
            dialogs.show_error(self.root, "No encontrado", "Seleccione un archivo válido.")
            return

        dialog = dialogs.FileFormDialog(
            self.root, title="ModFILE — Modificar archivo",
            initial_name=name, initial_content=current_content,
        )
        dialog.name_entry.configure(state="disabled")  # no se permite renombrar aquí, eso es MoVer
        self.root.wait_window(dialog)
        if dialog.result is None:
            return
        _, new_content = dialog.result
        try:
            self.fs.modify_file(path, new_content)
        except DiskFullError:
            dialogs.show_disk_full(self.root)
            return
        self._refresh_all()

    def cmd_properties(self):
        name = self._selected_name()
        if name is None:
            return
        try:
            props = self.fs.get_properties(self._full_path(name))
        except PathNotFoundError:
            dialogs.show_error(self.root, "No encontrado", "Seleccione un archivo o directorio válido.")
            return

        message = (
            f"Nombre: {props['nombre']}\n"
            f"Extensión: {props.get('extension', '-')}\n"
            f"Tipo: {props['tipo']}\n"
            f"Fecha de creación: {props['fecha_creacion']}\n"
            f"Fecha de modificación: {props['fecha_modificacion']}\n"
            f"Tamaño: {props['tamaño']} bytes"
        )
        dialogs.show_info(self.root, f"Propiedades de {name}", message)

    def cmd_view_file(self):
        name = self._selected_name()
        if name is None:
            return
        try:
            content = self.fs.read_file(self._full_path(name))
        except PathNotFoundError:
            dialogs.show_error(self.root, "No encontrado", "Seleccione un archivo válido.")
            return
        dialogs.show_info(self.root, f"Contenido de {name}", content)

    def cmd_move(self):
        dialog = dialogs.MoveDialog(self.root, current_path=self.fs.get_current_path())
        self.root.wait_window(dialog)
        if dialog.result is None:
            return
        source, dest = dialog.result
        try:
            self.fs.move(self._full_path(source), dest)
        except PathNotFoundError:
            dialogs.show_error(self.root, "No encontrado", f"'{source}' no existe en el directorio actual.")
            return
        except DuplicateNameError:
            dialogs.show_error(self.root, "Nombre ocupado", f"Ya existe algo llamado '{dest}' en el destino.")
            return
        self._refresh_all()

    def cmd_copy(self):
        dialog = dialogs.CopyDialog(self.root, current_virtual_path=self.fs.get_current_path())
        self.root.wait_window(dialog)
        if dialog.result is None:
            return
        mode, source, dest = dialog.result

        try:
            if mode == "real_a_virtual":
                self._copy_real_a_virtual(source, dest)
            elif mode == "virtual_a_real":
                self._copy_virtual_a_real(source, dest)
            else:
                self._copy_virtual_a_virtual(source, dest)
        except FileNotFoundError:
            dialogs.show_error(self.root, "No encontrado", f"No se encontró el archivo real '{source}'.")
            return
        except PathNotFoundError as e:
            dialogs.show_error(self.root, "No encontrado", f"No existe en el File System: {e}")
            return
        except DuplicateNameError as e:
            if dialogs.confirm_overwrite(self.root, str(e)):
                # Reintenta sobrescribiendo en el lado virtual
                try:
                    self._copy_with_overwrite(mode, source, dest)
                except DiskFullError:
                    dialogs.show_disk_full(self.root)
                    return
            else:
                return
        except DiskFullError:
            dialogs.show_disk_full(self.root)
            return
        except UnicodeDecodeError:
            dialogs.show_error(
                self.root, "Archivo no soportado",
                "El archivo real no es texto plano legible (ej. es binario). "
                "Este simulador solo copia contenido de texto.",
            )
            return

        self._refresh_all()
        dialogs.show_info(self.root, "CoPY", "Copia completada correctamente.")

    def _copy_real_a_virtual(self, real_path, virtual_dest_dir):
        with open(real_path, "r", encoding="utf-8") as f:
            content = f.read()
        name = real_path.replace("\\", "/").rsplit("/", 1)[-1]

        original_dir = self.fs.get_current_path()
        self.fs.change_dir(virtual_dest_dir)
        try:
            self.fs.create_file(name, content)
        finally:
            self.fs.change_dir(original_dir)

    def _copy_virtual_a_real(self, virtual_source, real_dest_path):
        path = virtual_source if virtual_source.startswith("/") else self._full_path(virtual_source)
        content = self.fs.read_file(path)
        with open(real_dest_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _copy_virtual_a_virtual(self, source_name, dest_dir):
        self.fs.copy(self._full_path(source_name), dest_dir)

    def _copy_with_overwrite(self, mode, source, dest):
        """Reintenta una copia tras confirmar sobrescritura, borrando
        primero lo que ya existe en el destino virtual."""
        if mode == "real_a_virtual":
            name = source.replace("\\", "/").rsplit("/", 1)[-1]
            original_dir = self.fs.get_current_path()
            self.fs.change_dir(dest)
            try:
                self.fs.remove(self._full_path(name), recursive=True)
            except PathNotFoundError:
                pass
            self.fs.change_dir(original_dir)
            self._copy_real_a_virtual(source, dest)
        elif mode == "virtual_a_real":
            # Sobrescribir un archivo real es directo, open(..., "w") ya lo hace
            self._copy_virtual_a_real(source, dest)
        else:
            name = source if "/" not in source else source.rsplit("/", 1)[-1]
            try:
                self.fs.remove(f"{dest.rstrip('/')}/{name}", recursive=True)
            except PathNotFoundError:
                pass
            self._copy_virtual_a_virtual(source, dest)

    def cmd_remove(self):
        name = self._selected_name()
        if name is None:
            return
        path = self._full_path(name)
        try:
            self.fs.remove(path, recursive=False)
        except PathNotFoundError:
            dialogs.show_error(self.root, "No encontrado", "El elemento ya no existe.")
            return
        except NotEmptyError:
            # El directorio no está vacío: se confirma con el usuario y,
            # si acepta, se reintenta como borrado recursivo.
            if dialogs.confirm_recursive_delete(self.root, name):
                try:
                    self.fs.remove(path, recursive=True)
                except PathNotFoundError:
                    dialogs.show_error(self.root, "No encontrado", "El elemento ya no existe.")
                    return
            else:
                return
        self._refresh_all()

    def cmd_find(self):
        pattern = dialogs.ask_name(self.root, "FIND", "Nombre o patrón a buscar (ej. '*.txt'):")
        if not pattern:
            return
        results = self.fs.find(pattern)
        if not results:
            dialogs.show_info(self.root, "FIND", f"No se encontraron coincidencias para '{pattern}'.")
            return
        message = "\n".join(results)
        dialogs.show_info(self.root, f"Resultados para '{pattern}'", message)

    def _on_dir_table_double_click(self, event):
        name = self._selected_name()
        if name is None:
            return
        # Si es un directorio, doble click navega dentro de él
        entries = {e["nombre"]: e for e in self.fs.list_dir()}
        entry = entries.get(name)
        if entry and entry["tipo"] == "dir":
            self._change_dir_to(name)

    # ------------------------------------------------------------------
    def run(self):
        self.root.mainloop()
