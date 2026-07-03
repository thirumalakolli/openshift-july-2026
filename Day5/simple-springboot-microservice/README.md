# greeting-service

A minimal Spring Boot microservice built to run on Red Hat OpenShift. It exposes
two REST endpoints and the Actuator health endpoints that OpenShift uses for
liveness and readiness probes.

- `GET /` — basic status, returns the responding pod name
- `GET /greeting?name=Jegan` — returns a greeting plus a timestamp
- `GET /actuator/health/liveness` — liveness probe
- `GET /actuator/health/readiness` — readiness probe

Built on Spring Boot 4.1.0, Java 21. Group/package: `org.tektutor`.

## Run locally

```
./mvnw spring-boot:run
curl http://localhost:8080/greeting?name=Jegan
```

## Deploy to OpenShift

There are two common paths. Pick one.

### Option A — Source-to-Image (no Dockerfile, OpenShift builds for you)

`oc new-app` detects the Maven project, builds it with the Java S2I builder
image, and creates the Deployment, Service, and ImageStream automatically.

```
oc new-project demo
oc new-app java:21~https://github.com/<you>/greeting-service.git \
  --name=greeting-service
oc expose service/greeting-service        # creates a Route
oc get route greeting-service             # grab the URL
```

Then add the probes (S2I does not set them for you):

```
oc set probe deployment/greeting-service \
  --readiness --get-url=http://:8080/actuator/health/readiness \
  --initial-delay-seconds=10
oc set probe deployment/greeting-service \
  --liveness --get-url=http://:8080/actuator/health/liveness \
  --initial-delay-seconds=20
```

### Option B — Build the image yourself, then apply the manifests

Spring Boot can build an OCI image without a Dockerfile using buildpacks:

```
./mvnw spring-boot:build-image -Dspring-boot.build-image.imageName=greeting-service:latest
```

Push that image to the OpenShift internal registry (or any registry your
cluster can pull from), set the `image:` field in `k8s/greeting-service.yaml`
to match, then:

```
oc apply -f k8s/greeting-service.yaml
oc get route greeting-service
```

## Verify

```
URL=$(oc get route greeting-service -o jsonpath='{.spec.host}')
curl -k https://$URL/greeting?name=Jegan
```

Scale up and watch the `pod` field in the response change as the Route
load-balances across replicas:

```
oc scale deployment/greeting-service --replicas=3
```
