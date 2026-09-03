from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "<h1> Hello from my DevOps pipeline! </h1>"


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)