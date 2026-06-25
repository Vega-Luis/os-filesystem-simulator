

import fnmatch

from .file_node import FileNode
from .exceptions import (
    DuplicateNameError,
    PathNotFoundError,
    InvalidNameError,
    NotEmptyError,
)


class FileSystem:
    def __init__(self, disk):
        """
        :param disk: instancia de VirtualDisk (storage/virtual_disk.py),
                      ya creada con create_disk() antes de pasarla aquí.
        """
        self.disk = disk
        self.root = FileNode("root", is_directory=True)
        self.current_directory = self.root

    # ------------------------------------------------------------------
    # Creación
    # ------------------------------------------------------------------

    def create_file(self, name, content=""):
        """Crea un archivo con contenido en el directorio actual.
        Lanza DuplicateNameError, DiskFullError (esta última viene
        directamente de disk.allocate, no se reatrapa aquí)."""
        self._validate_name(name)
        if self._find_child(name) is not None:
            raise DuplicateNameError(name)

        sectors = self.disk.allocate(len(content.encode("utf-8")))
        self.disk.write(sectors, content)

        file_node = FileNode(name, is_directory=False)
        file_node.sectors = sectors
        file_node.size = len(content.encode("utf-8"))
        self.current_directory.add_child(file_node)

    def mkdir(self, name):
        """Crea un directorio en el directorio actual.
        Lanza DuplicateNameError si ya existe."""
        self._validate_name(name)
        if self._find_child(name) is not None:
            raise DuplicateNameError(name)

        dir_node = FileNode(name, is_directory=True)
        self.current_directory.add_child(dir_node)

    # Alias por compatibilidad con el código previo, no rompe nada si
    # algo más del proyecto todavía llama create_directory.
    def create_directory(self, name):
        self.mkdir(name)

    # ------------------------------------------------------------------
    # Lectura / listado
    # ------------------------------------------------------------------

    def list_dir(self):
        """Lista el contenido del directorio actual como DirEntry."""
        entries = []
        for child in self.current_directory.children:
            entries.append({
                "nombre": child.name,
                "tipo": "dir" if child.is_directory else "file",
                "tamaño": 0 if child.is_directory else child.size,
            })
        return entries

    def read_file(self, path):
        """Devuelve el contenido del archivo en la ruta indicada."""
        node = self._resolve_path(path)
        if node.is_directory:
            raise InvalidNameError(f"'{path}' es un directorio, no un archivo.")
        return self.disk.read(node.sectors)

    def get_properties(self, path):
        """FileProperties: nombre, extensión, fechas, tamaño, tipo."""
        node = self._resolve_path(path)
        return {
            "nombre": node.name,
            "extension": node.extension,
            "fecha_creacion": node.creation_date.isoformat(),
            "fecha_modificacion": node.modification_date.isoformat(),
            "tamaño": node.size,
            "tipo": "dir" if node.is_directory else "file",
        }

    def get_current_path(self):
        """Ruta absoluta del directorio actual, ej '/Documentos/Fotos'."""
        parts = []
        node = self.current_directory
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        if not parts:
            return "/"
        return "/" + "/".join(reversed(parts))

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def change_dir(self, target):
        """Acepta '..' para subir, un nombre relativo, o una ruta absoluta."""
        if target == "..":
            if self.current_directory.parent is not None:
                self.current_directory = self.current_directory.parent
            return

        if target.startswith("/"):
            node = self._resolve_path(target)
            if not node.is_directory:
                raise PathNotFoundError(target)
            self.current_directory = node
            return

        child = self._find_child(target)
        if child is None or not child.is_directory:
            raise PathNotFoundError(target)
        self.current_directory = child

    # Alias por compatibilidad con nombres previos
    def change_directory(self, target):
        self.change_dir(target)

    # ------------------------------------------------------------------
    # Modificación
    # ------------------------------------------------------------------

    def modify_file(self, path, content):
        """Reemplaza el contenido de un archivo existente."""
        node = self._resolve_path(path)
        if node.is_directory:
            raise InvalidNameError(f"'{path}' es un directorio, no un archivo.")

        # Libera los sectores viejos y reserva nuevos: más simple y
        # correcto que intentar reusar in-place si el tamaño cambió.
        self.disk.free(node.sectors)
        new_sectors = self.disk.allocate(len(content.encode("utf-8")))
        self.disk.write(new_sectors, content)

        node.sectors = new_sectors
        node.size = len(content.encode("utf-8"))
        from datetime import datetime
        node.modification_date = datetime.now()

    def move(self, source, destination):
        """Mueve (o renombra, si destination es solo un nombre nuevo en
        el mismo directorio) un archivo o directorio."""
        node = self._resolve_path(source) if source.startswith("/") else self._find_child(source)
        if node is None:
            raise PathNotFoundError(source)

        if "/" not in destination:
            # Rename dentro del mismo directorio
            if self._find_child(destination) is not None:
                raise DuplicateNameError(destination)
            node.name = destination
            return

        # Mover a otro directorio: destino = ruta de directorio + nuevo nombre
        dest_parent_path, new_name = destination.rsplit("/", 1)
        dest_parent = self._resolve_path(dest_parent_path or "/")
        if not dest_parent.is_directory:
            raise PathNotFoundError(destination)
        if any(c.name == new_name for c in dest_parent.children):
            raise DuplicateNameError(new_name)

        node.parent.children.remove(node)
        node.name = new_name or node.name
        dest_parent.add_child(node)

    def copy(self, source, destination):
        """
        CoPY virtual -> virtual. Copia un archivo o directorio (de forma
        recursiva) de 'source' a 'destination' dentro del file system.

        'source' puede ser un nombre relativo al directorio actual o una
        ruta absoluta. 'destination' es la ruta del directorio donde se
        quiere colocar la copia (no incluye el nombre final: se conserva
        el nombre original; si ya existe algo con ese nombre ahí, lanza
        DuplicateNameError).
        """
        node = self._resolve_path(source) if source.startswith("/") else self._find_child(source)
        if node is None:
            raise PathNotFoundError(source)

        dest_dir = self._resolve_path(destination)
        if not dest_dir.is_directory:
            raise PathNotFoundError(destination)
        if any(c.name == node.name for c in dest_dir.children):
            raise DuplicateNameError(node.name)

        copy_node = self._deep_copy_node(node)
        dest_dir.add_child(copy_node)

    def _deep_copy_node(self, node):
        """Crea una copia de un FileNode. Si es archivo, reserva sectores
        nuevos en disco con el mismo contenido (no comparte sectores con
        el original, para que borrar uno no afecte al otro)."""
        copy_node = FileNode(node.name, is_directory=node.is_directory)

        if node.is_directory:
            for child in node.children:
                copy_node.add_child(self._deep_copy_node(child))
        else:
            content = self.disk.read(node.sectors)
            new_sectors = self.disk.allocate(len(content.encode("utf-8")))
            self.disk.write(new_sectors, content)
            copy_node.sectors = new_sectors
            copy_node.size = node.size

        return copy_node

    # ------------------------------------------------------------------
    # Eliminación
    # ------------------------------------------------------------------

    def remove(self, path, recursive=False):
        """Elimina un archivo o directorio. recursive=True requerido
        para borrar directorios no vacíos."""
        node = self._resolve_path(path)

        if node.is_directory and node.children and not recursive:
            raise NotEmptyError(node.name)

        self._free_all_sectors(node)

        if node.parent is not None:
            node.parent.children.remove(node)

    # Alias por compatibilidad
    def delete(self, path, recursive=False):
        self.remove(path, recursive=recursive)

    def _free_all_sectors(self, node):
        """Libera recursivamente los sectores de un archivo o de todo
        el contenido de un directorio antes de eliminarlo."""
        if node.is_directory:
            for child in list(node.children):
                self._free_all_sectors(child)
        elif node.sectors:
            self.disk.free(node.sectors)

    # ------------------------------------------------------------------
    # Búsqueda y visualización
    # ------------------------------------------------------------------

    def find(self, pattern, node=None, current_path="/", results=None):
        """Busca por nombre exacto o wildcard (ej '*.txt'). Devuelve
        lista de rutas absolutas."""
        if node is None:
            node = self.root
        if results is None:
            results = []

        node_path = current_path if current_path != "/" else "/"
        full_path = node_path if node is self.root else (
            f"{node_path.rstrip('/')}/{node.name}" if node_path != "/" else f"/{node.name}"
        )

        if node is not self.root and fnmatch.fnmatch(node.name, pattern):
            results.append(full_path)

        if node.is_directory:
            for child in node.children:
                self.find(pattern, child, full_path, results)

        return results

    def tree(self):
        """String ya formateado representando el árbol completo."""
        return self._build_tree_string(self.root, "")

    def _build_tree_string(self, node, prefix):
        line = f"{prefix}{node.name}/\n" if node.is_directory else f"{prefix}{node.name}\n"
        result = line
        if node.is_directory:
            for child in node.children:
                result += self._build_tree_string(child, prefix + "  ")
        return result

    # Alias por compatibilidad
    def get_directory_tree(self):
        return self.tree()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _validate_name(self, name):
        if not name or not name.strip():
            raise InvalidNameError("El nombre no puede estar vacío.")
        for forbidden in ("/", "\\"):
            if forbidden in name:
                raise InvalidNameError(f"El nombre no puede contener '{forbidden}'.")

    def _find_child(self, name):
        """Busca un hijo directo por nombre en el directorio actual."""
        for child in self.current_directory.children:
            if child.name == name:
                return child
        return None

    def _resolve_path(self, path):
        """Resuelve una ruta absoluta (ej '/Documentos/nota.txt') a su
        FileNode. Lanza PathNotFoundError si no existe."""
        if path in ("/", ""):
            return self.root

        parts = [p for p in path.split("/") if p]
        node = self.root
        for part in parts:
            if not node.is_directory:
                raise PathNotFoundError(path)
            found = None
            for child in node.children:
                if child.name == part:
                    found = child
                    break
            if found is None:
                raise PathNotFoundError(path)
            node = found
        return node
