#!/bin/bash

python /dependency-report.py /repo/pool/packages/

cp data_* /aditya-home/data-files/

python /dependency-report.py /repo/pool/community/

cp data_* /aditya-home/data-files/
