"""
Excepciones compartidas entre file_system/ y storage/.
"""


class DuplicateNameError(Exception):
    """Ya existe un archivo/directorio con ese nombre en el directorio actual."""
    pass


class DiskFullError(Exception):
    """No hay suficientes sectores libres para completar la operación."""
    pass


class PathNotFoundError(Exception):
    """La ruta indicada no existe en el file system."""
    pass


class InvalidNameError(Exception):
    """Nombre de archivo/directorio inválido (vacío, caracteres no permitidos, etc.)."""
    pass


class NotEmptyError(Exception):
    """Se intentó eliminar un directorio no vacío sin pedir borrado recursivo."""
    pass