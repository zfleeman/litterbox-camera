import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import time
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import os

# pull required information from the environment
email_user = os.getenv('EMAIL_USER')
email_pass = os.getenv('EMAIL_PASS')
img_url = os.getenv('IMG_URL')
cam_user = os.getenv('CAM_USER')
cam_pass = os.getenv('CAM_PASS')
from_email = os.getenv('FROM_EMAIL')
to_emails = os.getenv('TO_EMAILS').split(',')
smtp_server = os.getenv('SMTP_SERVER')

def litterbox_email(stamp):
    msg = MIMEMultipart()
    msg['Subject'] = f'New Litterbox Image - {stamp[:-11]}'
    msg['From'] = from_email

    with open(stamp + ".jpg", 'rb') as f:
        data = f.read()
    text = MIMEText("Motion detected at Litterbox Prime.")
    msg.attach(text)
    image = MIMEImage(data, name="litter.jpg")
    msg.attach(image)

    s = smtplib.SMTP(smtp_server, 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(email_user, email_pass)

    s.sendmail(msg['From'], to_emails, msg.as_string())
    s.quit()


def motion_detector():
  
  previous_frame = None
  
  while True:
    time.sleep(5)
    img = requests.get(img_url, auth=HTTPBasicAuth(cam_user, cam_pass)) # 

    # opencv2 samples ripped from
    # https://towardsdatascience.com/image-analysis-for-beginners-creating-a-motion-detector-with-opencv-4ca6faba4b42

    # 1. Load image; convert to RGB
    img_brg = np.array(Image.open(BytesIO(img.content)))
    img_rgb = cv2.cvtColor(src=img_brg, code=cv2.COLOR_BGR2RGB)

    # 2. Prepare image; grayscale and blur
    prepared_frame = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    prepared_frame = cv2.GaussianBlur(src=prepared_frame, ksize=(5,5), sigmaX=0)

    # 3. Set previous frame and continue if there is None
    if (previous_frame is None):
      # First frame; there is no previous one yet
      previous_frame = prepared_frame
      continue
    
    # calculate difference and update previous frame
    diff_frame = cv2.absdiff(src1=previous_frame, src2=prepared_frame)

    # 80 diff seemed to capture a "change event" - ZWF
    if diff_frame.max() > 80: 
      previous_frame = prepared_frame

      # 4. Dilute the image a bit to make differences more seeable; more suitable for contour detection
      kernel = np.ones((5, 5))
      diff_frame = cv2.dilate(diff_frame, kernel, 1)

      # 5. Only take different areas that are different enough (>20 / 255)
      thresh_frame = cv2.threshold(src=diff_frame, thresh=20, maxval=255, type=cv2.THRESH_BINARY)[1]

      contours, _ = cv2.findContours(image=thresh_frame, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
      for contour in contours:
        if cv2.contourArea(contour) < 50:
          # too small: skip!
          continue
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(img=img_rgb, pt1=(x, y), pt2=(x + w, y + h), color=(0, 255, 0), thickness=2)

      stamp = datetime.strftime(datetime.now(), "%A %B %d %I-%M-%S%p")

      # write image to disk for easier reading with MIMEImage
      cv2.imwrite(stamp + ".jpg", img_rgb)

      print(f'New Litterbox Image - {stamp}')

      litterbox_email(stamp)

if __name__ == "__main__":
  motion_detector()