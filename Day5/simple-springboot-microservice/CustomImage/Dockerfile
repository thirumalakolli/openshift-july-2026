FROM alpine:latest

RUN apk update && apk add openjdk21

COPY app.jar .

CMD ["java", "-jar", "./app.jar"]
