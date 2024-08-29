# VERIFIED ACTIONS THAT CAN TRIGGER A NOTIFICATION EVENT
ACTION_PUCHASE_POLICY = "purchase_policy"
""" Action to purchase a policy"""

ACTION_ACCEPT_POLICY = "accept_policy"
""" Action to accept a policy"""

ACTION_CANCEL_POLICY = "cancel_policy"
""" Action to cancel a policy"""

ACTION_STATUS_UPDATE = "status_update"
""" Action to update the status of a policy"""

ACTION_RENEW_POLICY = "renew_policy"
""" Action to renew a policy"""

ACTION_CLAIM_POLICY = "claim_policy"
""" Action to claim a policy"""

# MESSAGES AND SUBJECT BODIES FOR NOTIFICATION EVENTS
MESSAGE_CUSTOMER_PURCHASE_POLICY = "You have successfully purchased a policy"
MESSAGE_MERCHANT_PURCHASE_POLICY = "Policy purchase successful!"
""" Message for purchasing a policy"""

MESSAGE_CUSTOMER_ACCEPT_POLICY = "You have successfully accepted a policy"
""" Message for accepting a policy"""

MESSAGE_CUSTOMER_CANCEL_POLICY = "Your policy have been cancelled!"
MESSAGE_MERCHANT_CANCEL_POLICY = "Your customer's policy have been cancelled!"
""" Message for cancelling a policy"""

MESSAGE_CUSTOMER_STATUS_UPDATE = "The status of your policy has been updated"
MESSAGE_MERCHANT_STATUS_UPDATE = "The status of a customer's policy has been updated"
""" Message for updating the status of a policy"""

MESSAGE_CUSTOMER_RENEW_POLICY = "Policy renewal successful!"
MESSAGE_MERCHANT_RENEW_POLICY = "Policy renewal successful!"
""" Message for renewing a policy"""

MESSAGE_CUSTOMER_CLAIM_POLICY = "We've received your claim request"
MESSAGE_MERCHANT_CLAIM_POLICY = "We've received a claim request for a customer's policy"
""" Message for claiming a policy"""


ACTION_REGISTRY = {
    ACTION_PUCHASE_POLICY: {
        "customer": {
            "subject": MESSAGE_CUSTOMER_PURCHASE_POLICY,
            "body": "You have successfully purchased a policy",
        },
        "merchant": {
            "subject": MESSAGE_MERCHANT_PURCHASE_POLICY,
            "body": "A customer has just purchased a policy",
            "template": "superpool/emails/superpool-purchase-policy.html",
        },
    },
    ACTION_ACCEPT_POLICY: {
        "customer": {
            "subject": MESSAGE_CUSTOMER_ACCEPT_POLICY,
            "body": "You have successfully accepted a policy",
        },
        "merchant": {
            "subject": MESSAGE_CUSTOMER_ACCEPT_POLICY,
            "body": "A customer has just accepted a policy",
        },
    },
    ACTION_CANCEL_POLICY: {
        "customer": {
            "subject": MESSAGE_CUSTOMER_CANCEL_POLICY,
            "body": "Your policy have been cancelled!",
        },
        "merchant": {
            "subject": MESSAGE_MERCHANT_CANCEL_POLICY,
            "body": "A customer has just cancelled a policy",
            "template": "superpool/emails/superpool-cancel-policy.html",
        },
    },
    ACTION_STATUS_UPDATE: {
        "customer": {
            "subject": MESSAGE_CUSTOMER_STATUS_UPDATE,
            "body": "The status of your policy has been updated",
        },
        "merchant": {
            "subject": MESSAGE_MERCHANT_STATUS_UPDATE,
            "body": "The status of a customer's policy has been updated",
        },
    },
    ACTION_RENEW_POLICY: {
        "customer": {
            "subject": MESSAGE_CUSTOMER_RENEW_POLICY,
            "body": "Policy renewal successful!",
        },
        "merchant": {
            "subject": MESSAGE_MERCHANT_RENEW_POLICY,
            "body": "A customer has just renewed a policy",
            "template": "superpool/emails/superpool-renew-policy.html",
        },
    },
    ACTION_CLAIM_POLICY: {
        "customer": {
            "subject": MESSAGE_CUSTOMER_CLAIM_POLICY,
            "body": "We've received your claim request",
        },
        "merchant": {
            "subject": MESSAGE_MERCHANT_CLAIM_POLICY,
            "body": "A customer has just submitted a claim request",
            "template": "superpool/emails/superpool-submit-claim.html",
        },
    },
}
""" Registry of actions and their corresponding messages"""
