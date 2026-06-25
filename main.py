"""
Punto de entrada de la aplicación.

Conecta las tres piezas del proyecto:
    VirtualDisk  -> el disco físico con sectores (storage/)
    FileSystem   -> la lógica de archivos/directorios (file_system/)
    MainWindow   -> la interfaz gráfica con Tkinter (gui/)

CREATE se pide ahora de forma interactiva: al iniciar la aplicación se
muestra un diálogo donde el usuario indica la cantidad de sectores y el
tamaño de cada sector. Si ya existe un disco virtual guardado de una
sesión anterior, se avisa y se reabre con su tamaño original (el
enunciado exige que el archivo de disco no se elimine al cerrar la app).
"""

import os
import tkinter as tk

from storage.virtual_disk import VirtualDisk
from file_system.file_system import FileSystem
from gui.main_window import MainWindow
from gui import dialogs

DEFAULT_SECTOR_COUNT = 200
DEFAULT_SECTOR_SIZE = 64
DISK_PATH = "disk/virtual_disk.bin"


def main():
    # Ventana raíz, necesaria para poder mostrar el diálogo de CREATE
    # antes de construir la ventana principal. CreateDiskDialog se
    # encarga de centrarse y hacerse visible por sí mismo.
    root = tk.Tk()
    root.geometry("1x1+0+0")

    disk_already_exists = os.path.exists(DISK_PATH) and os.path.getsize(DISK_PATH) > 0

    create_dialog = dialogs.CreateDiskDialog(
        root,
        default_sector_count=DEFAULT_SECTOR_COUNT,
        default_sector_size=DEFAULT_SECTOR_SIZE,
        disk_already_exists=disk_already_exists,
    )

    root.withdraw()
    root.wait_window(create_dialog)

    if create_dialog.result is None:
        # El usuario canceló el CREATE: no hay disco con qué trabajar.
        root.destroy()
        return

    sector_count, sector_size = create_dialog.result

    disk = VirtualDisk()
    disk.create_disk(
        sector_count=sector_count,
        sector_size=sector_size,
        path=DISK_PATH,
    )

    fs = FileSystem(disk)

    app = MainWindow(fs, root=root)
    app.run()


if __name__ == "__main__":
    main()

