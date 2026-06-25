"""
Maneja qué sectores están libres/ocupados y la cadena de encadenamiento
(asignación enlazada) de cada archivo. Todo en memoria, tal como permite
el enunciado ("el puntero no es necesario que lo tengan en el mismo sector").
"""

from typing import List, Optional, Dict


class SectorManager:
    def __init__(self, sector_count: int):
        self.sector_count = sector_count
        # Todos los sectores empiezan libres
        self.free_sectors = set(range(sector_count))
        # Cadena enlazada: sector actual -> siguiente sector (None si es el último)
        self.chain: Dict[int, Optional[int]] = {}

    def find_first_fit(self, needed: int) -> List[int]:
        """
        Busca 'needed' sectores libres usando First Fit: recorre los
        sectores en orden de índice y toma los primeros que estén libres,
        sin necesidad de que sean contiguos (asignación enlazada).

        Devuelve la lista de sectores en el orden en que quedarán
        encadenados. No los marca como ocupados todavía (eso lo hace
        VirtualDisk.allocate después de confirmar que hay suficientes).
        """
        if needed <= 0:
            return []

        if needed > len(self.free_sectors):
            return []  # VirtualDisk decide lanzar DiskFullError

        found = []
        for sector in range(self.sector_count):
            if sector in self.free_sectors:
                found.append(sector)
                if len(found) == needed:
                    break
        return found

    def mark_allocated(self, sector_list: List[int]) -> None:
        """Marca los sectores como ocupados y construye la cadena enlazada
        en el orden recibido."""
        for sector in sector_list:
            self.free_sectors.discard(sector)

        for i, sector in enumerate(sector_list):
            if i + 1 < len(sector_list):
                self.chain[sector] = sector_list[i + 1]
            else:
                self.chain[sector] = None  # último sector de la cadena

    def free_sectors_list(self, sector_list: List[int]) -> None:
        """Libera los sectores indicados y borra su entrada en la cadena."""
        for sector in sector_list:
            self.free_sectors.add(sector)
            self.chain.pop(sector, None)

    def get_chain_from(self, start_sector: int) -> List[int]:
        """Devuelve la lista completa de sectores siguiendo la cadena
        a partir de start_sector."""
        chain = []
        current = start_sector
        visited = set()
        while current is not None:
            if current in visited:
                # Protección ante una cadena corrupta/circular
                break
            visited.add(current)
            chain.append(current)
            current = self.chain.get(current)
        return chain

    def available_sectors(self) -> int:
        return len(self.free_sectors)