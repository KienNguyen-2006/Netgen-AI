import json
import os

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from ai_generator import generate_rows
from data_handler import (
    allowed_file,
    append_rows,
    get_dataset_info,
    get_schema_prompt,
    load_dataset,
    paginate_df,
    save_upload,
    OUTPUT_FOLDER,
)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Invalid file type. Please upload a CSV file.", "error")
        return redirect(url_for("index"))

    filepath = save_upload(file)
    session["filepath"] = filepath
    session["filename"] = file.filename
    return redirect(url_for("dataset"))


@app.route("/dataset")
def dataset():
    filepath = session.get("filepath")
    if not filepath or not os.path.exists(filepath):
        flash("No dataset loaded. Please upload a CSV file first.", "error")
        return redirect(url_for("index"))

    df = load_dataset(filepath)
    info = get_dataset_info(df)
    page = request.args.get("page", 1, type=int)
    pagination = paginate_df(df, page)

    return render_template(
        "dataset.html",
        filename=session.get("filename"),
        info=info,
        pagination=pagination,
    )


@app.route("/generate", methods=["POST"])
def generate():
    filepath = session.get("filepath")
    if not filepath or not os.path.exists(filepath):
        flash("No dataset loaded. Please upload a CSV file first.", "error")
        return redirect(url_for("index"))

    try:
        num_rows = int(request.form.get("num_rows", 5))
        if num_rows < 1 or num_rows > 100:
            raise ValueError
    except (TypeError, ValueError):
        flash("Please enter a valid number of rows (1–100).", "error")
        return redirect(url_for("dataset"))

    df = load_dataset(filepath)
    schema_prompt = get_schema_prompt(df)

    try:
        generated = generate_rows(schema_prompt, num_rows)
    except RuntimeError as exc:
        flash(str(exc), "error")
        return redirect(url_for("dataset"))

    session["generated_rows"] = json.dumps(generated)

    info = get_dataset_info(df)
    return render_template(
        "preview.html",
        filename=session.get("filename"),
        columns=info["columns"],
        sample_rows=info["sample"],
        generated_rows=generated,
    )


@app.route("/confirm", methods=["POST"])
def confirm():
    filepath = session.get("filepath")
    generated_json = session.get("generated_rows")

    if not filepath or not generated_json:
        flash("Session expired. Please start over.", "error")
        return redirect(url_for("index"))

    generated = json.loads(generated_json)
    output_path = append_rows(filepath, generated)

    session.pop("generated_rows", None)
    session["output_path"] = output_path

    output_filename = os.path.basename(output_path)
    flash(
        f"Successfully appended {len(generated)} rows! "
        f"Download your augmented dataset below.",
        "success",
    )
    return redirect(url_for("dataset", saved=output_filename))


@app.route("/discard", methods=["POST"])
def discard():
    session.pop("generated_rows", None)
    flash("Generated rows discarded.", "info")
    return redirect(url_for("dataset"))


@app.route("/download/<filename>")
def download(filename):
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(filepath):
        flash("File not found.", "error")
        return redirect(url_for("dataset"))
    return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
