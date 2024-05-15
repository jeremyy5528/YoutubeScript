pip3 install -r requirements.txt
docker compose up
docker exec ollama ollama pull llama3:8b
docker exec ollama ollama pull ycchen/breeze-7b-instruct-v1_0