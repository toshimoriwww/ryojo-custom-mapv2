from flask import Flask, render_template, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Flaskアプリを初期化
app = Flask(__name__)

# --- Firebase Admin SDK の初期化 ---
# Cloud Run環境では、環境変数から自動で認証情報が読み込まれる
# ローカル開発時のみ、サービスアカウントキーファイルを使用する
if not firebase_admin._apps:
    try:
        # GOOGLE_APPLICATION_CREDENTIALS環境変数が設定されていればそれを使う
        # Cloud Runでは自動で設定される
        cred = credentials.ApplicationDefault()
    except Exception:
        # ローカル開発用のフォールバック
        try:
            cred = credentials.Certificate("serviceAccountKey.json")
            print("ローカル用のserviceAccountKey.jsonを使用して初期化します。")
        except FileNotFoundError:
            print("警告: サービスアカウントキーが見つかりません。Cloud Run環境外ではFirestoreに接続できません。")
            cred = None # credがNoneのままだと後でエラーになる

    if cred:
        firebase_admin.initialize_app(cred)

db = firestore.client()
# Firestoreのコレクション名
COLLECTION_NAME = 'cases' 

@app.route('/')
def index():
    """トップページ（地図表示）をレンダリング"""
    return render_template('index.html')

@app.route('/api/locations') 
def get_locations():
    """Firestoreから位置情報データを取得してJSON形式で返すAPI"""
    try:
        docs_stream = db.collection(COLLECTION_NAME).stream()
        locations_data = []
        for doc in docs_stream:
            data = doc.to_dict()
            # 緯度(lat)と経度(lng)がGeoPoint型の場合の処理
            if 'location' in data and isinstance(data['location'], firestore.GeoPoint):
                locations_data.append({
                    "name": data.get("name", "名称未設定"),
                    "lat": data["location"].latitude,
                    "lng": data["location"].longitude
                })
        return jsonify(locations_data)
    except Exception as e:
        print(f"APIエラー: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # ローカル開発サーバーの起動
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
