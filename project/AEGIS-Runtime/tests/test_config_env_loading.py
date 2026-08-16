import os
import subprocess
import sys
from pathlib import Path


def test_env_loads_regardless_of_working_directory():
    """
    Regression test for a real bug: config.py used to call
    load_dotenv() with no arguments, which only searches *upward*
    from the process's current working directory -- never downward
    into subfolders. Anyone running the app from the project root
    (one level above AEGIS-Runtime/, as required so the "apex" and
    "backend" packages both import correctly) would never have their
    GEMINI_API_KEY found, no matter how correctly it was set in
    AEGIS-Runtime/.env.

    This test runs a fresh Python subprocess with its working
    directory set to the project root (one level up from
    AEGIS-Runtime/) -- exactly the scenario that was broken -- and
    confirms the key set in AEGIS-Runtime/.env is actually picked up.
    """
    repo_root = Path(__file__).resolve().parent.parent  # AEGIS-Runtime/
    project_root = repo_root.parent  # one level up

    script = (
        "import sys; "
        f"sys.path.insert(0, r'{repo_root}'); "
        "from backend.config.config import get_gemini_client; "
        "import os; "
        "print('KEY_FOUND=' + str(bool(os.getenv('GEMINI_API_KEY'))))"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )

    assert "KEY_FOUND=True" in result.stdout, (
        f"Expected GEMINI_API_KEY to be found when run from the "
        f"project root, but it wasn't. stdout={result.stdout!r} "
        f"stderr={result.stderr!r}"
    )


if __name__ == "__main__":
    test_env_loads_regardless_of_working_directory()
    print("Config .env loading test passed!")
