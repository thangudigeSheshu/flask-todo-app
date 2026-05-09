import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from seed_data import DEFAULT_TODOS

# Create the Flask application object
app = Flask(__name__)

# Ensure Flask's instance folder exists before SQLite tries to create todo.db.
os.makedirs(app.instance_path, exist_ok=True)

# Configure where SQLAlchemy should store/read the database.
# DATABASE_URL lets a hosting platform provide PostgreSQL or another DB later.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create a SQLAlchemy database instance that is attached to this Flask app
db = SQLAlchemy(app)

# Helper function to create timestamps in Indian Standard Time (Asia/Kolkata)
def indianTime():
    # Get the timezone object
    ist = pytz.timezone('Asia/Kolkata')
    # Return current time in that timezone
    return datetime.now(ist)

# Define the database model/table structure.
# Each instance of TOdo corresponds to one TODO row in the database.
class TOdo(db.Model):
    # Primary key column: unique identifier for each row.
    sno = db.Column(db.Integer, primary_key=True)

    # Title column: stored as string, cannot be NULL
    title = db.Column(db.String(200), nullable=False)

    # Description column: stored as string, cannot be NULL
    desc = db.Column(db.String(500), nullable=False)

    # created_at column: stores datetime and auto-fills using indianTime()
    created_at = db.Column(db.DateTime, default=indianTime)

# Create database tables if they don't exist yet.
# app.app_context() is required because db.create_all() needs Flask app context.
with app.app_context():
    db.create_all()
    if TOdo.query.count() == 0:
        for title, desc in DEFAULT_TODOS:
            db.session.add(TOdo(title=title, desc=desc))
        db.session.commit()

# Route for the homepage.
# Methods=['GET','POST'] means:
# - GET: show the form + current todo list
# - POST: handle form submission to create a new todo
@app.route('/', methods=['GET', 'POST'])
def home():
    # Used to show SweetAlert (or other UI) on successful insert
    success = False

    # Check if the URL includes '?updated=True' after an update operation
    updated = request.args.get('updated')

    # If form was submitted, create a new todo record
    if request.method == 'POST':
        # Read submitted form fields
        tit = request.form['title']
        desc = request.form['desc']

        # Create a new TOdo object and add it to the DB session
        db.session.add(TOdo(title=tit, desc=desc))

        # Commit saves changes permanently to the database
        db.session.commit()

        # Mark success for UI feedback
        success = True

    # Fetch all todos from the database
    allTodo = TOdo.query.all()

    # Render the index.html template with data
    return render_template('index.html', allTodo=allTodo, success=success, updated=updated)

# Route to delete a todo.
# Example: /delete/3 deletes the todo with sno=3
@app.route('/delete/<int:sno>')
def delete(sno):
    # Get the todo row that matches this sno
    todo = TOdo.query.filter_by(sno=sno).first()

    if todo:
        # Delete it from the database session
        db.session.delete(todo)

        # Save changes
        db.session.commit()

    # Redirect so the browser sees the fresh todo list after deletion.
    return redirect('/')

# Route to update a todo.
# Methods=['GET','POST'] means:
# - GET: show the update form filled with current values
# - POST: receive form submission and update the DB
@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    # Load the todo that we want to update
    todo = TOdo.query.filter_by(sno=sno).first()

    # If the user submitted the form, update fields
    if request.method == 'POST':
        # Update title and description from form inputs
        todo.title = request.form['title']
        todo.desc = request.form['desc']

        # Update created_at to current time (note: usually you'd use updated_at instead)
        todo.created_at = indianTime()

        # Commit changes to database
        db.session.commit()

        # Redirect back to the homepage with updated=True query parameter
        return redirect('/?updated=True')

    # If GET request, render the update template with the todo object
    return render_template('update.html', todo=todo)

# Only runs the Flask server when app.py is executed directly (not imported)
if __name__ == '__main__':
    # debug=True enables auto-reload + better error pages
    app.run(debug=True)

