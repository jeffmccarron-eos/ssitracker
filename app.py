import streamlit as st
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
TRACKING_NUMBER = "36162578"
TOTAL_DISTANCE = 2694
TQL_URL = "https://trax.tql.com/shipment-tracking"

st.set_page_config(page_title="NGS Shipment Tracker", page_icon="🚚")

def get_tracking_data():
    with sync_playwright() as p:
        # Launch browser (headless=True means no window pops up)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(TQL_URL, wait_until="networkidle")
            
            # 1. Enter the tracking value
            # Note: Selectors may need adjustment if TQL changes their site structure
            page.fill('input[placeholder*="Track"]', TRACKING_NUMBER)
            
            # 2. Click Track Shipment
            page.click('button:has-text("Track")')
            
            # Wait for the table to load
            page.wait_for_selector('table', timeout=10000)
            
            # 3. Extract "Miles to delivery" 
            # This logic assumes the 'Miles to delivery' is in a specific table cell
            # We look for the text and get the associated value
            miles_remaining_str = page.locator('td:right-of(:text("Miles to delivery"))').first.inner_text()
            
            # Clean numeric data (remove commas/text)
            miles_remaining = int(''.join(filter(str.isdigit, miles_remaining_str)))
            browser.close()
            return miles_remaining
        except Exception as e:
            browser.close()
            st.error(f"Error accessing TQL data: {e}")
            return None

# --- UI DISPLAY ---
st.title("🚚 NGS Projector Enclosure Tracker")
st.write(f"**Tracking Number:** {TRACKING_NUMBER}")

# Data Refresh Logic
if 'last_val' not in st.session_state:
    st.session_state.last_val = get_tracking_data()
    st.session_state.last_update = datetime.now().strftime("%H:%M:%S")

remaining = st.session_state.last_val

if remaining is not None:
    traveled = TOTAL_DISTANCE - remaining
    percent_complete = min(traveled / TOTAL_DISTANCE, 1.0)

    # Progress Bar Visualization
    st.subheader(f"Current Status: {remaining:,} miles to go")
    st.progress(percent_complete)
    
    col1, col2 = st.columns(2)
    col1.metric("Miles Traveled", f"{traveled:,}")
    col2.metric("Remaining", f"{remaining:,}")

    st.info(f"Last updated from TQL at: {st.session_state.last_update}")
else:
    st.warning("Waiting for TQL system response...")

# --- AUTO-UPDATE SCHEDULER ---
# This checks the time and triggers a refresh at :00 and :30
now = datetime.now()
if now.minute == 0 or now.minute == 30:
    st.rerun()

st.caption("Auto-updates every 30 minutes (on the :00 and :30).")