"""MastercamXML - Manufacturing Data Platform."""
from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_db, get_user_preferences, update_user_preference
from parser import parse_xml_file

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production' 

@app.route('/import', methods=['GET', 'POST'])
def import_part():
    """Import XML file."""
    db = get_db()
    prefs = get_user_preferences(db)

    if request.method == 'POST':
        machine = request.form.get('machine', '').strip()
        filepath = request.form.get('filepath', '').strip()

        # Validate inputs
        if not machine:
            flash('Machine number is required', 'error')
            return redirect(url_for('import_part'))

        if not filepath:
            flash('File path is required', 'error')
            return redirect(url_for('import_part'))

        # Parse and import
        try:
            part_id = parse_xml_file(filepath, machine)
            flash(f'Successfully imported part (ID: {part_id})', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error importing: {e}", "error")
            return redirect(url_for('import_part'))

    # Get reqeust - show form
    db.close()
    return render_template('import.html', default_machine=prefs['default_machine'])


@app.before_request
def before_request():
    """Ensure database exists before each request."""
    init_db()

@app.route('/')
def index():
    """Dashboard - show imported parts."""
    db = get_db()
    parts = db.execute('SELECT * FROM parts ORDER BY import_date DESC').fetchall()
    db.close()
    return render_template('index.html', parts=parts)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
