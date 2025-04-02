import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    data = request.json
    logger.info("📥 Received Data: %s", data)

    command = data.get("command", "").strip()

    if command == "/일감":
        response_data = {
            "responseType": "ephemeral",
            "text": "📝 **새 업무 요청**",
            "attachments": [
                {
                    "title": "📝 업무 요청서",
                    "fields": [
                        {"title": "제목", "value": " ", "short": False},
                        {"title": "내용", "value": " ", "short": False},
                        {"title": "기간", "value": " ", "short": True},
                        {"title": "담당자", "value": " ", "short": True},
                        {"title": "기획서", "value": " ", "short": False}
                    ]
                },
                {
                    "callbackId": "task_request",
                    "actions": [
                        {
                            "name": "submit_task",
                            "type": "button",
                            "text": "Submit",
                            "value": "업무 요청",
                            "style": "primary"
                        },
                        {
                            "name": "cancel_task",
                            "type": "button",
                            "text": "Cancel",
                            "value": "cancel"
                        }
                    ]
                }
            ]
        }

        logger.info("✅ Sending interactive message: %s", response_data)
        return jsonify(response_data), 200

    elif data.get("callbackId") == "task_request":
        action_value = data.get("actionValue", "")
        action_text = data.get("actionText", "")

        if action_value == "업무 요청":
            response_data = {
                "responseType": "inChannel",
                "text": f"✅ **업무 요청이 제출되었습니다!**\n\n"
                        f"📌 *제목:* (사용자가 입력한 제목)\n"
                        f"📌 *내용:* (사용자가 입력한 내용)\n"
                        f"📌 *기간:* (사용자가 입력한 기간)\n"
                        f"📌 *담당자:* (사용자가 입력한 담당자)\n"
                        f"📌 *기획서:* (사용자가 입력한 기획서)"
            }

            logger.info("✅ 업무 요청이 정상적으로 처리되었습니다.")
            return jsonify(response_data), 200

        elif action_value == "cancel":
            return jsonify({"responseType": "ephemeral", "text": "❌ 업무 요청이 취소되었습니다."}), 200

    logger.warning("❌ Unknown command received: %s", command)
    return jsonify({"text": "Unknown command", "responseType": "ephemeral"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
