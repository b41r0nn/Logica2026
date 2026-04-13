"""
medicamento.py
Clase de dominio que representa un medicamento con nombre y hora de toma.
"""
import datetime


class Medicamento:
    """Representa un medicamento con su nombre y hora de toma programada."""

    def __init__(self, nombre: str, hora: datetime.time):
        if not nombre or not isinstance(nombre, str):
            raise ValueError("El nombre del medicamento debe ser una cadena no vacía.")
        if not isinstance(hora, datetime.time):
            raise TypeError("La hora debe ser un objeto datetime.time.")
        self.nombre = nombre.strip()
        self.hora = hora

    def __repr__(self) -> str:
        return f"Medicamento(nombre='{self.nombre}', hora={self.hora.strftime('%H:%M')})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Medicamento):
            return NotImplemented
        return self.nombre == other.nombre and self.hora == other.hora
