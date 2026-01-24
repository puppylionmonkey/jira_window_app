pyinstaller --noconfirm --onedir --windowed --name "Jira下載器" --collect-all flet --collect-all playwright --add-data ".venv\Lib\site-packages\ywright\driver;playwright\driver" main.py   
