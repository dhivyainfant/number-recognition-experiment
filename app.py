import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random
import time
from datetime import datetime
import os
import gspread
from google.oauth2.service_account import Credentials

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Initialize session state
if 'trials' not in st.session_state:
    st.session_state.trials = 0
    st.session_state.current_number = None
    st.session_state.current_color = None
    st.session_state.start_time = None
    st.session_state.user_data = []
    st.session_state.user_info = None

def generate_trial_sequence():
    """Generate a balanced sequence of 30 trials: 10 per color, each digit appears 3 times"""
    colors = ['red', 'green', 'blue']
    trials = []

    # Create 3 sets of all digits (0-9), one for each color
    for color in colors:
        for digit in range(10):
            trials.append((digit, color))

    # Shuffle to randomize order
    random.shuffle(trials)
    return trials

def get_next_trial():
    """Get the next trial from the pre-generated sequence"""
    if 'trial_sequence' not in st.session_state or not st.session_state.trial_sequence:
        st.session_state.trial_sequence = generate_trial_sequence()

    if st.session_state.trials < len(st.session_state.trial_sequence):
        return st.session_state.trial_sequence[st.session_state.trials]
    return None, None

def save_to_google_sheets(data):
    """Save data to Google Sheets"""
    try:
        # Check if Google Sheets credentials are available
        if "gcp_service_account" in st.secrets:
            # Set up credentials
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']

            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=scope)
            client = gspread.authorize(credentials)

            # Open the Google Sheet (create it if it doesn't exist)
            sheet_name = st.secrets.get("sheet_name", "Number Recognition Results")
            try:
                sheet = client.open(sheet_name).sheet1
            except gspread.SpreadsheetNotFound:
                st.error(f"Google Sheet '{sheet_name}' not found. Please create it and share it with the service account email.")
                return False

            # Get existing data to check if we need to add headers
            existing_data = sheet.get_all_values()

            # If sheet is empty, add headers
            if not existing_data:
                headers = list(data.keys())
                sheet.append_row(headers)

            # Append the new row
            values = list(data.values())
            sheet.append_row(values)
            return True
        else:
            # Fallback to CSV if no credentials
            save_to_csv(data)
            return False
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        # Fallback to CSV
        save_to_csv(data)
        return False

def save_to_csv(data):
    """Fallback CSV saving function"""
    df = pd.DataFrame([data])
    csv_file = 'data/results.csv'

    # If file doesn't exist, write with header, else append without header
    if not os.path.isfile(csv_file):
        df.to_csv(csv_file, index=False)
    else:
        df.to_csv(csv_file, mode='a', header=False, index=False)

def main():
    st.title("Number Recognition Experiment")
    
    # Get user info if not already provided
    if st.session_state.user_info is None:
        with st.form("user_info_form"):
            name = st.text_input("Enter your name:")
            age = st.number_input("Enter your age:", min_value=5, max_value=120, step=1)
            submitted = st.form_submit_button("Start Experiment")
            
            if submitted and name:
                st.session_state.user_info = {'name': name, 'age': age}
                st.rerun()
        return
    

    if 'experiment_started' not in st.session_state:
        st.write("Click the button below to begin the experiment")

        if st.button("START EXPERIMENT", type="primary"):
            st.session_state.experiment_started = True
            st.rerun()
        return
    
    # Display current trial info
    st.write(f"Trial {st.session_state.trials + 1} of 30")

    # Generate new number and color for current trial
    st.session_state.current_number, st.session_state.current_color = get_next_trial()

    # Set start time when displaying new number
    if 'trial_start_time' not in st.session_state or st.session_state.get('new_trial', True):
        st.session_state.start_time = time.time()
        st.session_state.new_trial = False

    # Display the number with the selected color (larger font)
    st.markdown(
        f'<h1 style="color:{st.session_state.current_color};text-align:center;font-size:200px;font-weight:bold;margin:50px 0;">'
        f'{st.session_state.current_number}'
        '</h1>',
        unsafe_allow_html=True
    )
    
    # Instructions
    st.write("Just type the number you see!")

    # Check if input was already captured for this trial
    if not st.session_state.get(f'processed_{st.session_state.trials}', False):
        # Keystroke capture component
        result = components.html(f"""
        <div style="width: 100%; height: 80px; text-align: center; font-size: 20px; padding: 20px;">
            <div id="feedback" style="color: #666;">Waiting for input...</div>
        </div>

        <script>
        let captured = false;
        const parent = window.parent;

        function captureKey(event) {{
            // Only capture number keys 0-9
            if (!captured && event.key >= '0' && event.key <= '9') {{
                captured = true;
                event.preventDefault();

                // Show feedback
                document.getElementById('feedback').textContent = 'You pressed: ' + event.key;
                document.getElementById('feedback').style.color = '#000';
                document.getElementById('feedback').style.fontWeight = 'bold';

                // Send the key to Streamlit
                parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: event.key
                }}, '*');
            }}
        }}

        // Capture at document level
        document.addEventListener('keydown', captureKey);
        parent.document.addEventListener('keydown', captureKey, true);

        // Focus on the component to ensure it receives events
        window.focus();
        </script>
        """, height=80)

        # Process the captured keystroke
        if result is not None and isinstance(result, str) and result in '0123456789':
            end_time = time.time()
            reaction_time_ms = (end_time - st.session_state.start_time) * 1000

            # Record the data
            trial_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                'name': st.session_state.user_info['name'],
                'age': st.session_state.user_info['age'],
                'displayed_number': st.session_state.current_number,
                'displayed_color': st.session_state.current_color,
                'user_input': result,
                'is_correct': result == str(st.session_state.current_number),
                'reaction_time_ms': round(reaction_time_ms, 2)
            }

            # Mark as processed and save
            st.session_state[f'processed_{st.session_state.trials}'] = True
            st.session_state.user_data.append(trial_data)
            save_to_google_sheets(trial_data)

            # Update trial counter
            st.session_state.trials += 1

            # Check if experiment is complete
            if st.session_state.trials >= 30:
                st.session_state.experiment_complete = True
            else:
                st.session_state.new_trial = True
                time.sleep(0.2)  # Brief pause to show feedback
                st.rerun()

    # Check if experiment is complete
    if st.session_state.get('experiment_complete'):
        st.success("Experiment complete! Thank you for participating!")
        st.download_button(
            label="Download Your Results",
            data=pd.DataFrame(st.session_state.user_data).to_csv(index=False),
            file_name="experiment_results.csv",
            mime="text/csv"
        )

        if st.button("Start Over"):
            st.session_state.clear()
            st.rerun()
        return

if __name__ == "__main__":
    main()