import uuid
from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from vonage import Client, Sms
# from dotenv import load_dotenv
# import os

# load_dotenv()

my_key = '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'

db = firestore.client()

VONAGE_API_KEY = "1ce5e2b3"
VONAGE_API_SECRET = "Nfm7AZb5HnqLNJ1n"

vonage_client = Client(key=VONAGE_API_KEY, secret=VONAGE_API_SECRET)

vonage_sms = Sms(vonage_client)

user_ref = db.collection('users')
station_ref = db.collection('stations')

userapi = Blueprint('userapi', __name__)

# **********************************Add User API*****************************************
@userapi.route('/add', methods=['POST'])
def create():
    try:
        id = uuid.uuid4()
        user_ref.document("pthakare").set(request.json)
        return jsonify({'success': True}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

# **********************************List Users API*****************************************
@userapi.route('/list', methods=['GET'])
def read_users():
    try:
        users = [doc.to_dict() for doc in user_ref.stream()]
        return jsonify(users), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

# **********************************Specific User API*****************************************
@userapi.route('/spec_user/<string:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user_doc = user_ref.document(user_id).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()

            subcollection_ref = user_ref.document(user_id).collection('feedbacks')
            subcollection_data = [doc.to_dict() for doc in subcollection_ref.stream()]

            user_data['subcollection_data'] = subcollection_data

            return jsonify(user_data), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return f"An Error Occurred: {e}"
    
# **********************************Specific Station API*****************************************
@userapi.route('/spec_station/<string:station_name>', methods=['GET'])
def get_station(station_name):
    try:
        station_doc = station_ref.document(station_name).get()

        if station_doc.exists:
            station_data = station_doc.to_dict()

            subcollection_ref = station_ref.document(station_name).collection('feedbacks')
            subcollection_data = [doc.to_dict() for doc in subcollection_ref.stream()]

            ratings = [int(feedback.get('ratings', 0)) for feedback in subcollection_data]
            mean_rating = mean(ratings) if ratings else 0

            station_data['subcollection_data'] = subcollection_data
            station_data['mean_rating'] = mean_rating

            return jsonify(station_data), 200
        else:
            return jsonify({'error': 'Station not found'}), 404
    except Exception as e:
        return jsonify({'error': f"An error occurred: {e}"}), 500


# **********************************GET FEEDBACK API*****************************************
@userapi.route('/feedback', methods=['GET'])
def get_feedback():
    try:
        feedback_list = []

        for user_doc in user_ref.stream():
            user_data = user_doc.to_dict()
            user_id = user_doc.id

            feedback_collection_ref = user_ref.document(user_id).collection('feedbacks')

            for feedback_doc in feedback_collection_ref.stream():
                feedback_data = feedback_doc.to_dict()

                feedback_object = {
                    'user_id': user_id,
                    'feedback_text': feedback_data.get('text', 'No text available'),
                    'feedback_ratings': feedback_data.get('ratings', None),
                    'date': feedback_data.get('date', None),
                    'police_station': feedback_data.get('station_name', None),
                    'user_name': user_data.get('name', None)
                }
                feedback_list.append(feedback_object)

        return jsonify(feedback_list), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

# **********************************ADD FEEDBACK API*****************************************
from datetime import datetime
import pytz

@userapi.route('/feedback/add/<string:user_id>', methods=['POST'])
def add_feedback(user_id):
    try:
        feedback_data = request.json

        user_doc = user_ref.document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_name = user_data.get('name')
        else:
            return jsonify({'error': 'User not found'}), 404

        ist = pytz.timezone('Asia/Kolkata')
        feedback_data['date'] = datetime.now(ist).isoformat()
        
        feedback_data['user_name'] = user_name

        feedback_collection_ref = user_ref.document(user_id).collection('feedbacks')
        feedback_doc_ref = feedback_collection_ref.add(feedback_data)

        station_name = feedback_data.get('station_name', None)

        if station_name:
            station_feedback_ref = station_ref.document(station_name).collection('feedbacks')
            station_doc_ref = station_feedback_ref.add(feedback_data)

            return jsonify({'success': True, 'feedback_id': feedback_doc_ref[1].id, 'station_feedback_id': station_doc_ref[1].id}), 200

        return jsonify({'success': True, 'feedback_id': feedback_doc_ref[1].id}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"


# **********************************List Stations API*****************************************
from statistics import mean

@userapi.route('/listStations', methods=['GET'])
def read_stations():
    try:
        stations_data = []

        for station_doc in station_ref.stream():
            station_data = station_doc.to_dict()

            feedback_collection_ref = station_ref.document(station_doc.id).collection('feedbacks')
            feedback_data = [doc.to_dict() for doc in feedback_collection_ref.stream()]

            overall_rating = calculate_overall_rating(feedback_data)
            station_data['overall_rating'] = overall_rating

            station_data['feedbacks'] = feedback_data

            stations_data.append(station_data)

        return jsonify(stations_data), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

def calculate_overall_rating(feedback_data):
    ratings = [int(feedback.get('ratings', 0)) for feedback in feedback_data]

    overall_rating = mean(ratings) if ratings else 0

    return overall_rating

    
# **********************************SEND SMS API*****************************************
@userapi.route('/send_sms', methods=['POST'])
def send_sms():
    try:
        data = request.json

        to_phone_number = data.get('to_phone_number', None)
        if not to_phone_number:
            return jsonify({'error': 'Invalid phone number'}), 400

        sms_text = data.get('sms_text', 'A text message sent using the Vonage SMS API')

        response_data = vonage_sms.send_message(
            {
                "from": "Vonage APIs",
                "to": to_phone_number,
                "text": sms_text,
            }
        )

        if response_data["messages"][0]["status"] == "0":
            return jsonify({'success': True, 'message_id': response_data["messages"][0]["message-id"]}), 200
        else:
            return jsonify({'error': f"Message failed with error: {response_data['messages'][0]['error-text']}"}), 500

    except Exception as e:
        return jsonify({'error': f"An error occurred: {e}"}), 500
    

# **********************************POST CASE API*****************************************
@userapi.route('/case/add/<string:station_name>', methods=['POST'])
def post_case(station_name):
    try:
        case_data = request.json

        case_number = case_data.get('case_number')

        if not case_number:
            return jsonify({'error': 'Case number is required in the request data'}), 400

        ist = pytz.timezone('Asia/Kolkata')
        case_data['date'] = datetime.now(ist).isoformat()

        cases_collection_ref = station_ref.document(station_name).collection('cases').document(case_number)

        cases_collection_ref.set(case_data)

        case_data_with_id = cases_collection_ref.get().to_dict()

        return jsonify({'success': True, 'case_data': case_data_with_id}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"


# **********************************GET CASES API*****************************************
@userapi.route('/get_cases/<string:station_name>', methods=['GET'])
def get_cases(station_name):
    try:
        cases_collection_ref = station_ref.document(station_name).collection('cases')

        cases = [doc.to_dict() for doc in cases_collection_ref.stream()]

        return jsonify(cases), 200
    except Exception as e:
        return f"An Error Occurred: {e}"
    

# **********************************UPDATE STATION STATUS API*****************************************
@userapi.route('/update_station_status/<string:station_name>', methods=['PUT'])
def update_station_status(station_name):
    try:
        new_status = request.json.get('new_status')

        status_mapping = {'approve': 1, 'reject': 2}

        if new_status not in status_mapping:
            return jsonify({'error': 'Invalid status provided. Must be "approve" or "reject".'}), 400

        station_doc_ref = station_ref.document(station_name)

        station_doc_ref.update({'status': status_mapping[new_status]})

        return jsonify({'success': True, 'message': f'Status updated to {status_mapping[new_status]} for station {station_name}'}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"


# **********************************SUMMARIZE THE DATA*****************************************
from openai import OpenAI

client = OpenAI(api_key=my_key)

@userapi.route('/generate_summary', methods=['POST'])  
def generate_summary():
    try:
        request_data = request.json
        
        json_data = request_data.get('data', [])

        feedback_texts = [item["text"] for item in json_data]

        input_text = "\n".join(feedback_texts)

        prompt = f"""
        Consider you are summarizing feedback on a police station's performance. Compile the following feedback into a concise summary. 
        Maintain clarity, avoid jargon, and keep the summary under 150 words.

        {input_text}

        Additionally, analyze the sentiments expressed in the feedback and provide a count. Out of the given texts:

        happy: {len([1 for item in json_data if "positive" in item["text"].lower() or "satisfied" in item["text"].lower()])}
        sad: {len([1 for item in json_data if "unpleasant" in item["text"].lower() or "disappointed" in item["text"].lower()])}
        """

        engine_version = "gpt-3.5-turbo-instruct"

        response = client.completions.create(
            model=engine_version,
            prompt=prompt,
            max_tokens=150
        )

        summary = response.choices[0].text

        return jsonify({'summary': summary}), 200

    except Exception as e:
        return jsonify({'error': f"An error occurred: {e}"}), 500



