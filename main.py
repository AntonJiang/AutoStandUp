import os.path
import sys

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly',
          'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/drive.appdata']

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret_688549307326-ba24onctnfdh6vdagtq48ijkppfepg4u.apps.googleusercontent.com.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

doc_service = build('docs', 'v1', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)


def get_all_files(folder_id='1ljfytcSZi1d0er46Z7FxI5yL85QnAAoI'):
    page_token = None
    files = []
    while True:
        response = drive_service.files().list(q=f"'{folder_id}' in parents",
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name)',
                                              pageToken=page_token).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return files


def get_recent_workflows(days):
    return get_all_files()[:days]


def get_all_text_run(doc):
    runs = []
    for paragraph in doc['body']['content']:
        if 'paragraph' in paragraph.keys():
            for element in paragraph['paragraph']['elements']:
                runs.append(element['textRun'])
    return runs


def flatten(t):
    return [item for sublist in t for item in sublist]


def is_strike(textRun):
    return 'strikethrough' in textRun['textStyle'] and textRun['textStyle']['strikethrough']


def clean_and_dedup(runs):
    return list(dict.fromkeys([t.strip() for t in runs]))


def print_array(arr):
    [print(f'{item}') for item in arr]


def main(days):

    recent_flows = get_recent_workflows(days)

    def get_doc(file_id):
        return doc_service.documents().get(documentId=file_id).execute()

    docs = [get_doc(item['id']) for item in recent_flows]

    striked_tRun = flatten([[tRun for tRun in get_all_text_run(doc) if is_strike(tRun)] for doc in docs])

    striked_tRun = [run['content'] for run in striked_tRun if run['content'] != '\n']

    work_done = clean_and_dedup(striked_tRun)

    print_array(work_done)


if __name__ == '__main__':
    main(days=int(sys.argv[1]))
