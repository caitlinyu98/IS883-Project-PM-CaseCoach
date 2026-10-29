def show_report(res):
    report = res["report"]
    with st.chat_message("assistant"):
        st.subheader("Your feedback report")
        score = report.get("overall_score")
        if score is not None:
            st.metric("Overall score", f"{score} / 5")
        st.write(report["overall_summary"])
        if report["strengths"]:
            st.markdown("**Strengths**")
            for s in report["strengths"]:
                st.markdown(f"- {s}")
        st.markdown("**What to work on**")
        if not report["weaknesses"]:
            st.markdown("- None flagged.")
        for w in report["weaknesses"]:
            st.markdown(f"- **{TAXONOMY[w['tag']]}**: {w['evidence']}  \n  Fix: {w['fix']}")
        if report["next_steps"]:
            st.markdown("**Next steps**")
            for s in report["next_steps"]:
                st.markdown(f"- {s}")
        if res["meta"].get("retrieval_failed"):
            st.caption("Note: rubric retrieval was unavailable, so this report used the base prompt only.")
