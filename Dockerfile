# Python 3.9 の公式イメージを使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をインストールするために必要なファイルをコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコンテナにコピー
COPY . .

# Firebaseサービスアカウントキーは環境変数から読み込むため、コンテナイメージには含めない
# ローカルテストのために含める場合は、COPY . . の前に serviceAccountKey.json をコピーする

# ポート 8080 を公開 (Cloud Runの要件)
EXPOSE 8080

# アプリケーションをGunicornで起動
# Cloud Runは環境変数 PORT でポートを渡すため、8080をデフォルト値として設定
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app