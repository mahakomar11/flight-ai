# Flight AI

Chat bot generating recommendations of how to mitigate a jet lag because of a flight.

## Local run

To run bot locally in docker containers, the following command can be used:
```commandline
make dev-compose-up
```

Environments variables will be read from .env-dev file. To change file with environment variables, use:
```commandline
DEV_ENV_FILE=[YOUR FILE] make dev-compose-up
```

You will need OpenAI ApiKey, Telegram bot token and ApiKey for FlightInfoAPI (https://rapidapi.com/oag-oag-default/api/flight-info-api/).

## Deploy

The application can be deployed to Kubernetes cluster with following commands:
```commandline
make build-and-push
```
The command will build and push all necessary docker images. To deploy application to the cluster, first, create secret object with following variables:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: flightai-secret
  namespace: [YOUR NAMESPACE]
stringData:
  RABBITMQ_USER:
  RABBITMQ_PASS:
  ERLANG_COOKIE:
  POSTGRES_USER:
  POSTGRES_PASSWORD:
  POSTGRES_NAME:
  BOT_TOKEN:
  FLIGHT_API_KEY:
  OPEN_AI_KEY:

```
Command for this is
```commandline
kubectl apply -f secret.yml
```
Then helm chart can be installed:
```commandline
NAMESPACE=[YOUR NAMESPACE] make deploy
```

The application is ready!

To uninstall helm chart, use:
```commandline
make uninstall
```