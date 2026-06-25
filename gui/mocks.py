

from file_system.exceptions import (
    DuplicateNameError,
    DiskFullError,
    PathNotFoundError,
    NotEmptyError,
)


class MockFS:
    def __init__(self):
        self.current_path = "/"
        # Estructura falsa en memoria, solo para tener algo que mostrar
        self._fake_tree = {
            "/": {
                "Documentos": {"tipo": "dir"},
                "Fotos": {"tipo": "dir"},
                "nota.txt": {"tipo": "file", "tamaño": 12},
            },
            "/Documentos": {
                "tarea.docx": {"tipo": "file", "tamaño": 4096},
            },
            "/Fotos": {
                "perro.jpg": {"tipo": "file", "tamaño": 204800},
            },
        }

    def mkdir(self, name: str) -> None:
        print(f"[MockFS] mkdir({name})")
        if name in self._current_dir_dict():
            raise DuplicateNameError(name)
        self._current_dir_dict()[name] = {"tipo": "dir"}

    def create_file(self, name: str, content: str) -> None:
        print(f"[MockFS] create_file({name}, len={len(content)})")
        if name in self._current_dir_dict():
            raise DuplicateNameError(name)
        self._current_dir_dict()[name] = {"tipo": "file", "tamaño": len(content)}

    def modify_file(self, path: str, content: str) -> None:
        print(f"[MockFS] modify_file({path})")

    def remove(self, path: str, recursive: bool = False) -> None:
        print(f"[MockFS] remove({path}, recursive={recursive})")
        parent_path, name = self._split_path(path)
        parent_dict = self._fake_tree.get(parent_path, {})

        if name not in parent_dict:
            raise PathNotFoundError(path)

        entry = parent_dict[name]
        if entry.get("tipo") == "dir":
            child_path = f"{parent_path}/{name}" if parent_path != "/" else f"/{name}"
            has_content = bool(self._fake_tree.get(child_path))
            if has_content and not recursive:
                raise NotEmptyError(name)
            self._fake_tree.pop(child_path, None)

        del parent_dict[name]

    def move(self, source: str, destination: str) -> None:
        print(f"[MockFS] move({source} -> {destination})")

    def list_dir(self):
        entries = []
        for nombre, info in self._current_dir_dict().items():
            entries.append({
                "nombre": nombre,
                "tipo": info["tipo"],
                "tamaño": info.get("tamaño", 0),
            })
        return entries

    def change_dir(self, target: str) -> None:
        """
        Acepta:
        - '..' para subir un nivel
        - el nombre de un subdirectorio del directorio actual (relativo)
        - una ruta absoluta (ej. '/Documentos')
        """
        print(f"[MockFS] change_dir({target})")

        if target == "..":
            if self.current_path == "/":
                return  # ya está en la raíz, no hay a dónde subir
            self.current_path = self.current_path.rsplit("/", 1)[0] or "/"
            return

        if target.startswith("/"):
            new_path = target
        else:
            base = "" if self.current_path == "/" else self.current_path
            new_path = f"{base}/{target}"

        entry = self._current_dir_dict().get(target) if not target.startswith("/") else None
        is_known_dir = new_path in self._fake_tree or (entry and entry.get("tipo") == "dir")

        if new_path != "/" and not is_known_dir:
            raise PathNotFoundError(target)

        self.current_path = new_path

    def find(self, pattern: str):
        print(f"[MockFS] find({pattern})")
        return ["/Documentos/tarea.docx"]

    def tree(self) -> str:
        return "/\n├── Documentos/\n│   └── tarea.docx\n├── Fotos/\n│   └── perro.jpg\n└── nota.txt"

    def get_properties(self, path: str):
        return {
            "nombre": path.split("/")[-1],
            "extension": "txt",
            "fecha_creacion": "2026-06-22T10:00:00",
            "fecha_modificacion": "2026-06-22T10:00:00",
            "tamaño": 12,
            "tipo": "file",
        }

    def read_file(self, path: str) -> str:
        return "(contenido simulado del archivo)"

    def get_current_path(self) -> str:
        return self.current_path

    def _current_dir_dict(self):
        return self._fake_tree.setdefault(self.current_path, {})

    def _split_path(self, path: str):
        """Divide una ruta absoluta en (ruta_padre, nombre)."""
        if "/" not in path.strip("/"):
            return "/", path.strip("/")
        parent, name = path.rsplit("/", 1)
        return (parent or "/"), name
