"""
main.py
Punto de entrada del sistema de alertas de medicamentos.
Carga la configuración desde .env, lee el CSV con pandas,
e inicia el monitor que revisa cada minuto si es hora de algún medicamento
y, si corresponde, envía un correo electrónico de alerta.
"""
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

from cargador_csv import CargadorCSV
from medicamento import Medicamento
from notificador import NotificadorCorreo


# ──────────────────────────────────────────────
# Clase MonitorMedicamentos
# ──────────────────────────────────────────────
class MonitorMedicamentos:
    """
    Revisa periódicamente la hora actual y, si coincide con la hora de
    algún medicamento, solicita al notificador que envíe la alerta.
    """

    def __init__(
        self,
        medicamentos: list,
        notificador: NotificadorCorreo,
        intervalo_segundos: int = 60,
        ruta_csv: str = "medicamentos.csv",
    ):
        self.medicamentos = medicamentos
        self.notificador = notificador
        self.intervalo_segundos = intervalo_segundos
        self.ruta_csv = ruta_csv
        self._cargador = CargadorCSV()

    # ------------------------------------------------------------------
    def _recargar_csv(self) -> None:
        """Recarga el CSV para reflejar cambios en caliente."""
        try:
            self.medicamentos = self._cargador.cargar(self.ruta_csv)
        except Exception as exc:
            print(f"⚠️  No se pudo recargar el CSV: {exc}")

    # ------------------------------------------------------------------
    def iniciar(self) -> None:
        """Bucle principal: revisa la hora y envía alertas cuando corresponde."""
        print(
            f"🟢 Monitor iniciado — revisando cada {self.intervalo_segundos} segundo(s).\n"
            f"   Medicamentos cargados: {[m.nombre for m in self.medicamentos]}\n"
            f"   Presiona Ctrl+C para detener.\n"
        )

        ultimo_dia_recarga = datetime.now().date()

        try:
            while True:
                ahora = datetime.now()

                # Recarga el CSV una vez al día (a la medianoche)
                if ahora.date() != ultimo_dia_recarga:
                    print("🔄 Nuevo día detectado — recargando el CSV...")
                    self._recargar_csv()
                    ultimo_dia_recarga = ahora.date()

                hora_actual = ahora.time().replace(second=0, microsecond=0)

                for med in self.medicamentos:
                    if med.hora == hora_actual:
                        print(f"⏰ [{ahora.strftime('%H:%M')}] Hora de tomar {med.nombre}")
                        self.notificador.enviar_alerta(med)

                time.sleep(self.intervalo_segundos)

        except KeyboardInterrupt:
            print("\n⏹️  Monitor detenido por el usuario. ¡Hasta pronto!")


# ──────────────────────────────────────────────
# Carga de configuración
# ──────────────────────────────────────────────
def cargar_configuracion() -> dict:
    """
    Lee las variables de entorno desde el archivo .env.
    Lanza SystemExit si falta alguna variable obligatoria.
    """
    # Busca .env junto al script, independientemente del directorio de trabajo
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(dotenv_path=_env_path)

    variables = {
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME"),
        "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD"),
        "MAIL_ALERT": os.getenv("MAIL_ALERT"),
        "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "SMTP_PORT": os.getenv("SMTP_PORT", "587"),
    }

    obligatorias = ["MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_ALERT"]
    faltantes = [v for v in obligatorias if not variables[v]]
    if faltantes:
        print(
            f"❌ Faltan las siguientes variables en el archivo .env: {faltantes}\n"
            "   Edita proyecto_medicamentos/.env con tus credenciales y vuelve a intentarlo."
        )
        sys.exit(1)

    try:
        variables["SMTP_PORT"] = int(variables["SMTP_PORT"])
    except ValueError:
        print("❌ SMTP_PORT debe ser un número entero.")
        sys.exit(1)

    # Convertir lista de destinatarios separados por coma
    variables["MAIL_ALERT"] = [
        d.strip() for d in variables["MAIL_ALERT"].split(",") if d.strip()
    ]

    return variables


# ──────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────
def main() -> None:
    print("=" * 55)
    print("  Sistema de alertas de medicamentos vía correo")
    print("=" * 55)

    cfg = cargar_configuracion()

    # Ruta al CSV (misma carpeta que main.py)
    # Usa horariosmedicamentos.csv si existe, si no cae en medicamentos.csv
    _base = os.path.dirname(__file__)
    _preferido = os.path.join(_base, "horariosmedicamentos.csv")
    _alternativo = os.path.join(_base, "medicamentos.csv")
    ruta_csv = _preferido if os.path.exists(_preferido) else _alternativo

    try:
        medicamentos = CargadorCSV().cargar(ruta_csv)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    notificador = NotificadorCorreo(
        smtp_server=cfg["SMTP_SERVER"],
        smtp_port=cfg["SMTP_PORT"],
        username=cfg["MAIL_USERNAME"],
        password=cfg["MAIL_PASSWORD"],
        destinatarios=cfg["MAIL_ALERT"],
    )

    monitor = MonitorMedicamentos(
        medicamentos=medicamentos,
        notificador=notificador,
        intervalo_segundos=60,
        ruta_csv=ruta_csv,
    )
    monitor.iniciar()


if __name__ == "__main__":
    main()
