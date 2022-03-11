# Qamuy-lite

Lightweight implementation of Qamuy

## How to install

```
poetry install
```

## How to run API server locally

```
poetry run uvicorn ql_worker.main:app --reload
```

## How to build a docker image

```
docker build -t ql-worker  --secret id=SSHKEYPLUS,src=$HOME/.ssh/id_rsa .
```

For M1 mac

It is needed `--platform linux/amd64` option.
```
docker build -t ql-worker  --secret id=SSHKEYPLUS,src=$HOME/.ssh/id_rsa --platform linux/amd64 .
```
## For developers

### Testing

```
./post_local.sh vqe <path_to_input_json>
./post.sh vqe <path_to_input_json>
```

### Deployment to GCP

```
gcloud builds submit --tag gcr.io/qamuy-lite/worker
gcloud run deploy ql-worker --image gcr.io/qamuy-lite/worker --platform managed --region=asia-northeast1 --port=8080
```
