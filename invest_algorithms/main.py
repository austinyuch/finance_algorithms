# Run locally:   uv run uvicorn api:app --reload
# Run in cloud:  API_HOST=0.0.0.0 uv run python main.py
# Swagger/docs:  http://127.0.0.1:2224/docs

import sys
import traceback

import uvicorn

import confs as cfg

if __name__ == "__main__":
    try:
        uvicorn.run(
            app="api:app",
            host=cfg.dic_api["host"],
            port=cfg.dic_api["port"],
            workers=cfg.dic_api["workers"],
            log_level=cfg.dic_api["log_level"],
            reload=cfg.dic_api["reload"],
        )
    except KeyboardInterrupt:
        print("\nExiting\n")
    except Exception:
        print("Failed to Start API")
        traceback.print_exc(file=sys.stdout)
        print("Exiting\n")
