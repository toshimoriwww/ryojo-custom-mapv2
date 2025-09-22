import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import os
import math

# --- Firebase Admin SDK の初期化 ---
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    if not firebase_admin._apps:
        # storageBucketの指定は不要になったので削除
        firebase_admin.initialize_app(cred) 
except FileNotFoundError:
    print("エラー: serviceAccountKey.jsonが見つかりません。")
    exit()

db = firestore.client()

# --- 定数設定 ---
EXCEL_FILE = 'customization_data.xlsx'
COLLECTION_NAME = 'cases'

# --- 削除機能 ---
def delete_collection(coll_ref, batch_size=50):
    # (この関数は変更なし)
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0
    for doc in docs:
        print(f'Deleting doc {doc.id}')
        doc.reference.delete()
        deleted += 1
    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

# --- メインの処理 ---
def initialize_or_update_db():
    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"Excelファイル '{EXCEL_FILE}' を読み込みました。")
    except FileNotFoundError:
        print(f"エラー: Excelファイル '{EXCEL_FILE}' が見つかりません。")
        return
    
    # 既存データの削除
    print(f"コレクション '{COLLECTION_NAME}' 内の既存データをすべて削除します...")
    coll_ref = db.collection(COLLECTION_NAME)
    delete_collection(coll_ref)
    print("既存データの削除が完了しました。")

    # Excelの各行を処理
    for index, row in df.iterrows():
        data = row.to_dict()

        for key, value in data.items():
            if isinstance(value, float) and math.isnan(value):
                data[key] = None

        if not data.get('整備名'):
            print(f"行 {index+2} をスキップ: 必須データ（整備名）が不足しています。")
            continue

        # --- ▼▼▼ 画像処理ロジックを大幅に簡略化 ▼▼▼ ---
        if '写真' in data and data['写真']:
            image_filename = str(data['写真'])
            # Webサイトで使うためのURLパスを直接作成
            data['image_url'] = f"/static/images/{image_filename}"
        
        if '写真' in data:
            del data['写真']
        # --- ▲▲▲ ここまで ▲▲▲ ---

        # 緯度経度の変換
        if data.get('緯度'):
            data['latitude'] = float(data['緯度'])
            del data['緯度']
        if data.get('経度'):
            data['longitude'] = float(data['経度'])
            del data['経度']

        doc_id = str(data['整備名'])
        try:
            db.collection(COLLECTION_NAME).document(doc_id).set(data) 
            print(f"Firestoreにドキュメントを追加しました: {doc_id}")
        except Exception as e:
            print(f"エラー: ドキュメント '{doc_id}' の書き込みに失敗しました - {e}")

    print("Firestoreのデータ更新が完了しました。")
    
if __name__ == "__main__":
    initialize_or_update_db()