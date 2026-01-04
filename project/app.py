from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>Hello</h1>"

@app.route("/home")
def home():
    return "<h1>Home</h1>"

@app.route("/json")
def json():
    return {"mykey": "JSON Value!", "myList": [1,2,3,4,5]}

@app.route("/dynamic", defaults={"user_input": "default"})
@app.route("/dynamic/<user_input>")
def dynamic(user_input):
    return f"The user entered: {user_input}"

@app.route("/query")
def query():
    hello = request.args.get("hello")
    return f"The query string contains {hello}"

@app.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        return f"{user_input} POSTed"
    return "<form method='POST'><input type='text' name='user_input'><input type='submit'/></form>"