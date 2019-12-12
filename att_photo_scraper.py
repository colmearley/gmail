# from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64, requests, datetime, json

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
service = None

def connect():
    global service
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    print('Connecting to Gmail Service')
    service = build('gmail', 'v1', credentials=creds)

def main():
    connect()
    with open('config.json') as f:
        config = json.load(f)

    process_page(q=config['q'])

def process_page(q,page_token=None):
    results = service.users().messages().list(userId='me',q=q,pageToken=page_token).execute()
    for message in results['messages']:
       try:
           process_message(message['id'])
       except Exception as ex:
           print('Error processing message :: ID:'+message['id']+' :: Error Message:'+ex)
           raise
    if 'nextPageToken' in results:
        process_page(page_token=results['nextPageToken'],q=q)

def process_message(message_id):
    message = service.users().messages().get(userId='me',id=message_id).execute()
    message_date = datetime.datetime.utcfromtimestamp(int(message['internalDate']) // 1000).strftime('%Y%m%d')
    date_path = os.path.join('photos', message_date)
    if os.path.exists(date_path):
        return

    # print('Processing Message: ID: '+message_id+' Date: '+message_date)
    print('Processing Message. Date:'+message_date)
    if not os.path.exists(date_path):
        os.makedirs(date_path)

    att_id = message['payload']['parts'][1]['body']['attachmentId']
    attachment = service.users().messages().attachments().get(userId='me',messageId=message_id,id=att_id).execute()
    data = base64.urlsafe_b64decode(attachment['data'])
    with open(os.path.join(date_path,'att.pdf'), 'wb') as f:
        f.write(data)

    for token in data.split():
        if b'.jpeg' in token:
            url = str(token,'utf-8')[1:-1]
            filename = url.split('/')[-1]
            savepath = os.path.join(date_path,filename)
            if os.path.exists(savepath):
                pass
            else:
                print('Downloading: ',url)
                file_data = requests.get(url)
                filename = url.split('/')[-1]
                with open(os.path.join(date_path,filename), 'wb') as f:
                    f.write(file_data.content)

if __name__ == '__main__':
    main()
