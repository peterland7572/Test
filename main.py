import requests
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    """Dooray에서 받은 명령을 처리하는 엔드포인트"""
    data = request.json
    logger.info("📥 Received Data: %s", data)
    tenant_domain = data.get("tenantDomain")
    channel_id = data.get("channelId")
    command = data.get("command", "").strip()
    cmd_token = data.get("cmdToken", "")
    trigger_id = data.get("triggerId", "")
    dooray_dialog_url = f"https://{tenant_domain}/messenger/api/channels/{channel_id}/dialogs"
    if command == "/일감":
        dialog_data = {
            "token": cmd_token,
            "triggerId": trigger_id,
            "callbackId": "work_task",
            "dialog": {
                "callbackId": "work_task",
                "title": "📌 새 업무 등록",
                "submitLabel": "등록",
                "elements": [
                    {"type": "text", "label": "제목", "name": "title", "optional": False},
                    {"type": "textarea", "label": "내용", "name": "content", "optional": False},
                    {"type": "text", "label": "기간", "name": "duration", "optional": False},
                    {"type": "text", "label": "기획서 (URL)", "name": "document", "optional": True}
                ]
            }
        }

        headers = {"token": cmd_token}
        response = requests.post(dooray_dialog_url, json=dialog_data, headers=headers)

        if response.status_code == 200:
            logger.info("✅ Dialog 생성 요청 성공")
            return jsonify({"responseType": "ephemeral", "text": "📢 업무 입력 창을 열었습니다."}), 200
        else:
            logger.error("❌ Dialog 생성 요청 실패: %s", response.text)
            return jsonify({"responseType": "ephemeral", "text": "⚠️ 업무 입력 창을 여는 데 실패했습니다."}), 500

    return jsonify({"text": "Unknown command", "responseType": "ephemeral"}), 400


@app.route("/interactive-webhook", methods=["POST"])
def interactive_webhook():
    """Dooray Interactive Message 요청을 처리하는 웹훅"""
    data = request.json
    logger.info("📥 Received Interactive Action: %s", data)

    # 필수 데이터 추출
    tenant_domain = data.get("tenant", {}).get("domain")  # 수정: tenant 객체에서 domain 가져오기
    channel_id = data.get("channel", {}).get("id")  # 수정: channel 객체에서 id 가져오기
    callback_id = data.get("callbackId")
    submission = data.get("submission", {})
    cmd_token = data.get("cmdToken", "")
    responseUrl = data.get("responseUrl", "")

    logger.info("🌐resresponseUrl URL: %s", resresponseUrl)

    # 로그 추가
    logger.debug("📌 Extracted tenantDomain: %s, channelId: %s", tenant_domain, channel_id)
    logger.debug("🔄 Extracted callbackId: %s", callback_id)

    # 필수 값 확인
    if not tenant_domain or not channel_id:
        logger.error("❌ tenantDomain 또는 channelId 누락")
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 잘못된 요청입니다. (tenantDomain 또는 channelId 없음)"}), 400

    # Dooray API URL 구성
    dooray_dialog_url = f"https://{tenant_domain}/messenger/api/channels/{channel_id}/dialogs"
    logger.info("🌐 Dooray API URL: %s", dooray_dialog_url)

    # 업무 등록 처리
    if callback_id == "work_task":
        if not submission:
            logger.warning("⚠️ No submission data received: %s", submission)
            return jsonify({"responseType": "ephemeral", "text": "⚠️ 입력된 데이터가 없습니다."}), 400

        title = submission.get("title", "제목 없음")
        content = submission.get("content", "내용 없음")
        duration = submission.get("duration", "미정")
        document = submission.get("document", "없음")

        # 로그 추가
        logger.debug("📝 Parsed Submission Data - Title: %s, Content: %s, Duration: %s, Document: %s",
                     title, content, duration, document)

        response_data = {
            "responseType": "inChannel",
            "text": f"📌 **새 업무 요청이 등록되었습니다!**\n"
                    f"📍 **제목:** {title}\n"
                    f"📍 **내용:** {content}\n"
                    f"📍 **기간:** {duration}\n"
                    f"📍 **기획서:** {document if document != '없음' else '없음'}"
        }

        return jsonify({"responseType": "inChannel", "text": "✅ 메시지가 성공적으로 전송되었습니다!"}), 200

'''
        headers = {"token": cmd_token}
        response = requests.post(responseUrl, json=response_data, headers=headers)

        if response.status_code == 200:
            logger.info("✅ 메시지 전송 성공")
            return jsonify({"responseType": "inChannel", "text": "✅ 메시지가 성공적으로 전송되었습니다!"}), 200
        else:
            logger.error("❌ 메시지 전송 실패: %s", response.text)
            return jsonify({"responseType": "ephemeral", "text": "⚠️ 메시지 전송에 실패했습니다."}), 500
'''


        # logger.info("✅ 업무 요청이 정상적으로 등록되었습니다: %s", response_data)
        # return jsonify({"responseType": "inChannel", "text": response_data}), 200

    else:
        logger.warning("⚠️ 알 수 없는 callbackId: %s", callback_id)
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 처리할 수 없는 요청입니다."}), 400



if __name__ == "__main__":
    app.run(host="0.0.0.0")
