from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    data = request.json  # JSON 데이터 파싱
    command_text = data.get("text", "").strip()  # 입력한 명령어 내용
    response_message = ''
    # 특정 키워드에 대한 응답 설정
    if command_text.lower() == "jira":
        response_message = {
            "title": "도움말",
            "text": "사용 가능한 명령어 리스트:\n1. `/help` - 도움말 표시\n2. `/status` - 현재 상태 조회",
        }

    return jsonify({"message": "데이터 수신 성공!", "received_data": response_message}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0")



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
