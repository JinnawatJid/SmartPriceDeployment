"""
RPA Script: Create Sales Quote in D365 BC
1. Click +New button
2. Click Review or update the value for No.
3. Select the matching quote series based on input code
4. Fill Customer No. and press Enter
5. Fill Sales Admin and press Enter
6. Fill External Document No. (our quote number)
7. Fill Your Reference
8. Add Item (Item No.)
9. Press Tab 5 times and fill Description
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import sys
import json
import os

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_rpa_data():
    """
    Load RPA data from JSON file if exists, otherwise return None
    """
    temp_file = "rpa_temp_data.json"
    if os.path.exists(temp_file):
        try:
            with open(temp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                print("[OK] Loaded data from rpa_temp_data.json")
                return data
        except Exception as e:
            print(f"[WARNING] Failed to load JSON data: {e}")
            return None
    return None

def convert_quote_code(input_code):
    """
    Convert quote code from format like 'TRQT' to 'TRSQ-QT'
    Rules: Take first 2 chars + 'SQ-' + last 2 chars
    """
    if len(input_code) < 4:
        print(f"[WARNING]  Warning: Input code '{input_code}' is too short. Using as-is.")
        return input_code
    
    first_two = input_code[:2]
    last_two = input_code[-2:]
    converted = f"{first_two}SQ-{last_two}"
    
    print(f"[INFO] Converting: {input_code} → {converted}")
    return converted

def create_sales_quote(quote_code, rpa_data=None):
    """
    Automate creating a sales quote with specific series code
    """
    print("[START] Starting RPA script for Sales Quote creation...")
    print(f"[INFO] Quote code: {quote_code}")
    
    # Convert the quote code
    target_series = convert_quote_code(quote_code)
    
    # Chrome options to connect to existing browser
    chrome_options = Options()
    chrome_options.debugger_address = "127.0.0.1:9222"
    
    try:
        print("🔌 Connecting to existing Chrome browser...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Get all window handles (tabs)
        windows = driver.window_handles
        print(f"[OK] Found {len(windows)} open tabs")
        
        # Search for D365 BC Sales Quotes tab
        target_window = None
        for window in windows:
            driver.switch_to.window(window)
            current_url = driver.current_url
            current_title = driver.title
            
            print(f"📄 Checking tab: {current_title[:50]}...")
            
            if 'businesscentral' in current_url.lower() and 'sales' in current_url.lower():
                target_window = window
                print(f"[OK] Found Sales Quotes tab: {current_title}")
                break
            elif 'Sales Quotes' in current_title or 'ใบเสนอราคาขาย' in current_title:
                target_window = window
                print(f"[OK] Found Sales Quotes tab: {current_title}")
                break
        
        if not target_window:
            print("[WARNING]  Could not find Sales Quotes tab automatically")
            print("   Using current active tab instead...")
            target_window = driver.current_window_handle
        
        driver.switch_to.window(target_window)
        print(f"[LOCATION] Current page: {driver.current_url}")
        time.sleep(1)
        
        # STEP 1: Click +New button
        print("\n" + "="*60)
        print("STEP 1: Clicking +New button")
        print("="*60)
        
        js_click_new = """
        function ClickNewButton() {
            var button = document.querySelector('button[aria-label="New"]');
            if (button) {
                button.click();
                return 'Clicked New button in main document';
            }
            
            var iframes = document.querySelectorAll('iframe');
            for (var i = 0; i < iframes.length; i++) {
                try {
                    var iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                    button = iframeDoc.querySelector('button[aria-label="New"]');
                    if (button) {
                        button.click();
                        return 'Clicked New button in iframe ' + i;
                    }
                } catch (e) {}
            }
            throw new Error('New button not found');
        }
        return ClickNewButton();
        """
        
        try:
            result = driver.execute_script(js_click_new)
            print(f"[OK] {result}")
        except Exception as e:
            print(f"[ERROR] Failed to click New button: {str(e)}")
            return
        
        time.sleep(2)
        
        # STEP 2: Click Review button
        print("\n" + "="*60)
        print("STEP 2: Clicking 'Review or update the value for No.' button")
        print("="*60)
        
        js_click_review = """
        function ClickReviewButton() {
            var button = document.querySelector('a[aria-label="Review or update the value for No."]');
            if (button) {
                button.click();
                return 'Clicked Review button in main document';
            }
            
            button = document.querySelector('a.ms-nav-assisteditbutton-embedded');
            if (button) {
                button.click();
                return 'Clicked Review button (by class) in main document';
            }
            
            var iframes = document.querySelectorAll('iframe');
            for (var i = 0; i < iframes.length; i++) {
                try {
                    var iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                    button = iframeDoc.querySelector('a[aria-label="Review or update the value for No."]');
                    if (button) {
                        button.click();
                        return 'Clicked Review button in iframe ' + i;
                    }
                    button = iframeDoc.querySelector('a.ms-nav-assisteditbutton-embedded');
                    if (button) {
                        button.click();
                        return 'Clicked Review button (by class) in iframe ' + i;
                    }
                } catch (e) {}
            }
            throw new Error('Review button not found');
        }
        return ClickReviewButton();
        """
        
        try:
            result = driver.execute_script(js_click_review)
            print(f"[OK] {result}")
        except Exception as e:
            print(f"[ERROR] Failed to click Review button: {str(e)}")
            return
        
        time.sleep(2)
        
        # STEP 3: Find and click the matching series
        print("\n" + "="*60)
        print(f"STEP 3: Finding and clicking series '{target_series}'")
        print("="*60)
        
        js_click_series = f"""
        function ClickSeries() {{
            var targetText = '{target_series}';
            
            // ลองหาใน main document
            var links = document.querySelectorAll('a.stringcontrol-read');
            for (var i = 0; i < links.length; i++) {{
                if (links[i].textContent.trim() === targetText) {{
                    links[i].click();
                    return 'Clicked series "' + targetText + '" in main document';
                }}
            }}
            
            // ลองหาทุก link ที่มี text ตรงกัน
            links = document.querySelectorAll('a');
            for (var i = 0; i < links.length; i++) {{
                if (links[i].textContent.trim() === targetText) {{
                    links[i].click();
                    return 'Clicked series "' + targetText + '" (generic link) in main document';
                }}
            }}
            
            // ลองหาใน iframe
            var iframes = document.querySelectorAll('iframe');
            for (var j = 0; j < iframes.length; j++) {{
                try {{
                    var iframeDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                    
                    links = iframeDoc.querySelectorAll('a.stringcontrol-read');
                    for (var i = 0; i < links.length; i++) {{
                        if (links[i].textContent.trim() === targetText) {{
                            links[i].click();
                            return 'Clicked series "' + targetText + '" in iframe ' + j;
                        }}
                    }}
                    
                    links = iframeDoc.querySelectorAll('a');
                    for (var i = 0; i < links.length; i++) {{
                        if (links[i].textContent.trim() === targetText) {{
                            links[i].click();
                            return 'Clicked series "' + targetText + '" (generic link) in iframe ' + j;
                        }}
                    }}
                }} catch (e) {{}}
            }}
            
            throw new Error('Series "' + targetText + '" not found');
        }}
        return ClickSeries();
        """
        
        try:
            result = driver.execute_script(js_click_series)
            print(f"[OK] {result}")
        except Exception as e:
            print(f"[ERROR] Failed to click series: {str(e)}")
            print(f"[TIP] Make sure the series '{target_series}' exists in the list")
            return
        
        time.sleep(2)
        
        # Get data from JSON or use defaults
        customer_no = rpa_data.get("customer_no", "00001AY") if rpa_data else "00001AY"
        sales_admin = rpa_data.get("sales_admin", "20614") if rpa_data else "20614"
        external_doc_no = rpa_data.get("external_doc_no", "TRQT-001/001") if rpa_data else "TRQT-001/001"
        your_reference = rpa_data.get("your_reference", "TRQT-2602/0010") if rpa_data else "TRQT-2602/0010"
        
        # STEP 4: Fill in Customer No.
        print("\n" + "="*60)
        print(f"STEP 4: Filling in Customer No.: {customer_no}")
        print("="*60)
        
        js_fill_customer = f"""
        function FillCustomerNo() {{
            var customerNo = '{customer_no}';
            
            // ลองหา input ด้วย id
            var input = document.querySelector('input#b2egee');
            if (input) {{
                input.value = customerNo;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                
                // กด Enter
                var enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true
                }});
                input.dispatchEvent(enterEvent);
                
                return 'Filled Customer No. and pressed Enter (by id) in main document';
            }}
            
            // ลองหาด้วย aria-labelledby
            input = document.querySelector('input[aria-labelledby="b2eglbl"]');
            if (input) {{
                input.value = customerNo;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                
                var enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true
                }});
                input.dispatchEvent(enterEvent);
                
                return 'Filled Customer No. and pressed Enter (by aria-labelledby) in main document';
            }}
            
            // ลองหาด้วย class และ role
            var inputs = document.querySelectorAll('input.stringcontrol-edit[role="combobox"]');
            for (var i = 0; i < inputs.length; i++) {{
                if (inputs[i].maxLength === 20) {{
                    inputs[i].value = customerNo;
                    inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    var enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true
                    }});
                    inputs[i].dispatchEvent(enterEvent);
                    
                    return 'Filled Customer No. and pressed Enter (by class) in main document';
                }}
            }}
            
            // ลองหาใน iframe
            var iframes = document.querySelectorAll('iframe');
            for (var j = 0; j < iframes.length; j++) {{
                try {{
                    var iframeDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                    
                    input = iframeDoc.querySelector('input#b2egee');
                    if (input) {{
                        input.value = customerNo;
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        var enterEvent = new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true
                        }});
                        input.dispatchEvent(enterEvent);
                        
                        return 'Filled Customer No. and pressed Enter (by id) in iframe ' + j;
                    }}
                    
                    input = iframeDoc.querySelector('input[aria-labelledby="b2eglbl"]');
                    if (input) {{
                        input.value = customerNo;
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        var enterEvent = new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true
                        }});
                        input.dispatchEvent(enterEvent);
                        
                        return 'Filled Customer No. and pressed Enter (by aria-labelledby) in iframe ' + j;
                    }}
                    
                    inputs = iframeDoc.querySelectorAll('input.stringcontrol-edit[role="combobox"]');
                    for (var i = 0; i < inputs.length; i++) {{
                        if (inputs[i].maxLength === 20) {{
                            inputs[i].value = customerNo;
                            inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                            inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                            
                            var enterEvent = new KeyboardEvent('keydown', {{
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            }});
                            inputs[i].dispatchEvent(enterEvent);
                            
                            return 'Filled Customer No. and pressed Enter (by class) in iframe ' + j;
                        }}
                    }}
                }} catch (e) {{}}
            }}
            
            throw new Error('Customer No. input field not found');
        }}
        return FillCustomerNo();
        """
        
        try:
            result = driver.execute_script(js_fill_customer)
            print(f"[OK] {result}")
        except Exception as e:
            print(f"[ERROR] Failed to fill Customer No.: {str(e)}")
            return
        
        # Wait for page to load after entering customer
        print("[WAIT] Waiting for page to load after customer selection...")
        time.sleep(5)  # เพิ่มจาก 3 เป็น 5 วินาที
        
        # STEP 5: Select Sales Admin from dropdown
        print("\n" + "="*60)
        print(f"STEP 5: Selecting Sales Admin: {sales_admin}")
        print("="*60)
        
        # Step 6.1: Type the sales admin code in the input field
        js_type_sales_admin = f"""
        function TypeSalesAdmin() {{
            var salesAdminCode = '{sales_admin}';
            console.log('=== Looking for Sales Admin input field ===');
            
            // ลองหาใน iframe ก่อน
            var iframes = document.querySelectorAll('iframe');
            console.log('Found ' + iframes.length + ' iframes');
            
            for (var j = 0; j < iframes.length; j++) {{
                try {{
                    var iframeDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                    
                    // ลองหาด้วย aria-labelledby ที่มี "Sales Admin" ในชื่อ
                    var inputs = iframeDoc.querySelectorAll('input[role="combobox"]');
                    console.log('Found ' + inputs.length + ' combobox inputs in iframe ' + j);
                    
                    for (var i = 0; i < inputs.length; i++) {{
                        var ariaLabelledBy = inputs[i].getAttribute('aria-labelledby') || '';
                        console.log('  Input ' + i + ': aria-labelledby="' + ariaLabelledBy + '"');
                        
                        // ตรวจสอบว่า label มีคำว่า Sales Admin หรือไม่
                        if (ariaLabelledBy) {{
                            var label = iframeDoc.getElementById(ariaLabelledBy);
                            if (label && (label.textContent.includes('Sales Admin') || label.textContent.includes('พนักงานขาย'))) {{
                                console.log('Found Sales Admin input field');
                                inputs[i].focus();
                                inputs[i].value = salesAdminCode;
                                inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                                inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return 'Typed Sales Admin code in iframe ' + j;
                            }}
                        }}
                    }}
                }} catch (e) {{
                    console.log('Error accessing iframe ' + j + ': ' + e.message);
                }}
            }}
            
            // ลองหาใน main document
            var inputs = document.querySelectorAll('input[role="combobox"]');
            console.log('Found ' + inputs.length + ' combobox inputs in main document');
            
            for (var i = 0; i < inputs.length; i++) {{
                var ariaLabelledBy = inputs[i].getAttribute('aria-labelledby') || '';
                if (ariaLabelledBy) {{
                    var label = document.getElementById(ariaLabelledBy);
                    if (label && (label.textContent.includes('Sales Admin') || label.textContent.includes('พนักงานขาย'))) {{
                        console.log('Found Sales Admin input field in main document');
                        inputs[i].focus();
                        inputs[i].value = salesAdminCode;
                        inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return 'Typed Sales Admin code in main document';
                    }}
                }}
            }}
            
            return 'Sales Admin input field not found';
        }}
        return TypeSalesAdmin();
        """
        
        try:
            result = driver.execute_script(js_type_sales_admin)
            print(f"[OK] {result}")
            if 'not found' in result:
                print("[WARNING]  Sales Admin input field not found - continuing anyway...")
                time.sleep(2)
            else:
                # Wait for dropdown to appear
                print("[WAIT] Waiting for dropdown to appear...")
                time.sleep(2)
                
                # Step 6.2: Click the matching record in dropdown
                js_select_from_dropdown = f"""
                function SelectFromDropdown() {{
                    var targetCode = '{sales_admin}';
                    console.log('=== Looking for Sales Admin record: ' + targetCode + ' ===');
                    
                    // ลองหาใน iframe
                    var iframes = document.querySelectorAll('iframe');
                    for (var j = 0; j < iframes.length; j++) {{
                        try {{
                            var iframeDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                            
                            // หา link ที่มี class stringcontrol-read และ text ตรงกับ targetCode
                            var links = iframeDoc.querySelectorAll('a.stringcontrol-read');
                            console.log('Iframe ' + j + ': Found ' + links.length + ' links');
                            
                            for (var i = 0; i < links.length; i++) {{
                                var text = links[i].textContent.trim();
                                if (i < 5) {{
                                    console.log('  Link ' + i + ': "' + text + '"');
                                }}
                                if (text === targetCode) {{
                                    console.log('Found matching record: ' + text);
                                    links[i].click();
                                    return 'Clicked Sales Admin record "' + targetCode + '" in iframe ' + j;
                                }}
                            }}
                        }} catch (e) {{
                            console.log('Error accessing iframe ' + j + ': ' + e.message);
                        }}
                    }}
                    
                    // ลองหาใน main document
                    var links = document.querySelectorAll('a.stringcontrol-read');
                    console.log('Main document: Found ' + links.length + ' links');
                    for (var i = 0; i < links.length; i++) {{
                        var text = links[i].textContent.trim();
                        if (text === targetCode) {{
                            console.log('Found matching record in main document: ' + text);
                            links[i].click();
                            return 'Clicked Sales Admin record "' + targetCode + '" in main document';
                        }}
                    }}
                    
                    return 'Sales Admin record "' + targetCode + '" not found in dropdown';
                }}
                return SelectFromDropdown();
                """
                
                result = driver.execute_script(js_select_from_dropdown)
                print(f"[OK] {result}")
                if 'not found' in result:
                    print("[WARNING]  Sales Admin record not found in dropdown - continuing anyway...")
        except Exception as e:
            print(f"[WARNING]  Could not select Sales Admin: {str(e)}")
            print("   Continuing anyway...")
        
        time.sleep(2)
        
        # STEP 6: Click "Show more" button in General section
        print("\n" + "="*60)
        print("STEP 6: Clicking 'Show more' button in General section")
        print("="*60)
        
        js_click_show_more = """
        function ClickShowMoreButton() {
            console.log('=== Looking for Show more button in General section ===');
            
            // ลองหาใน iframe ก่อน
            var iframes = document.querySelectorAll('iframe');
            console.log('Found ' + iframes.length + ' iframes');
            
            for (var j = 0; j < iframes.length; j++) {
                try {
                    var iframeDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                    
                    // หา span ที่มี class ms-nav-columns-caption และมี text "General"
                    var captions = iframeDoc.querySelectorAll('span.ms-nav-columns-caption');
                    console.log('Iframe ' + j + ': Found ' + captions.length + ' captions');
                    
                    for (var i = 0; i < captions.length; i++) {
                        var captionText = captions[i].querySelector('.caption-text');
                        if (captionText && captionText.textContent.trim() === 'General') {
                            console.log('Found General caption');
                            
                            // หา parent element ของ caption
                            var parent = captions[i].parentElement;
                            if (parent) {
                                // หาปุ่ม Show more ใน parent หรือ sibling elements
                                var showMoreBtn = parent.querySelector('button.show-more-fields-button');
                                if (showMoreBtn) {
                                    console.log('Found Show more button in General section');
                                    showMoreBtn.click();
                                    return 'Clicked Show more button in General section (iframe ' + j + ')';
                                }
                                
                                // ลองหาใน next sibling
                                var nextSibling = parent.nextElementSibling;
                                if (nextSibling) {
                                    showMoreBtn = nextSibling.querySelector('button.show-more-fields-button');
                                    if (showMoreBtn) {
                                        console.log('Found Show more button in next sibling');
                                        showMoreBtn.click();
                                        return 'Clicked Show more button in General section (iframe ' + j + ')';
                                    }
                                }
                            }
                        }
                    }
                    
                    // วิธีที่ 2: หาปุ่มที่มี aria-label="General, Show more"
                    var button = iframeDoc.querySelector('button[aria-label="General, Show more"]');
                    if (button) {
                        console.log('Found Show more button by aria-label');
                        button.click();
                        return 'Clicked Show more button (by aria-label) in iframe ' + j;
                    }
                } catch (e) {
                    console.log('Error accessing iframe ' + j + ': ' + e.message);
                }
            }
            
            // ลองหาใน main document
            console.log('Searching in main document...');
            
            var captions = document.querySelectorAll('span.ms-nav-columns-caption');
            console.log('Found ' + captions.length + ' captions in main document');
            
            for (var i = 0; i < captions.length; i++) {
                var captionText = captions[i].querySelector('.caption-text');
                if (captionText && captionText.textContent.trim() === 'General') {
                    console.log('Found General caption in main document');
                    
                    var parent = captions[i].parentElement;
                    if (parent) {
                        var showMoreBtn = parent.querySelector('button.show-more-fields-button');
                        if (showMoreBtn) {
                            console.log('Found Show more button in General section');
                            showMoreBtn.click();
                            return 'Clicked Show more button in General section (main document)';
                        }
                        
                        var nextSibling = parent.nextElementSibling;
                        if (nextSibling) {
                            showMoreBtn = nextSibling.querySelector('button.show-more-fields-button');
                            if (showMoreBtn) {
                                console.log('Found Show more button in next sibling');
                                showMoreBtn.click();
                                return 'Clicked Show more button in General section (main document)';
                            }
                        }
                    }
                }
            }
            
            // วิธีที่ 2
            var button = document.querySelector('button[aria-label="General, Show more"]');
            if (button) {
                console.log('Found Show more button by aria-label in main document');
                button.click();
                return 'Clicked Show more button (by aria-label) in main document';
            }
            
            throw new Error('Show more button in General section not found');
        }
        return ClickShowMoreButton();
        """
        
        try:
            result = driver.execute_script(js_click_show_more)
            print(f"[OK] {result}")
        except Exception as e:
            print(f"[ERROR] Failed to click Show more button: {str(e)}")
            return
        
        print("[WAIT] Waiting 2 seconds for fields to expand...")
        time.sleep(2)
        
        # STEP 6.5: Fill External Document No.
        print("\n" + "="*60)
        print(f"STEP 6.5: Filling External Document No.: {external_doc_no}")
        print("="*60)
        
        js_fill_external_doc = f"""
        function FillExternalDoc() {{
            var value = '{external_doc_no}';
            
            function tryFill(doc) {{
                // หา input ด้วย id="bs1ee" (External Document No.)
                var input = doc.querySelector('input#bs1ee');
                if (input) {{
                    input.focus();
                    input.value = value;
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
                return false;
            }}
            
            // ลองใน main document
            if (tryFill(document)) {{
                return "Filled External Document No. in main document";
            }}
            
            // ลองใน iframe
            var iframes = document.querySelectorAll('iframe');
            for (var i = 0; i < iframes.length; i++) {{
                try {{
                    var iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                    if (tryFill(iframeDoc)) {{
                        return "Filled External Document No. in iframe " + i;
                    }}
                }} catch (e) {{}}
            }}
            
            throw new Error("External Document No. field not found");
        }}
        return FillExternalDoc();
        """
        
        try:
            result = driver.execute_script(js_fill_external_doc)
            print(f"[OK] {result}")
        except Exception as e:
            print(f"[ERROR] Failed to fill External Document No.: {str(e)}")
            # Continue anyway, not critical
        
        time.sleep(2)
        
        # STEP 7: Fill in Your Reference
        print("\n" + "="*60)
        print(f"STEP 7: Filling Your Reference: {your_reference}")
        print("="*60)
        
        js_fill_your_reference = f"""
        function FillYourReference() {{
            var value = '{your_reference}';
            
            function tryFill(doc) {{
                // หา label ที่มี text = Your Reference
                var labels = doc.querySelectorAll('label, span, div');
                for (var i = 0; i < labels.length; i++) {{
                    var text = labels[i].textContent?.trim();
                    if (text === "Your Reference") {{
                        // หา input ที่อยู่ใกล้ label นี้
                        var parent = labels[i].closest('div');
                        if (!parent) continue;
                        
                        var input = parent.querySelector('input[type="text"]');
                        if (input) {{
                            input.focus();
                            input.value = value;
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                    }}
                }}
                return false;
            }}
            
            // 1️⃣ ลองใน main document
            if (tryFill(document)) {{
                return "Filled Your Reference in main document";
            }}
            
            // 2️⃣ ลองใน iframe
            var iframes = document.querySelectorAll("iframe");
            for (var i = 0; i < iframes.length; i++) {{
                try {{
                    var iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                    if (tryFill(iframeDoc)) {{
                        return "Filled Your Reference in iframe " + i;
                    }}
                }} catch (e) {{}}
            }}
            
            throw new Error("Your Reference field not found");
        }}
        return FillYourReference();
        """
        
        try:
            result = driver.execute_script(js_fill_your_reference)
            print(f"[OK] {result}")
        except Exception as e:
            print(f"[ERROR] Failed to fill Your Reference: {str(e)}")
            return
        
        time.sleep(2)
        
        # STEP 8-11: Add Items (Loop for multiple items)
        # Get items from JSON data or use default test items
        if rpa_data and "items" in rpa_data:
            items_to_add = rpa_data["items"]
            print("[OK] Using items from API data")
        else:
            # Default test items
            items_to_add = [
                {
                    "item_code": "A010010100101",
                    "description": "อลูมิเนียมเส้น Test Variant",
                    "quantity": "20",
                    "unit_price": "500"
                },
                {
                    "item_code": "G123456789012",
                    "description": "กระจกใส 5mm",
                    "quantity": "10",
                    "price_per_sqft": "24",
                    "price_per_sheet": "300"
                },
                {
                    "item_code": "A020020200202",
                    "description": "อลูมิเนียมแผ่น Test 2",
                    "quantity": "15",
                    "unit_price": "450"
                }
            ]
            print("[WARNING]  Using default test items")
        
        print("\n" + "="*60)
        print(f"STEP 8-11: Adding {len(items_to_add)} items")
        print("="*60)
        
        # Import ActionChains and Keys for real keyboard simulation
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys
        
        # JavaScript to switch to iframe
        js_switch_to_iframe = """
        function SwitchToFormIframe() {
            var iframes = document.querySelectorAll('iframe');
            for (var i = 0; i < iframes.length; i++) {
                try {
                    var iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                    var lookupBtn = iframeDoc.querySelector('a[aria-label="Choose a value for No."]');
                    if (lookupBtn) {
                        return i;
                    }
                } catch (e) {}
            }
            return -1;
        }
        return SwitchToFormIframe();
        """
        
        for item_index, item in enumerate(items_to_add, 1):
            print("\n" + "-"*60)
            print(f"Processing Item {item_index}/{len(items_to_add)}: {item['item_code']}")
            print("-"*60)
            
            item_code = item['item_code']
            description_text = item['description']
            quantity = item['quantity']
            is_glass_item = item_code.upper().startswith('G')
            
            # STEP 8: Add Item Code
            print(f"\n[Item {item_index}] Step 8: Adding Item Code: {item_code}")
            
            js_add_item = f"""
            function AddItem() {{
                var itemCode = '{item_code}';
                
                function tryAdd(doc) {{
                    // หา lookup ปุ่มของช่อง No.
                    var lookupBtn = doc.querySelector('a[aria-label="Choose a value for No."]');
                    if (!lookupBtn) return false;
                    
                    // หา input ที่ถูกควบคุมโดย aria-controls
                    var inputId = lookupBtn.getAttribute('aria-controls');
                    if (!inputId) return false;
                    
                    var input = doc.getElementById(inputId);
                    if (!input) return false;
                    
                    // focus
                    input.focus();
                    
                    // ใส่ค่า
                    input.value = itemCode;
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    return true;
                }}
                
                // 1️⃣ ลอง main document
                if (tryAdd(document)) {{
                    return "Item added in main document";
                }}
                
                // 2️⃣ ลอง iframe
                var iframes = document.querySelectorAll('iframe');
                for (var i = 0; i < iframes.length; i++) {{
                    try {{
                        var iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                        if (tryAdd(iframeDoc)) {{
                            return "Item added in iframe " + i;
                        }}
                    }} catch (e) {{}}
                }}
                
                throw new Error("Item No. field not found");
            }}
            return AddItem();
            """
            
            try:
                result = driver.execute_script(js_add_item)
                print(f"[OK] {result}")
            except Exception as e:
                print(f"[ERROR] Failed to add item: {str(e)}")
                continue
            
            # Wait 2 seconds after adding item
            print("[WAIT] Waiting 1 seconds after adding item...")
            time.sleep(1)
            
            # STEP 9: Fill Description
            print(f"\n[Item {item_index}] Step 9: Filling Description: {description_text}")
            
            try:
                # Switch to the iframe
                iframe_index = driver.execute_script(js_switch_to_iframe)
                if iframe_index >= 0:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    driver.switch_to.frame(iframes[iframe_index])
                
                # Create ActionChains object
                actions = ActionChains(driver)
                
                # สำหรับบรรทัดแรก: ต้องรอให้ระบบโหลด Description อัตโนมัติก่อน
                if item_index == 1:
                    print("[WAIT] First item - waiting 1 seconds for auto-description...")
                    time.sleep(2)
                
                # 1. กด Tab 1 ครั้ง
                print("[WAIT] Pressing Tab 1 time...")
                actions.send_keys(Keys.TAB).perform()
                time.sleep(1)
                
                # 2. กด Tab อีก 3 ครั้ง
                print("[WAIT] Pressing Tab 3 more times...")
                for i in range(3):
                    actions.send_keys(Keys.TAB).perform()
                    time.sleep(0.5)
                
                # 3. รอ 2 วินาที
                print("[WAIT] Waiting 1 seconds...")
                time.sleep(1)
                
                # 4. กด Ctrl+A, Delete, แล้วพิมพ์ Description
                print("[WAIT] Selecting all text (Ctrl+A)...")
                actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                time.sleep(0.5)
                
                print("[WAIT] Deleting selected text...")
                actions.send_keys(Keys.DELETE).perform()
                time.sleep(0.5)
                
                print(f"[WAIT] Typing new description: {description_text}")
                actions.send_keys(description_text).perform()
                
                driver.switch_to.default_content()
                print(f"[OK] Description filled successfully")
                
            except Exception as e:
                print(f"[ERROR] Failed to fill Description: {str(e)}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
                continue
            
            time.sleep(2)
            
            # STEP 10: Fill Quantity
            print(f"\n[Item {item_index}] Step 10: Filling Quantity: {quantity}")
            
            try:
                iframe_index = driver.execute_script(js_switch_to_iframe)
                if iframe_index >= 0:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    driver.switch_to.frame(iframes[iframe_index])
                
                actions = ActionChains(driver)
                
                time.sleep(1)
 
                # 2. กด Tab อีก 3ครั้ง
                print("[WAIT] Pressing Tab 3 more times...")
                for i in range(3):
                    actions.send_keys(Keys.TAB).perform()
                    time.sleep(0.5)
                
                # พิมพ์ Quantity
                print(f"[WAIT] Typing quantity: {quantity}")
                actions.send_keys(quantity).perform()
                
                driver.switch_to.default_content()
                print(f"[OK] Quantity filled successfully")
                
            except Exception as e:
                print(f"[ERROR] Failed to fill Quantity: {str(e)}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
                continue
            
            time.sleep(2)
            
            # STEP 11: Fill Price
            print(f"\n[Item {item_index}] Step 11: Filling price")
            
            try:
                iframe_index = driver.execute_script(js_switch_to_iframe)
                if iframe_index >= 0:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    driver.switch_to.frame(iframes[iframe_index])
                
                actions = ActionChains(driver)
                
                if is_glass_item:
                    # สินค้าขึ้นต้นด้วย G (กระจก)
                    print("[WAIT] Item starts with 'G' - filling glass prices...")
                    
                    # กด Tab 2 ครั้ง
                    print("[WAIT] Pressing Tab 2 times to reach price per sq.ft...")
                    for i in range(2):
                        actions.send_keys(Keys.TAB).perform()
                        time.sleep(0.5)
                    
                    # ใส่ราคาต่อตารางฟุต
                    price_per_sqft = item.get('price_per_sqft', '24')
                    print(f"[WAIT] Typing price per sq.ft: {price_per_sqft}")
                    actions.send_keys(price_per_sqft).perform()
                    time.sleep(0.5)
                    
                    # กด Tab 1 ครั้ง
                    print("[WAIT] Pressing Tab 1 time to reach price per sheet...")
                    actions.send_keys(Keys.TAB).perform()
                    time.sleep(0.5)
                    
                    # ใส่ราคาต่อแผ่น
                    price_per_sheet = item.get('price_per_sheet', '300')
                    print(f"[WAIT] Typing price per sheet: {price_per_sheet}")
                    actions.send_keys(price_per_sheet).perform()
                    
                    print(f"[OK] Glass prices filled: {price_per_sqft} baht/sq.ft, {price_per_sheet} baht/sheet")
                    
                else:
                    # สินค้าไม่ใช่กระจก
                    print("[WAIT] Item does not start with 'G' - filling unit price...")
                    
                    # กด Tab 3 ครั้ง
                    print("[WAIT] Pressing Tab 3 times to reach unit price...")
                    for i in range(3):
                        actions.send_keys(Keys.TAB).perform()
                        time.sleep(0.5)
                    
                    # ใส่ราคา
                    unit_price = item.get('unit_price', '500')
                    print(f"[WAIT] Typing unit price: {unit_price}")
                    actions.send_keys(unit_price).perform()
                    
                    print(f"[OK] Unit price filled: {unit_price} baht")
                
                driver.switch_to.default_content()
                
            except Exception as e:
                print(f"[ERROR] Failed to fill price: {str(e)}")
                try:
                    driver.switch_to.default_content()
                except:
                    pass
                continue
            
            time.sleep(2)
            
            # If not the last item, press Tab 7 times to go to next line
            if item_index < len(items_to_add):
                print(f"\n[Item {item_index}] Moving to next line...")
                
                try:
                    iframe_index = driver.execute_script(js_switch_to_iframe)
                    if iframe_index >= 0:
                        iframes = driver.find_elements(By.TAG_NAME, "iframe")
                        driver.switch_to.frame(iframes[iframe_index])
                    
                    actions = ActionChains(driver)
                    
                    # กด Tab 7 ครั้งเพื่อไปบรรทัดใหม่
                    print("[WAIT] Pressing Tab 7 times to go to next line...")
                    for i in range(7):
                        actions.send_keys(Keys.TAB).perform()
                        time.sleep(0.5)
                    
                    driver.switch_to.default_content()
                    print(f"[OK] Moved to next line")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to move to next line: {str(e)}")
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
                
                time.sleep(2)
            actions.send_keys(Keys.TAB).perform()
            time.sleep(0.5)
        
        print("\n" + "="*60)
        print(f"[OK] All {len(items_to_add)} items added successfully!")
        print("="*60)
        
        time.sleep(2)
        
        print("\n" + "="*60)
        print("[OK] RPA script completed successfully!")
        print("\n" + "="*60)
        print("[OK] RPA script completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"[ERROR] Error occurred: {str(e)}")
        print("\n[TIP] Make sure Chrome is running with remote debugging:")
        print('   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')

    

if __name__ == "__main__":
    # Load RPA data from JSON file (if called from API)
    rpa_data = load_rpa_data()
    
    # Get quote code from command line argument or prompt user
    if len(sys.argv) > 1:
        quote_code = sys.argv[1]
    else:
        print("[INFO] Enter the quote code (e.g., TRQT, AYSQ, etc.):")
        quote_code = input("Quote code: ").strip().upper()
    
    if not quote_code:
        print("[ERROR] No quote code provided. Exiting.")
        sys.exit(1)
    
    # Pass rpa_data to the function
    create_sales_quote(quote_code, rpa_data)
