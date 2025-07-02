docker stop relive_cruilla_0
docker start relive_cruilla_0
docker container exec relive_cruilla_0 /bin/bash -c "cd /home/app/ && python main.py"