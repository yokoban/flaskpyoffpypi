import json
import re

import requests
from flask import Flask, Response, jsonify, make_response, request, render_template

app = Flask(__name__)


PYPI_PACKAGE_JSON_URL = "https://pypi.org/pypi/"
PYPI_PROJECT_URL = "https://pypi.org/project/"
PYPI_PACKAGE_LIST = "https://pypi.org/simple/"


def prepare_response(data):
    response = flask.make_response(data)
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


def parse_package(target):
    pattern = re.compile("([a-zA-Z0-9_\-]+)(?:\s+|)(?:(\([^\)]+\)|))")

    if target.find("extra") > 0:
        return "", ""

    res = re.findall(pattern, target)[0]

    return res[0], res[1]


def get_requires_dist(target):
    url = f"{PYPI_PACKAGE_JSON_URL}{target}/json"
    res = requests.get(url)
    requires = json.loads(res.text)["info"]["requires_dist"]

    return requires


def get_require_packages(target, requires={}):
    if target == "":
        return

    packages = get_requires_dist(target)

    if packages is not None:
        for package in packages:
            name, ver = parse_package(package)
            if name != "" and name not in requires:
                print(name)
                get_require_packages(name, requires)

                requires[name] = {
                    "name": name,
                    "ver": ver,
                    "link": f"{PYPI_PROJECT_URL}{name}",
                }

    return requires


def get_pypi_all_package_list():
    response = requests.get(PYPI_PACKAGE_LIST)
    pattern = re.compile("<a.*?>(.*?)</a>")
    packages_list = re.findall(pattern, response.text)
    return packages_list


def max_length(target):
    max_len = -1
    for row in target:
        if max_len < len(row):
            max_len = len(row)

    return max_len


def htmlspecialchars(data):
    result = data
    result = result.replace("&", "")
    result = result.replace('"', "")
    result = result.replace("'", "")
    result = result.replace("<", "")
    result = result.replace(">", "")

    return result


@app.route("/<name>")
def off_pypi(name):
    if re.search(r"robots.txt", name):
        return "", 200

    pypi_provide_list = get_pypi_all_package_list()

    if name not in pypi_provide_list:
        print("not in")
        response = make_response(
            f"{htmlspecialchars(name)} is a package not provided by pypi"
        )
        return response, 400

    requires = get_require_packages(name)

    return render_template(
        "index.html", packages=[row for row in requires.values()], name=name
    )


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 80

    app.debug = False
    app.run(host=host, port=port)
