"""Web server for browsing notes."""

import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify
import markdown
import asyncio
from urllib.parse import quote, unquote

from .storage import NotesStorage
from .search import NotesSearcher


app = Flask(__name__)
storage = NotesStorage()
searcher = NotesSearcher(storage)


def async_to_sync(coro):
    """Helper to run async functions in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route("/")
def index():
    """Home page showing all projects."""
    projects = storage.list_projects()
    return render_template("index.html", projects=projects)


@app.route("/project/<project_name>")
def project_view(project_name):
    """View all notes in a project."""
    # Decode URL-encoded project name
    project_name = unquote(project_name)
    notes = storage.list_notes(project_name)
    
    # Generate deep link
    deep_link = request.host_url.rstrip('/') + url_for('project_view', project_name=quote(project_name))
    
    return render_template(
        "project.html", 
        project=project_name, 
        notes=notes,
        deep_link=deep_link
    )


@app.route("/note/<project_name>/<title>")
def note_view(project_name, title):
    """View a specific note."""
    # Decode URL-encoded parameters
    project_name = unquote(project_name)
    title = unquote(title)
    version = request.args.get("version")
    
    try:
        content, timestamp = async_to_sync(storage.retrieve_note(project_name, title, version))
        html_content = markdown.markdown(content, extensions=["fenced_code", "tables"])
        
        # Generate deep link
        deep_link = request.host_url.rstrip('/') + url_for(
            'note_view', 
            project_name=quote(project_name),
            title=quote(title)
        )
        if version:
            deep_link += f"?version={quote(version)}"
        
        return render_template(
            "note.html",
            project=project_name,
            title=title,
            content=html_content,
            timestamp=timestamp,
            deep_link=deep_link,
        )
    except FileNotFoundError:
        return f"Note not found: {project_name} / {title}", 404


@app.route("/search")
def search_view():
    """Search for notes."""
    query = request.args.get("q", "")
    project = request.args.get("project")
    
    if not query:
        return render_template("search.html", query="", results=[])
    
    # Ensure index is built
    if not searcher.index:
        async_to_sync(searcher.rebuild_index())
    
    results = searcher.search(query, project)
    
    return render_template("search.html", query=query, results=results)


@app.route("/rebuild_index")
def rebuild_index_view():
    """Rebuild the search index."""
    count = async_to_sync(searcher.rebuild_index())
    return redirect(url_for("index", message=f"Index rebuilt: {count} notes"))


@app.route("/api/deep-link/project/<project_name>")
def api_project_deep_link(project_name):
    """API endpoint to get deep link for a project."""
    project_name = unquote(project_name)
    deep_link = request.host_url.rstrip('/') + url_for('project_view', project_name=quote(project_name))
    
    return jsonify({
        "project": project_name,
        "deep_link": deep_link,
        "url": url_for('project_view', project_name=quote(project_name), _external=True)
    })


@app.route("/api/deep-link/note/<project_name>/<title>")
def api_note_deep_link(project_name, title):
    """API endpoint to get deep link for a note."""
    project_name = unquote(project_name)
    title = unquote(title)
    version = request.args.get("version")
    
    deep_link = request.host_url.rstrip('/') + url_for(
        'note_view',
        project_name=quote(project_name),
        title=quote(title)
    )
    if version:
        deep_link += f"?version={quote(version)}"
    
    return jsonify({
        "project": project_name,
        "title": title,
        "version": version,
        "deep_link": deep_link,
        "url": url_for('note_view', project_name=quote(project_name), title=quote(title), _external=True)
    })


def create_templates():
    """Create template files if they don't exist."""
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Base template
    base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Notes Manager{% endblock %}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        header h1 { margin-bottom: 10px; }
        nav a {
            color: #3498db;
            text-decoration: none;
            margin-right: 15px;
            font-weight: 500;
        }
        nav a:hover { text-decoration: underline; }
        .content {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .project-list, .note-list {
            list-style: none;
        }
        .project-list li, .note-list li {
            padding: 15px;
            margin: 10px 0;
            background: #ecf0f1;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .project-list li a, .note-list li a {
            color: #2c3e50;
            text-decoration: none;
            font-weight: 500;
        }
        .project-list li:hover, .note-list li:hover {
            background: #d5dbdb;
        }
        .search-form {
            margin: 20px 0;
        }
        .search-form input[type="text"] {
            width: 70%;
            padding: 10px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        .search-form button {
            padding: 10px 20px;
            font-size: 16px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .search-form button:hover {
            background: #2980b9;
        }
        .search-result {
            padding: 15px;
            margin: 15px 0;
            background: #ecf0f1;
            border-radius: 5px;
            border-left: 4px solid #27ae60;
        }
        .search-result h3 {
            margin-bottom: 5px;
        }
        .search-result .meta {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .search-result .excerpt {
            color: #555;
            line-height: 1.5;
        }
        pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        code {
            background: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        .metadata {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .metadata p {
            margin: 5px 0;
        }
        .deep-link-container {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }
        .deep-link-container h3 {
            margin-bottom: 10px;
            color: #2c3e50;
            font-size: 16px;
        }
        .deep-link-input {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .deep-link-input input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            background: white;
        }
        .deep-link-input button {
            padding: 10px 20px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 500;
            white-space: nowrap;
        }
        .deep-link-input button:hover {
            background: #2980b9;
        }
        .deep-link-input button:active {
            background: #21618c;
        }
        .copy-success {
            color: #27ae60;
            font-size: 14px;
            margin-left: 10px;
            display: none;
        }
        .copy-success.show {
            display: inline;
        }
    </style>
    <script>
        function copyToClipboard(elementId) {
            const input = document.getElementById(elementId);
            input.select();
            input.setSelectionRange(0, 99999);
            
            try {
                document.execCommand('copy');
                const successMsg = document.getElementById(elementId + '-success');
                successMsg.classList.add('show');
                setTimeout(() => {
                    successMsg.classList.remove('show');
                }, 2000);
            } catch (err) {
                alert('Failed to copy: ' + err);
            }
        }
    </script>
</head>
<body>
    <header>
        <h1>📝 Notes Manager</h1>
        <nav>
            <a href="{{ url_for('index') }}">Home</a>
            <a href="{{ url_for('search_view') }}">Search</a>
            <a href="{{ url_for('rebuild_index_view') }}">Rebuild Index</a>
        </nav>
    </header>
    <div class="content">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""
    
    # Index template
    index_html = """{% extends "base.html" %}

{% block title %}Projects - Notes Manager{% endblock %}

{% block content %}
<h2>Projects</h2>
{% if projects %}
<ul class="project-list">
    {% for project in projects %}
    <li>
        <a href="{{ url_for('project_view', project_name=project) }}">
            📁 {{ project }}
        </a>
    </li>
    {% endfor %}
</ul>
{% else %}
<p>No projects found. Start by creating a note using the MCP server!</p>
{% endif %}
{% endblock %}
"""
    
    # Project template
    project_html = """{% extends "base.html" %}

{% block title %}{{ project }} - Notes Manager{% endblock %}

{% block content %}
<h2>📁 {{ project }}</h2>

<div class="deep-link-container">
    <h3>🔗 Share this project</h3>
    <div class="deep-link-input">
        <input type="text" id="project-deep-link" value="{{ deep_link }}" readonly>
        <button onclick="copyToClipboard('project-deep-link')">📋 Copy Link</button>
        <span id="project-deep-link-success" class="copy-success">✓ Copied!</span>
    </div>
</div>

{% if notes %}
<ul class="note-list">
    {% for note in notes %}
    <li>
        <a href="{{ url_for('note_view', project_name=project, title=note.title) }}">
            📄 {{ note.title }}
        </a>
        <br>
        <small style="color: #7f8c8d;">Latest version: {{ note.latest_version }}</small>
    </li>
    {% endfor %}
</ul>
{% else %}
<p>No notes in this project yet.</p>
{% endif %}
<p><a href="{{ url_for('index') }}">← Back to Projects</a></p>
{% endblock %}
"""
    
    # Note template
    note_html = """{% extends "base.html" %}

{% block title %}{{ title }} - Notes Manager{% endblock %}

{% block content %}
<div class="metadata">
    <p><strong>Project:</strong> <a href="{{ url_for('project_view', project_name=project) }}">{{ project }}</a></p>
    <p><strong>Version:</strong> {{ timestamp }}</p>
</div>

<div class="deep-link-container">
    <h3>🔗 Share this note</h3>
    <div class="deep-link-input">
        <input type="text" id="note-deep-link" value="{{ deep_link }}" readonly>
        <button onclick="copyToClipboard('note-deep-link')">📋 Copy Link</button>
        <span id="note-deep-link-success" class="copy-success">✓ Copied!</span>
    </div>
</div>

<h2>{{ title }}</h2>
<hr>
<div>
    {{ content | safe }}
</div>
<p><a href="{{ url_for('project_view', project_name=project) }}">← Back to {{ project }}</a></p>
{% endblock %}
"""
    
    # Search template
    search_html = """{% extends "base.html" %}

{% block title %}Search - Notes Manager{% endblock %}

{% block content %}
<h2>🔍 Search Notes</h2>
<form method="get" action="{{ url_for('search_view') }}" class="search-form">
    <input type="text" name="q" placeholder="Search notes..." value="{{ query }}">
    <button type="submit">Search</button>
</form>

{% if query %}
    {% if results %}
    <h3>Found {{ results|length }} result(s) for "{{ query }}"</h3>
    {% for result in results %}
    <div class="search-result">
        <h3>
            <a href="{{ url_for('note_view', project_name=result.project, title=result.title) }}">
                {{ result.title }}
            </a>
        </h3>
        <div class="meta">
            Project: {{ result.project }} | Relevance: {{ "%.1f"|format(result.score) }}%
        </div>
        <div class="excerpt">{{ result.excerpt }}</div>
    </div>
    {% endfor %}
    {% else %}
    <p>No results found for "{{ query }}".</p>
    {% endif %}
{% endif %}
{% endblock %}
"""
    
    # Only write templates if they don't exist (for development)
    # In Docker, templates are created during build
    if not (templates_dir / "base.html").exists():
        (templates_dir / "base.html").write_text(base_html, encoding="utf-8")
    if not (templates_dir / "index.html").exists():
        (templates_dir / "index.html").write_text(index_html, encoding="utf-8")
    if not (templates_dir / "project.html").exists():
        (templates_dir / "project.html").write_text(project_html, encoding="utf-8")
    if not (templates_dir / "note.html").exists():
        (templates_dir / "note.html").write_text(note_html, encoding="utf-8")
    if not (templates_dir / "search.html").exists():
        (templates_dir / "search.html").write_text(search_html, encoding="utf-8")


def main():
    """Entry point for the web server."""
    # Create templates on first run
    create_templates()
    
    # Rebuild search index
    async_to_sync(searcher.rebuild_index())
    
    # Run the Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    main()
