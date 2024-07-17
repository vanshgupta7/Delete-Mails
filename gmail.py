import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
import base64 

SCOPES = ['https://mail.google.com/']

# Driver function
def main():
	local_credentials = None
	if os.path.exists("token.json"):
		local_credentials = Credentials.from_authorized_user_file("token.json", SCOPES)
	# If there are no (valid) credentials available, let the user log in.
	if not local_credentials or not local_credentials.valid:
		if local_credentials and local_credentials.expired and local_credentials.refresh_token:
			local_credentials.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
				"credentials.json", SCOPES
			)
			local_credentials = flow.run_local_server(port=0)
			# Save the credentials for the next run
			with open("token.json", "w") as token:
				token.write(local_credentials.to_json())

	
	service = build("gmail", "v1", credentials=local_credentials)
	filtered_list = search_messages(service=service,query="from: discuss@leetcode.com")
	print(len(filtered_list))
	# mark_read(service=service,messages=filtered_list)
	for msg in filtered_list:
		# read_message(service=service,message=msg)
		delete_message(service=service, message=msg)

# Function to get all the labels present in the users list
def get_all_labels(service):

	try:
	  	# Call the Gmail API
		results = service.users().labels().list(userId="me").execute()
		labels = results.get("labels", [])

		if not labels:
			print("No labels found.")
			return
		print("Labels:")
		for label in labels:
			print(label["name"])

	except HttpError as error:
		# TODO(developer) - Handle errors from gmail API.
		print(f"An error occurred: {error}")

# Function to read a particular message
def read_message(service,message):
	txt = service.users().messages().get(userId='me', id=message['id']).execute() 

	# Use try-except to avoid any Errors 
	try: 
	# Get value of 'payload' from dictionary 'txt' 
		payload = txt['payload'] 
		headers = payload['headers'] 

		# Look for Subject and Sender Email in the headers 
		for d in headers: 
			if d['name'] == 'Subject': 
				subject = d['value'] 
			if d['name'] == 'From': 
				sender = d['value'] 

		# The Body of the message is in Encrypted format. So, we have to decode it. 
		# Get the data and decode it with base 64 decoder. 
		parts = payload.get('parts')[0] 
		data = parts['body']['data'] 
		data = data.replace("-","+").replace("_","/") 
		decoded_data = base64.b64decode(data) 

		# Now, the data obtained is in lxml. So, we will parse  
		# it with BeautifulSoup library 

		# soup = BeautifulSoup(decoded_data , "lxml") 
		# body = soup.body() 

		# Printing the subject, sender's email and message 
		print("Subject: ", subject) 
		print("From: ", sender) 
		print("Message: ", decoded_data) 
		print('\n') 
	except Exception as error:
		print(error) 
		pass

# Simple function to delete a particular message
def delete_message(service, message):
	try:
		response = service.users().messages().delete(userId='me', id=message['id']).execute()
		return response
	except Exception as error:
		print(error) 

# Function to convert a 1D list to a 2D list such that each list has a maximum of 999 elements
# This is done because batchModify has a limit of max 1000 elements in a list
def create_2d_list(original_list, m):
    # Initialize the 2D list
    new_2d_list = []
    
    # Iterate over the original list, taking m elements at a time
    for i in range(0, len(original_list), m):
        # Slice the list from i to i + m and append to the 2D list
        new_2d_list.append(original_list[i:i + m])
    
    return new_2d_list

# Function to mark read a particular set of messages
def mark_read(service,messages):
	new_list = create_2d_list(messages,999)

	for ls in new_list:
		assert(len(ls)<1000)
		response =  service.users().messages().batchModify(
		userId='me',
		body={
			'ids': [ msg['id'] for msg in ls ],
			'removeLabelIds': ['UNREAD']
		}
		).execute()

# Function to display all the messages
def get_all_messages(service):
	result = service.users().messages().list(userId='me').execute() 

	# We can also pass maxResults to get any number of emails. Like this: 
	# result = service.users().messages().list(maxResults=200, userId='me').execute() 
	messages = result.get('messages') 

	# messages is a list of dictionaries where each dictionary contains a message id. 

	# iterate through all the messages 
	for msg in messages: 
		# Get the message from its id 
		txt = service.users().messages().get(userId='me', id=msg['id']).execute() 

		try: 
		# Get value of 'payload' from dictionary 'txt' 
			payload = txt['payload'] 
			headers = payload['headers'] 

			# Look for Subject and Sender Email in the headers 
			for d in headers: 
				if d['name'] == 'Subject': 
					subject = d['value'] 
				if d['name'] == 'From': 
					sender = d['value'] 

			# The Body of the message is in Encrypted format. So, we have to decode it. 
			# Get the data and decode it with base 64 decoder. 
			parts = payload.get('parts')[0] 
			data = parts['body']['data'] 
			data = data.replace("-","+").replace("_","/") 
			decoded_data = base64.b64decode(data) 

			# Now, the data obtained is in lxml. So, we will parse  
			# it with BeautifulSoup library 

			# soup = BeautifulSoup(decoded_data , "lxml") 
			# body = soup.body() 

			# Printing the subject, sender's email and message 
			print("Subject: ", subject) 
			print("From: ", sender) 
			print("Message: ", decoded_data) 
			print('\n') 
		except Exception as error:
			print(error) 
			pass
		break

# Returns a list of emails that match a particular query
# Can use query="label: UNREAD" to find all UNREAD messages
# Check this https://support.google.com/mail/answer/7190 link for more info
def search_messages(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

if __name__ == "__main__":
  main()