import setuptools

with open("README.md", "r") as f:
    description = f.read()

setuptools.setup(
    name = "sqlite-integrated",
    version = "0.0.1",
    author = "Balder Holst",
    author_email = "balderwh@gmail.com",
    packages = ["sqlite_integrated"],
    description = "Easily manipulate sqlite databases with dictionaries",
    long_description = description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/BalderHolst/sqlite-integrated",
    license = "MIT",
    python_requires = ">=3.7",
    install_requires = []
    )
