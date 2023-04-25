FROM python:3.8.10

RUN pip install Flask==2.2.2
RUN pip install requests==2.22.0
RUN pip install redis==4.5.1
RUN pip install matplotlib==3.7.1

COPY app.py /app.py
COPY helicopter_flight_path.json /helicopter_flight_path.json
COPY rover_drive_path.json /rover_drive_path.json

CMD ["python", "app.py"]

