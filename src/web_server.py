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
    message = request.args.get("message")
    error = request.args.get("error")
    return render_template("index.html", projects=projects, message=message, error=error)


@app.route("/project/<project_name>")
def project_view(project_name):
    """View all notes in a project."""
    # Decode URL-encoded project name
    project_name = unquote(project_name)
    notes = storage.list_notes(project_name)
    message = request.args.get("message")
    error = request.args.get("error")
    
    # Generate deep link
    deep_link = request.host_url.rstrip('/') + url_for('project_view', project_name=quote(project_name))
    
    return render_template(
        "project.html", 
        project=project_name, 
        notes=notes,
        deep_link=deep_link,
        message=message,
        error=error
    )


@app.route("/note/<project_name>/<title>")
def note_view(project_name, title):
    """View a specific note."""
    # Decode URL-encoded parameters
    project_name = unquote(project_name)
    title = unquote(title)
    version = request.args.get("version")
    message = request.args.get("message")
    error = request.args.get("error")
    
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
            message=message,
            error=error,
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


@app.route("/delete/project/<project_name>", methods=["POST"])
def delete_project(project_name):
    """Delete a project and all its notes."""
    project_name = unquote(project_name)
    
    try:
        # Use storage's method to get correct sanitized path
        project_path = storage._get_project_dir(project_name)
        if project_path.exists() and project_path.is_dir():
            import shutil
            shutil.rmtree(project_path)
            
            # Rebuild search index after deletion
            async_to_sync(searcher.rebuild_index())
            
            return redirect(url_for("index", message=f"Project '{project_name}' deleted successfully"))
        else:
            return redirect(url_for("index", error=f"Project '{project_name}' not found"))
    except Exception as e:
        return redirect(url_for("index", error=f"Error deleting project: {str(e)}"))


@app.route("/delete/note/<project_name>/<title>", methods=["POST"])
def delete_note(project_name, title):
    """Delete a specific note (all versions)."""
    project_name = unquote(project_name)
    title = unquote(title)
    
    try:
        # Use storage's method to get correct sanitized path
        project_path = storage._get_project_dir(project_name)
        if not project_path.exists():
            return redirect(url_for("project_view", project_name=quote(project_name), 
                          error=f"Project '{project_name}' not found"))
        
        # Delete all versions of the note
        deleted_count = 0
        for file_path in project_path.glob(f"{title}_*.md"):
            file_path.unlink()
            deleted_count += 1
        
        if deleted_count > 0:
            # Rebuild search index after deletion
            async_to_sync(searcher.rebuild_index())
            
            return redirect(url_for("project_view", project_name=quote(project_name),
                          message=f"Note '{title}' deleted ({deleted_count} version(s))"))
        else:
            return redirect(url_for("project_view", project_name=quote(project_name),
                          error=f"Note '{title}' not found"))
    except Exception as e:
        return redirect(url_for("project_view", project_name=quote(project_name),
                      error=f"Error deleting note: {str(e)}"))


