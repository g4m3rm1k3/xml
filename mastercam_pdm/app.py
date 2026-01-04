"""MastercamPDM - Manufacturing Data Platform."""
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import init_db, get_db, get_or_create_user_preference, update_user_preference
from parser import parse_xml_file, is_linear_program

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Path to Mastercam shared reports folder
# Template: C:\Users\Public\Documents\Shared Mastercam {version}\common\reports\xml
MASTERCAM_REPORTS_TEMPLATE = r"C:\Users\Public\Documents\Shared Mastercam {version}\common\reports\xml"

# Supported versions
MASTERCAM_VERSIONS = ['2024', '2025', '2026']


def get_reports_folder(version):
    """Get the XML reports folder for a given Mastercam version."""
    return MASTERCAM_REPORTS_TEMPLATE.format(version=version)


@app.before_request
def before_request():
    """Ensure database exists and load preferences."""
    init_db()


@app.route('/')
def index():
    """Dashboard - show configuration and imported parts."""
    db = get_db()
    
    # Get user preferences
    prefs = get_or_create_user_preference(db)
    
    parts = db.execute('''
        SELECT part_id, part_name, mastercam_version, machine, import_date,
               (SELECT COUNT(*) FROM operations WHERE operations.part_id = parts.part_id) as op_count
        FROM parts ORDER BY import_date DESC
    ''').fetchall()
    
    return render_template('index.html', 
                          parts=parts, 
                          prefs=prefs,
                          versions=MASTERCAM_VERSIONS)


@app.route('/set-preferences', methods=['POST'])
def set_preferences():
    """Update user preferences."""
    db = get_db()
    version = request.form.get('mastercam_version')
    machine = request.form.get('default_machine')
    
    update_user_preference(db, version, machine)
    flash('Preferences saved', 'success')
    return redirect(url_for('index'))


@app.route('/import', methods=['GET', 'POST'])
def import_part():
    """Import XML file."""
    db = get_db()
    prefs = get_or_create_user_preference(db)
    
    if request.method == 'POST':
        filename = request.form.get('filename')
        folder = request.form.get('folder', os.path.dirname(__file__) + '/..')
        machine = request.form.get('machine', '')
        
        if not machine:
            flash('Machine number is required', 'error')
            return redirect(url_for('import_part'))
        
        if filename:
            filepath = os.path.join(folder, filename)
            if os.path.exists(filepath):
                try:
                    part_id = parse_xml_file(filepath, machine)
                    flash(f'Successfully imported {filename}', 'success')
                    return redirect(url_for('part_detail', part_id=part_id))
                except Exception as e:
                    flash(f'Error importing: {e}', 'error')
            else:
                flash(f'File not found: {filename}', 'error')
        return redirect(url_for('import_part'))
    
    # GET - show available files from version-specific folder
    version = prefs.get('mastercam_version', '2026')
    xml_folder = get_reports_folder(version)
    
    xml_files = []
    folder_exists = os.path.exists(xml_folder)
    
    if folder_exists:
        xml_files = [f for f in os.listdir(xml_folder) if f.endswith('.xml')]
    
    return render_template('import.html', 
                          files=xml_files, 
                          folder=xml_folder,
                          folder_exists=folder_exists,
                          prefs=prefs,
                          versions=MASTERCAM_VERSIONS)


@app.route('/part/<int:part_id>')
def part_detail(part_id):
    """Show part details with operations grouped by subprogram."""
    db = get_db()
    
    part = db.execute(
        'SELECT * FROM parts WHERE part_id = ?', (part_id,)
    ).fetchone()
    
    if not part:
        flash('Part not found', 'error')
        return redirect(url_for('index'))
    
    # Get operations grouped by subprogram
    operations = db.execute('''
        SELECT o.*, ta.name as assembly_name, ta.tool_name, ta.holder_name
        FROM operations o
        LEFT JOIN tool_assemblies ta ON o.assembly_id = ta.assembly_id
        WHERE o.part_id = ?
        ORDER BY o.subprogram_number, o.op_order
    ''', (part_id,)).fetchall()
    
    # Group operations by subprogram for display
    subprograms = {}
    for op in operations:
        sp = op['subprogram_number'] or 'Main'
        if sp not in subprograms:
            subprograms[sp] = []
        subprograms[sp].append(op)
    
    return render_template('part_detail.html', part=part, subprograms=subprograms)


@app.route('/assemblies')
def assemblies():
    """Browse tool assemblies."""
    db = get_db()
    type_filter = request.args.get('type')
    
    if type_filter:
        assemblies = db.execute('''
            SELECT ta.*, COUNT(o.operation_id) as usage_count
            FROM tool_assemblies ta
            LEFT JOIN operations o ON ta.assembly_id = o.assembly_id
            WHERE ta.tool_type = ?
            GROUP BY ta.assembly_id
            ORDER BY ta.name
        ''', (type_filter,)).fetchall()
    else:
        assemblies = db.execute('''
            SELECT ta.*, COUNT(o.operation_id) as usage_count
            FROM tool_assemblies ta
            LEFT JOIN operations o ON ta.assembly_id = o.assembly_id
            GROUP BY ta.assembly_id
            ORDER BY ta.name
        ''').fetchall()
    
    # Get unique types for filter
    types = db.execute('SELECT DISTINCT tool_type FROM tool_assemblies WHERE tool_type IS NOT NULL').fetchall()
    
    return render_template('assemblies.html', 
                          assemblies=assemblies, 
                          types=[t['tool_type'] for t in types],
                          current_filter=type_filter)


@app.route('/assembly/<int:assembly_id>')
def assembly_detail(assembly_id):
    """Show assembly details with usage across operations."""
    db = get_db()
    
    # Get assembly info
    assembly = db.execute(
        'SELECT * FROM tool_assemblies WHERE assembly_id = ?', (assembly_id,)
    ).fetchone()
    
    if not assembly:
        flash('Assembly not found', 'error')
        return redirect(url_for('assemblies'))
    
    # Get all operations using this assembly
    usages = db.execute('''
        SELECT o.*, p.part_name, p.machine
        FROM operations o
        JOIN parts p ON o.part_id = p.part_id
        WHERE o.assembly_id = ?
        ORDER BY p.part_name, o.op_order
    ''', (assembly_id,)).fetchall()
    
    # Group by part
    parts_usage = {}
    for usage in usages:
        part_name = usage['part_name']
        if part_name not in parts_usage:
            parts_usage[part_name] = {
                'machine': usage['machine'],
                'operations': []
            }
        parts_usage[part_name]['operations'].append(usage)
    
    return render_template('assembly_detail.html', 
                          assembly=assembly, 
                          parts_usage=parts_usage,
                          total_usage=len(usages))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
