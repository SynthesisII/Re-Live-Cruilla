trap 'docker stop relive_cruilla_0; exit' HUP INT TERM EXIT

docker stop relive_cruilla_0
docker start relive_cruilla_0
xdg-open http://127.0.0.1:7860/
docker container exec relive_cruilla_0 /bin/bash -c "cd /home/app/ && python main.py"