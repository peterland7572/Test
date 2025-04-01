import logging
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🚀 실제 Dooray 사용자 ID로 변경해야 함
MENTION_USERS = {
    "조현웅": '[@조현웅/SGE 품질검증팀](dooray://3570973280734982045/members/3790034441950345057 "member")'
}

@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    data = request.json
    logger.info("📥 Received Data: %s", data)

    command = data.get("command", "").strip()
    command_text = data.get("text", "").strip()
    response_url = data.get("responseUrl")  # 🚀 비동기 응답 URL

    if command == "/일감":
        response_message = (
            "**지라 일감 요청드립니다.**\n\n"
            "제목 :\n"
            "내용 :\n"
            "기간 :\n"
            "담당자 :\n"
            "기획서 :"
             "\n"
         "(dooray://3570973280734982045/members/3790034441950345057 \"member\")[@조현웅/SGE 품질검증팀]"  # 직접 문자열을 삽입
             "\n"
         "@조현웅/SGE 품질검증팀(dooray://3570973280734982045/members/3790034441950345057 \"member\")"  # 직접 문자열을 삽입
             "\n"
        )

        # 🚀 Dooray가 인식할 수 있는 응답 포맷
        response_data = {
            "text": "[링크](http://www.daum.net) Why",
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
    app.run(host="0.0.0.0", port=5000, debug=True)
