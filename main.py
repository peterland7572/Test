import logging
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🚀 실제 Dooray 사용자 ID로 변경해야 함
MENTION_USERS = {
    "조현웅1": "[@조현웅/SGE 품질검증팀](dooray://3570973280734982045/members/3790034441950345057 \"member\") ",
    "조현웅": "[@조현웅/SGE 품질검증팀](dooray://3570973280734982045/members/3790034441950345057 \"member\") ",
    "김주현": "[@조현웅/SGE 품질검증팀](dooray://3570973280734982045/members/3790034441950345057 \"member\") ",
}

@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    data = request.json
    logger.info("📥 Received Data: %s", data)

    if not data:
        logger.warning("❌ No data received in request!")
        return jsonify({"text": "Invalid request", "responseType": "ephemeral"}), 400

    command = data.get("command", "").strip()
    command_text = data.get("text", "").strip()
    response_url = data.get("responseUrl")

    if command == "/일감":
        response_message = (
            f"{MENTION_USERS['조현웅1']} {MENTION_USERS['조현웅']} {MENTION_USERS['김주현']}\n"
            "**지라 일감 요청드립니다.**\n\n"
            "**제목** :\n"
            "**내용** :\n"
            "**기간** :\n"
            "**담당자** :\n"
            "**기획서** :"
        )

        response_data = {
            "text": response_message,
            "responseType": "inChannel"
        }

        logger.info("✅ Sending immediate response: %s", response_data)

        if response_url:
            try:
                res = requests.post(response_url, json=response_data)
                res.raise_for_status()
                logger.info("✅ Sent async response to Dooray: %s, Status: %s", response_url, res.status_code)
            except requests.exceptions.RequestException as e:
                logger.error("❌ Failed to send async response: %s", e)

        return jsonify(response_data), 200

    logger.warning("❌ Unknown command received: %s", command)
    return jsonify({"text": "Unknown command", "responseType": "ephemeral"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
