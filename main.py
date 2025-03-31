import logging
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    data = request.json
    logger.info("📥 Received Data: %s", data)

    command = data.get("command", "").strip()
    command_text = data.get("text", "").strip()
    response_url = data.get("responseUrl")  # 🚀 비동기 응답 URL

    if command == "/jira":
        response_message = f"you said '{command_text}'" if command_text else "you said nothing."

        # 🚀 Dooray가 인식할 수 있는 응답 포맷
        response_data = {
            "text": response_message,
            "responseType": "ephemeral"  # ephemeral = 사용자에게만 보이는 응답
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
    app.run(host="0.0.0.0", port=5000)




'''
def dooray_webhook():
    data = request.json  # Dooray에서 받은 데이터
    command_text = data.get("text", "").strip()  # 입력한 명령어 내용

    # 특정 키워드에 대한 응답 설정
    if command_text.lower() == "help":
        response_message = {
            "title": "도움말",
            "text": "사용 가능한 명령어 리스트:\n1. `/help` - 도움말 표시\n2. `/status` - 현재 상태 조회",
            "webHookServiceType": "TEAMS",
        }
    elif command_text.lower() == "status":
        response_message = {
            "title": "시스템 상태",
            "text": "✅ 서버 정상 작동 중\n🕒 현재 시간: 12:30 PM",
            "webHookServiceType": "TEAMS",
        }
    else:
        response_message = {
            "title": "알 수 없는 명령어",
            "text": f"입력한 명령어 `{command_text}` 를 이해할 수 없습니다. `/help` 를 입력해 보세요!",
            "webHookServiceType": "TEAMS",
        }

    return jsonify(response_message)

'''
