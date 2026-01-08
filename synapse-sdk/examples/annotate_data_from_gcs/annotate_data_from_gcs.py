import os

from google.cloud import storage as google_storage

from synapse_sdk import Synapse

BUCKET_NAME = "my-bucket"  # specify your bucket name here
GOOGLE_APPLICATION_CREDENTIALS = (
    "my-service-account-credentials.json"  # specify your GCS credentials
)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

google_client = google_storage.Client()
bucket = google_client.get_bucket(BUCKET_NAME)
tasks = []
for filename in bucket.list_blobs():
    tasks.append({"image": f"gs://{BUCKET_NAME}/{filename}"})


SYNAPSE_URL = os.getenv("SYNAPSE_URL", "http://localhost:8080")
API_KEY = os.getenv("SYNAPSE_API_KEY")

client = Synapse(base_url=SYNAPSE_URL, api_key=API_KEY)


project = client.projects.create(
    title="Image Annotation Project from SDK",
    label_config="""
    <View>
        <Image name="image" value="$image"/>
        <RectangleLabels name="objects" toName="image">
            <Choice value="Airplane"/>
            <Choice value="Car"/>
        </RectangleLabels>
    </View>
    """,
)


ls.import_storage.gcs.create(
    project=project.id,
    bucket=BUCKET_NAME,
    google_application_credentials=open(GOOGLE_APPLICATION_CREDENTIALS, "r").read(),
    use_blob_urls=True,
    presign=True,
    presign_ttl=15,
    title="GCS storage",
    regex_filter=".*",
)


# Importing via tasks list still works without storage
for t in tasks:
    ls.tasks.create(project=project.id, data=t)
