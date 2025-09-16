from telegraph import Telegraph
import logging

from html import escape
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegraphService:
    def __init__(self, access_token: str):
        """
        Initialize the Telegraph client and create an account if no access token exists.
        """
        self.telegraph = Telegraph(access_token=access_token)
        self.author_name = 'BCN Transit Bot'

    def create_page(self, title: str, alerts) -> str:
        """
        Create a new Telegraph page.

        Args:
            title (str): Title of the page.
            html_content (str): Content in HTML format.

        Returns:
            str: URL of the created page.
        """
        try:
            response = self.telegraph.create_page(
                title=title,
                html_content=self.generate_telegraph_html(alerts)[:30000], # Telegraph has a limit of 64KB per page
                author_name=self.author_name
            )
            page_url = "https://telegra.ph/" + response["path"]
            logger.info(f"Telegraph page created: {page_url}")
            return page_url
        except Exception as e:
            logger.error(f"Failed to create Telegraph page: {e}")


    # lang: "es" | "en" | "ca"
    def generate_telegraph_html(self, alerts, title="Incidencias de la línea"):
        def fmt_date(s):
            try:
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt = datetime.strptime(s, fmt)
                        return dt.strftime("%d/%m/%Y %H:%M")
                    except ValueError:
                        continue
            except Exception:
                pass
            return s

        def get_status_emoji(status):
                status = (status or "").upper()
                return {
                    "WARNING": "⚠️",
                    "INFO": "ℹ️",
                    "CLOSED": "⛔",
                    "RESOLVED": "✅"
                }.get(status, "ℹ️")

        def get_cause_emoji(cause):
            cause = (cause or "").upper()
            return {
                "MAINTENANCE": "🛠️",
                "CONSTRUCTION": "🏗️",
                "INCIDENT": "⚠️",
                "TRAFFIC": "🚦"
            }.get(cause, "")

        html = []
        html.append(f"<h3>{escape(str(title))}</h3>")

        if not alerts:
            html.append("<p><em>No hay incidencias en este momento.</em></p>")
            return "".join(html)

        for a in alerts:
            header_txt = ""
            body_txt = ""
            for p in (a.publications or []):
                if p.headerEs or p.textEs:
                    header_txt, body_txt = p.headerEs or "", p.textEs or ""
                    break

            # Entidades afectadas
            ent_rows = []
            for e in (a.affected_entities or []):
                ent_rows.append(
                    f"<li><b>{escape(e.line_name or e.line_code or '')}</b> — "
                    f"{escape(e.station_name or e.station_code or '')}"
                    f"{' · ' + escape(e.direction_name) if e.direction_name else ''}"
                    f"{' · ' + escape(e.entrance_name) if e.entrance_name else ''}</li>"
                )
            affected_html = ""
            if ent_rows:
                affected_html = f"""
    <p><u>Áreas afectadas:</u></p>
    <ul>
        {''.join(ent_rows)}
    </ul>
    """

            # Fechas
            period_html = f"<p><b>Desde:</b> {a.begin_date or ''}"
            if a.end_date:
                period_html += f" · <b>Hasta:</b> {a.end_date or ''}"
            period_html += "</p>"

            # Texto de la publicación
            body_html = ""
            if body_txt:
                safe_body = escape(body_txt).replace("\n", "<br>")
                body_html = f"<p>{safe_body}</p>"

            status_emoji = get_status_emoji(a.status)
            cause_emoji = get_cause_emoji(a.cause)

            html.append(f"""
    <hr>
    <p><b><u>🚨 {escape(header_txt or 'Incidencia')}</u></b></p>
    <p><b>ID:</b> {escape(str(a.id) )}</p>
    <p><b>Estado:</b> {status_emoji} {escape(a.status or 'Desconocido')}</p>
    <p><b>Causa:</b> {cause_emoji} {escape(a.cause or 'Desconocida')}</p>
    {period_html}
    {affected_html}
    {body_html}
    _______________________________________
    """)

        return "".join(html)
