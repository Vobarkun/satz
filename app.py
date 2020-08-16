from flask import Flask
import satz

app = Flask(__name__)
app.debug = True

@app.route('/')
def top():
    s = satz.satz()
    return "<h1>" + s + "<h1>"

@app.route('/<word>')
def f(word = ""):
    s = satz.satz(word)
    return "<h1>" + s + "<h1>"