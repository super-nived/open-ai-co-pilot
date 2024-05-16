from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
import os
import json
from vector import *
from Getfile import *
from werkzeug.utils import secure_filename
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)
CORS(app)

app.secret_key = os.urandom(24)

openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)


ID_STORE = 'ids_store.json'

def save_ids(key, id_value):
    """Save key-id pair to a JSON file."""
    try:
        data = load_ids()
        data[key] = id_value
        with open(ID_STORE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving ID for key '{key}': {e}")

def load_ids():
    """Load all key-id pairs from a JSON file."""
    try:
        if os.path.exists(ID_STORE):
            with open(ID_STORE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading IDs: {e}")
        return {}

def DeleteFile(id):
    try:
        client.files.delete(file_id=id)
        return "file delted done"
    except:
        return 'file deleted error'

@app.route('/',methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/post_data', methods=['POST'])
def post_data():
    if 'file' in request.files:
        file = request.files['file']
        # data_string = file.read()
        try:
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            # Ensure the 'temp' directory exists
            directory = os.path.join(os.getcwd(), 'temp')
            if not os.path.exists(directory):
                os.makedirs(directory)
            filepath = os.path.join(directory, secure_filename('AAS.json'))
            file.save(filepath)
            print('data saved as in temp folder ')
            message_file = client.files.create(file=open("temp/AAS.json", "rb"), purpose="assistants")
            save_ids('file_id',message_file.id)
            vector_id = create_vector_store('AAsvector',message_file.id)
            save_ids('vector_id',vector_id)
            return jsonify({"message": "File uploaded successfully"}), 200
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400
    else:
        print('error third')
        return jsonify({"error": "Request must contain JSON data"}), 400



@app.route('/query_data', methods=['POST'])
def query_data():
    if 'query' in request.form:
        data = request.form['query']
        # print(data,'.sd..sdf.sd')
        if  data:
                vector_id = load_ids()['vector_id']
                if vector_id:
                    thread = client.beta.threads.create(
                    messages=[
                        {
                        "role": "user",
                        "content":data ,
                        # Attach the new file to the message.
                        # "attachments": [
                        #     { "file_id":"file-fBYOB4T16e2TltdVCesAjURL", "tools": [{"type": "file_search"}] }
                        # ],
                        
                        }
                    ],
                    tool_resources={
                            "file_search": {
                            "vector_store_ids": [vector_id]
                            }
                        }
                    )
                    run = client.beta.threads.runs.create_and_poll(
                        thread_id=thread.id, assistant_id="asst_0KMA6mk2h61u6jJtnXw3pcNe",instructions="your name is ass-co-pilot ,if user is asking for an image, video,manuals, glbfile, or pdf link in a file, you should respond like direct link for display in corresponding tag so avoid '' this one in link also give response in json format { link : url }. There's no need to explain anything. If none of these, you can answer based on your requirement."

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
                    return jsonify({"message": "Please upload a file to ask questions."}), 200
        else:
            print('error 2')
            return jsonify({"error": "must contain a 'query' key."}), 400
    else:
        print('error 3')
        return jsonify({"error": "Please enter a valid question."}), 400

@app.route('/end_chat', methods=['POST'])
def endChat():
    file_id = load_ids()['file_id']
    vector_id = load_ids()['vector_id']
    if vector_id and file_id:
            try:
                delete_vector_store(vector_id)
                save_ids('vector_id','')
                delete_file(file_id)
                save_ids('file_id','')

                return jsonify({"message": "Chat ended and resources cleaned up."}), 200
            except Exception as e:
                print(f"Error ending chat: {e}")
                return jsonify({"error": "Error ending chat."}), 500
    else:
        return jsonify({"error": "file_id and vector_id are required to end chat."}), 400

if __name__ == '__main__':
    app.run(debug=True)
