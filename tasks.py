from celery import Celery
from celery import shared_task
from llm_utils import call_llm
app = Celery('shared_task')
app.conf.broker_url = "redis://localhost:6379"
app.conf.result_backend = "redis://localhost:6379"


@shared_task
def generate_personalized_data(prompt):
    # Generate the data in background using LLM and Celery
    data = call_llm(prompt)
    print(data)