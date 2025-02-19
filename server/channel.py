## channel.py - a simple message channel
##
from better_profanity import profanity
from flask import Flask, request, jsonify
import json
import requests


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'isFJDJAKFAKDFASJDFKFLDASÖFJDLAKSKFJASFÖA'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'http://vm146.rz.uni-osnabrueck.de/hub'
HUB_AUTHKEY = 'Crr-K24d-2N'
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "BeachLeague Chat"
CHANNEL_TOPIC = "Beach Volleyball"
CHANNEL_WELCOME_MESSAGE = "Welcome to BeachLeague Chat! Talk about beach volleyball, tournaments, and tips."
CHANNEL_ENDPOINT = "http://vm146.rz.uni-osnabrueck.de/u078/aiweb3/server/channel.wsgi" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'messages.json'
CHANNEL_TYPE_OF_SERVICE = 'aiweb24:chat'

profanity.load_censor_words() # setting up word filtering

@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
                                "name": CHANNEL_NAME,
                                "endpoint": CHANNEL_ENDPOINT,
                                "authkey": CHANNEL_AUTHKEY,
                                "type_of_service": CHANNEL_TYPE_OF_SERVICE,
                             }))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        print(response.text)
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    # check if message is present
    message = request.json
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    if not 'extra' in message:
        extra = None
    else:
        extra = message['extra']

    messages = read_messages()

    # Block messages with profanity
    if not profanity_check(message['content']):  
        return "Message blocked due to inappropriate content", 200  

    messages.append({
        'content': message['content'],
        'sender': message['sender'],
        'timestamp': message['timestamp'],
        'extra': extra,
    })

    # Generate a bot response if relevant
    bot_response = answering_messages(message['content'])
    if bot_response:
        messages.append({
            'content': bot_response,
            'sender': 'BeachBot',
            'timestamp': message['timestamp'],
            'extra': None,
        })

    
    messages = messages[-50:]

    save_messages(messages)  

    return "OK", 200

def read_messages():
    global CHANNEL_FILE, CHANNEL_WELCOME_MESSAGE
    try:
        f = open(CHANNEL_FILE, 'r')
    except FileNotFoundError:
        return [{'content': CHANNEL_WELCOME_MESSAGE, 'sender': 'System', 'timestamp': '0000-00-00T00:00:00Z', 'extra': None}]
    
    try:
        messages = json.load(f)
    except json.decoder.JSONDecodeError:
        messages = []
    f.close()

    # Ensure the welcome message is always included at the beginning
    if not messages or messages[0]['content'] != CHANNEL_WELCOME_MESSAGE:
        messages.insert(0, {
            'content': CHANNEL_WELCOME_MESSAGE,
            'sender': 'System',
            'timestamp': '0000-00-00T00:00:00Z',
            'extra': None,
        })

    return messages


def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

def profanity_check(message_content):
    return not profanity.contains_profanity(message_content)


def answering_messages(message_content):
    message_content = message_content.lower()
    if "osnabrück" in message_content:
        if "court" in message_content:
            return "There are several beachvolleyball courts across Osnabrück, for example in Wüste, Nahne and at Klushügel!"
        if "tournament" in message_content:
            return "There is a beachvolleyball league in Osnabrück! Checkout at www.instagram.com/beachliga_os/!"

    if "rule" in message_content or "rules" in message_content:
        return "You can read/download the newest regulation at www.fivb.com/beach-volleyball/the-game/official-rules-of-the-games/."
    
    if "professional" in message_content and "watch" in message_content:
        return "The German Beach Tour can be watched for free. Checkout Spontent on Twitch!"
    
    if "float" in message_content:
        return "A serve with minimal spin, causing the ball to move unpredictably in the air, making it difficult for the receiver to track."
    
    if "top spin" in message_content:
        return "A serve with heavy spin that dips quickly, making it more challenging for the opponent to pass due to its fast downward trajectory."

    if "block" in message_content:
        return "A defensive technique where players jump near the net to intercept or deflect an opponent's attack."
    if "pass" in message_content:
        return "A fundamental technique for receiving the serve or attack, typically executed using the forearms to direct the ball to the setter."
    if "set" in message_content:
        return "The act of using the hands to deliver an accurate ball to a teammate, typically in preparation for an attack."
    if "spike" in message_content:
        return "An offensive move where a player jumps and hits the ball with force, aiming for a spot on the opponent’s court."
    if "digger" in message_content:
        return "A defensive move to receive and control a hard-hit ball, typically done using the forearms or with an open hand technique."
    if "roll shot" in message_content:
        return "A softer attack technique where the ball is hit with minimal spin, often used to place the ball in a strategic location over the block."
    if "cut shot" in message_content:
        return " A shot made with a quick wrist movement, causing the ball to curve sharply and land in the opponent’s court, usually to one side."
    if "jump serve" in message_content:
        return " A powerful serve executed by jumping and striking the ball in mid-air, typically generating more speed and spin than a regular serve."
 
    return "Alright! 🌴"


# Start development web server
# run flask --app channel.py register
# to register channel with hub

# if __name__ == '__main__':
#     app.run(port=80, debug=True)
