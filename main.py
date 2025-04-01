import logging
import requests
import csv
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🚀 CSV 파일을 읽어와 슬래시 커맨드 매핑
COMMANDS = {}

def load_commands(csv_file="commands.csv"):
    """CSV 파일에서 슬래시 커맨드와 응답 메시지를 읽어들임"""
    global COMMANDS
    COMMANDS.clear()  # 기존 데이터 초기화
    try:
        with open(csv_file, mode="r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                command = row["command"].strip()
                response_message = row["response_message"].strip()
                COMMANDS[command] = response_message
        logger.info("✅ CSV 파일 로드 완료: %s", COMMANDS)
    except Exception as e:
        logger.error("❌ CSV 파일을 읽는 중 오류 발생: %s", e)

# 초기 실행 시 CSV 로드
load_commands()

@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    """Dooray 슬래시 커맨드 처리"""
    data = request.json
    logger.info("📥 Received Data: %s", data)

    command = data.get("command", "").strip()
    response_url = data.get("responseUrl")  # 🚀 비동기 응답 URL

    if command in COMMANDS:
        response_message = COMMANDS[command]  # CSV에서 불러온 응답 메시지

        # 🚀 Dooray가 인식할 수 있는 응답 포맷
        response_data = {
            "text": response_message,
            "responseType": "inChannel"  # ephemeral = 사용자에게만 보이는 응답
        }

        # 🚀 즉시 응답
        logger.info("✅ Sending immediate response: %s", response_data)

        # 🚀 비동기 응답 (responseUrl이 있는 경우 Dooray에 전송)
        if response_url:
            requests.post(response_url, json=response_data)
            logger.info("✅ Sent async response to Dooray: %s", response_url)

        return jsonify(response_data), 200

    logger.warning("❌ Unknown command received: %s", command)
    return jsonify({"text": "Unknown command", "responseType": "ephemeral"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0")
