#!/usr/bin/env bash

rm -rf dist_reader
pip install --platform manylinux2014_x86_64 --implementation cp --only-binary=:all: -r requirements.txt -t dist_reader
pip install -I bs4 -t dist_writer
pip install -I atlassian-python-api -t dist_writer

#remove extraneous bits from installed packages
rm -r dist_reader/*.dist-info
cp llm.py loadInfo.py hackaton.json token.json dist_reader/
cd dist_reader && zip -r lambda.zip *