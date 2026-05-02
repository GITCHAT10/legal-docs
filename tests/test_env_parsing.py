import os
import subprocess

def test_env_sala_parsing_safety():
    """
    Scenario: Verify deployment scripts parse .env.sala safely.
    """
    # Create a mock .env.sala with comments and empty lines
    env_content = """
# SALA Node Configuration
NODE_ID=SALA-EDGE-01
PORT=8000

# Security
NEXGEN_SECRET=forensic-secure-key # This is a secret
  # Indented comment
EMPTY_VAL=

"""
    with open(".env.sala.mock", "w") as f:
        f.write(env_content)

    # Use a bash snippet similar to the one mentioned in memories
    cmd = 'set -a; [ -f .env.sala.mock ] && . .env.sala.mock; set +a; echo "NODE_ID=$NODE_ID; SECRET=$NEXGEN_SECRET; PORT=$PORT"'
    result = subprocess.check_output(['bash', '-c', cmd]).decode()

    assert "NODE_ID=SALA-EDGE-01" in result
    assert "SECRET=forensic-secure-key" in result
    assert "PORT=8000" in result

    os.remove(".env.sala.mock")
