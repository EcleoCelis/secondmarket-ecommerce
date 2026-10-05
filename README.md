# SecondMarket E-Commerce Foundation

SecondMarket is a simple secondhand e-commerce concept with two primary roles:

- Buyer
- Admin as seller

This repository currently contains the foundation, database/domain models, and authentication/RBAC modules. The Flask backend lives in `backend/`, while frontend HTML/CSS/JavaScript lives in `frontend/`.

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Then open:

- Storefront: `http://127.0.0.1:5000/`
- Login: `http://127.0.0.1:5000/login.html`
- Register: `http://127.0.0.1:5000/register.html`
- API health: `http://127.0.0.1:5000/api/v1/health`
- API metadata: `http://127.0.0.1:5000/api/v1/system/info`

## Test

```powershell
pytest
```

## Module Roadmap

The development sequence is documented in `backend/docs/modules/modules.md`.
