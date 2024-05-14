from flask import Flask, render_template, session, request, redirect, url_for
from flask_bootstrap import Bootstrap5
import numpy as np
from PIL import Image
from collections import Counter
import math

# Also: pip install Pillows

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
DEFAULT_TITLE = "Image Colour Palette Generator"
DEFAULT_SUBTITLE = "Upload your image and we'll show you the top 10 most common colours in your image!"
UPLOAD_FAIL_TITLE = "Upload Failed"
UPLOAD_FAIL_SUBTITLE = ("Sorry, no image was uploaded or your image failed to upload. "
                        "Check if your file has a valid extension (.png, .jpg, .jpeg).")
UPLOAD_SUCCESS_TITLE = "Upload Successful!"
UPLOAD_SUCCESS_SUBTITLE = "Your image was uploaded successfully!"

app = Flask(__name__)
Bootstrap5(app)
app.secret_key = "Some secret key"


def allowed_file(filename):
    if "." in filename and filename.split(".")[-1].lower() in ALLOWED_EXTENSIONS:
        return True
    else:
        return False


# Applies the Euclidean Distance Function to see if colours are similar or not
def euclidean_distance(color1, color2):
    r_diff = color1[0] - color2[0]
    g_diff = color1[1] - color2[1]
    b_diff = color1[2] - color2[2]
    distance = math.sqrt(r_diff ** 2 + g_diff ** 2 + b_diff ** 2)
    return distance


# Colours above the threshold are judged to be different, below the threshold are judged as similar and filtered out
def filter_similar_colours(colours, threshold=40):
    filtered_colours = []
    for colour in colours:
        is_different = True
        for filtered_colour in filtered_colours:
            distance = euclidean_distance(colour, filtered_colour)

            if distance <= threshold:
                is_different = False
                break

        if is_different:
            filtered_colours.append(colour)
    return filtered_colours


@app.route("/")
def home():
    filtered_rgb_values = session.get('filtered_rgb_values', None)
    title = session.get('title', DEFAULT_TITLE)
    subtitle = session.get('subtitle', DEFAULT_SUBTITLE)
    session.pop('filtered_rgb_values', None)
    session.pop('title', None)
    session.pop('subtitle', None)
    return render_template("index.html", filtered_rgb_values=filtered_rgb_values, title=title, subtitle=subtitle)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if file and allowed_file(file.filename):
        img = Image.open(file)
        img_array = np.array(img)

        # Converts from height x width x channels format to number of pixels x channels format.
        # The 1st arg of -1 tells NumPy to automatically calculate the appropriate dimension size
        # and ensure that the total number of elements remains the same.
        pixels = img_array.reshape(-1, img_array.shape[-1])

        # Converts each row (each pixel) to a tuple (since numpy arrays are not hashable)
        pixel_tuples = [tuple(pixel) for pixel in pixels]
        counter = Counter(pixel_tuples)

        rgb_values = [colour[0] for colour in counter.most_common(10000)]
        # Converts from NumPy's uint8 to Python's int. This is to avoid "TypeError: Object of type uint8
        # is not JSON serializable" and integer overflow issues when using Euclidean dist formula:
        converted_rgb_values = [(int(rgb[0]), int(rgb[1]), int(rgb[2])) for rgb in rgb_values]
        filtered_rgb_values = filter_similar_colours(converted_rgb_values)[:10]

        session["filtered_rgb_values"] = filtered_rgb_values
        session["title"] = UPLOAD_SUCCESS_TITLE
        session["subtitle"] = UPLOAD_SUCCESS_SUBTITLE
    else:
        session["title"] = UPLOAD_FAIL_TITLE
        session["subtitle"] = UPLOAD_FAIL_SUBTITLE

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
