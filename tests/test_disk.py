"""
tests/test_disk.py
Pruebas de VirtualDisk y SectorManager.

Correr con: python -m pytest tests/test_disk.py -v
o simplemente: python tests/test_disk.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storage.virtual_disk import VirtualDisk
from storage.sector_manager import SectorManager
from file_system.exceptions import DiskFullError

TEST_DISK_PATH = "disk/test_virtual_disk.bin"


class TestSectorManager(unittest.TestCase):
    def test_first_fit_basico(self):
        sm = SectorManager(10)
        sectors = sm.find_first_fit(3)
        self.assertEqual(sectors, [0, 1, 2])

    def test_first_fit_no_contiguo(self):
        sm = SectorManager(10)
        sm.mark_allocated([0, 1, 2])
        sm.free_sectors_list([1])  # libera el sector 1, queda hueco
        sectors = sm.find_first_fit(2)
        # debe tomar el 1 (libre) y el 3 (siguiente libre), aunque no sean
        # contiguos con nada en particular
        self.assertEqual(sectors, [1, 3])

    def test_insuficientes_sectores(self):
        sm = SectorManager(3)
        sectors = sm.find_first_fit(5)
        self.assertEqual(sectors, [])  # VirtualDisk decide lanzar DiskFullError

    def test_cadena_enlazada(self):
        sm = SectorManager(10)
        sm.mark_allocated([5, 2, 8])
        chain = sm.get_chain_from(5)
        self.assertEqual(chain, [5, 2, 8])

    def test_liberar_sectores(self):
        sm = SectorManager(5)
        sm.mark_allocated([0, 1, 2])
        sm.free_sectors_list([1])
        self.assertIn(1, sm.free_sectors)
        self.assertNotIn(0, sm.free_sectors)


class TestVirtualDisk(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DISK_PATH):
            os.remove(TEST_DISK_PATH)
        self.disk = VirtualDisk()
        self.disk.create_disk(sector_count=10, sector_size=8, path=TEST_DISK_PATH)

    def tearDown(self):
        if os.path.exists(TEST_DISK_PATH):
            os.remove(TEST_DISK_PATH)

    def test_create_disk_tamano_correcto(self):
        expected_size = 16 + 10 * 8  # header + sectores
        self.assertEqual(os.path.getsize(TEST_DISK_PATH), expected_size)

    def test_allocate_sectores_suficientes(self):
        # "hola mundo" = 10 bytes, sector_size=8 -> necesita 2 sectores
        sectors = self.disk.allocate(10)
        self.assertEqual(len(sectors), 2)

    def test_write_and_read_un_sector(self):
        sectors = self.disk.allocate(5)
        self.disk.write(sectors, "hola!")
        content = self.disk.read(sectors)
        self.assertEqual(content, "hola!")

    def test_write_and_read_varios_sectores(self):
        content_original = "Este es un contenido más largo que ocupa varios sectores de prueba."
        sectors = self.disk.allocate(len(content_original))
        self.disk.write(sectors, content_original)
        content_leido = self.disk.read(sectors)
        self.assertEqual(content_leido, content_original)

    def test_disco_lleno(self):
        # 10 sectores de 8 bytes = 80 bytes total
        with self.assertRaises(DiskFullError):
            self.disk.allocate(1000)

    def test_free_libera_espacio(self):
        sectors = self.disk.allocate(40)  # 5 sectores
        space_before = self.disk.available_space()
        self.disk.free(sectors)
        space_after = self.disk.available_space()
        self.assertGreater(space_after, space_before)

    def test_available_space_inicial(self):
        # 10 sectores de 8 bytes, ninguno ocupado
        self.assertEqual(self.disk.available_space(), 80)

    def test_reabrir_disco_existente_no_lo_borra(self):
        sectors = self.disk.allocate(5)
        self.disk.write(sectors, "hola!")

        # Simula reabrir la app: nueva instancia de VirtualDisk sobre el
        # mismo archivo
        disk2 = VirtualDisk()
        disk2.create_disk(sector_count=10, sector_size=8, path=TEST_DISK_PATH)

        # El archivo no se borró ni cambió de tamaño
        self.assertEqual(os.path.getsize(TEST_DISK_PATH), 16 + 10 * 8)
        # El contenido físico sigue en los mismos sectores (aunque el FS
        # en memoria ya no lo "sepa", el enunciado solo exige que el
        # archivo no se elimine)
        self.assertEqual(disk2.read(sectors), "hola!")


if __name__ == "__main__":
    unittest.main()
