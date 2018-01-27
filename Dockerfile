FROM alpine:latest

# Installing dependencies
RUN apk add --update python-dev py-pip gcc g++ make libffi-dev openssl-dev

# Copying the code
COPY . /usr/local/quantcoin

# Installing more dependencies
RUN pip install -r /usr/local/quantcoin/requirements.txt

# Exposing directory were wallet will be stored
VOLUME /root

EXPOSE 65234
ENTRYPOINT ["python", "/usr/local/quantcoin/quantcoin/client.py", "-p", "65234", "-s", "/root/wallet.qc", "-x", "/root/wallet.qc-priv"]
