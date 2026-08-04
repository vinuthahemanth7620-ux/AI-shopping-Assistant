from app import create_app, db

app = create_app()

if __name__ == '__main__':
    # Initialize tables if connected to DB
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Database connection auto-creation skipped: {e}")
            
    app.run(host='0.0.0.0', port=5000, debug=True)
