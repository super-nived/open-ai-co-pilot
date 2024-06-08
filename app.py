from flask import Flask, request, jsonify, g, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from openai import OpenAI
from dotenv import load_dotenv
import sqlite3
import os
import json
import requests
from bs4 import BeautifulSoup
from vector import create_vector_store, delete_vector_store
from Getfile import client

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')  # Change this!

# Initialize JWT Manager
jwt = JWTManager(app)

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

# Constants
ID_STORE = 'ids_store.json'
DATABASE = 'database.db'

# Database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Initialize database
def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_files (
                file_id TEXT NOT NULL,
                vector_id TEXT NOT NULL,
                thread_id TEXT,
                chat_thread_id TEXT,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        ''')
        db.commit()

init_db()

def check_and_update_column(table_name, column_name, column_type, user_id, new_value):
    db = get_db()
    column_exists = False

    # Check if the column exists
    try:
        db.execute(f'SELECT {column_name} FROM {table_name} LIMIT 1')
        column_exists = True
    except sqlite3.OperationalError as e:
        if f'no such column: {column_name}' in str(e):
            # Add column if it does not exist
            try:
                db.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
                db.commit()
                print(f"Column '{column_name}' added to '{table_name}'.")
            except sqlite3.OperationalError as e:
                print(f"Failed to add column '{column_name}': {e}")
                return False

    # Update the column value
    try:
        if column_exists or not column_exists:  # This condition is now redundant but left for clarity.
            db.execute(f'UPDATE {table_name} SET {column_name} = ? WHERE user_id = ?', (new_value, user_id))
            db.commit()
            print(f"Column '{column_name}' in '{table_name}' updated successfully.")
            return True
    except sqlite3.Error as e:
        print(f"Failed to update column '{column_name}': {e}")
        return False

    return False

# Helper functions for ID store
def save_ids(key, id_value):
    try:
        data = load_ids()
        data[key] = id_value
        with open(ID_STORE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving ID for key '{key}': {e}")

def load_ids():
    try:
        if os.path.exists(ID_STORE):
            with open(ID_STORE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading IDs: {e}")
        return {}

# Routes
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    hashed_password = generate_password_hash(password)
    db = get_db()

    try:
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user:
            return jsonify({'error': 'Username already exists'}), 409  # Conflict

        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        db.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        print(f"Error registering user: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    db = get_db()

    try:
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            access_token = create_access_token(identity=user['user_id'])
            return jsonify({'access_token': access_token}), 200
        return jsonify({'message': 'Invalid username or password'}), 401  # Unauthorized
    except Exception as e:
        print(f"Error logging in: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/home')
@jwt_required()
def index():
    return jsonify({'message': 'Logged in successfully'}), 200

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/post_data', methods=['POST'])
@jwt_required()
def post_data():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    try:
        file_bytes = file.read()
        message_file = client.files.create(
            file=(file.filename, file_bytes, 'application/octet-stream'), purpose="assistants")
        vector_id = create_vector_store('AAsvector', message_file.id)

        db = get_db()
        user_file = db.execute('SELECT * FROM user_files WHERE user_id = ?', (user_id,)).fetchone()

        if user_file:
            db.execute('UPDATE user_files SET file_id = ?, vector_id = ?, thread_id = NULL WHERE user_id = ?',
            (message_file.id, vector_id, user_id))
        else:
             db.execute('INSERT INTO user_files (file_id, vector_id, thread_id, user_id) VALUES (?, ?, NULL, ?)',
            (message_file.id, vector_id, user_id))

        db.commit()

        return jsonify({"message": "File processed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/query_data', methods=['POST'])
@jwt_required()
def query_data():
    user_id = get_jwt_identity()

    if 'query' not in request.form:
        return jsonify({"message": "Please enter a valid question."}), 400
    data = request.form['query']
    print(data,'lll')
    db = get_db()
    try:
        user_files = db.execute('SELECT file_id, vector_id FROM user_files WHERE user_id = ?', (user_id,)).fetchone()
        if not user_files or not user_files['vector_id']:
            return jsonify({"message": "No files found for this user. Please upload a file first."}), 400
        
        vector_id = user_files['vector_id']
        try:
            threadIdstroe = db.execute('SELECT  thread_id FROM user_files WHERE user_id = ?', (user_id,)).fetchone()
            thread_id = threadIdstroe['thread_id']
            print(thread_id,'this')
        except Exception as e:
            thread_id = None
            print('There is no data related to this thread_id.')

        if not thread_id:
            # Create a new thread if no thread_id is present
            thread = client.beta.threads.create(
                messages=[
                    {"role": "user", "content": data}
                ],
                tool_resources={
                    "file_search": {"vector_store_ids": [vector_id]}
                }
            )
            print('Creating a new thread for the user query...')
            # Check if 'thread_id' column exists, add it if not, and update it with the new thread id
            check_and_update_column('user_files', 'thread_id', 'TEXT', user_id, thread.id)
            db.commit()
            thread_id = thread.id

            # Run the thread using the existing or new thread_id
            run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id="asst_eH8AX6gak9olVcLkuA5QSmwT",instructions="your name is ass-co-pilot ,if user is asking for an image, video,manuals, glbfile, or pdf link in a file, you should respond like direct link for display in corresponding tag so avoid '' this one in link also give response in json format { link : url }. There's no need to explain anything. If none of these, you can answer based on your requirement."
            )

            messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

            message_content = messages[0].content[0].text
            annotations = message_content.annotations
            citations = []
            for index, annotation in enumerate(annotations):
                message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")

            print(message_content.value)
            print("\n".join(citations),'kkkkkk')
            return jsonify({"message":message_content.value}), 200
        else:
            # Add the user's message to the thread
            client.beta.threads.messages.create(thread_id=thread_id,
                                                
                                                role="user",
                                                content=data)

            # Run the Assistant
            run = client.beta.threads.runs.create(thread_id=thread_id,
                                                  instructions=" retieve all information in vector store then check any queryabout that.  your name is ass-co-pilot ,if user is asking for an image, video,manuals, glbfile, or pdf link in a file, you should respond like direct link for display in corresponding tag so avoid '' this one in link also give response in json format { link : url }. There's no need to explain anything. If none of these, you can answer based on your requirement."
                                                ,assistant_id="asst_eH8AX6gak9olVcLkuA5QSmwT")

            # Wait for the Run to complete
            while True:
                run_status = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                            run_id=run.id)
                if run_status.status == 'completed':
                    break
                # time.sleep(1)  # Wait for a second before checking again

            # Retrieve and return the latest message from the assistant
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            response = messages.data[0].content[0].text.value

            print(f"Assistant response: {response}")
            return jsonify({"message": response})
    except sqlite3.OperationalError as e:
        if 'no such column: thread_id' in str(e):
            # Handle missing column case
            print(f"Database schema error: {e}")
            return jsonify({"error": "Database schema is outdated. Please update the database schema."}), 500
        else:
            print(f"Database error: {e}")
            return jsonify({"error": "An error occurred with the database."}), 500
    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    user_id = get_jwt_identity()

    if 'query' not in request.form:
        return jsonify({"message": "Please enter a valid question."}), 400

    data = request.form['query']
    print(data,'kkkkkkkkkk')
    db = get_db()
    try:
        try:
            threadIdstroe = db.execute('SELECT  chat_thread_id FROM user_files WHERE user_id = ?', (user_id,)).fetchone()
            thread_id = threadIdstroe['chat_thread_id']
            print(thread_id,'this')
        except Exception as e:
            thread_id = None
            print('There is no data related to this thread_id.')

        if not thread_id:
            # Create a new thread if no thread_id is present
            thread = client.beta.threads.create(
                messages=[
                    {"role": "user", "content": data}
                ]
            )
            print('Creating a new thread for the user query...')
            # Check if 'thread_id' column exists, add it if not, and update it with the new thread id
            check_and_update_column('user_files', 'chat_thread_id', 'TEXT', user_id, thread.id)
            db.commit()
            thread_id = thread.id

            # Run the thread using the existing or new thread_id
            run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id="asst_eH8AX6gak9olVcLkuA5QSmwT",instructions="your name is ass-co-pilot ,if user is asking for an image, video,manuals, glbfile, or pdf link in a file, you should respond like direct link for display in corresponding tag so avoid '' this one in link also give response in json format { link : url }. There's no need to explain anything. If none of these, you can answer based on your requirement."
            )

            messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

            message_content = messages[0].content[0].text
            annotations = message_content.annotations
            citations = []
            for index, annotation in enumerate(annotations):
                message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
                if file_citation := getattr(annotation, "file_citation", None):
                    cited_file = client.files.retrieve(file_citation.file_id)
                    citations.append(f"[{index}] {cited_file.filename}")

            print(message_content.value)
            print("\n".join(citations),'kkkkkk')
            return jsonify({"message":message_content.value}), 200
        else:
            # Add the user's message to the thread
            client.beta.threads.messages.create(thread_id=thread_id,
                                                
                                                role="user",
                                                content=data)

            # Run the Assistant
            run = client.beta.threads.runs.create(thread_id=thread_id,
                                                  instructions=" retieve all information in vector store then check any query about that.  your name is ass-co-pilot ,if user is asking for an image, video,manuals, glbfile, or pdf link in a file, you should respond like direct link for display in corresponding tag so avoid '' this one in link also give response in json format { link : url }. There's no need to explain anything. If none of these, you can answer based on your requirement."
                                                ,assistant_id="asst_eH8AX6gak9olVcLkuA5QSmwT")

            # Wait for the Run to complete
            while True:
                run_status = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                            run_id=run.id)
                if run_status.status == 'completed':
                    break
                # time.sleep(1)  # Wait for a second before checking again

            # Retrieve and return the latest message from the assistant
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            response = messages.data[0].content[0].text.value

            print(f"Assistant response: {response}")
            return jsonify({"message": response})
    except sqlite3.OperationalError as e:
        if 'no such column: thread_id' in str(e):
            # Handle missing column case
            print(f"Database schema error: {e}")
            return jsonify({"error": "Database schema is outdated. Please update the database schema."}), 500
        else:
            print(f"Database error: {e}")
            return jsonify({"error": "An error occurred with the database."}), 500
    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/end_query', methods=['GET'])
@jwt_required()
def end_query():
    user_id = get_jwt_identity()
    db = get_db()
    user_files = db.execute('SELECT file_id, vector_id, thread_id FROM user_files WHERE user_id = ?', (user_id,)).fetchone()

    if not user_files:
        return jsonify({"message": "No files found for this user. Please upload a file first."}), 400

    file_id, vector_id, thread_id = user_files['file_id'], user_files['vector_id'], user_files['thread_id']

    try:
        if thread_id:
            delete_vector_store(vector_id)
            # Assuming delete_file is properly defined somewhere
            # delete_file(file_id)
            client.beta.threads.delete(thread_id=thread_id)
 
        db.execute('UPDATE user_files SET file_id = ?, vector_id = ?, thread_id = NULL WHERE user_id = ?',
                   ("", "", user_id))
        db.commit()

        return jsonify({"message": "Chat ended and resources cleaned up."}), 200
    except Exception as e:
        print(f"Error ending chat: {e}")
        return jsonify({"message": "Error ending chat."}), 400

@app.route('/end_chat', methods=['GET'])
@jwt_required()
def end_chat():
    user_id = get_jwt_identity()
    db = get_db()
    try:
        user_files = db.execute('SELECT chat_thread_id FROM user_files WHERE user_id = ?', (user_id,)).fetchone()
        
        if not user_files or not user_files['chat_thread_id']:
            return jsonify({"message": "No chat thread found for this user."}), 400
        
        chat_thread_id = user_files['chat_thread_id']

        # Delete the chat thread using OpenAI client if needed
        client.beta.threads.delete(thread_id=chat_thread_id)

        # Update the database to remove the chat_thread_id
        db.execute('UPDATE user_files SET chat_thread_id = NULL WHERE user_id = ?', (user_id,))
        db.commit()

        return jsonify({"message": "Chat thread deleted successfully."}), 200
    except Exception as e:
        print(f"Error deleting chat thread: {e}")
        return jsonify({"error": "Failed to delete chat thread."}), 500

@app.route('/fetch_html', methods=['GET'])
@jwt_required()
def fetch_html():
    url = request.form.get('url')  # Fetch 'url' from form data
    if not url:
        return jsonify({"message": "Missing URL parameter"}), 400

    try:
        # Fetch the content from the URL
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for HTTP errors
        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract text
        text = soup.get_text(separator=' ', strip=True)
        return jsonify({"message": text}), 200
    except requests.RequestException as e:
        return jsonify({"message": str(e)}), 500
    
@app.route('/save_documentation', methods=['GET'])
@jwt_required()
def save_documentation():
    user_id = get_jwt_identity()

    # Get the documentation data from the request
    doc_title = request.form.get('doc_title')
    doc_content = request.form.get('doc_content')

    if not doc_title or not doc_content:
        return jsonify({"message": "Missing documentation title or content"}), 400

    # Save the documentation to the database
    db = get_db()
    try:
        db.execute('INSERT INTO Documentation (doc_title, doc_content) VALUES (?, ?)', 
                   (doc_title, doc_content))
        db.commit()
        return jsonify({"message": "Documentation saved successfully"}), 201
    except Exception as e:
        print(f"Error saving documentation: {e}")
        return jsonify({"error": "Failed to save documentation"}), 500


if __name__ == '__main__':
    app.run(debug=True)
