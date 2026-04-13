"""
cargador_csv.py
Clase responsable de leer el archivo CSV de medicamentos con pandas
y retornar una lista de objetos Medicamento.
"""
import pandas as pd
from medicamento import Medicamento


# Mapeo de nombres de columnas alternativos al nombre canónico
_ALIAS_MEDICAMENTO = {"medicamento", "Medicamento", "MEDICAMENTO", "nombre", "Nombre"}
_ALIAS_HORA = {"hora", "Hora", "HORA", "horario", "Horario", "HORARIO"}


class CargadorCSV:
    """Lee un CSV con columnas de medicamento y hora y devuelve objetos Medicamento.

    Acepta separadores ',' o ';' y nombres de columna en español
    (medicamento/Medicamento, hora/Hora, horario/Horario).
    """

    @staticmethod
    def _detectar_separador(ruta: str) -> str:
        """Devuelve ',' o ';' según cuál aparece más en la primera línea del archivo."""
        with open(ruta, encoding="utf-8-sig", errors="replace") as f:
            primera = f.readline()
        return ";" if primera.count(";") >= primera.count(",") else ","

    @staticmethod
    def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
        """Renombra columnas alternativas a 'medicamento' y 'hora'."""
        renombrar = {}
        for col in df.columns:
            col_limpio = col.strip().strip('"')
            if col_limpio in _ALIAS_MEDICAMENTO:
                renombrar[col] = "medicamento"
            elif col_limpio in _ALIAS_HORA:
                renombrar[col] = "hora"
        return df.rename(columns=renombrar)

    @staticmethod
    def _leer_como_texto(ruta: str, sep: str) -> pd.DataFrame:
        """
        Fallback: lee el archivo línea a línea, quita comillas envolventes
        y divide por el separador. Útil cuando cada fila está entre comillas.
        """
        filas = []
        with open(ruta, encoding="utf-8-sig", errors="replace") as f:
            for linea in f:
                linea = linea.strip().strip('"')
                if linea:
                    partes = [p.strip().strip('"') for p in linea.split(sep)]
                    filas.append(partes)
        if not filas:
            raise ValueError("El archivo CSV está vacío.")
        encabezado = filas[0]
        datos = filas[1:]
        return pd.DataFrame(datos, columns=encabezado)

    def cargar(self, ruta: str) -> list:
        """
        Lee el CSV en `ruta` y retorna una lista de Medicamento.
        Las filas con formato de hora inválido son omitidas con un aviso.
        """
        try:
            sep = self._detectar_separador(ruta)
            df = pd.read_csv(ruta, sep=sep, skipinitialspace=True, encoding="utf-8-sig")
            # Limpiar comillas extras que algunos editores agregan
            df.columns = [c.strip().strip('"') for c in df.columns]
            df = self._normalizar_columnas(df)

            # Si la detección normal produce una sola columna con el separador
            # dentro, el archivo usa comillas envolventes por fila → fallback
            if len(df.columns) == 1 and sep in df.columns[0]:
                df = self._leer_como_texto(ruta, sep)
                df.columns = [c.strip().strip('"') for c in df.columns]
                df = self._normalizar_columnas(df)
        except FileNotFoundError:
            raise FileNotFoundError(f"No se encontró el archivo CSV: {ruta}")
        except Exception as exc:
            raise RuntimeError(f"Error al leer el CSV: {exc}") from exc

        columnas_requeridas = {"medicamento", "hora"}
        if not columnas_requeridas.issubset(df.columns):
            raise ValueError(
                f"El CSV debe contener columnas de medicamento y hora. "
                f"Columnas encontradas: {set(df.columns)}"
            )

        medicamentos = []
        for idx, row in df.iterrows():
            try:
                hora = pd.to_datetime(str(row["hora"]), format="%H:%M").time()
                medicamentos.append(Medicamento(str(row["medicamento"]), hora))
            except (ValueError, TypeError) as exc:
                print(
                    f"⚠️  Fila {idx + 2} ignorada — formato de hora inválido "
                    f"('{row['hora']}'): {exc}"
                )

        if not medicamentos:
            raise ValueError("No se cargó ningún medicamento válido desde el CSV.")

        print(f"✅ {len(medicamentos)} medicamento(s) cargado(s) desde '{ruta}'.")
        return medicamentos
