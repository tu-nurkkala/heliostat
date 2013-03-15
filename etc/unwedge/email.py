import smtplib
from email.mime.text import MIMEText

from_addr = 'tnurkkala@cse.taylor.edu'
to_addr = 'tom@nurknet.com'

msge = MIMEText('Test message')
msge['Subject'] = 'Hello from Python'
msge['From'] = from_addr
msge['To'] = to_addr

smtp = smtplib.SMTP('localhost')
smtp.sendmail(fro_addr, [to_addr], msge.as_string())
smtp.quit()
