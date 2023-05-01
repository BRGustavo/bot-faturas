FROM python:3
COPY . /API
WORKDIR /API
RUN pip install -r ./requirements.txt
RUN playwright install
CMD python ./main.py
