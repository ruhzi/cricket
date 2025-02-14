import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json

st.set_page_config(page_title="Cricket Field Simulator", layout="wide")

# Inject enhanced custom CSS
custom_css = """
<style>
/* Hide default Streamlit header, footer, and sidebar navigation */
header {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stSidebarNav"] {display: none;}

/* Style the main container */
.reportview-container .main .block-container {
    padding: 2rem;
    max-width: 100%;
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    border-radius: 10px;
}

/* Body and background styling */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(to right, #ece9e6, #ffffff);
    margin: 0;
}

/* Title styling */
h1 {
    color: #2c3e50;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    margin-bottom: 0.5em;
}

/* General text styling */
p, label, .css-1d391kg {
    color: #333;
}

/* Sidebar styling with a darker theme */
[data-testid="stSidebar"] {
    background-color: #2c3e50;
    border-right: 1px solid #1a252f;
    padding: 1rem;
    color: white;
}

/* Ensure sidebar text is white */
[data-testid="stSidebar"] * {
    color: white;
}

/* Customize Streamlit buttons */
button {
    background-color: #2c3e50;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0.5em 1em;
    cursor: pointer;
    transition: background-color 0.3s ease;
}
button:hover {
    background-color: #34495e;
}

/* Customize download button */
a[data-baseweb="button"] {
    background-color: #2c3e50 !important;
    color: white !important;
    border-radius: 4px !important;
    padding: 0.5em 1em !important;
    text-decoration: none !important;
}
a[data-baseweb="button"]:hover {
    background-color: #34495e !important;
}
</style>
"""


st.markdown(custom_css, unsafe_allow_html=True)



field_radius = 50      
pitch_length = 22      
inner_circle_radius = 30  

st.title("\U0001F3CF Cricket Field Simulator")
st.write("Choose a format, adjust fielding positions, and validate restrictions.")

batsman_handedness = st.sidebar.radio("Select Batsman Handedness", options=["Right-handed", "Left-handed"])
st.sidebar.markdown(f"**Batsman: {batsman_handedness}**")

selected_format = st.sidebar.selectbox("Choose Match Format", ["T20", "ODI", "Test"])
if selected_format == "Test":
    overs = 0
elif selected_format == "T20":
    overs = st.sidebar.slider("Overs Completed", 1, 20, 1)
else:
    overs = st.sidebar.slider("Overs Completed", 1, 50, 1)

def get_max_outside_circle(overs, format):
    if format == "Test":
        return 11
    elif format == "T20":
        return 2 if overs <= 6 else 5
    elif format == "ODI":
        if overs <= 10:
            return 2
        elif overs <= 40:
            return 4
        else:
            return 5
    return 11

max_outside = get_max_outside_circle(overs, selected_format)

def clip_to_circle(point, radius):
    x, y = point
    d = np.sqrt(x**2 + y**2)
    return (x * radius / d, y * radius / d) if d > radius else point

new_presets = {
    "Wicketkeeper": (5, -28),
    "First Slip": (12, -21),
    "Second Slip": (15, -20),
    "Third Slip": (18, -18),
    "Gully": (26, -15),
    "Leg Slip": (-12, -21),
    "Silly Point": (18, -9),
    "Short Leg": (-15, -7),
    "Point": (26, -10),
    "Cover": (24, 0),
    "Mid-Off": (26, 14),
    "Mid-On": (-26, 14),
    "Mid-Wicket": (-27, 0),
    "Square Leg": (-27, -11),
    "Short Fine Leg": (-20, -20),
    "Third Man": (40, -35),
    "Deep Cover": (45, 15),
    "Long Off": (45, 35),
    "Long On": (-45, 35),
    "Deep Mid-Wicket": (-40, 15),
    "Deep Square Leg": (-40, -5),
    "Fine Leg": (-35, -25),
    "Bowler": (0, 28)
}

def adjust_for_handedness(point, handedness):
    x, y = point
    return (-x, y) if handedness == "Left-handed" else point

