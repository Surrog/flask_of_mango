sudo docker stop prevision
sudo docker rm prevision
sudo docker run -it --rm --name prevision -p 5000:5000 --env-file .env surrog/flask_of_mango
