from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from datetime import timedelta
import sqlite3

import requests

app = Flask(__name__)

# Secret key pour les sessions
app.secret_key = '2d6af66c469b448eb818e8c08feb87d8'

# Durée de vie de la session : 2 minutes
app.permanent_session_lifetime = timedelta(minutes=2)  # Session permanente pendant 2 minutes

# Middleware pour rediriger si l'utilisateur n'est pas connecté
@app.before_request
def require_login():
    # Vérifier si l'utilisateur n'est pas connecté et rediriger vers la page de login
    allowed_routes = ['login', 'register', 'serve_static_files']
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))  # Redirige vers la page de connexion si l'utilisateur n'est pas connecté

# Route pour servir les fichiers statiques
@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('static', filename)

# Initialisation de la base de données
def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        ''')
        conn.commit()

# Appel à la fonction d'initialisation de la base de données au démarrage de l'application
init_db()





# Route pour l'index

@app.route('/')
def index():
   
    return render_template('index.html')


@app.route('/commande')
def commande():
    return render_template('commande.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/menu')
def menu():
    # Appel à l'API pour récupérer les recettes
    recipes = get_recipes()
    return render_template('menu.html', recipes=recipes)
# Fonction pour récupérer des recettes de l'API Spoonacular
def get_recipes():
    url = f'https://api.spoonacular.com/recipes/random?apiKey={app.secret_key}&number=12'
    response = requests.get(url)
    data = response.json()
    
    if 'recipes' in data:
        recipes = data['recipes']
        return recipes
    return []

@app.route('/recipe/<int:recipe_id>')
def recipe_details(recipe_id):
    # Récupérer les détails de la recette depuis l'API Spoonacular
    url = f'https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={app.secret_key}'
    response = requests.get(url)
    recipe = response.json()

    # Passer les détails de la recette au template
    return render_template('recipe_details.html', recipe=recipe)


@app.route('/admin_users', methods=['GET', 'POST'])
def admin_users():
    user_to_edit = None  # Variable pour stocker les données de l'utilisateur à modifier

    # Récupérer les utilisateurs existants
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()

    # Si nous avons un `user_id` dans les paramètres de la requête, récupérer les informations de l'utilisateur
    user_id = request.args.get('user_id')
    if user_id:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_to_edit = cursor.fetchone()  # Récupérer l'utilisateur à modifier

    # Gestion des actions d'ajout, de mise à jour et de suppression d'un utilisateur
    if request.method == 'POST':
        action = request.form['action']

        if action == 'add':
            username = request.form['username']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            password = request.form['password']

            # Insérer un nouvel utilisateur dans la base de données
            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO users (username, first_name, last_name, email, password) 
                                   VALUES (?, ?, ?, ?, ?)''', 
                               (username, first_name, last_name, email, password))
                conn.commit()
                flash("User added successfully!", "success")
                return redirect(url_for('admin_users'))

        elif action == 'update':
            user_id = request.form['user_id']
            username = request.form['username']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            password = request.form['password']

            # Mettre à jour les informations de l'utilisateur
            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''UPDATE users SET username = ?, first_name = ?, last_name = ?, email = ?, password = ? 
                                   WHERE id = ?''', 
                               (username, first_name, last_name, email, password, user_id))
                conn.commit()
                flash("User updated successfully!", "success")
                return redirect(url_for('admin_users'))

        elif action == 'delete':
            user_id = request.form['user_id']

            # Supprimer un utilisateur
            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                conn.commit()
                flash("User deleted successfully!", "success")
                return redirect(url_for('admin_users'))

    return render_template('admin_users.html', users=users, user_to_edit=user_to_edit)



# Route pour l'inscription
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not all([username, first_name, last_name, email, password, confirm_password]):
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''INSERT INTO users (username, first_name, last_name, email, password) 
                                   VALUES (?, ?, ?, ?, ?)''', 
                               (username, first_name, last_name, email, password))
                conn.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Email already exists!", "danger")
                return redirect(url_for('register'))

    return render_template('register.html')

# Route pour la connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))  # Si l'utilisateur est déjà connecté, rediriger vers la page d'accueil

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not all([email, password]):
            flash("All fields are required!", "danger")
            return redirect(url_for('login'))

        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
            user = cursor.fetchone()

            if user:
                session.permanent = True
                session['user_id'] = user[0]  # ID de l'utilisateur
                session['username'] = user[1]  # Nom d'utilisateur
                flash(f"Welcome, {user[1]}!", "success")
                return redirect(url_for('index'))  # Redirige vers la page d'accueil après la connexion
            else:
                flash("Invalid email or password!", "danger")
                return redirect(url_for('login'))

    return render_template('login.html')

# Route pour la déconnexion
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# Initialiser et démarrer l'application
if __name__ == '__main__':
    app.run(debug=True)
