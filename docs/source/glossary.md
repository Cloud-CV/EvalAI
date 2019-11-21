## Glossary

### Challenge

An event, run by an institute or organization, wherein a number of researchers, students, and data scientists participate and compete with each other over a period of time. Each challenge has a start time and generally an end time too.

### Challenge host

A member of the host team who organizes a challenge. In our system, it is a form of representing a user. This user can be in the organizing team of many challenges, and hence for each challenge, its challenge host will be different.

### Challenge host team

A group of challenge hosts who organizes a challenge. They are identified by a unique team name.

### Challenge phase

A challenge phase represents a distinct stage of the challenge. Over a period of time, challenge organizers have started to use the challenge phase as a way to:

1.  Decide when to evaluate submissions on a subset of the test-set or when to evaluate on the whole test-set (for e.g, [VQA Challenge 2019](https://evalai.cloudcv.org/web/challenges/challenge-page/163/overview))
2.  Use different challenge phases as different tracks of the same challenge (for e.g., [CARLA Autonomous Driving Challenge](https://evalai.cloudcv.org/web/challenges/challenge-page/246/phases))

### Challenge phase split

A challenge phase split is the relation between a challenge phase and dataset splits for a challenge with a many-to-many relation. This is used to set the privacy of submissions (public/private) to different dataset splits for different challenge phases.

### Dataset

A dataset in EvalAI is the main entity in which an AI challenge is based on. Participants are expected to make submissions corresponding to different splits of the corresponding dataset.

### Dataset split

A dataset is generally divided into different parts called dataset split. Generally, a dataset has three different splits:

- Training set
- Validation set
- Test set

### EvalAI

EvalAI is an open-source web platform that aims to be the state of the art in AI. Its goal is to help AI researchers, practitioners, and students to host, collaborate, and participate in AI challenges organized around the globe.

### Leaderboard

The leaderboard can be defined as a scoreboard listing the names of the teams along with their current scores. Currently, each challenge has its own leaderboard.

### Phase

A challenge can be divided into many phases (or challenge phases). A challenge phase can have the same or different start and end date than the challenge start and end date.

### Participant

A member of the team competing against other teams for any particular challenge. It is a form of representing a user. A user can participate in many challenges, hence for each challenge, its participant entry will be different.

### Participant team

A group of one or more participants who are taking part in a challenge. They are identified uniquely by a team name.

### Submission

A way of submitting your results to the platform, so that it can be evaluated and ranked amongst others. A submission can be public or private, depending on the challenge.

### Submission worker

A python script which processes submission messages received from a queue. It does the heavy lifting task of receiving a submission, performing mandatory checks, and then evaluating the submission and updating its status in the database.

### Team

A model, present in `web` app, which helps CloudCV register new contributors as a core team member or simply an open source contributor.

### Test annotation file

This is generally a file uploaded by a challenge host and is associated with a challenge phase. This file is used for ranking the submission made by a participant. An annotation file can be shared by more than one challenge phase. In the codebase, this is present as a file field attached to challenge phase model.
