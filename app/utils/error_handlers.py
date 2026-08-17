from flask import render_template, request, jsonify


def register_error_handlers(app):
    """Register custom HTTP & JSON error handlers for Flask application"""

    def is_json_request():
        return (
            request.is_json or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            request.path.startswith('/ai/') or
            request.path.startswith('/api/') or
            request.path.startswith('/cart/') or
            request.path.startswith('/wishlist/')
        )

    @app.errorhandler(400)
    def bad_request(e):
        if is_json_request():
            return jsonify({'success': False, 'ai_response': 'Bad request or invalid parameters. Please try again.', 'message': str(e)}), 400
        return render_template('errors/500.html'), 400

    @app.errorhandler(404)
    def page_not_found(e):
        if is_json_request():
            return jsonify({'success': False, 'ai_response': 'Requested endpoint not found.', 'message': 'Not Found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        if is_json_request():
            return jsonify({'success': False, 'ai_response': 'An internal server error occurred. Please try again.', 'message': 'Internal Server Error'}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(e):
        if is_json_request():
            return jsonify({'success': False, 'ai_response': 'Access forbidden.', 'message': 'Forbidden'}), 403
        return render_template('errors/404.html'), 403

    try:
        from flask_wtf.csrf import CSRFError
        @app.errorhandler(CSRFError)
        def handle_csrf_error(e):
            if is_json_request():
                return jsonify({'success': False, 'ai_response': 'CSRF token missing or expired. Please refresh the page and try again.', 'message': e.description}), 400
            return render_template('errors/500.html'), 400
    except Exception:
        pass
