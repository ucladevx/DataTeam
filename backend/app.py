from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    pass

app.run(port=7000)

