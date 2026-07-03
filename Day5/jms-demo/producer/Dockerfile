FROM registry.access.redhat.com/ubi8/openjdk-17 AS build

# Set workdir
RUN mkdir hello 
WORKDIR /home/jboss/hello

# Copy pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline

# Copy source and build
COPY src ./src
RUN mvn clean package -DskipTests

# ======================
# 2. Runtime Stage
# ======================
FROM registry.access.redhat.com/ubi8/openjdk-17-runtime

# Set non-root user for OpenShift compatibility
USER 1001

# Set working dir
WORKDIR /deployments

# Copy the built jar
COPY --from=build /home/jboss/hello/target/*.jar app.jar

# Expose Spring Boot default port
EXPOSE 8080

# Run app
ENTRYPOINT ["java", "-jar", "app.jar"]
