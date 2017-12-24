FROM alpine:latest

#UPDATE
RUN apk add --update python py-pip

COPY . /usr/local/quantcoin

EXPOSE 65234
CMD ["pip", "install", "-r", "/usr/local/quantcoin/requirements.txt"]
CMD ["python", "/usr/local/quantcoin/quantcoin/client.py", "-p", "65234", "-s", "/root/wallet.qc", "-x", "/root/wallet.qc-priv"]
