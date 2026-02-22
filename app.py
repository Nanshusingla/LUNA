import sys
import os
from dotenv import load_dotenv

# 1) Path fix (optional, but fine for iCloud folders)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2) Load .env FIRST (must be before importing services that read env vars)
load_dotenv()

from flask import Flask, render_template

# 3) Import Blueprints AFTER load_dotenv()
from routes.timer import timer_bp, start_timer_watcher_once
from routes.fake_call import fake_call_bp
from routes.help_poles import help_bp

app = Flask(__name__)

# 4) Register Blueprints ONCE
app.register_blueprint(timer_bp)
app.register_blueprint(fake_call_bp)
app.register_blueprint(help_bp)

# 5) Main page
@app.route("/")
def index():
    return render_template("index.html")

# 6) Run
if __name__ == "__main__":
    start_timer_watcher_once()  # start background timer watcher once
    app.run(debug=True, port=5003)