#!/usr/bin/env python3
"""
visualize_schema.py — Visualize the database schema
FIXED: Saves files in database/schema_docs folder
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime


def find_database():
    """Find the database file using same logic as database.py"""
    script_dir = Path(__file__).parent

    # Priority 1: Same directory as script
    db_path = script_dir / "unified_country_database.db"
    if db_path.exists():
        return str(db_path)

    # Priority 2: Parent directory
    parent_db = script_dir.parent / "unified_country_database.db"
    if parent_db.exists():
        return str(parent_db)

    # Priority 3: data subdirectory
    data_db = script_dir / "data" / "unified_country_database.db"
    if data_db.exists():
        return str(data_db)

    # If not found, return default path (will show better error)
    return str(db_path)


# Set output directory relative to script location
script_dir = Path(__file__).parent
OUTPUT_DIR = script_dir / "schema_docs"
DB_PATH = find_database()


def get_schema_info(db_path):
    """Extract complete schema information from database."""
    if not Path(db_path).exists():
        print(f"\n❌ ERROR: Database file not found at: {db_path}")
        print(f"\nSearched in:")
        script_dir = Path(__file__).parent
        print(f"  - {script_dir / 'unified_country_database.db'}")
        print(f"  - {script_dir.parent / 'unified_country_database.db'}")
        print(f"  - {script_dir / 'data' / 'unified_country_database.db'}")
        print(f"\n💡 Make sure you ran: python3 database.py")
        return {}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    schema_info = {}

    for table in tables:
        # Get table info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]

        # Get indexes
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()

        schema_info[table] = {
            'columns': [
                {
                    'cid': col[0],
                    'name': col[1],
                    'type': col[2],
                    'notnull': bool(col[3]),
                    'default': col[4],
                    'pk': bool(col[5])
                }
                for col in columns
            ],
            'row_count': row_count,
            'indexes': [idx[1] for idx in indexes]
        }

    conn.close()
    return schema_info


def create_text_schema(schema_info, output_path):
    """Create a text-based schema documentation."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("DATABASE SCHEMA DOCUMENTATION\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")

        for table_name, info in schema_info.items():
            f.write(f"\n{'='*80}\n")
            f.write(f"TABLE: {table_name}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Row Count: {info['row_count']:,}\n")

            if info['indexes']:
                f.write(f"Indexes: {', '.join(info['indexes'])}\n")

            f.write(f"\nColumns ({len(info['columns'])}):\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Name':<30} {'Type':<15} {'Null':<6} {'Key':<6} {'Default'}\n")
            f.write("-" * 80 + "\n")

            for col in info['columns']:
                null_str = 'NULL' if not col['notnull'] else 'NOT NULL'
                pk_str = 'PK' if col['pk'] else ''
                default_str = str(col['default']) if col['default'] else ''

                f.write(f"{col['name']:<30} {col['type']:<15} {null_str:<6} {pk_str:<6} {default_str}\n")

            f.write("\n")

    print(f"✓ Created text schema: {output_path}")


def create_markdown_schema(schema_info, output_path):
    """Create a Markdown schema documentation."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Database Schema Documentation\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("---\n\n")

        # Table of contents
        f.write("## Tables\n\n")
        for table_name, info in schema_info.items():
            f.write(f"- [{table_name}](#{table_name.lower()}) ({info['row_count']:,} rows)\n")
        f.write("\n---\n\n")

        # Detailed table info
        for table_name, info in schema_info.items():
            f.write(f"## {table_name}\n\n")
            f.write(f"**Row Count:** {info['row_count']:,}\n\n")

            if info['indexes']:
                f.write(f"**Indexes:** {', '.join(info['indexes'])}\n\n")

            f.write("### Columns\n\n")
            f.write("| Column | Type | Null | Key | Default |\n")
            f.write("|--------|------|------|-----|---------|\n")

            for col in info['columns']:
                null_str = '✓' if not col['notnull'] else '✗'
                pk_str = '🔑' if col['pk'] else ''
                default_str = str(col['default']) if col['default'] else ''

                f.write(f"| {col['name']} | {col['type']} | {null_str} | {pk_str} | {default_str} |\n")

            f.write("\n")

    print(f"✓ Created Markdown schema: {output_path}")


def create_html_schema(schema_info, output_path):
    """Create an interactive HTML schema browser."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Schema Viewer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header h1 { font-size: 2rem; margin-bottom: 0.5rem; }
        .header p { opacity: 0.9; }

        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }

        .table-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .table-card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .table-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .table-card h3 {
            color: #667eea;
            margin-bottom: 0.5rem;
            font-size: 1.25rem;
        }

        .table-card .row-count {
            color: #666;
            font-size: 0.9rem;
        }

        .table-card .indexes {
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: #888;
        }

        .table-detail {
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: none;
        }

        .table-detail.active { display: block; }

        .table-detail h2 {
            color: #667eea;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #667eea;
        }

        .columns-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }

        .columns-table th {
            background: #f8f9fa;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }

        .columns-table td {
            padding: 0.75rem;
            border-bottom: 1px solid #e9ecef;
        }

        .columns-table tr:hover {
            background: #f8f9fa;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-pk {
            background: #667eea;
            color: white;
        }

        .badge-notnull {
            background: #f59e0b;
            color: white;
        }

        .back-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 1rem;
        }

        .back-btn:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🗄️ Database Schema Viewer</h1>
        <p>Interactive schema browser for unified_country_database.db</p>
    </div>

    <div class="container">
        <div id="tableList" class="table-list">
