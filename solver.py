from DrissionPage import Chromium, ChromiumOptions
import time
import os

co = ChromiumOptions()
co.auto_port()
co.set_timeouts(base=1)

# GitHub Actions compatibility flags
co.set_argument('--no-sandbox')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--disable-gpu')

# Change this to the path of the folder containing the extension
EXTENSION_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "turnstilePatch"))

# Check if extension exists
if os.path.exists(EXTENSION_PATH):
    co.add_extension(EXTENSION_PATH)
    print(f"✓ Extension loaded from: {EXTENSION_PATH}")
else:
    print(f"⚠ Warning: Extension not found at {EXTENSION_PATH}")

browser = Chromium(co)
page = browser.get_tabs()[-1]

print("Navigating to dlhd.dad...")
page.get("https://dlstreams.top/")
print("✓ Page loaded")

def getTurnstileToken():
    print("\nAttempting to solve Turnstile challenge...")
    page.run_js("try { turnstile.reset() } catch(e) { }")

    turnstileResponse = None

    for i in range(0, 15):
        turnstileResponse = page.run_js("try { return turnstile.getResponse() } catch(e) { return null }")
        if turnstileResponse:
            print(f"✓ Token obtained on attempt {i+1}")
            return turnstileResponse
        
        try:
            challengeSolution = page.ele("@name=cf-turnstile-response")
            challengeWrapper = challengeSolution.parent()
            challengeIframe = challengeWrapper.shadow_root.ele("tag:iframe")
            
            challengeIframe.run_js("""
window.dtp = 1
function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

let screenX = getRandomInt(800, 1200);
let screenY = getRandomInt(400, 600);

Object.defineProperty(MouseEvent.prototype, 'screenX', { value: screenX });
Object.defineProperty(MouseEvent.prototype, 'screenY', { value: screenY });
            """)
            
            challengeIframeBody = challengeIframe.ele("tag:body").shadow_root
            challengeButton = challengeIframeBody.ele("tag:input")
            challengeButton.click()
            print(f"  Attempt {i+1}/15 - Button clicked, waiting...")
        except Exception as e:
            print(f"  Attempt {i+1}/15 - Error: {str(e)[:50]}")
            pass
        time.sleep(1)
    
    print("⚠ Failed to solve after 15 attempts, refreshing page...")
    page.refresh()
    raise Exception("Failed to solve turnstile")

# Get one token and exit (for GitHub Actions)
try:
    print(f"\n{'='*50}")
    print(f"Token Request")
    print(f"{'='*50}")
    token = getTurnstileToken()
    print(f"\n✓ TOKEN: {token}\n")
    print("✓ Success!")
except Exception as e:
    print(f"\n✗ Error: {e}")
    exit(1)
