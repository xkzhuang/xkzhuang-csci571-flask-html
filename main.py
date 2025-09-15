import os
from pathlib import Path
from flask import Flask, render_template, send_from_directory

from blueprints.search import create_search_blueprint
from services.google_map_service import GoogleMapService
from services.ticketmaster_service import TicketMasterService


def create_app() -> Flask:
    base_dir = Path(__file__).resolve().parent

    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
        static_url_path="/static",
    )

    # Load API keys from environment
    google_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    ticketmaster_api_key = os.getenv("TICKETMASTER_API_KEY", "")

    # Initialize services
    google_service = GoogleMapService(api_key=google_api_key)
    ticketmaster_service = TicketMasterService()

    # Register blueprints
    app.register_blueprint(
        create_search_blueprint(ticketmaster_service, google_service, ticketmaster_api_key)
    )

    # Routes to serve index
    @app.route("/")
    @app.route("/index.html")
    def index():
        return render_template("index.html")

    # Serve files from media/ directory
    @app.route("/media/<path:filename>")
    def media(filename: str):
        return send_from_directory(str(base_dir / "media"), filename)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
