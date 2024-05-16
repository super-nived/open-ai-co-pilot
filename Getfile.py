

from openai import OpenAI
client = OpenAI(api_key="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")


def create_file(file_path="temp/Ass.json", purpose="assistants"):
    try:
        with open(file_path, "rb") as file:
            file_response = client.files.create(
                file=file,
                purpose=purpose
            )
            print("File created successfully:", file_response)
            return file_response
    except Exception as e:
        print("An error occurred while creating the file:", e)
        return None

def delete_file(file_id):
    try:
        file_response = client.files.delete(file_id=file_id)
        print("File deleted successfully:", file_response)
        return file_response
    except Exception as e:
        print("An error occurred while deleting the file:", e)
        return None


# data =  [
#     'file-m4PJUVc8ztasBEjGwvmk0xw8',
#     'file-MFheoDp1X3xDpFhPnIt8ckWG',
#     'file-OSZ7cps8pIMsV2V3VryPlBq1',
#     'file-5vlj2tExYTAfD9vdh0U8aSKC',
#     'file-2W29WyXnhgNWqUPxWSTN9P9w',
#     'file-eTRL8nTCDurGd0DTQ7ptvHCN',
#     'file-k9IRxeBl1Td9ZcgJMioTfsOS',
#     'file-fBYOB4T16e2TltdVCesAjURL'
# ]

# for i in data:
#     client.files.delete(file_id=i)
#     print("file deletion done")

# files = client.files.list()
# print(files)


# assistant = client.beta.assistants.list()
# print(assistant)

# Upload the user provided file to OpenAI


#     {"id": "asst_rq5KUNLv1vwz50VFdDQXZ7ZH", "name": "AAS BOT IAPPS"},
#     {"id": "asst_ycyLWKP2BkoM7RMltnFM3yXq", "name": "Math Tutor"},
#     {"id": "asst_4Lx18Lw9DpXD9JtYdr6CHSSL", "name": "Math Tutor"},
#     {"id": "asst_9IgUXQdKYDue39qb9qDyQmP6", "name": "Math Tutor"},
#     {"id": "asst_88d7mJYqGc6de7lKmGJq9IZi", "name": "Math Tutor"},
#     {"id": "asst_s0434fqoT0nm6qi8TuP142GP", "name": "Financial Analyst Assistant"},
#     {"id": "asst_hmDSn941Z8j6lzKQCyYqeP5Q", "name": "Financial Analyst Assistant"}
# ]

# for i in data:
#     client.beta.assistants.delete(assistant_id=i['id'])
#     print("assistance deletion done")