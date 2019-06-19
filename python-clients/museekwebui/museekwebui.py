""" Web UI for MuSeek """

from flask import Flask, render_template, jsonify, request
from mudriver import MUDRIVER, MUWORKER

app = Flask(__name__)

@app.route("/")
def root():
    return render_template("index.html")

@app.route("/download", methods=["DELETE"])
def delete_download():
    if "rmfile" in request.form and request.form["rmfile"] == "true":
        MUDRIVER.remove_download(request.form["hash"])
    else:
        MUDRIVER.abort_download(request.form["hash"])
    return jsonify(success=True)

@app.route("/download", methods=["POST"])
def download():
    MUDRIVER.start_file_download(int(request.form["ticket"]),
                                 request.form["user"],
                                 int(request.form["index"]))
    return jsonify(success=True)

@app.route("/downloads")
def get_downloads():
    downloads = MUDRIVER.get_downloads()
    return jsonify(downloads)

@app.route("/upload", methods=["DELETE"])
def delete_upload():
    if "rmfile" in request.form and request.form["rmfile"] == "true":
        MUDRIVER.remove_upload(request.form["hash"])
    else:
        MUDRIVER.abort_upload(request.form["hash"])
    return jsonify(success=True)

@app.route("/uploads")
def get_uploads():
    uploads = MUDRIVER.get_uploads()
    return jsonify(uploads)

@app.route("/search", methods=["POST", "GET", "DELETE"])
def search():
    if request.method == "POST":
        MUDRIVER.start_search(request.form["query"])
    elif request.method == "DELETE":
        MUDRIVER.stop_search(int(request.form["ticket"]))
    elif request.method == "GET":
        ticket = int(request.args.get("ticket"))
        return jsonify(MUDRIVER.get_search_results_for_ticket(ticket))
    return jsonify(success=True)

@app.route("/searches")
def get_searches():
    return jsonify(MUDRIVER.get_searches())

@app.route("/users")
def get_users():
    return jsonify(MUDRIVER.get_users())

@app.route("/user")
def get_user():
    return jsonify(MUDRIVER.get_user(request.args.get("user")))

if __name__ == '__main__':
    MUWORKER.start()
    app.run(host="0.0.0.0", port=5000)
