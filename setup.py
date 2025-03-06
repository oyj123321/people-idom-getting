from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="wxdecrypt",
    version="0.1.0",
    author="开发者",
    author_email="example@example.com",
    description="微信/QQ数据库自动识别与解密工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/wxdecrypt",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "wxdecrypt=wxdecrypt.main:main",
        ],
    },
) 