sudo docker stop discord_rss
sudo docker rm discord_rss
sudo docker run -it --rm --name prevision --env-file .env surrog/flask_of_mango
