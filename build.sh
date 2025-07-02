docker build -t relive_cruilla .
docker run --gpus all -it --ipc host -v ${pwd}:/home/app/ -p 7860:7860 --name relive_cruilla_0 relive_cruilla bash