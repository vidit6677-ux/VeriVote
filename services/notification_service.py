import os

from twilio.rest import Client


def send_vote_confirmation_sms(
    phone,
    constituency,
    vote_reference
):
    """
    Send a Twilio trial SMS notification.

    For the Twilio trial account, we use the predefined
    Event Notifications template.

    The candidate name is never included.
    """

    # =====================================================
    # CHECK PHONE NUMBER
    # =====================================================

    if not phone:
        return {
            "success": False,
            "message": "No phone number registered for voter."
        }

    # =====================================================
    # GET TWILIO CONFIGURATION
    # =====================================================

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    # =====================================================
    # CHECK ACCOUNT SID
    # =====================================================

    if not account_sid:
        return {
            "success": False,
            "message": "TWILIO_ACCOUNT_SID is not configured."
        }

    # =====================================================
    # CHECK AUTH TOKEN
    # =====================================================

    if not auth_token:
        return {
            "success": False,
            "message": "TWILIO_AUTH_TOKEN is not configured."
        }

    # =====================================================
    # CHECK TWILIO PHONE NUMBER
    # =====================================================

    if not from_number:
        return {
            "success": False,
            "message": "TWILIO_PHONE_NUMBER is not configured."
        }

    # =====================================================
    # FORMAT PHONE NUMBER
    # =====================================================

    phone = str(phone).strip()

    if phone.startswith("0"):
        phone = "+91" + phone[1:]

    elif not phone.startswith("+"):
        phone = "+91" + phone

    # =====================================================
    # TWILIO TRIAL TEMPLATE
    # =====================================================
    #
    # Twilio trial accounts restrict custom SMS bodies.
    # Use the predefined Event Notifications template.
    #
    # =====================================================

    template_name = "sms_event_notifications"

    # =====================================================
    # SEND SMS
    # =====================================================

    try:

        client = Client(
            account_sid,
            auth_token
        )

        message = client.messages.create(
            body=template_name,
            from_=from_number,
            to=phone
        )

        return {
            "success": True,
            "message": "SMS sent successfully.",
            "message_sid": message.sid
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }