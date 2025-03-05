# Boiler GenAI

Description: This is a boilerplate for building genai applications.
You will find examples of how to build applications in the following folders:

- fintech
- foodtech
- proptech
- similarity
- retail

Some of the tools and libraries used are:

- Datagen (for generating data) link: https://datagen.shadai.ai
- LangSmith (for tracing)
- LangGraph (for building agents)
- LangChain (for building assistants)
- ChromaDB (for vector search)
- FastAPI (for the api)
- Streamlit (for the ui)
- AWS Bedrock (for the llm)
- Claude LLM (for the llm)

Run the following command to start the application:

```
docker compose up -d --build
```

To see logs, run:

```
docker compose logs -f -tail 100 container_name
```

To restart the application, run:

```
docker compose restart
```

To stop the application, run:

```
docker compose down
```

Database is in postgres service and can be accessed with the following credentials:

```
postgres://admin:123asd456@localhost:5432/testdb
```

Redis is in redis service and can be accessed with the following route:

```
redis://localhost:6379
```

This api runs on port 8080 and can be accessed with the following route:

```
http://localhost:8080/
```

This UI with streamlit runs on port 8081 and can be accessed with the following route:

```
http://localhost:8081/
```

To create a person, send a POST request to the following endpoint:

```
http://localhost:8080/create-person
```

with the following body:

```
{
  "email": "test@test.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

For amazon bedrock, the credentials are:

```
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=ID
AWS_SECRET_ACCESS_KEY=KEY
```
