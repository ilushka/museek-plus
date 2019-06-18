from flask import Flask, g, render_template, jsonify, request
from kvring import KeyValueRing
from mudriver import mudriver, muworker

app = Flask(__name__)

@app.route("/")
def root():
  return render_template("index.html")

@app.route("/download", methods=["DELETE"])
def delete_download():
  if "rmfile" in request.form and request.form["rmfile"] == "true":
    mudriver.remove_download(request.form["hash"])
  else:
    mudriver.abort_download(request.form["hash"])
  return jsonify(success=True)

@app.route("/download", methods=["POST"])
def download():
  mudriver.start_file_download(int(request.form["ticket"]), request.form["user"], int(request.form["index"]))
  return jsonify(success=True)

@app.route("/downloads")
def get_downloads():
  downloads = mudriver.get_downloads()
  return jsonify(downloads)

@app.route("/upload", methods=["DELETE"])
def delete_upload():
  if "rmfile" in request.form and request.form["rmfile"] == "true":
    mudriver.remove_upload(request.form["hash"])
  else:
    mudriver.abort_upload(request.form["hash"])
  return jsonify(success=True)

@app.route("/uploads")
def get_uploads():
  uploads = mudriver.get_uploads()
  return jsonify(uploads)

@app.route("/search", methods=["POST", "GET", "DELETE"])
def search():
  if request.method == "POST":
    mudriver.start_search(request.form["query"])
  elif request.method == "DELETE":
    mudriver.stop_search(int(request.form["ticket"]))
  elif request.method == "GET":
    return jsonify(mudriver.get_sresults_for_ticket(int(request.args.get("ticket"))))
  return jsonify(success=True)

@app.route("/searches")
def get_searches():
  return jsonify(mudriver.get_searches())

@app.route("/users")
def get_users():
  return jsonify(mudriver.get_users())

@app.route("/user")
def get_user():
  return jsonify(mudriver.get_user(request.args.get("user")))

if __name__ == '__main__':
  muworker.start()
  app.run(host="0.0.0.0", port=5000)

