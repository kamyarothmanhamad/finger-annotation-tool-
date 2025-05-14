from setuptools import setup, find_packages

with open("simple_mask_annotator/requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="simple-mask-annotator",
    version="0.1.0",
    description="A simple mask annotation tool using smooth curves",
    author="Kamyar",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "simple-mask-annotator=simple_mask_annotator.__main__:main",
        ],
    },
    python_requires=">=3.7",
)
