import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Config ----------
FSQ_BASE_URL = "https://places-api.foursquare.com"
FSQ_VERSION = "2025-06-17"  # must match the version header style you're using

DEFAULT_LL = "49.7500,8.6500"  # Seeheim-Jugenheim-ish; change as needed


# ---------- Foursquare client ----------
def fsq_search_places(query: str, ll: str, radius: int = 4000, limit: int = 8):
    api_key = os.getenv("FOURSQUARE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing FOURSQUARE_API_KEY")

    url = f"{FSQ_BASE_URL}/places/search"
    headers = {
        "accept": "application/json",
        "X-Places-Api-Version": FSQ_VERSION,
        "authorization": f"Bearer {api_key}",
    }
    params = {
        "query": query,
        "ll": ll,
        "radius": radius,
        "limit": limit,
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)
    # Helpful for debugging:
    if r.status_code != 200:
        return {"error": True, "status": r.status_code, "body": r.text}

    data = r.json()
    results = []
    for p in data.get("results", []):
        results.append(
            {
                "fsq_place_id": p.get("fsq_place_id"),
                "name": p.get("name"),
                "distance_m": p.get("distance"),
                "categories": [c.get("name") for c in (p.get("categories") or []) if c.get("name")],
                "address": (p.get("location") or {}).get("formatted_address"),
                "website": p.get("website"),
                "tel": p.get("tel"),
                "latitude": p.get("latitude"),
                "longitude": p.get("longitude"),
            }
        )

    return {"error": False, "results": results}


# ---------- OpenAI tool-calling loop ----------
def run_planner(messages, ll: str, radius: int, budget_eur: float):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "").strip())

    tools = [
        {
            "type": "function",
            "function": {
                "name": "fsq_search_places",
                "description": "Search for places near a lat/lon using Foursquare Places API.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search term, e.g. 'museum', 'cafe', 'park'."},
                        "ll": {"type": "string", "description": "Lat,lon string, e.g. '49.75,8.65'."},
                        "radius": {"type": "integer", "description": "Radius in meters."},
                        "limit": {"type": "integer", "description": "Max number of results."},
                    },
                    "required": ["query", "ll"],
                },
            },
        }
    ]

    # A tight system prompt that forces: budget awareness + citations/estimates + using Foursquare tool.
    system_msg = {
        "role": "system",
        "content": (
            "You are a day-trip planner.\n"
            "Goal: propose a realistic day-trip itinerary within the user's fixed budget.\n"
            "Rules:\n"
            "- Use fsq_search_places to fetch real nearby places before recommending venues.\n"
            "- Foursquare results do not include exact prices; clearly mark any costs as estimates.\n"
            "- Provide a per-item cost estimate and a running total not exceeding the budget.\n"
            "- Return a compact itinerary with times, travel notes, and place addresses.\n"
        ),
    }

    # Add context to user request so the model always has ll/budget in scope.
    context_msg = {
        "role": "user",
        "content": (
            f"Context:\n- Budget: {budget_eur:.2f} EUR\n- Search center (ll): {ll}\n- Search radius: {radius} m\n\n"
            "Plan a day trip for today based on my preferences in this chat."
        ),
    }

    convo = [system_msg] + messages + [context_msg]

    # Tool-calling loop (a few iterations is usually enough)
    for _ in range(6):
        resp = client.chat.completions.create(
            model=st.session_state.model,
            messages=convo,
            tools=tools,
            tool_choice="auto",
        )

        msg = resp.choices[0].message

        # If the model wants to call tools, execute them and append results.
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            convo.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [tc.model_dump() for tc in tool_calls],
                }
            )

            for tc in tool_calls:
                fn = tc.function.name
                args = json.loads(tc.function.arguments or "{}")

                if fn == "fsq_search_places":
                    out = fsq_search_places(
                        query=args.get("query", ""),
                        ll=args.get("ll", ll),
                        radius=int(args.get("radius", radius)),
                        limit=int(args.get("limit", 8)),
                    )
                else:
                    out = {"error": True, "message": f"Unknown tool: {fn}"}

                convo.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(out, ensure_ascii=False),
                    }
                )

            continue

        # No more tools requested -> final answer
        return msg.content or "(No response text.)"

    return "Planner stopped after too many tool calls. Try a more specific request (e.g., 'museum + coffee + scenic walk')."


# ---------- Streamlit UI ----------
def main():
    load_dotenv()

    st.set_page_config(page_title="Day Trip Planner (OpenAI + Foursquare)", layout="wide")
    st.title("Day Trip Planner (Chat + Foursquare)")

    # Basic key checks (don’t print secrets)
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Missing OPENAI_API_KEY in environment/.env")
        st.stop()
    if not os.getenv("FOURSQUARE_API_KEY"):
        st.error("Missing FOURSQUARE_API_KEY in environment/.env")
        st.stop()

    with st.sidebar:
        st.header("Trip settings")
        ll = st.text_input("Search center (lat,lon)", value=DEFAULT_LL)
        radius = st.slider("Search radius (m)", 500, 20000, 5000, step=500)
        budget = st.number_input("Budget (EUR)", min_value=0.0, value=40.0, step=5.0)

        st.header("Model")
        if "model" not in st.session_state:
            st.session_state.model = "gpt-5-nano-2025-08-07"
        st.session_state.model = st.text_input("OpenAI model", value=st.session_state.model)

        st.caption("Tip: Ask for a style (relaxed/packed), interests, and dietary needs.")

    # Chat state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Tell me your interests (e.g., nature, cafés, museums) and any constraints (time window, kids, mobility).",
            }
        ]

    # Render chat history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Input
    prompt = st.chat_input("What kind of day trip do you want?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Planning with real places..."):
                # Pass only user+assistant turns (excluding tool outputs) into the planner
                planner_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                    if m["role"] in ("user", "assistant")
                ]
                answer = run_planner(planner_messages, ll=ll, radius=radius, budget_eur=budget)
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