"""

    # Add table cards
    for table_name, info in schema_info.items():
        html += f"""
            <div class="table-card" onclick="showTable('{table_name}')">
                <h3>{table_name}</h3>
                <div class="row-count">{info['row_count']:,} rows • {len(info['columns'])} columns</div>
"""
        if info['indexes']:
            html += f"""
                <div class="indexes">📊 Indexes: {', '.join(info['indexes'])}</div>
"""
        html += """
            </div>
"""

    html += """
        </div>
"""

    # Add detail views
    for table_name, info in schema_info.items():
        html += f"""
        <div id="detail-{table_name}" class="table-detail">
            <button class="back-btn" onclick="showList()">← Back to Tables</button>
            <h2>{table_name}</h2>
            <p><strong>Rows:</strong> {info['row_count']:,}</p>
"""
        if info['indexes']:
            html += f"""
            <p><strong>Indexes:</strong> {', '.join(info['indexes'])}</p>
"""

        html += """
            <table class="columns-table">
                <thead>
                    <tr>
                        <th>Column</th>
                        <th>Type</th>
                        <th>Constraints</th>
                        <th>Default</th>
                    </tr>
                </thead>
                <tbody>
"""

        for col in info['columns']:
            constraints = []
            if col['pk']:
                constraints.append('<span class="badge badge-pk">PRIMARY KEY</span>')
            if col['notnull']:
                constraints.append('<span class="badge badge-notnull">NOT NULL</span>')

            constraints_html = ' '.join(constraints) if constraints else '—'
            default_html = col['default'] if col['default'] else '—'

            html += f"""
                    <tr>
                        <td><strong>{col['name']}</strong></td>
                        <td>{col['type']}</td>
                        <td>{constraints_html}</td>
                        <td>{default_html}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
        </div>
"""

    html += """
    </div>

    <script>
        function showTable(tableName) {
            document.getElementById('tableList').style.display = 'none';
            document.querySelectorAll('.table-detail').forEach(el => el.classList.remove('active'));
            document.getElementById('detail-' + tableName).classList.add('active');
        }

        function showList() {
            document.getElementById('tableList').style.display = 'grid';
            document.querySelectorAll('.table-detail').forEach(el => el.classList.remove('active'));
        }
    </script>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Created HTML schema viewer: {output_path}")


def create_graphviz_diagram(schema_info, output_path):
    """Create a Graphviz DOT file for ER diagram."""
    try:
        dot_content = """digraph schema {
    rankdir=LR;
    node [shape=record, style=filled, fillcolor=lightblue];

"""

        for table_name, info in schema_info.items():
            # Create node for table with escaped characters
            columns_list = []
            for col in info['columns'][:10]:  # Limit to first 10 columns
                pk_marker = " [PK]" if col['pk'] else ""
                columns_list.append(f"{col['name']} : {col['type']}{pk_marker}")

            columns_str = "\n".join(columns_list)

            if len(info['columns']) > 10:
                columns_str += f"\n... +{len(info['columns']) - 10} more"

            # Escape special characters for DOT format
            columns_str_escaped = columns_str.replace('"', '\"')

            dot_content += f'    {table_name} [label="{{<f0> {table_name}|{columns_str_escaped}}}"];\n'

        dot_content += "}\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dot_content)

        print(f"✓ Created Graphviz diagram: {output_path}")
        print(f"  To generate PNG: dot -Tpng {output_path} -o schema_diagram.png")

    except Exception as e:
        print(f"⚠️  Could not create Graphviz diagram: {e}")


def main():
    """Generate all schema visualizations."""
    print("="*60)
    print("DATABASE SCHEMA VISUALIZER")
    print("="*60)

    # Find and display database path
    print(f"\nDatabase file: {DB_PATH}")

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR.absolute()}")

    # Get schema information
    print(f"\nAnalyzing database...")
    schema_info = get_schema_info(DB_PATH)

    if not schema_info:
        print("\n❌ No tables found or database doesn't exist")
        print("\nMake sure you:")
        print("  1. Ran: python3 database.py")
        print("  2. Have unified_country_database.db in the same folder")
        return

    print(f"Found {len(schema_info)} tables\n")

    # Create visualizations
    create_text_schema(schema_info, OUTPUT_DIR / "schema.txt")
    create_markdown_schema(schema_info, OUTPUT_DIR / "schema.md")
    create_html_schema(schema_info, OUTPUT_DIR / "schema.html")
    create_graphviz_diagram(schema_info, OUTPUT_DIR / "schema.dot")

    # Save JSON
    json_path = OUTPUT_DIR / "schema.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(schema_info, f, indent=2)
    print(f"✓ Created JSON schema: {json_path}")

    print("\n" + "="*60)
    print("SCHEMA VISUALIZATION COMPLETE")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR.absolute()}")
    print("\nFiles created:")
    print("  1. schema.txt   - Text documentation")
    print("  2. schema.md    - Markdown documentation")
    print("  3. schema.html  - Interactive browser (RECOMMENDED)")
    print("  4. schema.dot   - Graphviz diagram source")
    print("  5. schema.json  - JSON schema export")
    print("\nTo view:")
    print(f"  Open in browser: {OUTPUT_DIR / 'schema.html'}")
    print("="*60)


if __name__ == "__main__":
    main()