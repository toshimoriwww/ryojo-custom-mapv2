from flask import Flask, render_template, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Flaskアプリを初期化。これだけで 'static' フォルダが自動的に認識されます。
app = Flask(__name__)

# --- Firebase Admin SDK の初期化 ---
# (この部分は変更ありません)
if not firebase_admin._apps:
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        cred = credentials.ApplicationDefault()
    else:
        try:
            cred = credentials.Certificate("serviceAccountKey.json")
        except FileNotFoundError:
            print("serviceAccountKey.jsonが見つかりません。ローカル開発ではこのファイルが必要です。")
            exit()
    firebase_admin.initialize_app(cred)

db = firestore.client()
# JavaScript側で 'locations' を使っている場合は、名前を合わせます
COLLECTION_NAME = 'cases' 

# --- ルート定義 ---

@app.route('/')
def index():
    return render_template('index.html')

# JS側の fetch('/api/locations') に合わせてパスを修正
@app.route('/api/locations') 
def get_locations():
    try:
        docs = db.collection(COLLECTION_NAME).stream()
        locations_data = [doc.to_dict() for doc in docs]
        return jsonify(locations_data)
    except Exception as e:
        print(f"APIエラー: {e}")
        return jsonify({"error": str(e)}), 500

#
# 不要なため、serve_static 関数は完全に削除します
#

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))