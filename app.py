from flask import Flask, render_template, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.types import GeoPoint # GeoPointの型をインポート
import os

# Flaskアプリを初期化
app = Flask(__name__)

# --- Firebase Admin SDK の初期化 ---
# このロジックで、Cloud Run上かローカル環境かを正しく判定します
if not firebase_admin._apps:
    # Cloud RunなどのGCP環境では 'K_SERVICE' 環境変数が自動的に設定されます
    if os.getenv('K_SERVICE'):
        print("GCP environment detected. Using default application credentials.")
        # GCP環境ではサービスアカウントキーは不要で、割り当てられた権限が自動で使われます
        cred = credentials.ApplicationDefault()
    else:
        # ローカル開発環境向けの処理
        print("Local environment detected. Looking for serviceAccountKey.json.")
        try:
            cred = credentials.Certificate("serviceAccountKey.json")
        except FileNotFoundError:
            print("FATAL: serviceAccountKey.json not found. This file is required for local development.")
            # ローカルでキーがない場合は、問題を明確にするためにサーバーを終了します
            exit(1)
            
    firebase_admin.initialize_app(cred)

db = firestore.client()
COLLECTION_NAME = 'cases' 

# --- ルート定義 ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/locations') 
def get_locations():
    try:
        docs = db.collection(COLLECTION_NAME).stream()
        locations_data = []
        for doc in docs:
            data = doc.to_dict()
            # --- GeoPointをJSONに変換する処理を、より安全な方法に修正 ---
            if 'location' in data and data['location'] is not None:
                # 'location'フィールドが本当にGeoPoint型かを確認
                if isinstance(data['location'], GeoPoint):
                    data['location'] = {
                        'latitude': data['location'].latitude,
                        'longitude': data['location'].longitude
                    }
                else:
                    # GeoPointではない場合、エラーにせず警告ログを出し、locationをNoneに設定
                    print(f"Warning: Document {doc.id} has a 'location' field that is not a GeoPoint. Type is {type(data['location']).__name__}")
                    data['location'] = None
            
            locations_data.append(data)
        return jsonify(locations_data)
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

