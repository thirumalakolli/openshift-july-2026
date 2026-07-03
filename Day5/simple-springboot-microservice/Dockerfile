# ---------- Stage 1: build the jar from source ----------
FROM registry.access.redhat.com/ubi9/openjdk-21:latest AS build
USER root
WORKDIR /build

# Copy the pom alone first and resolve dependencies, so this layer is
# cached and not redownloaded when only source code changes.
COPY pom.xml .
RUN mvn -B -ntp dependency:go-offline

# Now copy the source and build. Rename to a fixed name so the next
# stage does not depend on the version number in the jar.
COPY src ./src
RUN mvn -B -ntp clean package -DskipTests \
    && cp target/*.jar app.jar

# ---------- Stage 2: lean runtime image ----------
FROM registry.access.redhat.com/ubi9/openjdk-21-runtime:latest

# Carry over only the built jar. No JDK, no Maven, no source in the final image.
COPY --from=build /build/app.jar /deployments/app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/deployments/app.jar"]
