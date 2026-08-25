import sys
import os

# Windows consoles commonly default to a legacy code page (e.g. cp1252) that
# can't encode the Unicode symbols (checkmarks, arrows, bullets) this CLI
# prints. Force UTF-8 on the standard streams so those never crash with
# UnicodeEncodeError. Must happen before any other module in this app prints
# or reads input.
for _stream in (sys.stdout, sys.stderr, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        # reconfigure() is Python 3.7+ and only works on real text streams;
        # silently skip if the stream doesn't support it (e.g. some test
        # harnesses replace sys.stdout with a plain io.StringIO).
        pass

from getpass import getpass
from dotenv import load_dotenv
import shutil

# Import your modules
import api_client
# from user_auth import UserAuth
from cli import CLI
from optimizer import PromptOptimizer
# from launcher import ChatLauncher
from storage import Storage
import weblauncher

# Path to the environment configuration file
ENV_PATH = ".env"

def setup_api_keys():
    """
    Check if any supported provider's API key exists in the environment.
    If not, ask the user which provider they want to use and save its key
    to the .env file.
    """
    # Force reload environment variables (in case they were just updated)
    load_dotenv(ENV_PATH, override=True)

    if api_client.available_providers():
        return

    print("\n" + "="*60)
    print("   First Time Setup   ")
    print("   No API keys detected. Please configure one now.")
    print("   (Keys will be securely saved to the local .env file)")
    print("="*60 + "\n")

    print("Which AI provider would you like to use to power PromptPrompt?")
    options = list(api_client.PROVIDER_ENV_KEYS.items())
    for i, (name, _) in enumerate(options, 1):
        print(f"  {i}. {api_client.PROVIDER_LABELS[name]}")
    print("\n(Groq is recommended: fast and free. Get a key at https://console.groq.com/keys)")

    choice = input(f"\nEnter your choice (1-{len(options)}) [1]: ").strip() or "1"
    while not choice.isdigit() or not (1 <= int(choice) <= len(options)):
        choice = input(f"Please enter a number between 1 and {len(options)}: ").strip()

    provider, env_var = options[int(choice) - 1]
    new_key = getpass(f"\n{api_client.PROVIDER_LABELS[provider]} key ({env_var}, input hidden): ").strip()

    if new_key:
        # Append to .env file
        with open(ENV_PATH, "a") as f:
            f.write(f"\n{env_var}={new_key}")
        print(f"✓ {env_var} saved.")
    load_dotenv(ENV_PATH, override=True)


def choose_provider(providers):
    """
    If more than one provider is configured, ask the user which one should
    power this session. Returns a single provider name from `providers`.
    """
    if len(providers) == 1:
        return providers[0]

    print("\nMultiple AI providers are configured. Which should power this session?")
    for i, name in enumerate(providers, 1):
        print(f"  {i}. {api_client.PROVIDER_LABELS[name]}")

    choice = input(f"\nEnter your choice (1-{len(providers)}) [1]: ").strip() or "1"
    while not choice.isdigit() or not (1 <= int(choice) <= len(providers)):
        choice = input(f"Please enter a number between 1 and {len(providers)}: ").strip()

    return providers[int(choice) - 1]

def main():
    print("\n" + "*"*50)
    print("   PROMPT PROMPT SYSTEM STARTUP   ")
    print("*"*50 + "\n")
    
    # --- STEP 0: Check & Ask for API Keys ---
    setup_api_keys()

    # --- STEP 1: Initialize API Connection ---
    print("[System] Initializing AI Models...")
    try:
        # Re-read the environment variables and see which provider(s) are configured
        providers = api_client.available_providers()
        if not providers:
            print("[Error] No valid API keys found.")
            print("Please check the .env file or delete it to re-run setup.")
            sys.exit(1)

        selected_provider = choose_provider(providers)
        api = api_client.get_connector(selected_provider)

        print(f"[System] AI Models Connected. Using: {api_client.PROVIDER_LABELS[selected_provider]}")
    except ImportError as e:
        print(f"[Critical Error] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[Critical Error] Failed to connect to AI models: {e}")
        sys.exit(1)

    # --- STEP 2: Initialize Business Logic (Optimizer) ---
    print("[System] Loading Optimizer Logic...")
    try:
        # Pass the initialized API client to the optimizer
        optimizer = PromptOptimizer(api_client=api)
        storage = Storage()
        # launcher = ChatLauncher()
        launcher = weblauncher.WebLauncher(use_claude_code=True)
    except Exception as e:
        print(f"[Error] Failed to initialize optimizer: {e}")
        # print("Hint: Ensure you have a 'prompts' folder with .txt files.")
        sys.exit(1)

    # --- STEP 3: Get Claude Code path ---
    claude_code_path = None
    if launcher.use_claude_code:
        # Load config to check for saved path
        config = storage.load_config()
        claude_code_path = config.get("claude_code_path")

        # If not in config, check if it's in PATH
        if not claude_code_path:
            if shutil.which("claude"):
                claude_code_path = "claude"
                # Save to config for future use
                config["claude_code_path"] = claude_code_path
                storage.save_config(config)
            # If not in PATH either, CLI will prompt user later

    # --- STEP 4: Launch the CLI (View) ---
    print("[System] Launching User Interface...\n")
    try:
        # Pass the optimizer to the CLI
        cli_app = CLI(optimizer=optimizer, storage=storage, launcher=launcher)

        # If Claude Code enabled but no path found, prompt user
        if launcher.use_claude_code and not claude_code_path:
            claude_code_path = cli_app.get_claude_code_path()
            if claude_code_path:
                # Save to config
                config = storage.load_config()
                config["claude_code_path"] = claude_code_path
                storage.save_config(config)

        cli_app.run(claude_code_path=claude_code_path)
    except KeyboardInterrupt:
        print("\n[System] Program interrupted by user.")
    except Exception as e:
        print(f"\n[Error] An unexpected error occurred in the CLI: {e}")

if __name__ == "__main__":
    main()