from openai import OpenAI
client = OpenAI(api_key="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")

def create_assistant(name, instructions, model):
    """Create a new assistant with given parameters."""
    assistant = client.beta.assistants.create(
        name=name,
        instructions=instructions,
        model=model,
        tools=[{"type": "file_search"}]
    )
    return assistant

def create_vector_store(name="Financial Statements"):
    """Create a new vector store with a given name."""
    vector_store = client.beta.vector_stores.create(name=name)
    return vector_store

def upload_files_and_update_assistant(file_paths, assistant_id):
    """Upload files to the vector store and update the assistant with this vector store."""
    # Create the vector store
    vector_store = create_vector_store()
    
    # Open file streams
    file_streams = [open(path, "rb") for path in file_paths]
    
    # Upload files and poll for status
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )
    
    # Close file streams
    for stream in file_streams:
        stream.close()
    
    # Update the assistant with new vector store ID
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
    )
    
    return assistant, file_batch.status, file_batch.file_counts


# # Define file paths and assistant ID
# file_paths = ["Documentation.txt"]  # Make sure the file is in the root directory or provide the correct path
# assistant_id = "asst_eH8AX6gak9olVcLkuA5QSmwT"  # Replace with your actual assistant ID

# # Call the function and print the result
# assistant, status, file_counts = upload_files_and_update_assistant(file_paths, assistant_id)
# print(f"Assistant Updated: {assistant}")
# print(f"File Batch Status: {status}")
# print(f"File Counts: {file_counts}")



def query_assistant(prompt):
    # Create a thread with the user's message
    thread = client.beta.threads.create(
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Run the assistant with the created thread
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id="asst_eH8AX6gak9olVcLkuA5QSmwT",
        instructions="Your name is ass-co-pilot. if user asking anything retive data in you knowladge base then anser "
    )
    
    # Retrieve the latest message from the assistant
    messages = client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
    response = messages.data[0].content[0].text.value
    
    return response

# Example usage
prompt = "Tell me about AAs explorer."
response = query_assistant(prompt)
print(f"Assistant response: {response}")