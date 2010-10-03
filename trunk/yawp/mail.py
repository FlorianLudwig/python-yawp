import os
import smtplib
from email.mime.text import MIMEText

from genshi import template


TPL_PATH = os.path.join('tpl', 'emails')
TPL_LOADER = template.TemplateLoader(TPL_PATH, default_class=template.NewTextTemplate)
MAIL_FROM = None
MAIL_RELAY = 'localhost'


def send_mail(toaddrs, subject, body):
    """Send an email via smtp, all arguments must be utf-8 or unicode
       
       toaddrs is a list of receipients
    """
    if isinstance(body, unicode):
        body = body.encode('utf-8')
    if isinstance(subject, unicode):
        subject = subject.encode('utf-8')
    if isinstance(toaddrs, basestring):
        toaddrs = [toaddrs]
    msg = MIMEText(body, subject, 'utf-8')
    msg['From'] = MAIL_FROM
    msg['To'] = ','.join(toaddrs)
    msg['Subject'] = subject
    # The actual mail send
    s = smtplib.SMTP(MAIL_RELAY)
    s.sendmail(MAIL_FROM, toaddrs, msg.as_string(),
    s.quit()


# example using local sendmail:
#SENDMAIL = "/usr/sbin/sendmail" # sendmail location
#import os
#p = os.popen("%s -t -i" % SENDMAIL, "w")
#p.write("To: receiver@example.com\n")
#p.write("Subject: test\n")
#p.write("\n") # blank line separating headers from body
#p.write("Some text\n")
#p.write("some more text\n")
#sts = p.close()
#if sts != 0:
#    print "Sendmail exit status", sts
