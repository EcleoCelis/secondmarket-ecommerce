from werkzeug.exceptions import HTTPException

from backend.app.core.responses import error_response


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return error_response(
            message=error.description,
            status_code=error.code,
            code=error.name.lower().replace(" ", "_"),
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        app.logger.exception("Unhandled application error", exc_info=error)
        return error_response(
            message="An unexpected server error occurred.",
            status_code=500,
            code="internal_server_error",
        )
