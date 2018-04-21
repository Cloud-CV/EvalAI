def mail_body(host):
    body = {
        "passreset": "You're receiving this mail because your password has been reset at " + host
                     + "\nThanks for using our site!\n The " + host + " team",
    }
    return body


def mail_subject(host):
    subject = {
        "passreset": 'Password reset on ' + host,
    }
    return subject
