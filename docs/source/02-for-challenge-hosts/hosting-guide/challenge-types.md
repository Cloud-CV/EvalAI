# Challenge Types

We categorize the challenges in two categories:

1. **Prediction upload based challenges**: Participants upload predictions corresponding to ground truth labels in the form of a file (could be any format: `json`, `npy`, `csv`, `txt` etc.)

   Some of the popular prediction upload based challenges that we have hosted are shown below:

   <a href="https://eval.ai/web/challenges/list" target="_blank"><img src="../../_static/img/prediction-upload-challenges.png"></a><br />

   If you are interested in hosting prediction upload based challenges, then <a href="./host-challenge.html#host-prediction-upload-based-challenge">click here</a>.

   <br />

2. **Code-upload based challenges**: In these kind of challenges, participants upload their training code in the form of docker images using [EvalAI-CLI](https://github.com/Cloud-CV/evalai-cli/).

   We support two types of code-upload based challenges -
      - Code-Upload Based Challenge (without Static Dataset): These are usually reinforcement learning challenges which involve uploading a trained model in form of docker images and the environment is also saved in form of a docker image.
      - Static Code-Upload Based Challenge: These are challenges where the host might want the participants to upload models and they have static dataset on which they want to run the models and perform evaluations. This kind of challenge is especially useful in case of data privacy concerns.

   Some of the popular code-upload based challenges that we have hosted are shown below:

   <a href="https://eval.ai/web/challenges/list" target="_blank"><img src="../../_static/img/code-upload-challenges.png"></a>

   If you are interested in hosting code-upload based challenges, then <a href="./host_challenge.html#host-code-upload-based-challenge">click here</a>. If you are interested in hosting static code-upload based challenges, then <a href="./host_challenge.html#host-static-code-upload-based-challenge">click here</a>.

   A good reference would be the [Habitat Re-arrangement Challenge 2022](https://github.com/facebookresearch/habitat-challenge/tree/rearrangement-challenge-2022).