"""
RPA Script: Create Sales Quote in D365 BC
1. Click +New button
2. Click Review or update the value for No.
3. Select the matching quote series based on input code
4. Click OK button
5. Fill Customer No. and press Enter
6. Click Sales Admin dropdown and select from list
7. Fill Department Code, click blank area
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import sys

def convert_quote_code(input_code):
    """
    Convert quote code from format like 'TRQT' to 'TRSQ-QT'
    Rules: Take first 2 chars + 'SQ-' + last 2 chars
    """
    if len(input_code) < 4:
        print(f"⚠️  Warning: Input code '{input_code}' is too short. Using as-is.")
        return input_code
    
    first_two = input_code[:2]
    last_two = input_code[-2:]
    converted = f"{first_two}SQ-{last_two}"
    
    print(f"📝 Converting: {input_code} → {converted}")
    return converted

def create_sales_quote(quote_code):
    """
    Automate creating a sales quote with specific series code
    """
    print("🚀 Starting RPA script for Sales Quote creation...")
    print(f"📋 Quote code: {quote_code}")
    
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
        print(f"✅ Found {len(windows)} open tabs")
        
        # Search for D365 BC Sales Quotes tab
        target_window = None
        for window in windows:
            driver.switch_to.window(window)
            current_url = driver.current_url
            current_title = driver.title
            
            print(f"📄 Checking tab: {current_title[:50]}...")
            
            if 'businesscentral' in current_url.lower() and 'sales' in current_url.lower():
                target_window = window
                print(f"✅ Found Sales Quotes tab: {current_title}")
                break
            elif 'Sales Quotes' in current_title or 'ใบเสนอราคาขาย' in current_title:
                target_window = window
                print(f"✅ Found Sales Quotes tab: {current_title}")
                break
        
        if not target_window:
            print("⚠️  Could not find Sales Quotes tab automatically")
            print("   Using current active tab instead...")
            target_window = driver.current_window_handle
        
        driver.switch_to.window(target_window)
        print(f"📍 Current page: {driver.current_url}")
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
            print(f"✅ {result}")
        except Exception as e:
            print(f"❌ Failed to click New button: {str(e)}")
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
            print(f"✅ {result}")
        except Exception as e:
            print(f"❌ Failed to click Review button: {str(e)}")
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
            print(f"✅ {result}")
        except Exception as e:
            print(f"❌ Failed to click series: {str(e)}")
            print(f"💡 Make sure the series '{target_series}' exists in the list")
            return
        
        time.sleep(2)
        
        # STEP 4: Click OK button
        print("\n" + "="*60)
        print("STEP 4: Clicking OK button")
        print("="*60)
        
        js_click_ok = """
        function ClickOKButton() {
            // ลองหาปุ่ม OK ด้วย id
            var button = document.querySelector('button#b207');
            if (button) {
                button.click();
                return 'Clicked OK button (by id) in main document';
            }
            
            // ลองหาด้วย class และ text
            var buttons = document.querySelectorAll('button.highlight-btn');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === 'OK') {
                    buttons[i].click();
                    return 'Clicked OK button (by class) in main document';
                }
            }
            
            // ลองหาปุ่มที่มี text "OK"
            buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.trim() === 'OK') {
                    buttons[i].click();
                    return 'Clicked OK button (by text) in main document';
                }
            }
            
            // ลองหาใน iframe
            var iframes = document.querySelectorAll('iframe');
            for (var j = 0; j < iframes.length; j++) {
                try {
                    var iframeDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                    
                    button = iframeDoc.querySelector('button#b207');
                    if (button) {
                        button.click();
                        return 'Clicked OK button (by id) in iframe ' + j;
                    }
                    
                    buttons = iframeDoc.querySelectorAll('button.highlight-btn');
                    for (var i = 0; i < buttons.length; i++) {
                        if (buttons[i].textContent.trim() === 'OK') {
                            buttons[i].click();
                            return 'Clicked OK button (by class) in iframe ' + j;
                        }
                    }
                    
                    buttons = iframeDoc.querySelectorAll('button');
                    for (var i = 0; i < buttons.length; i++) {
                        if (buttons[i].textContent.trim() === 'OK') {
                            buttons[i].click();
                            return 'Clicked OK button (by text) in iframe ' + j;
                        }
                    }
                } catch (e) {}
            }
            
            throw new Error('OK button not found');
        }
        return ClickOKButton();
        """
        
        try:
            result = driver.execute_script(js_click_ok)
            print(f"✅ {result}")
        except Exception as e:
            print(f"❌ Failed to click OK button: {str(e)}")
            return
        
        time.sleep(2)
        
        # STEP 5: Fill in Customer No.
        customer_no = "00001AY"  # Hard-coded for now, will be parameterized later
        print("\n" + "="*60)
        print(f"STEP 5: Filling in Customer No.: {customer_no}")
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
            print(f"✅ {result}")
        except Exception as e:
            print(f"❌ Failed to fill Customer No.: {str(e)}")
            return
        
        # Wait for page to load after entering customer
        print("⏳ Waiting for page to load after customer selection...")
        time.sleep(5)  # เพิ่มจาก 3 เป็น 5 วินาที
        
        # STEP 6: Select Sales Admin from dropdown
        sales_admin = "20614"  # Hard-coded for now
        print("\n" + "="*60)
        print(f"STEP 6: Selecting Sales Admin: {sales_admin}")
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
            print(f"✅ {result}")
            if 'not found' in result:
                print("⚠️  Sales Admin input field not found - continuing anyway...")
                time.sleep(2)
            else:
                # Wait for dropdown to appear
                print("⏳ Waiting for dropdown to appear...")
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
                print(f"✅ {result}")
                if 'not found' in result:
                    print("⚠️  Sales Admin record not found in dropdown - continuing anyway...")
        except Exception as e:
            print(f"⚠️  Could not select Sales Admin: {str(e)}")
            print("   Continuing anyway...")
        
        time.sleep(2)
        
        # STEP 7: Fill in Department Code, click blank area
        department_code = "05AY"  # Hard-coded for now
        print("\n" + "="*60)
        print(f"STEP 7: Filling in Department Code: {department_code}")
        print("="*60)
        
        # Step 7.1: Type the department code in the input field
        js_type_department = f"""
        function TypeDepartmentCode() {{
            var deptCode = '{department_code}';
            console.log('=== Looking for Department Code input field ===');
            
            // ลองหาใน iframe ก่อน
            var iframes = document.querySelectorAll('iframe');
            console.log('Found ' + iframes.length + ' iframes');
            
            for (var j = 0; j < iframes.length; j++) {{
                try {{
                    var iframeDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                    
                    // ลองหาด้วย aria-labelledby ที่มี "Department" ในชื่อ
                    var inputs = iframeDoc.querySelectorAll('input[role="combobox"]');
                    console.log('Found ' + inputs.length + ' combobox inputs in iframe ' + j);
                    
                    for (var i = 0; i < inputs.length; i++) {{
                        var ariaLabelledBy = inputs[i].getAttribute('aria-labelledby') || '';
                        console.log('  Input ' + i + ': aria-labelledby="' + ariaLabelledBy + '"');
                        
                        // ตรวจสอบว่า label มีคำว่า Department หรือไม่
                        if (ariaLabelledBy) {{
                            var label = iframeDoc.getElementById(ariaLabelledBy);
                            if (label && (label.textContent.includes('Department') || label.textContent.includes('แผนก'))) {{
                                console.log('Found Department Code input field');
                                inputs[i].focus();
                                inputs[i].value = deptCode;
                                inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                                inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return 'Typed Department Code in iframe ' + j;
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
                    if (label && (label.textContent.includes('Department') || label.textContent.includes('แผนก'))) {{
                        console.log('Found Department Code input field in main document');
                        inputs[i].focus();
                        inputs[i].value = deptCode;
                        inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return 'Typed Department Code in main document';
                    }}
                }}
            }}
            
            return 'Department Code input field not found';
        }}
        return TypeDepartmentCode();
        """
        
        try:
            result = driver.execute_script(js_type_department)
            print(f"✅ {result}")
            if 'not found' in result:
                print("⚠️  Department Code input field not found - continuing anyway...")
                time.sleep(2)
            else:
                # Wait for dropdown to appear
                print("⏳ Waiting for dropdown to appear...")
                time.sleep(3)  # เพิ่มเวลารอเป็น 3 วินาที
                
                # Step 7.2: Click the matching record in dropdown
                js_select_dept_from_dropdown = f"""
                function SelectDeptFromDropdown() {{
                    var targetCode = '{department_code}';
                    console.log('=== Looking for Department Code record: ' + targetCode + ' ===');
                    
                    // ลองหาใน iframe
                    var iframes = document.querySelectorAll('iframe');
                    console.log('Found ' + iframes.length + ' iframes');
                    
                    for (var j = 0; j < iframes.length; j++) {{
                        try {{
                            var iframeDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                            
                            // วิธีที่ 1: หา td ที่มี role="gridcell" และมี link ข้างในที่ text ตรงกับ targetCode
                            var gridCells = iframeDoc.querySelectorAll('td[role="gridcell"]');
                            console.log('Iframe ' + j + ': Found ' + gridCells.length + ' grid cells');
                            
                            for (var i = 0; i < gridCells.length; i++) {{
                                var link = gridCells[i].querySelector('a.stringcontrol-read');
                                if (link && link.textContent.trim() === targetCode) {{
                                    console.log('Found matching grid cell with link: ' + link.textContent.trim());
                                    // ลองคลิกที่ td
                                    gridCells[i].click();
                                    return 'Clicked Department Code grid cell in iframe ' + j;
                                }}
                            }}
                            
                            // วิธีที่ 2: หา link โดยตรงที่มี title="Select record "05AY""
                            var linkByTitle = iframeDoc.querySelector('a[title*="Select record"][title*="' + targetCode + '"]');
                            if (linkByTitle) {{
                                console.log('Found link by title attribute');
                                linkByTitle.click();
                                return 'Clicked Department Code link by title in iframe ' + j;
                            }}
                            
                            // วิธีที่ 3: หา link ที่มี class stringcontrol-read และ text ตรงกับ targetCode
                            var links = iframeDoc.querySelectorAll('a.stringcontrol-read');
                            console.log('Iframe ' + j + ': Found ' + links.length + ' links with class stringcontrol-read');
                            
                            for (var i = 0; i < links.length; i++) {{
                                var text = links[i].textContent.trim();
                                if (i < 10) {{
                                    console.log('  Link ' + i + ': "' + text + '"');
                                }}
                                if (text === targetCode) {{
                                    console.log('Found matching link: ' + text);
                                    links[i].click();
                                    return 'Clicked Department Code link in iframe ' + j;
                                }}
                            }}
                            
                            // วิธีที่ 4: หา link ที่มี role="button" และ text ตรงกับ targetCode
                            var buttonLinks = iframeDoc.querySelectorAll('a[role="button"]');
                            console.log('Iframe ' + j + ': Found ' + buttonLinks.length + ' button links');
                            for (var i = 0; i < buttonLinks.length; i++) {{
                                var text = buttonLinks[i].textContent.trim();
                                if (text === targetCode) {{
                                    console.log('Found matching button link: ' + text);
                                    buttonLinks[i].click();
                                    return 'Clicked Department Code button link in iframe ' + j;
                                }}
                            }}
                        }} catch (e) {{
                            console.log('Error accessing iframe ' + j + ': ' + e.message);
                        }}
                    }}
                    
                    // ลองหาใน main document
                    console.log('Searching in main document...');
                    
                    // วิธีที่ 1: หา td ที่มี role="gridcell"
                    var gridCells = document.querySelectorAll('td[role="gridcell"]');
                    console.log('Main document: Found ' + gridCells.length + ' grid cells');
                    for (var i = 0; i < gridCells.length; i++) {{
                        var link = gridCells[i].querySelector('a.stringcontrol-read');
                        if (link && link.textContent.trim() === targetCode) {{
                            console.log('Found matching grid cell in main document');
                            gridCells[i].click();
                            return 'Clicked Department Code grid cell in main document';
                        }}
                    }}
                    
                    // วิธีที่ 2: หา link โดยตรง
                    var linkByTitle = document.querySelector('a[title*="Select record"][title*="' + targetCode + '"]');
                    if (linkByTitle) {{
                        console.log('Found link by title in main document');
                        linkByTitle.click();
                        return 'Clicked Department Code link by title in main document';
                    }}
                    
                    // วิธีที่ 3
                    var links = document.querySelectorAll('a.stringcontrol-read');
                    console.log('Main document: Found ' + links.length + ' links with class stringcontrol-read');
                    for (var i = 0; i < links.length; i++) {{
                        var text = links[i].textContent.trim();
                        if (text === targetCode) {{
                            console.log('Found matching link in main document: ' + text);
                            links[i].click();
                            return 'Clicked Department Code link in main document';
                        }}
                    }}
                    
                    return 'Department Code record "' + targetCode + '" not found in dropdown';
                }}
                return SelectDeptFromDropdown();
                """
                
                result = driver.execute_script(js_select_dept_from_dropdown)
                print(f"✅ {result}")
                if 'not found' in result:
                    print("⚠️  Department Code record not found in dropdown - continuing anyway...")
        except Exception as e:
            print(f"⚠️  Could not select Department Code: {str(e)}")
            print("   Continuing anyway...")
        
        print("⏳ Waiting 2 seconds before next step...")
        time.sleep(2)
        
        # STEP 8: Click "Show more" button in General section
        print("\n" + "="*60)
        print("STEP 8: Clicking 'Show more' button in General section")
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
            print(f"✅ {result}")
        except Exception as e:
            print(f"❌ Failed to click Show more button: {str(e)}")
            return
        
        print("⏳ Waiting 2 seconds for fields to expand...")
        time.sleep(2)
        
        print("\n" + "="*60)
        print("✅ RPA script completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        print("\n💡 Make sure Chrome is running with remote debugging:")
        print('   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')

if __name__ == "__main__":
    # Get quote code from command line argument or prompt user
    if len(sys.argv) > 1:
        quote_code = sys.argv[1]
    else:
        print("📋 Enter the quote code (e.g., TRQT, AYSQ, etc.):")
        quote_code = input("Quote code: ").strip().upper()
    
    if not quote_code:
        print("❌ No quote code provided. Exiting.")
        sys.exit(1)
    
    create_sales_quote(quote_code)
