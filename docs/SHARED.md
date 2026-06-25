# SHARED — Interfaz compartida entre módulos

Este documento describe cómo se conectan `file_system/`, `storage/` y
`gui/`. Si alguien cambia una firma aquí descrita, debe avisar a ambos
compañeros y actualizar este archivo en el mismo commit.

## 1. Cómo se conectan las piezas

```
main.py
  ├── VirtualDisk()           (storage/virtual_disk.py)
  │     .create_disk(sector_count, sector_size)
  │
  ├── FileSystem(disk)        (file_system/file_system.py)
  │     usa internamente disk.allocate / disk.write / disk.read / disk.free
  │
  └── MainWindow(fs)          (gui/main_window.py)
        solo llama métodos de FileSystem, nunca toca VirtualDisk directamente
```

## 2. Tipos de datos compartidos

### DirEntry (una fila de `list_dir()`)
```python
{
    "nombre": str,
    "tipo": str,     # "file" | "dir"
    "tamaño": int,    # bytes; 0 si es directorio
}
```

### FileProperties (resultado de `get_properties()`)
```python
{
    "nombre": str,
    "extension": str,
    "fecha_creacion": str,        # ISO 8601
    "fecha_modificacion": str,
    "tamaño": int,
    "tipo": str,                    # "file" | "dir"
}
```

### Rutas
Strings estilo Unix, absolutas desde la raíz: `"/Documentos/Fotos/foto.jpg"`.
La raíz es `"/"`. `change_dir()` también acepta nombres relativos al
directorio actual y `".."` para subir un nivel.

## 3. Excepciones (`file_system/exceptions.py`)

| Excepción            | Cuándo se lanza                                                |
|-----------------------|------------------------------------------------------------------|
| `DuplicateNameError`    | Ya existe un archivo/directorio con ese nombre                      |
| `DiskFullError`          | No hay suficientes sectores libres (la lanza `VirtualDisk`)            |
| `PathNotFoundError`       | La ruta indicada no existe                                              |
| `InvalidNameError`         | Nombre vacío o con caracteres no permitidos                                |
| `NotEmptyError`              | Se intentó eliminar un directorio no vacío sin `recursive=True`             |

La GUI captura todas estas para mostrar diálogos claros al usuario.

## 4. Interfaz de `FileSystem`

| Método                                       | Retorno              |
|------------------------------------------------|------------------------|
| `mkdir(name)`                                    | `None`                  |
| `create_file(name, content="")`                    | `None`                    |
| `modify_file(path, content)`                         | `None`                      |
| `remove(path, recursive=False)`                        | `None`                        |
| `move(source, destination)`                              | `None`                          |
| `list_dir()`                                                | `list[DirEntry]`                  |
| `change_dir(target)`                                          | `None`                              |
| `find(pattern)`                                                  | `list[str]` (rutas absolutas)          |
| `tree()`                                                          | `str` (formateado, listo para mostrar)    |
| `get_properties(path)`                                              | `FileProperties`                            |
| `read_file(path)`                                                      | `str`                                          |
| `get_current_path()`                                                      | `str`                                             |

## 5. Interfaz de `VirtualDisk`

| Método                                          | Retorno                |
|----------------------------------------------------|--------------------------|
| `create_disk(sector_count, sector_size, path=...)`    | `None`                      |
| `allocate(file_size)`                                   | `list[int]` (sectores)         |
| `free(sector_list)`                                        | `None`                            |
| `write(sector_list, content)`                                | `None`                               |
| `read(sector_list)`                                             | `str`                                   |
| `available_space()`                                                | `int` (bytes)                              |

`FileSystem` es el único que llama a `VirtualDisk`. La GUI nunca lo hace
directamente.

## 6. Mocks (desarrollo en paralelo)

`gui/mocks.py` define `MockFS`, que respeta esta misma interfaz con datos
simulados en memoria. Se usó durante el desarrollo de la GUI para no
depender de que `FileSystem` estuviera terminado. Ya no es necesario para
correr el proyecto (ver `main.py`), pero se conserva por si se necesita
para pruebas rápidas de la interfaz sin tocar el disco real.
