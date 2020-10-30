./stop.sh
sudo docker run -d --rm --name prevision -p 5000:5000 --env-file .env surrog/flask_of_mango