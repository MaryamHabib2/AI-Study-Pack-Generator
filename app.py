import streamlit as st
from workflow import generate_study_pack

st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 AI Study Pack Generator")
st.caption("A 3-stage personalized AI workflow: Plan → Assess → Refine")

with st.sidebar:
    st.header("📚 Study Preferences")

    topic = st.text_input(
        "Topic *",
        placeholder="e.g. Python Loops",
    )

    level = st.selectbox(
        "Learning Level",
        ["Beginner", "Intermediate", "Advanced"],
    )

    goals = st.text_area(
        "Learning Goals",
        placeholder="What do you want to understand or be able to do?",
    )

    study_time = st.text_input(
        "Available Study Time",
        placeholder="e.g. 45 minutes",
    )

    preferences = st.text_area(
        "Learning Preferences",
        placeholder="e.g. simple explanations, examples, visual analogies",
    )

    generate = st.button(
        "🚀 Generate Study Pack",
        type="primary",
        use_container_width=True,
    )

if generate:
    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()

    with st.status("Running the 3-stage AI workflow...", expanded=True) as status:
        st.write("🧠 Stage 1 — Planning & Content Generation")
        result = generate_study_pack(
            topic=topic,
            level=level,
            goals=goals,
            study_time=study_time,
            preferences=preferences,
        )

        if result["status"] == "failed":
            status.update(
                label=f"Workflow failed at {result['failed_stage']}",
                state="error",
            )
            st.error(result["error"])
            st.stop()

        st.write("📝 Stage 2 — Assessment & Quality Review")
        st.write("♻️ Stage 3 — Refinement & Final Study Pack")

        status.update(
            label="Study pack generated successfully!",
            state="complete",
        )

    final_pack = result["final_pack"]
    review = result["stages"]["stage_2"]["review"]

    st.success("Your personalized study pack is ready!")

    c1, c2, c3 = st.columns(3)
    c1.metric("AI Review Score", f"{review.get('score', 0)}/100")
    c2.metric("Workflow Stages", "3")
    c3.metric("Quality Status", review.get("overall_status", "N/A"))

    st.markdown(f"# {final_pack.get('title', 'Personalized Study Pack')}")

    st.subheader("🎯 Learning Objectives")
    for item in final_pack.get("learning_objectives", []):
        st.markdown(f"- {item}")

    st.subheader("📖 Study Notes")
    notes = final_pack.get("study_notes", [])
    if isinstance(notes, str):
        st.markdown(notes)
    else:
        for note in notes:
            st.markdown(f"- {note}")

    st.subheader("💡 Worked Examples")
    for example in final_pack.get("worked_examples", []):
        st.markdown(f"- {example}")

    st.subheader("📝 Practice Questions")
    for i, question in enumerate(final_pack.get("practice_questions", []), 1):
        if isinstance(question, dict):
            st.markdown(f"**{i}. {question.get('question', '')}**")
            for option in question.get("options", []):
                st.markdown(f"- {option}")
        else:
            st.markdown(f"**{i}. {question}**")

    st.subheader("✅ Answer Key")
    for answer in final_pack.get("answer_key", []):
        st.markdown(f"- {answer}")

    st.subheader("🔄 Revision Plan")
    for item in final_pack.get("revision_plan", []):
        st.markdown(f"- {item}")

    st.subheader("🔍 AI Quality Review")
    st.write(f"**Score:** {review.get('score', 'N/A')}/100")
    st.write(f"**Status:** {review.get('overall_status', 'N/A')}")

    if review.get("issues"):
        with st.expander("Review findings"):
            for issue in review["issues"]:
                st.markdown(f"- {issue}")

    st.download_button(
        "⬇️ Download Study Pack",
        data=result["markdown"],
        file_name="personalized_study_pack.md",
        mime="text/markdown",
        use_container_width=True,
    )

    with st.expander("🔧 View Workflow Context"):
        st.json(result)
else:
    st.info(
        "Enter your study requirements in the sidebar and click "
        "**Generate Study Pack**."
    )
