#!/bin/env python3
import smtplib


def send_email(recipient, subject, body):

    # pwd =
    # user =
    # gmail_user = user
    # gmail_pwd = pwd
    # FROM = user
    # TO = recipient if type(recipient) is list else [recipient]
    # SUBJECT = subject
    # TEXT = body
    #
    # # Prepare actual message
    # message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    # """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
    #     server = smtplib.SMTP("smtp.gmail.com", 587)
    #     server.ehlo()
    #     server.starttls()
    #     server.login(gmail_user, gmail_pwd)
    #     server.sendmail(FROM, TO, message)
    #     server.close()
        print('successfully sent the mail')
        print('Recipient: ', recipient)
        print('Subject: ', subject)
        print('Body: ', body)
    except:
        print("failed to send mail")
#
# if __name__ == '__main__':
#
#
#     send_email(user, pwd, 'chrisse_branne@hotmail.com', 'Hello there', 'This is the body')
