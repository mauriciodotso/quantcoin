FROM alpine:latest

#UPDATE
RUN apk add --update python-dev py-pip gcc g++ make libffi-dev openssl-dev

COPY . /usr/local/quantcoin

EXPOSE 65234
RUN pip install -r /usr/local/quantcoin/requirements.txt
CMD ["python", "/usr/local/quantcoin/quantcoin/client.py", "-p", "65234", "-s", "/root/wallet.qc", "-x", "/root/wallet.qc-priv"]
