
def parse_line(line):
    """Parse a line from .env file"""
    line = line.strip()
    if not line or line.startswith('#'):
        return None, None
    
    key_value = line.split('=', 1)
    if len(key_value) != 2:
        return None, None
        
    key, value = key_value
    key = key.strip()
    value = value.strip().strip('"\'')  # Remove quotes if present
    return key, value

def load_dotenv(dotenv_path='.env'):
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open(dotenv_path, 'r') as f:
            for line in f:
                key, value = parse_line(line)
                if key:
                    env_vars[key] = value
    except OSError:
        print(f"Could not load {dotenv_path}")
    return env_vars

_env_vars = {}

def load_env():
    """Load environment variables once"""
    global _env_vars
    if not _env_vars:
        _env_vars = load_dotenv()

def getenv(key, default=None):
    """Get an environment variable"""
    load_env()
    return _env_vars.get(key, default)