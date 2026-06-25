"""
tests/test_filesystem.py
Pruebas de FileSystem integrado con VirtualDisk.

Correr con: python -m unittest tests.test_filesystem -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storage.virtual_disk import VirtualDisk
from file_system.file_system import FileSystem
from file_system.exceptions import (
    DuplicateNameError,
    PathNotFoundError,
    NotEmptyError,
    DiskFullError,
)

TEST_DISK_PATH = "disk/test_fs.bin"


class TestFileSystem(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DISK_PATH):
            os.remove(TEST_DISK_PATH)
        self.disk = VirtualDisk()
        self.disk.create_disk(sector_count=50, sector_size=16, path=TEST_DISK_PATH)
        self.fs = FileSystem(self.disk)

    def tearDown(self):
        if os.path.exists(TEST_DISK_PATH):
            os.remove(TEST_DISK_PATH)

    def test_mkdir_y_list_dir(self):
        self.fs.mkdir("Documentos")
        entries = self.fs.list_dir()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["nombre"], "Documentos")
        self.assertEqual(entries[0]["tipo"], "dir")

    def test_mkdir_duplicado(self):
        self.fs.mkdir("Documentos")
        with self.assertRaises(DuplicateNameError):
            self.fs.mkdir("Documentos")

    def test_create_file_y_read_file(self):
        self.fs.create_file("nota.txt", "hola mundo")
        content = self.fs.read_file("/nota.txt")
        self.assertEqual(content, "hola mundo")

    def test_create_file_duplicado(self):
        self.fs.create_file("nota.txt", "contenido")
        with self.assertRaises(DuplicateNameError):
            self.fs.create_file("nota.txt", "otro contenido")

    def test_change_dir_y_get_current_path(self):
        self.fs.mkdir("Documentos")
        self.fs.change_dir("Documentos")
        self.assertEqual(self.fs.get_current_path(), "/Documentos")

    def test_change_dir_subir_con_puntos(self):
        self.fs.mkdir("Documentos")
        self.fs.change_dir("Documentos")
        self.fs.change_dir("..")
        self.assertEqual(self.fs.get_current_path(), "/")

    def test_change_dir_inexistente(self):
        with self.assertRaises(PathNotFoundError):
            self.fs.change_dir("NoExiste")

    def test_modify_file(self):
        self.fs.create_file("nota.txt", "version 1")
        self.fs.modify_file("/nota.txt", "version 2, mas larga que la anterior")
        self.assertEqual(self.fs.read_file("/nota.txt"), "version 2, mas larga que la anterior")

    def test_get_properties(self):
        self.fs.create_file("nota.txt", "contenido")
        props = self.fs.get_properties("/nota.txt")
        self.assertEqual(props["nombre"], "nota.txt")
        self.assertEqual(props["extension"], "txt")
        self.assertEqual(props["tipo"], "file")
        self.assertEqual(props["tamaño"], len("contenido"))

    def test_move_rename(self):
        self.fs.create_file("nota.txt", "contenido")
        self.fs.move("nota.txt", "notas.txt")
        entries = [e["nombre"] for e in self.fs.list_dir()]
        self.assertIn("notas.txt", entries)
        self.assertNotIn("nota.txt", entries)

    def test_move_a_otro_directorio(self):
        self.fs.mkdir("Documentos")
        self.fs.create_file("nota.txt", "contenido")
        self.fs.move("nota.txt", "/Documentos/nota.txt")

        raiz = [e["nombre"] for e in self.fs.list_dir()]
        self.assertNotIn("nota.txt", raiz)

        self.fs.change_dir("Documentos")
        documentos = [e["nombre"] for e in self.fs.list_dir()]
        self.assertIn("nota.txt", documentos)

    def test_remove_archivo(self):
        self.fs.create_file("nota.txt", "contenido")
        self.fs.remove("/nota.txt")
        self.assertEqual(self.fs.list_dir(), [])

    def test_remove_directorio_no_vacio_sin_recursive(self):
        self.fs.mkdir("Documentos")
        self.fs.change_dir("Documentos")
        self.fs.create_file("nota.txt", "contenido")
        self.fs.change_dir("..")
        with self.assertRaises(NotEmptyError):
            self.fs.remove("/Documentos", recursive=False)

    def test_remove_directorio_recursive(self):
        self.fs.mkdir("Documentos")
        self.fs.change_dir("Documentos")
        self.fs.create_file("nota.txt", "contenido")
        self.fs.change_dir("..")
        self.fs.remove("/Documentos", recursive=True)
        self.assertEqual(self.fs.list_dir(), [])

    def test_remove_libera_sectores_del_disco(self):
        espacio_inicial = self.disk.available_space()
        self.fs.create_file("nota.txt", "contenido de prueba para ocupar sectores")
        self.assertLess(self.disk.available_space(), espacio_inicial)

        self.fs.remove("/nota.txt")
        self.assertEqual(self.disk.available_space(), espacio_inicial)

    def test_find_con_wildcard(self):
        self.fs.mkdir("Documentos")
        self.fs.change_dir("Documentos")
        self.fs.create_file("tarea.txt", "x")
        self.fs.create_file("imagen.jpg", "x")
        self.fs.change_dir("..")

        resultados = self.fs.find("*.txt")
        self.assertEqual(resultados, ["/Documentos/tarea.txt"])

    def test_tree(self):
        self.fs.mkdir("Documentos")
        self.fs.change_dir("Documentos")
        self.fs.create_file("tarea.txt", "x")
        self.fs.change_dir("..")

        tree_str = self.fs.tree()
        self.assertIn("Documentos/", tree_str)
        self.assertIn("tarea.txt", tree_str)

    def test_disco_lleno_al_crear_archivo(self):
        # 50 sectores * 16 bytes = 800 bytes totales
        contenido_enorme = "x" * 2000
        with self.assertRaises(DiskFullError):
            self.fs.create_file("grande.txt", contenido_enorme)

    def test_copy_archivo_virtual_a_virtual(self):
        self.fs.mkdir("Destino")
        self.fs.create_file("nota.txt", "contenido original")
        self.fs.copy("/nota.txt", "/Destino")

        self.assertEqual(self.fs.read_file("/Destino/nota.txt"), "contenido original")
        # El original sigue intacto
        self.assertEqual(self.fs.read_file("/nota.txt"), "contenido original")

    def test_copy_es_independiente_del_original(self):
        self.fs.mkdir("Destino")
        self.fs.create_file("nota.txt", "version 1")
        self.fs.copy("/nota.txt", "/Destino")

        self.fs.modify_file("/Destino/nota.txt", "version modificada en la copia")

        self.assertEqual(self.fs.read_file("/nota.txt"), "version 1")
        self.assertEqual(self.fs.read_file("/Destino/nota.txt"), "version modificada en la copia")

    def test_copy_directorio_recursivo(self):
        self.fs.mkdir("Origen")
        self.fs.change_dir("Origen")
        self.fs.create_file("a.txt", "contenido a")
        self.fs.change_dir("..")
        self.fs.mkdir("Destino")

        self.fs.copy("/Origen", "/Destino")

        self.assertEqual(self.fs.read_file("/Destino/Origen/a.txt"), "contenido a")

    def test_copy_destino_duplicado(self):
        self.fs.mkdir("Destino")
        self.fs.create_file("nota.txt", "contenido")
        self.fs.copy("/nota.txt", "/Destino")
        with self.assertRaises(DuplicateNameError):
            self.fs.copy("/nota.txt", "/Destino")


if __name__ == "__main__":
    unittest.main()