@app.route("/rename/project/<project_name>", methods=["POST"])
def rename_project(project_name):
    """Rename a project."""
    project_name = unquote(project_name)
    new_name = request.form.get("new_name", "").strip()
    
    if not new_name:
        return redirect(url_for("project_view", project_name=quote(project_name),
                      error="New project name cannot be empty"))
    
    try:
        # Manually sanitize paths without creating directories
        # (can't use _get_project_dir because it creates the directory)
        safe_old = "".join(c for c in project_name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        safe_new = "".join(c for c in new_name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        
        old_path = storage.base_dir / safe_old
        new_path = storage.base_dir / safe_new
        
        if not old_path.exists():
            return redirect(url_for("index", error=f"Project '{project_name}' not found"))
        
        if new_path.exists():
            return redirect(url_for("project_view", project_name=quote(project_name),
                          error=f"Project '{new_name}' already exists"))
        
        old_path.rename(new_path)
        
        # Rebuild search index after rename
        async_to_sync(searcher.rebuild_index())
        
        return redirect(url_for("project_view", project_name=quote(new_name),
                      message=f"Project renamed from '{project_name}' to '{new_name}'"))
    except Exception as e:
        return redirect(url_for("project_view", project_name=quote(project_name),
                      error=f"Error renaming project: {str(e)}"))


@app.route("/rename/note/<project_name>/<title>", methods=["POST"])
def rename_note(project_name, title):
    """Rename a note (all versions)."""
    project_name = unquote(project_name)
    title = unquote(title)
    new_title = request.form.get("new_title", "").strip()
    
    if not new_title:
        return redirect(url_for("project_view", project_name=quote(project_name),
                      error="New note title cannot be empty"))
    
    try:
        # Use storage's method to get correct sanitized path
        project_path = storage._get_project_dir(project_name)
        
        if not project_path.exists():
            return redirect(url_for("project_view", project_name=quote(project_name),
                          error=f"Project '{project_name}' not found"))
        
        # Check if new title already exists
        existing_files = list(project_path.glob(f"{new_title}_*.md"))
        if existing_files:
            return redirect(url_for("project_view", project_name=quote(project_name),
                          error=f"Note '{new_title}' already exists"))
        
        # Rename all versions of the note
        renamed_count = 0
        for old_file in project_path.glob(f"{title}_*.md"):
            # Extract timestamp from old filename
            timestamp_part = old_file.stem.replace(f"{title}_", "")
            new_filename = f"{new_title}_{timestamp_part}.md"
            new_file = project_path / new_filename
            old_file.rename(new_file)
            renamed_count += 1
        
        if renamed_count > 0:
            # Rebuild search index after rename
            async_to_sync(searcher.rebuild_index())
            
            return redirect(url_for("note_view", project_name=quote(project_name), 
                          title=quote(new_title),
                          message=f"Note renamed from '{title}' to '{new_title}' ({renamed_count} version(s))"))
        else:
            return redirect(url_for("project_view", project_name=quote(project_name),
                          error=f"Note '{title}' not found"))
    except Exception as e:
        return redirect(url_for("project_view", project_name=quote(project_name),
                      error=f"Error renaming note: {str(e)}"))


@app.route("/edit/note/<project_name>/<title>", methods=["GET", "POST"])
def edit_note(project_name, title):
    """Edit a note's content."""
    project_name = unquote(project_name)
    title = unquote(title)
    
    if request.method == "GET":
        # Show edit form with current content
        try:
            content, timestamp = async_to_sync(storage.retrieve_note(project_name, title))
            return render_template(
                "edit_note.html",
                project=project_name,
                title=title,
                content=content,
                timestamp=timestamp
            )
        except FileNotFoundError:
            return redirect(url_for("project_view", project_name=quote(project_name),
                          error=f"Note '{title}' not found"))
    
    elif request.method == "POST":
        # Save edited content (creates new version)
        new_content = request.form.get("content", "")
        
        if not new_content.strip():
            return redirect(url_for("edit_note", project_name=quote(project_name), 
                          title=quote(title),
                          error="Content cannot be empty"))
        
        try:
            # Store note creates a new version with current timestamp
            result = async_to_sync(storage.store_note(project_name, title, new_content))
            
            # Rebuild search index
            async_to_sync(searcher.rebuild_index())
            
            return redirect(url_for("note_view", project_name=quote(project_name), 
                          title=quote(title),
                          message="Note updated successfully"))
        except Exception as e:
            return redirect(url_for("edit_note", project_name=quote(project_name), 
                          title=quote(title),
                          error=f"Error saving note: {str(e)}"))


@app.route("/create/note/<project_name>", methods=["GET", "POST"])
def create_note(project_name):
    """Create a new note in a project."""
    project_name = unquote(project_name)
    
    if request.method == "GET":
        # Show create form
        return render_template(
            "edit_note.html",
            project=project_name,
            title="",
            content="",
            timestamp=None,
            is_new=True
        )
    
    elif request.method == "POST":
        # Create new note
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        
        if not title:
            return redirect(url_for("create_note", project_name=quote(project_name)),
                          error="Title cannot be empty")
        
        if not content:
            return redirect(url_for("create_note", project_name=quote(project_name)),
                          error="Content cannot be empty")
        
        try:
            # Check if note already exists - use storage's method to get correct path
            project_path = storage._get_project_dir(project_name)
            if project_path.exists():
                existing = list(project_path.glob(f"{title}_*.md"))
                if existing:
                    return render_template(
                        "edit_note.html",
                        project=project_name,
                        title=title,
                        content=content,
                        timestamp=None,
                        is_new=True,
                        error=f"Note '{title}' already exists in this project"
                    )
            
            # Store the new note
            result = async_to_sync(storage.store_note(project_name, title, content))
            
            # Rebuild search index
            async_to_sync(searcher.rebuild_index())
            
            return redirect(url_for("note_view", project_name=quote(project_name), 
                          title=quote(title),
                          message="Note created successfully"))
        except Exception as e:
            return render_template(
                "edit_note.html",
                project=project_name,
                title=title,
                content=content,
                timestamp=None,
                is_new=True,
                error=f"Error creating note: {str(e)}"
            )


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
        .action-button {
            padding: 10px 20px;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 500;
            font-size: 14px;
            margin-left: 5px;
        }
        .action-button:hover {
            opacity: 0.8;
        }
        .small-action-button {
            padding: 5px 10px;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-weight: 500;
            font-size: 12px;
        }
        .small-action-button:hover {
            opacity: 0.8;
        }
        .message {
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            font-weight: 500;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
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

{% if message %}
<div class="message success">{{ message }}</div>
{% endif %}

{% if error %}
<div class="message error">{{ error }}</div>
{% endif %}

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
{% if message %}
<div class="message success">{{ message }}</div>
{% endif %}

{% if error %}
<div class="message error">{{ error }}</div>
{% endif %}

<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
    <h2>📁 {{ project }}</h2>
    <div>
        <a href="{{ url_for('create_note', project_name=project) }}" class="action-button" style="background: #27ae60; text-decoration: none; display: inline-block;">➕ Create Note</a>
        <button onclick="showRenameProjectDialog()" class="action-button" style="background: #f39c12;">🔄 Rename Project</button>
        <button onclick="confirmDeleteProject()" class="action-button" style="background: #e74c3c;">🗑️ Delete Project</button>
    </div>
</div>

<!-- Rename Project Dialog -->
<div id="rename-project-dialog" style="display: none; background: #f8f9fa; border: 2px solid #3498db; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
    <h3>Rename Project</h3>
    <form method="POST" action="{{ url_for('rename_project', project_name=project) }}">
        <input type="text" name="new_name" placeholder="New project name" required style="width: 70%; padding: 10px; margin-right: 10px;">
        <button type="submit" class="action-button" style="background: #27ae60;">✓ Rename</button>
        <button type="button" onclick="hideRenameProjectDialog()" class="action-button" style="background: #95a5a6;">✕ Cancel</button>
    </form>
</div>

<!-- Delete Project Form (hidden) -->
<form id="delete-project-form" method="POST" action="{{ url_for('delete_project', project_name=project) }}" style="display: none;"></form>

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
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <a href="{{ url_for('note_view', project_name=project, title=note.title) }}">
                    📄 {{ note.title }}
                </a>
                <br>
                <small style="color: #7f8c8d;">Latest version: {{ note.latest_version }}</small>
            </div>
            <div style="white-space: nowrap;">
                <button onclick="showRenameNoteDialog('{{ note.title }}')" class="small-action-button" style="background: #f39c12; padding: 5px 10px; margin-left: 5px;">✏️ Rename</button>
                <button onclick="confirmDeleteNote('{{ note.title }}')" class="small-action-button" style="background: #e74c3c; padding: 5px 10px;">🗑️ Delete</button>
            </div>
        </div>
        <!-- Rename Dialog for this note -->
        <div id="rename-note-{{ note.title }}" style="display: none; margin-top: 10px; background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <form method="POST" action="{{ url_for('rename_note', project_name=project, title=note.title) }}">
                <input type="text" name="new_title" placeholder="New note title" required style="width: 60%; padding: 8px; margin-right: 10px;">
                <button type="submit" class="small-action-button" style="background: #27ae60;">✓ Rename</button>
                <button type="button" onclick="hideRenameNoteDialog('{{ note.title }}')" class="small-action-button" style="background: #95a5a6;">✕ Cancel</button>
            </form>
        </div>
        <!-- Delete Form for this note (hidden) -->
        <form id="delete-note-{{ note.title }}" method="POST" action="{{ url_for('delete_note', project_name=project, title=note.title) }}" style="display: none;"></form>
    </li>
    {% endfor %}
</ul>
{% else %}
<p>No notes in this project yet.</p>
{% endif %}

<p><a href="{{ url_for('index') }}">← Back to Projects</a></p>

<script>
function showRenameProjectDialog() {
    document.getElementById('rename-project-dialog').style.display = 'block';
}

function hideRenameProjectDialog() {
    document.getElementById('rename-project-dialog').style.display = 'none';
}

function confirmDeleteProject() {
    if (confirm('Are you sure you want to delete the entire project "{{ project }}" and all its notes? This cannot be undone.')) {
        document.getElementById('delete-project-form').submit();
    }
}

function showRenameNoteDialog(noteTitle) {
    document.getElementById('rename-note-' + noteTitle).style.display = 'block';
}

function hideRenameNoteDialog(noteTitle) {
    document.getElementById('rename-note-' + noteTitle).style.display = 'none';
}

function confirmDeleteNote(noteTitle) {
    if (confirm('Are you sure you want to delete the note "' + noteTitle + '" and all its versions? This cannot be undone.')) {
        document.getElementById('delete-note-' + noteTitle).submit();
    }
}
</script>

{% endblock %}
"""
    
    # Note template
    note_html = """{% extends "base.html" %}

{% block title %}{{ title }} - Notes Manager{% endblock %}

{% block content %}
{% if message %}
<div class="message success">{{ message }}</div>
{% endif %}

{% if error %}
<div class="message error">{{ error }}</div>
{% endif %}

<div class="metadata">
    <p><strong>Project:</strong> <a href="{{ url_for('project_view', project_name=project) }}">{{ project }}</a></p>
    <p><strong>Version:</strong> {{ timestamp }}</p>
</div>

<div style="display: flex; justify-content: space-between; align-items: center; margin: 20px 0;">
    <div class="deep-link-container" style="flex-grow: 1; margin-right: 20px;">
        <h3>🔗 Share this note</h3>
        <div class="deep-link-input">
            <input type="text" id="note-deep-link" value="{{ deep_link }}" readonly>
            <button onclick="copyToClipboard('note-deep-link')">📋 Copy Link</button>
            <span id="note-deep-link-success" class="copy-success">✓ Copied!</span>
        </div>
    </div>
    <div>
        <a href="{{ url_for('edit_note', project_name=project, title=title) }}" class="action-button" style="background: #3498db; text-decoration: none; display: inline-block;">✏️ Edit Note</a>
        <button onclick="showRenameNoteDialog()" class="action-button" style="background: #f39c12;">🔄 Rename Note</button>
        <button onclick="confirmDeleteNote()" class="action-button" style="background: #e74c3c;">🗑️ Delete Note</button>
    </div>
</div>

<!-- Rename Note Dialog -->
<div id="rename-note-dialog" style="display: none; background: #f8f9fa; border: 2px solid #3498db; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
    <h3>Rename Note</h3>
    <form method="POST" action="{{ url_for('rename_note', project_name=project, title=title) }}">
        <input type="text" name="new_title" placeholder="New note title" value="{{ title }}" required style="width: 70%; padding: 10px; margin-right: 10px;">
        <button type="submit" class="action-button" style="background: #27ae60;">✓ Rename</button>
        <button type="button" onclick="hideRenameNoteDialog()" class="action-button" style="background: #95a5a6;">✕ Cancel</button>
    </form>
</div>

<!-- Delete Note Form (hidden) -->
<form id="delete-note-form" method="POST" action="{{ url_for('delete_note', project_name=project, title=title) }}" style="display: none;"></form>

<h2>{{ title }}</h2>
<hr>
<div>
    {{ content | safe }}
</div>
<p><a href="{{ url_for('project_view', project_name=project) }}">← Back to {{ project }}</a></p>

<script>
function showRenameNoteDialog() {
    document.getElementById('rename-note-dialog').style.display = 'block';
}

function hideRenameNoteDialog() {
    document.getElementById('rename-note-dialog').style.display = 'none';
}

function confirmDeleteNote() {
    if (confirm('Are you sure you want to delete the note "{{ title }}" and all its versions? This cannot be undone.')) {
        document.getElementById('delete-note-form').submit();
    }
}
</script>

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
    
    # Edit/Create Note template
    edit_note_html = """{% extends "base.html" %}

{% block title %}{% if is_new %}Create{% else %}Edit{% endif %} Note - Notes Manager{% endblock %}

{% block content %}
{% if message %}
<div class="message success">{{ message }}</div>
{% endif %}

{% if error %}
<div class="message error">{{ error }}</div>
{% endif %}

<h2>{% if is_new %}➕ Create New Note{% else %}✏️ Edit Note{% endif %}</h2>

<div class="metadata" style="margin-bottom: 20px;">
    <p><strong>Project:</strong> <a href="{{ url_for('project_view', project_name=project) }}">{{ project }}</a></p>
    {% if timestamp %}
    <p><strong>Current Version:</strong> {{ timestamp }}</p>
    <p style="color: #e67e22;"><strong>Note:</strong> Editing will create a new version with the current timestamp.</p>
    {% endif %}
</div>

<form method="POST" style="width: 100%;">
    {% if is_new %}
    <div style="margin-bottom: 20px;">
        <label for="title" style="display: block; font-weight: bold; margin-bottom: 5px;">Note Title:</label>
        <input type="text" id="title" name="title" value="{{ title }}" required 
               style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px;"
               placeholder="Enter note title...">
    </div>
    {% else %}
    <div style="margin-bottom: 20px;">
        <label style="display: block; font-weight: bold; margin-bottom: 5px;">Note Title:</label>
        <p style="font-size: 18px; color: #2c3e50; margin: 0;">{{ title }}</p>
    </div>
    {% endif %}
    
    <div style="margin-bottom: 20px;">
        <label for="content" style="display: block; font-weight: bold; margin-bottom: 5px;">Content (Markdown):</label>
        <textarea id="content" name="content" required 
                  style="width: 100%; min-height: 400px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; 
                         font-family: 'Courier New', Consolas, monospace; font-size: 14px; line-height: 1.6;"
                  placeholder="# Note Title&#10;&#10;Write your note content here in Markdown format...&#10;&#10;## Features&#10;- Bullet points&#10;- **Bold text**&#10;- *Italic text*&#10;- [Links](https://example.com)&#10;- Code blocks&#10;">{{ content }}</textarea>
    </div>
    
    <div style="display: flex; gap: 10px; align-items: center;">
        <button type="submit" class="action-button" style="background: #27ae60; font-size: 16px; padding: 12px 24px;">
            💾 {% if is_new %}Create Note{% else %}Save Changes{% endif %}
        </button>
        <a href="{% if title %}{{ url_for('note_view', project_name=project, title=title) }}{% else %}{{ url_for('project_view', project_name=project) }}{% endif %}" 
           class="action-button" style="background: #95a5a6; text-decoration: none; display: inline-block; font-size: 16px; padding: 12px 24px;">
            ✕ Cancel
        </a>
        <div style="flex-grow: 1;"></div>
        <button type="button" onclick="togglePreview()" class="action-button" style="background: #3498db; font-size: 16px; padding: 12px 24px;">
            👁️ Preview
        </button>
    </div>
</form>

<!-- Preview area -->
<div id="preview-area" style="display: none; margin-top: 30px; padding: 20px; background: white; border: 2px solid #3498db; border-radius: 5px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h3 style="margin: 0;">📄 Preview</h3>
        <button onclick="togglePreview()" class="action-button" style="background: #95a5a6;">✕ Close Preview</button>
    </div>
    <hr>
    <div id="preview-content" style="padding: 20px;"></div>
</div>

<div style="margin-top: 30px; padding: 20px; background: #ecf0f1; border-radius: 5px;">
    <h3>📝 Markdown Quick Reference</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 15px;">
        <div>
            <strong>Headers:</strong><br>
            <code># H1</code><br>
            <code>## H2</code><br>
            <code>### H3</code>
        </div>
        <div>
            <strong>Emphasis:</strong><br>
            <code>**bold**</code><br>
            <code>*italic*</code><br>
            <code>~~strikethrough~~</code>
        </div>
        <div>
            <strong>Lists:</strong><br>
            <code>- Bullet point</code><br>
            <code>1. Numbered item</code><br>
            <code>- [ ] Checkbox</code>
        </div>
        <div>
            <strong>Links & Images:</strong><br>
            <code>[text](url)</code><br>
            <code>![alt](image.jpg)</code>
        </div>
        <div>
            <strong>Code:</strong><br>
            <code>`inline code`</code><br>
            <code>```language</code><br>
            <code>code block</code><br>
            <code>```</code>
        </div>
        <div>
            <strong>Other:</strong><br>
            <code>> Blockquote</code><br>
            <code>---</code> (horizontal rule)<br>
            <code>| Table | Header |</code>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
function togglePreview() {
    const previewArea = document.getElementById('preview-area');
    const content = document.getElementById('content').value;
    
    if (previewArea.style.display === 'none') {
        // Show preview
        const previewContent = document.getElementById('preview-content');
        if (typeof marked !== 'undefined') {
            previewContent.innerHTML = marked.parse(content);
        } else {
            previewContent.textContent = 'Markdown library not loaded. Showing raw content:\\n\\n' + content;
        }
        previewArea.style.display = 'block';
        previewArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        // Hide preview
        previewArea.style.display = 'none';
    }
}

// Keyboard shortcuts
document.getElementById('content').addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        this.form.submit();
    }
    
    // Ctrl/Cmd + P to preview
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        togglePreview();
    }
    
    // Tab to insert spaces (not change focus)
    if (e.key === 'Tab') {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
    }
});
</script>

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
    if not (templates_dir / "edit_note.html").exists():
        (templates_dir / "edit_note.html").write_text(edit_note_html, encoding="utf-8")


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
