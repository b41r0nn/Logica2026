"""
notificador.py
Clase NotificadorCorreo: gestiona el envío de alertas por correo electrónico
usando SMTP con inicio de sesión TLS.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

from medicamento import Medicamento


class NotificadorCorreo:
    """Envía correos de alerta de medicamento vía SMTP."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        destinatarios: List[str],
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.destinatarios = destinatarios

    # ------------------------------------------------------------------
    def _construir_mensaje(self, med: Medicamento) -> MIMEMultipart:
        """Construye el mensaje MIME para la alerta del medicamento dado."""
        asunto = f"Recordatorio de medicamento: {med.nombre}"
        cuerpo = (
            f"Hola,\n\n"
            f"Es hora de tomar {med.nombre} a las {med.hora.strftime('%H:%M')}.\n\n"
            f"Por favor, no olvides tomar tu medicamento.\n\n"
            f"— Sistema de alertas de medicamentos"
        )

        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = ", ".join(self.destinatarios)
        msg["Subject"] = asunto
        msg.attach(MIMEText(cuerpo, "plain", "utf-8"))
        return msg

    # ------------------------------------------------------------------
    def enviar_alerta(self, med: Medicamento) -> bool:
        """
        Envía el correo de alerta para `med`.
        Retorna True si se envió correctamente, False en caso de error.
        Los errores se muestran por consola pero NO propagan la excepción,
        así el monitor no se detiene ante fallos de red o SMTP.
        """
        msg = self._construir_mensaje(med)
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.username, self.destinatarios, msg.as_string())
            server.quit()
            print(
                f"📧 Correo enviado a {self.destinatarios} "
                f"— Medicamento: {med.nombre} ({med.hora.strftime('%H:%M')})"
            )
            return True
        except Exception as e:
            print(f"❌ Error al enviar correo: {str(e)}")
        return False
