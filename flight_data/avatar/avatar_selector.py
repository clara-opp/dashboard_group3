import streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(layout="wide")
st.title("Choose Your Character")

# Replace these with your actual hosted URLs (these demo URLs are public)
AVATARS = [
    {
        "id": "astronaut",
        "name": "Astronaut",
        "model": "https://modelviewer.dev/shared-assets/models/Astronaut.glb",
        "thumb": "https://modelviewer.dev/shared-assets/models/thumbnails/Astronaut.webp",
        "desc": "Ready for space"
    },
    {
        "id": "robot",
        "name": "Robot Expressive",
        "model": "https://modelviewer.dev/shared-assets/models/RobotExpressive.glb",
        "thumb": "https://modelviewer.dev/shared-assets/models/thumbnails/RobotExpressive.webp",
        "desc": "Expressive robot"
    },
    # add more avatar dicts (up to ~10) here...
]

# init session state
if "selected_avatar" not in st.session_state:
    st.session_state.selected_avatar = None

# Show grid of thumbnails + select buttons
num_cols = 3
cols = st.columns(num_cols)
for i, avatar in enumerate(AVATARS):
    col = cols[i % num_cols]
    with col:
        st.image(avatar["thumb"], use_column_width=True)
        st.markdown(f"**{avatar['name']}**")
        if avatar.get("desc"):
            st.caption(avatar["desc"])
        # use avatar id for unique button key
        if st.button(f"Select {avatar['name']}", key=f"select_{avatar['id']}"):
            st.session_state.selected_avatar = avatar["id"]

# Show currently selected avatar (large preview)
if st.session_state.selected_avatar is None:
    st.info("No avatar selected yet — click **Select** under a thumbnail.")
else:
    # find avatar object safely
    sel = next((a for a in AVATARS if a["id"] == st.session_state.selected_avatar), None)
    if sel is None:
        st.error("Selected avatar not found (internal error).")
    else:
        st.markdown(f"### Selected: {sel['name']}")
        if sel.get("desc"):
            st.write(sel["desc"])

        # model-viewer embed (lazy — only loaded when selected)
        model_html = f"""
        <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
        <model-viewer src="{sel['model']}"
                      alt="{sel['name']}"
                      auto-rotate
                      camera-controls
                      exposure="1"
                      style="width:100%; height:480px; background-color:#f6f6f6;">
        </model-viewer>
        """
        components_html(model_html, height=520)

        if st.button("Confirm selection"):
            st.success(f"You chose {sel['name']} ✅")
            # place your save/next-step logic here
