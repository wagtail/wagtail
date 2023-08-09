# Writing documentation

Wagtail documentation is written in **four modes** of information delivery.
Each type of information delivery has a purpose and targets a specific audience.

-   [](doc_mode_tutorial), learning-oriented
-   [](doc_mode_how_to_guide), goal-oriented
-   [](doc_mode_reference), information-oriented
-   [](doc_mode_explanation), understanding-oriented

We are following Daniele Procida's [Diátaxis documentation framework](https://diataxis.fr/).

(choose_a_writing_mode)=

## Choose a writing mode

Each page of the Wagtail documentation should be written in a single mode of information delivery.
Single pages with mixed modes are harder to understand.
If you have documents that mix the types of information delivery,
it’s best to split them up. Add links to the first section of each document to cross-reference other documents on the same topic.

Writing documentation in a specific mode will help our users to understand and quickly find what they are looking for.

(doc_mode_tutorial)=

## Tutorial

Tutorials are designed to be **learning-oriented** resources that guide newcomers through a specific topic. To help effective learning, tutorials should provide examples to illustrate the subjects they cover.

Tutorials may not necessarily follow best practices. They are designed to make it easier to get started. A tutorial is concrete and particular. It must be repeatable, instil confidence, and should result in success, every time, for every learner.

### Do

-   Use conversational language
-   Use contractions, speak in the first person plural, and be reassuring. For example: “We’re going to do this.”
-   Use pictures or concrete outputs of code to reassure people that they’re on the right track.
    For example: “Your new login page should look like this:” or “Your directory should now have three files”.

### Don’t

-   Tell people what they’re going to learn.
    Instead, tell them what tasks they’re going to complete.
-   Use optionality in a tutorial. The word ‘if’ is a sign of danger!
    For example: “If you want to do this…”
    The expected actions and outcomes should be unambiguous.
-   Assume that learners have a prior understanding of the subject.

[More about tutorials](https://diataxis.fr/tutorials/)

(doc_mode_how_to_guide)=

## How-to guide

A guide offers advice on how best to achieve a given task.
How-to guides are **task-oriented** with a clear **goal or objective**.

### Do

-   Name the guide well - ensure that the learner understands what exactly the guide does.
-   Focus on actions and outcomes. For example: “If you do X, Y should happen.”
-   Assume that the learner has a basic understanding of the general concepts
-   Point the reader to additional resources

### Don’t

-   Use an unnecessarily strict tone of voice. For example: “You must absolutely NOT do X.”

[More about how-to guides](https://diataxis.fr/how-to-guides/)

(doc_mode_reference)=

## Reference

Reference material is **information-oriented**.
A reference is well-structured and allows the reader to find information about a specific topic.
They should be short and to the point. Boring is fine! Use an imperative voice.
For example: “Inherit from the Page model”.

Most references will be auto-generated based on doc-strings in the Python code.

[More about reference](https://diataxis.fr/reference/)

(doc_mode_explanation)=

## Explanation

Explanations are **understanding-oriented**.
They are high-level and offer context to concepts and design decisions.
There is little or no code involved in explanations,
which are used to deepen the theoretical understanding of a practical draft.
Explanations are used to establish connections and may require some prior knowledge of the principles being explored.

[More about explanation](https://diataxis.fr/explanation/)
