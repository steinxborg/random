from DrissionPage import Chromium, ChromiumOptions
import time
import os
from xvfbwrapper import Xvfb

# Start virtual display
vdisplay = Xvfb(width=1920, height=1080)
vdisplay.start()

try:
    co = ChromiumOptions()
    co.auto_port()
    co.set_timeouts(base=1)

    # Change this to the path of the folder containing the extension
    EXTENSION_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "turnstilePatch"))
    
    # Check if extension exists
    if os.path.exists(EXTENSION_PATH):
        co.add_extension(EXTENSION_PATH)
        print(f"✓ Extension loaded from: {EXTENSION_PATH}")
    else:
        print(f"⚠ Warning: Extension not found at {EXTENSION_PATH}")

    # Headless configuration (uncomment if needed)
    """
    co.headless()
    
    from sys import platform
    if platform == "linux" or platform == "linux2":
        platformIdentifier = "X11; Linux x86_64"
    elif platform == "darwin":
        platformIdentifier = "Macintosh; Intel Mac OS X 10_15_7"
    elif platform == "win32":
        platformIdentifier = "Windows NT 10.0; Win64; x64"
    
    co.set_user_agent(f"Mozilla/5.0 ({platformIdentifier}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    """

    browser = Chromium(co)
    page = browser.get_tabs()[-1]
    
    print("Navigating to dlhd.dad...")
    page.get("https://dlhd.dad/")
    print("✓ Page loaded")

    def getTurnstileToken():
        print("\nAttempting to solve Turnstile challenge...")
        page.run_js("try { turnstile.reset() } catch(e) { }")

        turnstileResponse = None

        for i in range(0, 15):
            try:
                turnstileResponse = page.run_js("try { return turnstile.getResponse() } catch(e) { return null }")
                if turnstileResponse:
                    print(f"✓ Token obtained on attempt {i+1}")
                    return turnstileResponse
                
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

    # Main loop
    attempt = 1
    while True:
        try:
            print(f"\n{'='*50}")
            print(f"Token Request #{attempt}")
            print(f"{'='*50}")
            token = getTurnstileToken()
            print(f"\n✓ TOKEN: {token}\n")
            attempt += 1
            time.sleep(2)  # Wait before next attempt
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}")
            attempt += 1

finally:
    # Stop virtual display
    print("\nCleaning up...")
    vdisplay.stop()
    print("✓ Virtual display stopped")
