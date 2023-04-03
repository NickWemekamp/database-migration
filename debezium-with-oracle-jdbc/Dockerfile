ARG DEBEZIUM_VERSION
FROM quay.io/debezium/connect:2.2
ENV KAFKA_CONNECT_JDBC_DIR=$KAFKA_CONNECT_PLUGINS_DIR/kafka-connect-jdbc
ENV KAFKA_CONNECT_TRANSFORM_COMMON_DIR=$KAFKA_CONNECT_PLUGINS_DIR/kafka-connect-transform-commons

ARG POSTGRES_VERSION=42.4.1
ARG KAFKA_JDBC_VERSION=5.3.2

# These should point to the driver version to be used
ENV MAVEN_DEP_DESTINATION=$KAFKA_HOME/libs \
    ORACLE_JDBC_REPO="com/oracle/database/jdbc" \
    ORACLE_JDBC_GROUP="ojdbc8" \
    ORACLE_JDBC_VERSION="21.6.0.0" \
    ORACLE_JDBC_MD5=312e6f4ec9932bbf74a4461669970c4b

RUN docker-maven-download central "$ORACLE_JDBC_REPO" "$ORACLE_JDBC_GROUP" "$ORACLE_JDBC_VERSION" "$ORACLE_JDBC_MD5"

# Deploy PostgreSQL JDBC Driver
RUN cd /kafka/libs && curl -sO https://jdbc.postgresql.org/download/postgresql-$POSTGRES_VERSION.jar
# Deploy Kafka Connect JDBC
RUN mkdir $KAFKA_CONNECT_JDBC_DIR && cd $KAFKA_CONNECT_JDBC_DIR &&\
	curl -sO https://packages.confluent.io/maven/io/confluent/kafka-connect-jdbc/$KAFKA_JDBC_VERSION/kafka-connect-jdbc-$KAFKA_JDBC_VERSION.jar


RUN mkdir $KAFKA_CONNECT_TRANSFORM_COMMON_DIR && cd /tmp &&\
    curl -sO https://d1i4a15mxbxib1.cloudfront.net/api/plugins/jcustenborder/kafka-connect-transform-common/versions/0.1.0.58/jcustenborder-kafka-connect-transform-common-0.1.0.58.zip &&\
    unzip *.zip && mv /tmp/jcustenborder-kafka-connect-transform-common-0.1.0.58/lib/* $KAFKA_CONNECT_TRANSFORM_COMMON_DIR && rm *.zip && ls $KAFKA_CONNECT_TRANSFORM_COMMON_DIR \
    && cd $KAFKA_CONNECT_TRANSFORM_COMMON_DIR && curl -sO https://repo1.maven.org/maven2/com/google/guava/guava/31.1-jre/guava-31.1-jre.jar

USER kafka