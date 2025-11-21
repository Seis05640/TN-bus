# TN-bus Security & Code Quality Review

_Date: 2024-11-21_

## Scope & Methodology
- Reviewed all Python sources (`app.py`, `integ.py`, `scrap.py`, `scrap2.py`) plus repo configuration files, datasets, and dependency manifests.
- Looked for secret exposure, insecure network usage, unsafe deserialization, authentication/authorization gaps, input validation, and logging practices.
- Evaluated repository layout, coding style, duplication, dependency hygiene, and presence of automated tests/documentation.

## Security Findings
| Severity | Finding | Evidence & Impact | Recommendation |
| --- | --- | --- | --- |
| **High** | **Secrets committed to source control** | Real Google Maps and OpenWeather API keys were previously committed in `.env`. Although the file has now been removed and replaced with `.env.example`, those keys must be considered compromised and rotated everywhere they were used. | Rotate all exposed keys immediately, keep `.env` out of version control going forward, and inject secrets via environment variables/secret managers. |
| **High** | **Lack of secret management/validation in ingestion scripts** | `integ.py` loads Google Maps and Weatherstack keys at import time without validating presence or scopes, and `scrap.py`/`scrap2.py` hard-code query parameters. Combined with missing auth, compromised scripts could leak credentials via console output. | Centralize credential loading, validate configuration before executing API calls, and fail fast with clear errors. Avoid printing secrets in logs.
| **High** | **Insecure HTTP request to Weatherstack** | `integ.py` calls `http://api.weatherstack.com/...` (line 42) which transmits API keys and location data in plaintext, allowing MITM snooping or tampering. | Switch to `https://` endpoints (Weatherstack supports TLS) and enforce TLS verification. |
| **High** | **Unsafe model deserialization** | `app.py` loads `delay_predictor_model.pkl` via `joblib.load` at import time without verifying integrity. Pickle/joblib files are executable – a tampered model can execute arbitrary code on app startup. | Sign models (e.g., with SHA-256 hashes) or store them in a trusted artifact store. Validate hash before loading and avoid loading user-supplied artifacts. |
| **Medium** | **No authentication/authorization on the Streamlit app** | The app exposes prediction functionality and underlying model publicly. Depending on deployment, this can leak proprietary models or enable abuse (e.g., scraping). | If deployed beyond internal demo usage, gate access (OIDC/SAML, Streamlit Cloud auth) and enforce per-user quotas/logging. |
| **Medium** | **User-controlled strings sent directly to third-party APIs** | `integ.py` forwards values from CSV columns (`From`, `To`) directly to Google Maps and Weatherstack without validation/whitelisting. Malicious or malformed values could be used for SSRF-style probing through those services. | Normalize and validate all free-text inputs (length, charset, whitelist of known depots) before calling external APIs. |
| **Medium** | **Verbose console logging may leak PII/operational data** | `integ.py` prints route pairs and weather descriptions for every iteration, which, combined with real-time schedules, may expose sensitive operational info if logs are centralized. | Replace `print` statements with structured logging at appropriate log levels and scrub PII/location data if not necessary. |
| **Low** | **No network timeouts or retry limits** | `requests.get` in `integ.py`/`scrap2.py` has no timeout, allowing the process to hang indefinitely and potentially exhaust resources. | Use short timeouts (`requests.get(..., timeout=10)`) and defensive retry logic with exponential backoff. |
| **Low** | **Undocumented data retention** | Numerous CSV/Pickle artifacts (e.g., `SETCbustimings_1_0.csv`, `tamilvandi_bus_data.csv`) are stored in the repo, creating compliance risks if they contain user data. | Define retention policies, move data to secured storage, and keep only synthetic/sample data in version control. |

