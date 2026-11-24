import os

from huggingface_hub import HfApi

REPO = "SSC-JHT-STS/hindi-academic-terminology"
api = HfApi(token=os.environ["HF_TOKEN"])

for name in ["terms.jsonl", "sentences.jsonl"]:
    api.upload_file(
        path_or_fileobj=f"build/{name}",
        path_in_repo=name,
        repo_id=REPO,
        repo_type="dataset",
        commit_message="Update from GitHub Action",
    )
    print("uploaded", name)
