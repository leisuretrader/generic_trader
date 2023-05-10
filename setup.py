from setuptools import setup, find_packages

setup(
    name="generic_trader",
    version="0.1.0",
    description="A Python library to interact with TD Ameritrade, Yahoo Finance, and Robinhood APIs",
    author="Jason Wu",
    author_email="jwu8715@gmail.com",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "pytz",
        "tda-api",
        "yfinance",
        "robin-stocks",
        "selenium",
        "webdriver-manager",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
