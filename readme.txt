py -3.12 -m venv --clear .venv
.venv\Scripts\activate.bat
py -3.12 -m pip install -U --upgrade-strategy eager -r requirements.txt
py 3.12 -m streamlit run streamlit_app.py