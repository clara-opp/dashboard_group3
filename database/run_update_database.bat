@echo off
cd /d "%~dp0"

if not exist logs mkdir logs

echo ======================================== >> logs\update_database.log
echo [%date% %time%] Starting database update >> logs\update_database.log
echo ======================================== >> logs\update_database.log

"C:\Users\lgoet\AppData\Local\Programs\Python\Python313\python.exe" -u update_database.py >> logs\update_database.log 2>&1

echo ======================================== >> logs\update_database.log
echo [%date% %time%] Update completed >> logs\update_database.log
echo ======================================== >> logs\update_database.log

exit
