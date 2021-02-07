#./bin/gunicorn --bind 0.0.0.0:5000 --workers=1 --access-logfile access.log --error-logfile error.log app:app
#.start.sh
#source start.sh

cd
cd /home/ubuntu/Desktop/Manager
sudo ufw allow 5000
gunicorn --bind 0.0.0.0:5000 wsgi:app &
python3 autoscalar.py &

