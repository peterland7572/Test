import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

# 📌 로그 설정
logging.basicConfig(level=logging.INFO)  # INFO 레벨 이상 로그 출력
logger = logging.getLogger(__name__)  # 로거 객체 생성

@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    data = request.json  # JSON 데이터 파싱
    logger.info("📥 Received Data: %s", data)  # 전체 데이터 로그 출력
    
    # 받은 텍스트(command)에 따라 처리
    command = data.get("command", "").strip()
    command_text = data.get("text", "").strip()  # 명령어 뒤에 입력된 텍스트
    logger.info("🔍 Received command: %s | Text: %s", command, command_text)  # 로그 출력

    # 명령어가 "/jira"일 때 응답 메시지 설정
    if command == "/jira":
        response_message = f"you said '{command_text}'" if command_text else "you said nothing."
        logger.info("✅ Responding with: %s", response_message)  # 응답 확인

        return jsonify({"message": response_message}), 200

    logger.warning("❌ Unknown command received: %s", command)
    return jsonify({"message": "Unknown command"}), 400

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
