FROM python:3.10
WORKDIR /usr/app/
COPY . .
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python","/usr/app/litterbox.py"]