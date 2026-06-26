import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, make_response, redirect, url_for
from .extensions import db, login_manager, csrf, mail, migrate
from .utils.media import (
    APP_FEATURES,
    logo_url,
    favicon_url,
    apple_touch_icon_url,
    favicon_16_url,
    sermon_placeholder_url,
    leader_placeholder_url,
    og_image_url,
    app_screenshots,
    qr_placeholder_url,
    app_page_url,
    app_qr_code_url,
)
from .utils.urls import cors_allow_origin
from .utils.social import get_social_links, CONTACT_ICON_BACKGROUNDS


def create_app():
    from config import ProductionConfig, config_by_name, get_config_name
    from .services.upload import ensure_upload_dirs

    config_name = get_config_name()
    if config_name == "production":
        ProductionConfig.validate()

    config_class = config_by_name.get(config_name, config_by_name["development"])
    app = Flask(__name__, instance_relative_config=False, static_folder='static', static_url_path='/static')
    app.config.from_object(config_class)

    os.makedirs("database", exist_ok=True)
    ensure_upload_dirs(app)

    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, "app.log"), maxBytes=1_048_576, backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        )
    )
    file_handler.setLevel(logging.INFO)
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Application startup")

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    @app.context_processor
    def inject_media_helpers():
        return {
            "logo_url": logo_url,
            "favicon_url": favicon_url,
            "apple_touch_icon_url": apple_touch_icon_url,
            "favicon_16_url": favicon_16_url,
            "sermon_placeholder_url": sermon_placeholder_url,
            "leader_placeholder_url": leader_placeholder_url,
            "og_image_url": og_image_url,
            "app_screenshots": app_screenshots,
            "qr_placeholder_url": qr_placeholder_url,
            "app_page_url": app_page_url,
            "app_qr_code_url": app_qr_code_url,
            "app_features": APP_FEATURES,
            "social_links": get_social_links(),
            "contact_social_backgrounds": CONTACT_ICON_BACKGROUNDS,
        }

    @app.after_request
    def add_cors_headers(response):
        if request.path.startswith("/api/"):
            origin = cors_allow_origin()
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
                response.headers["Vary"] = "Origin"
        return response

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.before_request
    def handle_api_preflight():
        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            origin = cors_allow_origin()
            if not origin:
                return make_response("CORS origin not allowed", 403)
            response = make_response("", 204)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
            response.headers["Vary"] = "Origin"
            return response

    from .routes.main_routes import main
    from .routes.auth_routes import auth
    from .routes.admin_routes import admin
    from .routes.sermon_routes import sermon
    from .routes.prayer_routes import prayer
    from .routes.class_routes import classes_bp
    from .routes.giving_routes import giving
    from .routes.api_routes import api

    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(admin, url_prefix="/admin")
    app.register_blueprint(sermon, url_prefix="/sermons")
    app.register_blueprint(prayer, url_prefix="/prayer")
    app.register_blueprint(classes_bp, url_prefix="/classes")
    app.register_blueprint(giving, url_prefix="/giving")
    app.register_blueprint(api)

    @app.route('/favicon.ico')
    def favicon():
        return redirect(url_for('static', filename='images/favicon.png'))

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app

