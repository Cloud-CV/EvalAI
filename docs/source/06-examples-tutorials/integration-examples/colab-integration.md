# Google Colab Integration

Colab is useful for GPU prototyping before submitting to EvalAI.

## Workflow

1. Mount Drive or download challenge data per host instructions.
2. Train or run inference in Colab.
3. Export predictions to the required submission format.
4. Download the result file to your machine or upload directly:
   - **CLI:** `evalai challenge ... submit` from a machine with the file
   - **Browser:** EvalAI **Submit** tab

## Authentication in Colab

Store your EvalAI token securely (Colab secrets, not in a public notebook):

```python
import os
os.environ["EVALAI_API_TOKEN"] = "<token>"
```

Prefer running CLI commands from your local environment if the notebook is shared publicly.

## See also

- [Jupyter notebook integration](jupyter-notebook.html)
- [EvalAI CLI](https://cli.eval.ai/)
