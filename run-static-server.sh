source .env

if [ ! "$(docker ps -q -f name=et-static)" ]; then
  if [ "$(docker ps -aq -f status=exited -f name=et-static)" ]; then
    docker rm et-static # cleanup
  fi
  docker run -d \
    --name et-static \
    -p ${STATIC_PORT}:80 \
    -v $(pwd)/static-conf/static:/srv \
    -v $(pwd)/static-conf/nginx.conf:/etc/nginx/conf.d/default.conf \
    nginx:alpine
fi