## Code Quality Observations
1. **Scripts instead of packages:** All functionality lives in top-level scripts with side effects executed on import. Refactor into reusable modules/functions to enable testing and reuse.
2. **Hard-coded constants:** Routes, dates, and selectors are hard-coded in scraping scripts, preventing reuse and encouraging code copies (`scrap.py` vs `scrap2.py`). Extract configuration to JSON/env vars and reuse helper utilities.
3. **Error handling:** Broad `except Exception` blocks (e.g., `app.py`, `scrap.py`) swallow specific errors and reduce observability. Catch specific exception types and surface meaningful messages.
4. **Type safety and validation:** No type hints or validation frameworks are used. Inputs from Streamlit widgets and CSV files should be validated (ranges, formats) before processing or persisting.
5. **Logging vs printing:** Scripts rely on `print` for instrumentation. Adopt Python’s `logging` module with structured logs and log levels.
6. **Resource management:** Selenium driver instances are not wrapped in context managers/`try/finally`; failures before `driver.quit()` will leak processes.
7. **Potential pandas pitfalls:** `df['Travel_Time_Min'] = None` stores `object` dtype instead of numeric, requiring downstream casting. Prefer `pd.NA`/`np.nan` and set `dtype` on creation.
8. **Lack of modular architecture:** Machine learning model loading, feature engineering, and inference logic are tightly coupled to the Streamlit UI. Introduce a library layer (e.g., `predictor.py`) that encapsulates model I/O and preprocessing.

## Dependencies & Maintenance
- `requirements.txt` only lists the Streamlit inference dependencies. The ingestion/scraping scripts require additional packages (`googlemaps`, `python-dotenv`, `requests`, `beautifulsoup4`, `selenium`, `undetected-chromedriver`, etc.) that are missing, making the environment non-reproducible.
- Current pinned versions have no widely publicized CVEs as of Nov 2024, but minor/patch updates exist (Streamlit ≥1.39.x, pandas ≥2.2.3, scikit-learn 1.5.x). Plan upgrades after running the model regression suite.
- No dependency auditing (`pip-audit`, `safety`) is configured. This should be automated in CI.
- Large binary artifacts (`delay_predictor_model.pkl`, CSVs) are tracked in Git, inflating the repo and making deployment harder. Consider storing them in object storage (S3/GCS) or using Git LFS.
- No lock file (e.g., `poetry.lock`, `pip-tools` output). Adopt a repeatable build tool.

## Testing & Documentation
- **Automated tests:** None present (no `tests/` folder, no CI steps). Add unit tests for preprocessing, integration tests for API ingestion, and regression tests for the ML model.
- **Data validation:** No schema checks (e.g., `pandera`, `pydantic`). This increases risk of silent data drift.
- **Documentation:** There is no README explaining setup, required environment variables, or how to retrain the model. Add onboarding documentation plus architecture diagrams for the data pipeline.

## Prioritized Action Plan
1. **Rotate and remove all committed secrets** immediately; add `.env.example` and leverage secret managers. *(High)*
2. **Enforce TLS and request timeouts** for all external API calls; add input validation before hitting third-party services. *(High)*
3. **Introduce safe model artifact handling** (signature/hash verification, controlled storage) before loading in `app.py`. *(High)*
4. **Modularize scripts and add logging/error-handling improvements** to make pipelines testable and observable. *(Medium)*
5. **Complete dependency manifest and add vulnerability auditing in CI.** *(Medium)*
6. **Add automated tests and documentation (README, architecture notes).** *(Medium/Low)*
7. **Refactor scraping and ingestion scripts** to accept parameters/config instead of hard-coded values, and manage browser lifecycles safely. *(Low)*

## Best Practice Recommendations
- Adopt a packaging/tooling standard (Poetry or pip-tools) to manage dependencies per module (app vs ingestion vs scraping).
- Use Pydantic or dataclasses for input schemas and conversions between UI/ML layers.
- Store models and encoders with metadata (version, checksum, training data commit) to make rollbacks/audits possible.
- Configure Streamlit secrets management or environment-based config, and add authentication middleware when deploying externally.
- Implement structured logging (JSON) and centralize logs with redaction policies.
- Add a linting/formatting toolchain (ruff/black/mypy) and enforce it through pre-commit hooks.
- Define a testing strategy: unit tests for feature engineering, integration tests for API clients (with vcrpy/mocking), and end-to-end smoke tests for the Streamlit UI (Playwright).
- Document data sources, retention policies, and privacy considerations to remain compliant with data-handling regulations.
