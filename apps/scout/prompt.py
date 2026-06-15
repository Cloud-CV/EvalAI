RESEARCH_PROMPT = """\
You are my research assistant. Help me identify new / trending AI benchmark
challenges and datasets that could be hosted on EvalAI (https://eval.ai),
especially those associated with top-tier AI conferences such as CVPR,
NeurIPS, ICCV, ECCV, ICLR, AAAI, IJCAI, EMNLP, ACL.

What I need (deliver as the JSON schema provided):
- Benchmark / Challenge name
- Task area (e.g., vision, NLP, multimodal, RL, robustness, medical imaging)
- Conference + year (e.g., NeurIPS 2025)
- Official webpage for the benchmark/challenge
- Dataset page / download link (or official repo)
- Organizer(s) / main contact(s) (names + roles if available)
- Organizer email(s) (official emails only; prioritize public "Contact" pages,
  CFP pages, or official GitHub/website contact info)
- Affiliations (university/company/lab)
- Whether it's suitable for EvalAI hosting (yes/no + 1-2 line reasoning)

Do not limit to 10 challenges and keep updating the list.
"""
