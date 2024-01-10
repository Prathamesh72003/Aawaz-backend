import uuid
from flask import Blueprint, request, jsonify
from firebase_admin import firestore

db = firestore.client()

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

            station_data['subcollection_data'] = subcollection_data

            return jsonify(station_data), 200
        else:
            return jsonify({'error': 'Station not found'}), 404
    except Exception as e:
        return f"An Error Occurred: {e}"



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
                    'police_station': feedback_data.get('station', None),
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
@userapi.route('/listStations', methods=['GET'])
def read_stations():
    try:
        stations = [doc.to_dict() for doc in station_ref.stream()]
        return jsonify(stations), 200
    except Exception as e:
        return f"An Error Occurred: {e}"
