# DFY Sparks DLAR Dashboard

This is a Streamlit dashboard that only shows DLAR data for the **DFY Sparks** entity.

## Files

- `app.py` - main Streamlit app
- `requirements.txt` - Python dependencies
- `.streamlit/secrets.toml` - optional local secrets file example

## Google Sheet Source

The app is currently connected to:

```text
https://docs.google.com/spreadsheets/d/1p4oZCjqQuAW8fv0kLZ1lU2NtMQaMi6K7Z0gzZUPt1Iw/export?format=csv&gid=0
```

Make sure the Google Sheet sharing permission is:

```text
Anyone with the link → Viewer
```

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Create a new GitHub repository.
2. Upload these files.
3. Go to Streamlit Cloud.
4. Select the GitHub repository.
5. Main file path should be:

```text
app.py
```

6. Deploy.

## Optional Streamlit Secrets

If you want to use Streamlit secrets instead of hardcoding the Google Sheet URL, add this:

```toml
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1p4oZCjqQuAW8fv0kLZ1lU2NtMQaMi6K7Z0gzZUPt1Iw/export?format=csv&gid=0"
```