adjusted_presets = { pos: clip_to_circle(adjust_for_handedness(coord, batsman_handedness), field_radius)
                     for pos, coord in new_presets.items() }

if "current_handedness" not in st.session_state:
    st.session_state.current_handedness = batsman_handedness
else:
    if st.session_state.current_handedness != batsman_handedness:
        updated_positions = {key: clip_to_circle((-x, y), field_radius) for key, (x, y) in st.session_state.field_positions.items()}
        st.session_state.field_positions = updated_positions
        st.session_state.current_handedness = batsman_handedness

if "field_positions" not in st.session_state:
    st.session_state.field_positions = {
        "Wicketkeeper": adjusted_presets["Wicketkeeper"],
        "Bowler": adjusted_presets["Bowler"]
    }

uploaded_file = st.sidebar.file_uploader("Upload JSON Field Setup", type=["json"])
if uploaded_file is not None:
    st.session_state.field_positions = json.load(uploaded_file)

st.sidebar.header("Adjust Fielding Positions")
preset_choice = st.sidebar.selectbox("Select Preset Position", list(adjusted_presets.keys()))
if st.sidebar.button("Add Preset Fielder"):
    st.session_state.field_positions[preset_choice] = adjusted_presets[preset_choice]

st.sidebar.subheader("Custom Field Placement")
custom_x = st.sidebar.slider("Custom X", -field_radius, field_radius, 0)
custom_y = st.sidebar.slider("Custom Y", -field_radius, field_radius, 0)
custom_name = st.sidebar.text_input("Custom Fielder Name", "Fielder")
if st.sidebar.button("Add Custom Fielder"):
    st.session_state.field_positions[custom_name] = clip_to_circle((custom_x, custom_y), field_radius)

if st.sidebar.button("Reset Fielders"):
    st.session_state.field_positions = {
        "Wicketkeeper": adjusted_presets["Wicketkeeper"],
        "Bowler": adjusted_presets["Bowler"]
    }

def draw_cricket_field():
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(-field_radius, field_radius)
    ax.set_ylim(-field_radius, field_radius)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Cricket Field Layout")
    
    field_circle = plt.Circle((0, 0), field_radius, color="green", alpha=0.3, edgecolor="black")
    inner_circle = plt.Circle((0, 0), inner_circle_radius, color='white', fill=False, linestyle='dashed')
    pitch = plt.Rectangle((-1, -pitch_length/2), 2, pitch_length, color='brown')
    ax.add_patch(field_circle); ax.add_patch(inner_circle); ax.add_patch(pitch)
    
    outside_circle = 0
    for fielder, (x, y) in st.session_state.field_positions.items():
        if np.sqrt(x**2 + y**2) > inner_circle_radius:
            outside_circle += 1
        ax.scatter(x, y, color='red', s=50, edgecolor='black', linewidth=1.2)
        ax.text(x + 2, y + 2, fielder, fontsize=10, color="white", ha="left",
                bbox=dict(facecolor='black', alpha=0.5))
    
    return fig, outside_circle

fig, outside_count = draw_cricket_field()
st.pyplot(fig)

if outside_count > max_outside:
    st.sidebar.error(f"⚠️ {outside_count} fielders outside 30-yard circle! Allowed: {max_outside}")
else:
    st.sidebar.success(f"✅ Fielding setup follows {selected_format} rules.")

st.sidebar.download_button(
    label="Save Field Setup",
    data=json.dumps(st.session_state.field_positions, indent=4),
    file_name="field_setup.json",
    mime="application/json"
)

st.markdown("""
    <div style="text-align: center; margin: 2rem auto; font-size: 1.1em; color: #666; padding: 12px; background-color: #d0d0d0; border-radius: 8px; width: fit-content;">
        Made by <a href="https://x.com/ruhzi57" target="_blank" style="color: #2c3e50; text-decoration: none;">ruhzi</a>
    </div>
    """, unsafe_allow_html=True)



