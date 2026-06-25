"""
Maneja el archivo físico que representa el disco virtual, dividido en
sectores, con asignación enlazada y estrategia First Fit.

Formato del archivo .bin:

    [HEADER][SECTOR 0][SECTOR 1]...[SECTOR N-1]

Header (16 bytes, fijo):
    - 8 bytes: sector_count (entero, big endian)
    - 8 bytes: sector_size  (entero, big endian)

Cada sector mide exactamente sector_size bytes en disco. El contenido de
un archivo se parte en chunks de sector_size y se escribe uno por sector,
en el orden que indique la lista de sectores recibida (que ya viene
encadenada lógicamente por SectorManager).

La cadena de encadenamiento (qué sector sigue a cuál) se maneja en
memoria, en SectorManager — el enunciado permite esto explícitamente.

Ver docs/SHARED.md para el contrato completo con filesystem/.
"""

import os
from typing import List

from storage.sector_manager import SectorManager
from file_system.exceptions import DiskFullError

HEADER_SIZE = 16  # bytes


class VirtualDisk:
    def __init__(self):
        self.path = None
        self.sector_count = 0
        self.sector_size = 0
        self.sector_manager: SectorManager = None

    def create_disk(self, sector_count: int, sector_size: int, path: str = "disk/virtual_disk.bin") -> None:
        """
        Crea el archivo .bin con el tamaño sector_count * sector_size + header.
        Si el archivo ya existe, lo abre y lee su header en vez de
        sobrescribirlo (así no se pierde un disco previo, tal como exige
        el enunciado: el archivo de disco no se debe eliminar al cerrar
        la app).
        """
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if os.path.exists(path) and os.path.getsize(path) >= HEADER_SIZE:
            self._open_existing_disk()
        else:
            self._create_new_disk(sector_count, sector_size)

    def _create_new_disk(self, sector_count: int, sector_size: int) -> None:
        self.sector_count = sector_count
        self.sector_size = sector_size
        self.sector_manager = SectorManager(sector_count)

        total_size = HEADER_SIZE + sector_count * sector_size
        with open(self.path, "wb") as f:
            header = sector_count.to_bytes(8, "big") + sector_size.to_bytes(8, "big")
            f.write(header)
            f.write(b"\x00" * (sector_count * sector_size))

        assert os.path.getsize(self.path) == total_size

    def _open_existing_disk(self) -> None:
        with open(self.path, "rb") as f:
            header = f.read(HEADER_SIZE)
        self.sector_count = int.from_bytes(header[0:8], "big")
        self.sector_size = int.from_bytes(header[8:16], "big")
        # El file system en memoria se pierde al cerrar la app (según el
        # enunciado), así que al reabrir tratamos todos los sectores como
        # libres nuevamente; no se mantiene un bitmap persistido en disco.
        self.sector_manager = SectorManager(self.sector_count)

    def allocate(self, file_size: int) -> List[int]:
        """
        Reserva los sectores necesarios para file_size bytes usando
        First Fit. Devuelve la lista de índices de sector, en el orden
        en que quedan encadenados.
        """
        needed = self._sectors_needed(file_size)
        if needed == 0:
            return []

        sectors = self.sector_manager.find_first_fit(needed)
        if len(sectors) < needed:
            raise DiskFullError(
                f"No hay suficientes sectores libres: se necesitan {needed}, "
                f"hay {self.sector_manager.available_sectors()} disponibles."
            )

        self.sector_manager.mark_allocated(sectors)
        return sectors

    def free(self, sector_list: List[int]) -> None:
        """Libera los sectores indicados."""
        self.sector_manager.free_sectors_list(sector_list)

    def write(self, sector_list: List[int], content: str) -> None:
        """
        Escribe el contenido distribuido en los sectores indicados, en
        el orden de la lista. Si el último sector queda con espacio
        libre, se rellena con ceros (fragmentación interna, esperada
        según el enunciado).
        """
        data = content.encode("utf-8")
        with open(self.path, "r+b") as f:
            for i, sector in enumerate(sector_list):
                start = i * self.sector_size
                chunk = data[start:start + self.sector_size]
                if len(chunk) < self.sector_size:
                    chunk = chunk + b"\x00" * (self.sector_size - len(chunk))
                f.seek(self._sector_offset(sector))
                f.write(chunk)

    def read(self, sector_list: List[int]) -> str:
        """Lee y reconstruye el contenido siguiendo la lista de sectores."""
        if not sector_list:
            return ""

        raw = bytearray()
        with open(self.path, "rb") as f:
            for sector in sector_list:
                f.seek(self._sector_offset(sector))
                raw.extend(f.read(self.sector_size))

        # Quitamos el padding de ceros del final (relleno del último sector)
        return raw.rstrip(b"\x00").decode("utf-8", errors="replace")

    def available_space(self) -> int:
        """Bytes disponibles actualmente en el disco."""
        return self.sector_manager.available_sectors() * self.sector_size

    def _sectors_needed(self, file_size: int) -> int:
        if file_size <= 0:
            return 0
        return -(-file_size // self.sector_size)  # ceil division

    def _sector_offset(self, sector: int) -> int:
        return HEADER_SIZE + sector * self.sector_size