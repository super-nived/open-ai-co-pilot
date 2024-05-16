from openai import OpenAI
client = OpenAI(api_key="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")



def create_vector_store(name,file_ids):
    try:
        vector_store = client.beta.vector_stores.create(
            name=name,
            file_ids=[file_ids]
        )
        print("Vector store created successfully:", vector_store)
        return vector_store.id
    except Exception as e:
        print("An error occurred while creating the vector store:", e)
        return None


def delete_vector_store(vector_store_id):
    try:
        vector_store = client.beta.vector_stores.delete(
            vector_store_id=vector_store_id
        )
        print("Vector store deleted successfully:", vector_store)
        return vector_store
    except Exception as e:
        print("An error occurred while deleted the vector store:", e)
        return None
    
def list_vector_store():
    try:
        vector_store = client.beta.vector_stores.list()
        print("Vector store listed successfully:", vector_store)
        return vector_store
    except Exception as e:
        print("An error occurred while listing the vector store:", e)
        return None
    
# list_vector_store() 
# list_vector_store()
# data = [
#     'vs_fjXbaDK6KUdrmi6v91mK1ClV',
#     'vs_vQjxjpvaIoN76g6hBxp6phTY',
#     'vs_snt4cHFNXdr9BKplZUGK4pxE'
# ]

# for i in data:
#     client.beta.vector_stores.delete(vector_store_id=i)
#     print('done')

# file =client.beta.vector_stores.create
# print(file)
