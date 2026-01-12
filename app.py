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

def get_random_number_and_color():
    # Ensure we don't get the same number consecutively
    while True:
        number = random.randint(0, 9)
        if number != st.session_state.current_number:
            break
    
    # Choose a random color
    colors = ['red', 'green', 'blue']
    color = random.choice(colors)
    
    return number, color

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

def process_input():
    input_key = f"input_{st.session_state.trials}"
    if st.session_state.get(input_key):
        user_input = st.session_state[input_key]
        # Process immediately when a single digit is entered
        if user_input and len(user_input) == 1:
            end_time = time.time()
            reaction_time = end_time - st.session_state.start_time

            # Record the data
            trial_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'name': st.session_state.user_info['name'],
                'age': st.session_state.user_info['age'],
                'displayed_number': st.session_state.current_number,
                'displayed_color': st.session_state.current_color,
                'user_input': user_input,
                'is_correct': user_input == str(st.session_state.current_number),
                'reaction_time_seconds': round(reaction_time, 3)
            }

            # Save to session state and Google Sheets
            st.session_state.user_data.append(trial_data)
            save_to_google_sheets(trial_data)

            # Update trial counter
            st.session_state.trials += 1

            # If we've reached the trial limit, show completion message
            if st.session_state.trials >= 30:
                st.balloons()
                st.session_state.experiment_complete = True
            else:
                # Trigger a rerun to show the next number
                st.session_state.last_key = True
                st.rerun()

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
        st.write("Press the spacebar to begin the experiment")

        # Use components.html to capture spacebar
        space_pressed = components.html("""
        <div style="width: 100%; height: 150px; text-align: center; padding: 40px;">
            <div style="font-size: 24px; color: #666;">Press SPACEBAR to start</div>
            <div id="status" style="margin-top: 20px; font-size: 18px; color: #000;"></div>
        </div>

        <script>
        let pressed = false;

        function captureSpace(event) {
            if (!pressed && event.code === 'Space') {
                pressed = true;
                event.preventDefault();
                document.getElementById('status').textContent = 'Starting...';

                // Send signal back to Streamlit
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: 'start'
                }, '*');
            }
        }

        // Capture at both levels
        document.addEventListener('keydown', captureSpace);
        window.parent.document.addEventListener('keydown', captureSpace, true);
        </script>
        """, height=150, key="space_capture")

        if space_pressed == 'start':
            st.session_state.experiment_started = True
            st.rerun()
        return
    
    # Display current trial info
    st.write(f"Trial {st.session_state.trials + 1} of 30")
    
    # Generate new number and color if this is the first trial or after a key press
    if st.session_state.current_number is None or 'last_key' in st.session_state:
        st.session_state.current_number, st.session_state.current_color = get_random_number_and_color()
        st.session_state.start_time = time.time()
        if 'last_key' in st.session_state:
            del st.session_state.last_key
    
    # Display the number with the selected color
    st.markdown(
        f'<h1 style="color:{st.session_state.current_color};text-align:center;font-size:100px;">'
        f'{st.session_state.current_number}'
        '</h1>',
        unsafe_allow_html=True
    )
    
    # Instructions
    st.write("Just type the number you see - no need to press Enter!")

    # Check if user has already input for this trial
    input_key = f"digit_input_{st.session_state.trials}"

    # JavaScript-based input capture that auto-advances
    result = components.html(f"""
    <div id="input-capture" style="width: 100%; height: 100px; text-align: center; font-size: 24px; padding: 20px;">
        <div id="instruction" style="color: #666;">Press any number key (0-9)</div>
        <div id="captured" style="color: #000; font-weight: bold; margin-top: 10px;"></div>
    </div>

    <script>
    const parent = window.parent;
    let captured = false;

    // Capture keyboard input
    document.addEventListener('keydown', function(event) {{
        if (!captured && event.key >= '0' && event.key <= '9') {{
            captured = true;
            document.getElementById('captured').textContent = 'You entered: ' + event.key;
            document.getElementById('instruction').textContent = 'Recording...';

            // Send the input back to Streamlit
            parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: event.key
            }}, '*');
        }}
    }});

    parent.document.addEventListener('keydown', function(event) {{
        if (!captured && event.key >= '0' && event.key <= '9') {{
            captured = true;
            document.getElementById('captured').textContent = 'You entered: ' + event.key;
            document.getElementById('instruction').textContent = 'Recording...';

            // Send the input back to Streamlit
            parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: event.key
            }}, '*');
        }}
    }}, true);
    </script>
    """, height=100, key=input_key)

    # Process the captured input
    if result and result not in [None, '']:
        if input_key not in st.session_state:
            st.session_state[input_key] = result

            # Record the data immediately
            end_time = time.time()
            reaction_time = end_time - st.session_state.start_time

            trial_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'name': st.session_state.user_info['name'],
                'age': st.session_state.user_info['age'],
                'displayed_number': st.session_state.current_number,
                'displayed_color': st.session_state.current_color,
                'user_input': result,
                'is_correct': result == str(st.session_state.current_number),
                'reaction_time_seconds': round(reaction_time, 3)
            }

            # Save to session state and Google Sheets
            st.session_state.user_data.append(trial_data)
            save_to_google_sheets(trial_data)

            # Update trial counter
            st.session_state.trials += 1

            # If we've reached the trial limit, show completion message
            if st.session_state.trials >= 30:
                st.balloons()
                st.session_state.experiment_complete = True
            else:
                # Trigger a rerun to show the next number
                st.session_state.last_key = True
                time.sleep(0.3)  # Brief pause to show the captured input
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