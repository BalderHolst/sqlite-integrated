import setuptools

with open("README.md", "r") as f:
    description = f.read()

setuptools.setup(
    name = "sqlite-integrated",
    version = "0.0.4",
    author = "Balder Holst",
    author_email = "balderwh@gmail.com",
    packages = ["sqlite_integrated"],
    description = "Easily manipulate sqlite3 databases with simple syntax",
    long_description = description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/BalderHolst/sqlite-integrated",
    license = "MIT",
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Database",
        ],
    package_dir={'': 'src'},
    python_requires = ">=3.7",
    install_requires = [
        "pandas>=1.3.5",
        ],
    extras_require={
            'dev': [
                'pytest'
            ]
        }
    )
