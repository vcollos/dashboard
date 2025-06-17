#!/bin/bash
cd /home/collos/apps/dashboard
source venv/bin/activate
nohup streamlit run diagnostico_vps.py --server.port=8504 > dashboard.log 2>&1 &